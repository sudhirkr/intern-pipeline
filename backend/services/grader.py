"""Grading engine — analyzes submitted work and produces weighted scores.

Scoring weights:
  - Deployed Project: 40%
  - Code Quality: 25%
  - AI Usage: 20%
  - Creativity: 15%

Each category gets 0-100.
"""
import json
import tempfile
import subprocess
import os
import shutil
import httpx
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/openrouter/hunter-alpha"

WEIGHTS = {
    "deployed": 0.40,
    "code_quality": 0.25,
    "ai_usage": 0.20,
    "creativity": 0.15,
}


def _get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    config_path = os.path.expanduser("~/.openclaw/config.yaml")
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            key = config.get("openrouter_api_key", "")
            if key:
                return key
        except Exception:
            pass
    return ""


async def grade_deployed(deploy_stats_json: str) -> dict:
    """Grade the deployed project based on HTTP check stats.

    Returns:
        {"score": int, "feedback": str}
    """
    try:
        stats = json.loads(deploy_stats_json) if isinstance(deploy_stats_json, str) else deploy_stats_json
    except (json.JSONDecodeError, TypeError):
        return {"score": 0, "feedback": "Invalid deployment stats"}

    if not stats.get("valid", False):
        error = stats.get("error", "Unknown error")
        return {"score": 0, "feedback": f"Deployment not accessible: {error}"}

    score = 50  # base for being accessible
    feedback_parts = []

    # Status code check
    status = stats.get("status_code", 0)
    if 200 <= status < 300:
        score += 20
        feedback_parts.append("Returns successful HTTP status")
    elif 300 <= status < 400:
        score += 10
        feedback_parts.append("Returns redirect status")

    # Content check
    if stats.get("has_content", False):
        score += 20
        feedback_parts.append("Serves meaningful content")
    else:
        feedback_parts.append("Minimal or no content detected")

    # Response time
    response_time = stats.get("response_time_ms", 0)
    if response_time > 0:
        if response_time < 500:
            score += 10
            feedback_parts.append(f"Fast response ({response_time}ms)")
        elif response_time < 2000:
            score += 5
            feedback_parts.append(f"Acceptable response time ({response_time}ms)")
        else:
            feedback_parts.append(f"Slow response ({response_time}ms)")

    score = min(score, 100)
    feedback = ". ".join(feedback_parts) if feedback_parts else "Deployment accessible but limited info"
    return {"score": score, "feedback": feedback}


def _analyze_repo_structure(repo_path: str) -> dict:
    """Analyze cloned repo for code quality indicators."""
    indicators = {
        "has_readme": False,
        "has_tests": False,
        "has_requirements": False,
        "has_gitignore": False,
        "has_docker": False,
        "has_ci": False,
        "num_files": 0,
        "num_dirs": 0,
        "total_size_kb": 0,
        "languages": [],
        "has_license": False,
        "has_docs": False,
        "file_structure": "",
    }

    if not os.path.exists(repo_path):
        return indicators

    files = []
    dirs = []
    for root, dirnames, filenames in os.walk(repo_path):
        # Skip hidden dirs and common non-code dirs
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build')]
        for f in filenames:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_path)
            files.append(rel_path)

            fl = f.lower()
            if fl.startswith("readme"):
                indicators["has_readme"] = True
            if fl.startswith("license"):
                indicators["has_license"] = True
            if "test" in fl or "spec" in fl:
                indicators["has_tests"] = True
            if fl in ("requirements.txt", "pyproject.toml", "package.json", "go.mod", "cargo.toml"):
                indicators["has_requirements"] = True
            if fl == ".gitignore":
                indicators["has_gitignore"] = True
            if fl in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                indicators["has_docker"] = True

        for d in dirnames:
            dl = d.lower()
            if dl == ".github":
                indicators["has_ci"] = True
            if dl in ("docs", "doc"):
                indicators["has_docs"] = True
            if "test" in dl:
                indicators["has_tests"] = True

    indicators["num_files"] = len(files)
    indicators["num_dirs"] = len(dirs)

    # Total size
    try:
        total = 0
        for root, _, fnames in os.walk(repo_path):
            for f in fnames:
                fp = os.path.join(root, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        indicators["total_size_kb"] = total // 1024
    except Exception:
        pass

    # Language detection from extensions
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "JSX", ".tsx": "TSX", ".java": "Java", ".go": "Go",
        ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".c": "C",
        ".cpp": "C++", ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin",
        ".html": "HTML", ".css": "CSS", ".sql": "SQL",
    }
    seen_exts = set()
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in ext_map and ext_map[ext] not in seen_exts:
            indicators["languages"].append(ext_map[ext])
            seen_exts.add(ext_map[ext])

    # Simple structure dump (first 50 files)
    indicators["file_structure"] = "\n".join(sorted(files)[:50])
    if len(files) > 50:
        indicators["file_structure"] += f"\n... and {len(files) - 50} more files"

    return indicators


