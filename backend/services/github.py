"""GitHub repository checker — validates repos and extracts basic stats."""
import re
import httpx
import logging

logger = logging.getLogger(__name__)

# GitHub API base
GITHUB_API = "https://api.github.com"


def _normalize_github_url(url: str) -> str:
    """Normalize various GitHub URL formats to owner/repo."""
    url = url.strip().rstrip("/")
    # Handle common URL patterns
    patterns = [
        r"github\.com/([^/]+/[^/]+)",
        r"github\.com/([^/]+/[^/]+)\.git",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1).replace(".git", "")
    # If it's already in owner/repo format
    if re.match(r"^[^/]+/[^/]+$", url):
        return url
    return url


async def check_github_repo(url: str) -> dict:
    """Check if a GitHub repo exists and is accessible. Returns stats dict.

    Returns:
        {
            "valid": bool,
            "owner_repo": str,
            "stars": int,
            "language": str,
            "description": str,
            "size_kb": int,
            "is_public": bool,
            "topics": list[str],
            "error": str | None
        }
    """
    owner_repo = _normalize_github_url(url)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get repo info from GitHub API
            resp = await client.get(f"{GITHUB_API}/repos/{owner_repo}")

            if resp.status_code == 404:
                return {
                    "valid": False,
                    "owner_repo": owner_repo,
                    "stars": 0,
                    "language": "",
                    "description": "",
                    "size_kb": 0,
                    "is_public": False,
                    "topics": [],
                    "error": "Repository not found or is private",
                }

            if resp.status_code == 403:
                # Rate limited or forbidden
                return {
                    "valid": False,
                    "owner_repo": owner_repo,
                    "stars": 0,
                    "language": "",
                    "description": "",
                    "size_kb": 0,
                    "is_public": False,
                    "topics": [],
                    "error": "GitHub API rate limited or access forbidden",
                }

            if resp.status_code != 200:
                return {
                    "valid": False,
                    "owner_repo": owner_repo,
                    "stars": 0,
                    "language": "",
                    "description": "",
                    "size_kb": 0,
                    "is_public": False,
                    "topics": [],
                    "error": f"GitHub API returned status {resp.status_code}",
                }

            data = resp.json()

            return {
                "valid": True,
                "owner_repo": owner_repo,
                "stars": data.get("stargazers_count", 0),
                "language": data.get("language", ""),
                "description": data.get("description", ""),
                "size_kb": data.get("size", 0),
                "is_public": not data.get("private", True),
                "topics": data.get("topics", []),
                "error": None,
            }

    except httpx.TimeoutException:
        return {
            "valid": False,
            "owner_repo": owner_repo,
            "stars": 0,
            "language": "",
            "description": "",
            "size_kb": 0,
            "is_public": False,
            "topics": [],
            "error": "Request to GitHub API timed out",
        }
    except Exception as e:
        logger.exception("GitHub check failed")
        return {
            "valid": False,
            "owner_repo": owner_repo,
            "stars": 0,
            "language": "",
            "description": "",
            "size_kb": 0,
            "is_public": False,
            "topics": [],
            "error": f"Unexpected error: {str(e)}",
        }
