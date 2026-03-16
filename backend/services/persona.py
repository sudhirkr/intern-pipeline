"""Persona generation service — calls OpenRouter API to analyze candidates."""
import json
import os
import httpx

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/hunter-alpha"

PERSONA_PROMPT = """You are an expert technical recruiter analyzing a candidate's application for an AI/ML internship program.

Given the candidate data below, generate a persona profile. Respond with ONLY valid JSON — no markdown, no explanation.

Required JSON format:
{{
  "skill_level": "Beginner" or "Intermediate" or "Advanced",
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2"],
  "learning_style": "project-based" or "classroom" or "self-taught",
  "assignment_fit": "A specific project type suggestion based on their profile",
  "risk_flags": ["flag1", "flag2"],
  "summary": "2-3 sentence overall assessment of the candidate"
}}

Rules:
- skill_level: Assess from skills, projects, experience. Beginner = mostly coursework, Intermediate = some real projects, Advanced = significant experience or complex projects.
- strengths: 2-4 specific strengths based on their profile.
- gaps: 1-3 areas for improvement.
- learning_style: Infer from their stated learning style and profile. Map: visual/reading → classroom, hands_on → project-based, mixed → self-taught.
- assignment_fit: Specific project type that matches their skills and interests.
- risk_flags: Any concerns (e.g., "limited experience", "no deployed projects", "vague motivation"). Empty array if none.
- summary: Concise, professional assessment.

Candidate Data:
- Name: {name}
- Email: {email}
- College: {college}
- Degree: {degree}
- Year: {year}
- Skills: {skills}
- Projects: {projects}
- Work Experience: {work_experience}
- Interests: {interests}
- Learning Style: {learning_style}
- Availability: {availability}
- Motivation: {motivation}
- Portfolio Links: {portfolio_links}
- Preferred Tech Stack: {preferred_tech_stack}
- AI Tool Usage: {ai_tool_usage}
- Challenge Solved: {challenge_solved}
"""


def _get_api_key() -> str:
    """Get OpenRouter API key from environment or OpenClaw config."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key

    # Try reading from OpenClaw config
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


def _build_prompt(candidate_data: dict) -> str:
    """Build the persona generation prompt from candidate data."""
    fields = [
        "name", "email", "college", "degree", "year", "skills", "projects",
        "work_experience", "interests", "learning_style", "availability",
        "motivation", "portfolio_links", "preferred_tech_stack",
        "ai_tool_usage", "challenge_solved",
    ]
    values = {}
    for f in fields:
        val = candidate_data.get(f)
        values[f] = val if val else "Not provided"
    return PERSONA_PROMPT.format(**values)


def _parse_persona_response(raw_text: str) -> dict:
    """Parse the LLM response into a persona dict. Handles JSON wrapped in markdown."""
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json ... ````)
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        persona = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        import re
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            persona = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse persona JSON from response: {text[:200]}")

    # Validate required fields
    required = ["skill_level", "strengths", "gaps", "learning_style", "assignment_fit", "risk_flags", "summary"]
    for field in required:
        if field not in persona:
            raise ValueError(f"Missing required field in persona: {field}")

    # Validate types
    if not isinstance(persona["strengths"], list):
        persona["strengths"] = [str(persona["strengths"])]
    if not isinstance(persona["gaps"], list):
        persona["gaps"] = [str(persona["gaps"])]
    if not isinstance(persona["risk_flags"], list):
        persona["risk_flags"] = [str(persona["risk_flags"])]

    # Validate enums
    valid_skill_levels = {"Beginner", "Intermediate", "Advanced"}
    if persona["skill_level"] not in valid_skill_levels:
        persona["skill_level"] = "Intermediate"

    valid_learning_styles = {"project-based", "classroom", "self-taught"}
    if persona["learning_style"] not in valid_learning_styles:
        persona["learning_style"] = "project-based"

    return persona


async def generate_persona(candidate_data: dict) -> dict:
    """Generate a persona profile for a candidate using the LLM.

    Args:
        candidate_data: dict with all candidate fields

    Returns:
        dict with persona fields (skill_level, strengths, gaps, etc.)

    Raises:
        ValueError: If API key is missing or response is invalid
        httpx.HTTPError: If the API call fails
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set. Set the environment variable or add it to OpenClaw config.")

    prompt = _build_prompt(candidate_data)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://intern-pipeline.local",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"]
    return _parse_persona_response(raw_text)


def candidate_to_dict(candidate) -> dict:
    """Convert a Candidate ORM object to a dict for persona generation."""
    return {
        "name": candidate.name,
        "email": candidate.email,
        "college": candidate.college,
        "degree": candidate.degree,
        "year": candidate.year,
        "skills": candidate.skills,
        "projects": candidate.projects,
        "work_experience": candidate.work_experience,
        "interests": candidate.interests,
        "learning_style": candidate.learning_style.value if candidate.learning_style else None,
        "availability": candidate.availability.value if candidate.availability else None,
        "motivation": candidate.motivation,
        "portfolio_links": candidate.portfolio_links,
        "preferred_tech_stack": candidate.preferred_tech_stack,
        "ai_tool_usage": candidate.ai_tool_usage,
        "challenge_solved": candidate.challenge_solved,
    }