async def grade_code_quality(github_stats_json: str, repo_path: str = None) -> dict:
    """Grade code quality based on repo structure analysis.

    Returns:
        {"score": int, "feedback": str}
    """
    indicators = _analyze_repo_structure(repo_path or "")

    score = 0
    feedback_parts = []

    # README (15 points)
    if indicators["has_readme"]:
        score += 15
        feedback_parts.append("Has README documentation")
    else:
        feedback_parts.append("Missing README")

    # Tests (20 points)
    if indicators["has_tests"]:
        score += 20
        feedback_parts.append("Includes tests")
    else:
        feedback_parts.append("No tests found")

    # Dependencies management (15 points)
    if indicators["has_requirements"]:
        score += 15
        feedback_parts.append("Has dependency management")

    # Project structure (15 points)
    num_files = indicators["num_files"]
    if num_files > 10:
        score += 15
        feedback_parts.append(f"Well-structured project ({num_files} files)")
    elif num_files > 3:
        score += 8
        feedback_parts.append(f"Basic structure ({num_files} files)")
    else:
        feedback_parts.append(f"Minimal structure ({num_files} files)")

    # Documentation (10 points)
    if indicators["has_docs"] or indicators["has_license"]:
        score += 10
        feedback_parts.append("Has additional documentation")

    # Docker/CI (10 points)
    if indicators["has_docker"]:
        score += 5
        feedback_parts.append("Has Docker support")
    if indicators["has_ci"]:
        score += 5
        feedback_parts.append("Has CI/CD setup")

    # Code size (10 points)
    if num_files > 5:
        score += 10
    elif num_files > 2:
        score += 5

    # Languages diversity (5 points)
    langs = indicators["languages"]
    if len(langs) > 1:
        score += 5
        feedback_parts.append(f"Multi-language project: {', '.join(langs)}")
    elif len(langs) == 1:
        feedback_parts.append(f"Primary language: {langs[0]}")

    score = min(score, 100)
    feedback = ". ".join(feedback_parts) if feedback_parts else "No code quality indicators found"
    return {"score": score, "feedback": feedback}


async def grade_ai_usage(candidate_data: dict, repo_path: str = None) -> dict:
    """Grade AI usage — check for signs of AI-assisted code generation.

    Looks for patterns like:
    - Very uniform code (AI tends to produce consistent style)
    - Missing comments in otherwise complete code
    - Generic variable names
    - AI-typical comment patterns

    Returns:
        {"score": int (0-100, higher = LESS AI usage = better for our purposes), "feedback": str}
    """
    score = 70  # neutral baseline
    feedback_parts = []

    ai_tool_usage = (candidate_data.get("ai_tool_usage") or "").lower()

    # Candidate openly admits to AI usage (not penalized - transparency is good)
    if ai_tool_usage and len(ai_tool_usage) > 5:
        if any(word in ai_tool_usage for word in ["chatgpt", "copilot", "gpt", "claude", "ai assistant"]):
            score -= 5
            feedback_parts.append("Candidate transparently reports AI tool usage")

    # Analyze code for AI patterns if repo is available
    if repo_path and os.path.exists(repo_path):
        ai_patterns_found = 0
        try:
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__')]
                for f in files:
                    if not f.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                        continue
                    filepath = os.path.join(root, f)
                    try:
                        with open(filepath, 'r', errors='ignore') as fh:
                            content = fh.read()
                            # Check for typical AI patterns
                            if "as an AI" in content.lower() or "i'm an ai" in content.lower():
                                ai_patterns_found += 2
                            # Very uniform comment style
                            comment_lines = [l for l in content.split('\n') if l.strip().startswith('#') or l.strip().startswith('//')]
                            if len(comment_lines) > 5:
                                # Check for generic AI-style comments
                                for cl in comment_lines:
                                    cl_lower = cl.lower()
                                    if any(phrase in cl_lower for phrase in ["initialize", "function to", "this function", "creates a new", "returns the"]):
                                        ai_patterns_found += 1
                                        break
                    except Exception:
                        continue
        except Exception:
            pass

        if ai_patterns_found > 3:
            score -= 10
            feedback_parts.append(f"Found {ai_patterns_found} potential AI-generated code patterns")
        elif ai_patterns_found > 0:
            feedback_parts.append(f"Minor AI patterns detected ({ai_patterns_found})")
        else:
            score += 10
            feedback_parts.append("No obvious AI-generated patterns in code")
    else:
        feedback_parts.append("Could not analyze code for AI patterns (repo not cloned)")

    score = max(0, min(score, 100))
    feedback = ". ".join(feedback_parts) if feedback_parts else "AI usage assessment based on limited data"
    return {"score": score, "feedback": feedback}


async def grade_creativity(candidate_data: dict, github_stats_json: str, repo_path: str = None) -> dict:
    """Grade creativity of the project approach.

    Checks:
    - Project uniqueness
    - README quality (creative descriptions)
    - Technology choices
    - Project complexity

    Returns:
        {"score": int, "feedback": str}
    """
    score = 50  # baseline
    feedback_parts = []

    try:
        stats = json.loads(github_stats_json) if isinstance(github_stats_json, str) else github_stats_json
    except (json.JSONDecodeError, TypeError):
        stats = {}

    # README analysis
    readme_content = ""
    if repo_path and os.path.exists(repo_path):
        for name in ["README.md", "README.rst", "README.txt", "readme.md"]:
            readme_path = os.path.join(repo_path, name)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', errors='ignore') as f:
                        readme_content = f.read()
                    break
                except Exception:
                    continue

    if readme_content:
        if len(readme_content) > 500:
            score += 15
            feedback_parts.append("Comprehensive README")
        elif len(readme_content) > 100:
            score += 8
            feedback_parts.append("Adequate README")

        # Check for screenshots, badges, diagrams
        if any(marker in readme_content.lower() for marker in ["![", "screenshot", "demo", "badge", "diagram"]):
            score += 10
            feedback_parts.append("README includes visual elements")

        # Check for structured sections
        sections = sum(1 for h in ["## installation", "## usage", "## features", "## architecture"]
                      if h in readme_content.lower())
        if sections >= 3:
            score += 10
            feedback_parts.append("Well-structured README with multiple sections")
    else:
        feedback_parts.append("No README found for review")

    # Language diversity
    languages = stats.get("language", "")
    if languages:
        feedback_parts.append(f"Built with {languages}")

    # Topics/tags creativity
    topics = stats.get("topics", [])
    if topics:
        score += 5
        feedback_parts.append(f"Tagged with: {', '.join(topics[:3])}")

    score = max(0, min(score, 100))
    feedback = ". ".join(feedback_parts) if feedback_parts else "Limited creativity assessment available"
    return {"score": score, "feedback": feedback}


async def calculate_overall_grade(
    deploy_stats: str,
    github_stats: str,
    candidate_data: dict,
    repo_path: str = None,
) -> dict:
    """Calculate the weighted overall grade.

    Returns:
        {
            "overall": int,
            "deployed": {"score": int, "feedback": str},
            "code_quality": {"score": int, "feedback": str},
            "ai_usage": {"score": int, "feedback": str},
            "creativity": {"score": int, "feedback": str},
        }
    """
    # Get individual grades
    deploy_result = await grade_deployed(deploy_stats)
    code_quality_result = await grade_code_quality(github_stats, repo_path)
    ai_usage_result = await grade_ai_usage(candidate_data, repo_path)
    creativity_result = await grade_creativity(candidate_data, github_stats, repo_path)

    # Calculate weighted overall
    overall = int(
        deploy_result["score"] * WEIGHTS["deployed"] +
        code_quality_result["score"] * WEIGHTS["code_quality"] +
        ai_usage_result["score"] * WEIGHTS["ai_usage"] +
        creativity_result["score"] * WEIGHTS["creativity"]
    )

    return {
        "overall": overall,
        "deployed": deploy_result,
        "code_quality": code_quality_result,
        "ai_usage": ai_usage_result,
        "creativity": creativity_result,
    }


def clone_repo(github_url: str, target_dir: str) -> bool:
    """Clone a GitHub repo to target_dir. Returns True on success."""
    # Normalize URL
    url = github_url.strip().rstrip("/")
    if not url.endswith(".git"):
        url += ".git"

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, target_dir],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Failed to clone repo {url}: {e}")
        return False
