"""
Resume parser service — extracts structured data from PDF/DOCX resumes.
Uses LLM (OpenRouter) for intelligent extraction, with regex fallback.
"""
import hashlib
import json
import os
import re
import tempfile
from typing import Optional
from pathlib import Path


def compute_resume_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file bytes for cache invalidation."""
    return hashlib.sha256(file_bytes).hexdigest()


# ── Text extraction from files ──

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    import pdfplumber
    import io

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    from docx import Document
    import io

    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from uploaded file based on extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF or DOCX.")


# ── LLM-based extraction ──

LLM_PROMPT = """You are a resume parser. Extract structured data from the resume text below.

Respond with ONLY valid JSON — no markdown, no explanation.

Required JSON format:
{{
  "name": "Full name or null",
  "email": "email@example.com or null",
  "phone": "phone number or null",
  "college": "University/college name or null",
  "degree": "Degree (e.g., B.Tech, MSc, MBA) or null",
  "year": "Current year of study (e.g., 3rd, Final) or null",
  "skills": "Comma-separated technical skills or null",
  "projects": "Brief project descriptions or null",
  "work_experience": "Work experience summary or null"
}}

Rules:
- Extract ONLY what is explicitly stated. Do not infer or fabricate.
- For skills: list individual technical skills (languages, frameworks, tools), NOT soft skills.
- For projects: include project name and brief tech description.
- For work experience: include company, role, and duration if available.
- If a field is not found, use null (not "N/A" or "Not provided").
- name should be the person's actual name, not section headers or other text.

Resume Text:
{resume_text}
"""


def _get_api_key() -> str:
    """Get OpenRouter API key from environment."""
    return os.environ.get("OPENROUTER_API_KEY", "")


async def parse_resume_with_llm(text: str) -> dict:
    """Use LLM to extract structured data from resume text."""
    import httpx

    api_key = _get_api_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    prompt = LLM_PROMPT.format(resume_text=text[:4000])  # Truncate to avoid token limits

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openrouter/auto",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1500,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_text
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].strip()

    result = json.loads(raw_text)

    # Validate and clean
    fields = ["name", "email", "phone", "college", "degree", "year", "skills", "projects", "work_experience"]
    for f in fields:
        if f not in result:
            result[f] = None
        # Convert empty strings to None
        if result[f] == "" or result[f] == "N/A" or result[f] == "Not provided":
            result[f] = None

    return result


# ── Regex fallback (original logic) ──

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"[\+]?[\d\-\s\(\)]{8,15}")
DEGREE_PATTERN = re.compile(
    r"(B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|B\.?E|M\.?E|B\.?A|M\.?A|"
    r"B\.?Com|M\.?Com|BCA|MCA|MBA|PhD|BBA|LLB|MBBS)",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(
    r"((?:1st|2nd|3rd|4th|5th|first|second|third|fourth|final)\s+year)",
    re.IGNORECASE,
)

SKILLS_SECTION = re.compile(r"^(?:technical\s+)?skills|proficienc|technolog", re.IGNORECASE | re.MULTILINE)
PROJECTS_SECTION = re.compile(r"^projects?|academic\s+projects?", re.IGNORECASE | re.MULTILINE)
EXPERIENCE_SECTION = re.compile(r"(?:work\s+)?experience|employment|internship", re.IGNORECASE | re.MULTILINE)
EDUCATION_SECTION = re.compile(r"^education|academic\s+background|qualification", re.IGNORECASE | re.MULTILINE)


def _extract_section(text: str, start_pattern: re.Pattern, next_patterns: list[re.Pattern]) -> str:
    """Extract text between a section header and the next section."""
    start_match = start_pattern.search(text)
    if not start_match:
        return ""

    start_pos = start_match.start()
    end_pos = len(text)
    for pattern in next_patterns:
        for match in pattern.finditer(text[start_pos + 1:]):
            candidate = start_pos + 1 + match.start()
            if candidate < end_pos:
                end_pos = candidate

    section_text = text[start_pos:end_pos].strip()
    lines = section_text.split("\n")
    if lines:
        lines = lines[1:]
    return "\n".join(lines).strip()


def _extract_name(text: str) -> Optional[str]:
    """Try to extract the candidate's name from the first few lines."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return None
    for line in lines[:5]:
        if EMAIL_PATTERN.search(line):
            continue
        if PHONE_PATTERN.search(line) and len(line) < 20:
            continue
        if any(kw in line.lower() for kw in ["resume", "cv", "curriculum", "profile", "objective", "summary"]):
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and all(w.replace(".", "").isalpha() for w in words):
            return line
    return None


def _extract_college(text: str) -> Optional[str]:
    """Try to extract college/university name."""
    college_keywords = [
        "university", "institute", "college", "iit", "iim", "nit", "bits",
        "school of", "academy", "vidyalaya",
    ]
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in college_keywords):
            college = line.strip()
            if len(college) < 200:
                return college
    return None


def parse_resume_text_regex(text: str) -> dict:
    """Parse resume text using regex patterns (fallback when LLM unavailable)."""
    result = {
        "name": None,
        "email": None,
        "phone": None,
        "college": None,
        "degree": None,
        "year": None,
        "skills": None,
        "projects": None,
        "work_experience": None,
    }

    email_match = EMAIL_PATTERN.search(text)
    if email_match:
        result["email"] = email_match.group(0).lower()

    phone_match = PHONE_PATTERN.search(text)
    if phone_match:
        result["phone"] = phone_match.group(0).strip()

    result["name"] = _extract_name(text)

    degree_match = DEGREE_PATTERN.search(text)
    if degree_match:
        result["degree"] = degree_match.group(0)

    year_match = YEAR_PATTERN.search(text)
    if year_match:
        result["year"] = year_match.group(0).title()

    result["college"] = _extract_college(text)

    all_sections = [SKILLS_SECTION, PROJECTS_SECTION, EXPERIENCE_SECTION, EDUCATION_SECTION]

    skills_text = _extract_section(text, SKILLS_SECTION, all_sections)
    if skills_text:
        skills = []
        for line in skills_text.split("\n"):
            line = line.strip().rstrip(",").strip()
            if line and len(line) < 100:
                line = re.sub(r"^[\•\-\*\·\▸\▹\◦\▪\‣]\s*", "", line)
                if line:
                    skills.append(line)
        result["skills"] = ", ".join(skills[:20]) if skills else None

    projects_text = _extract_section(text, PROJECTS_SECTION, all_sections)
    if projects_text:
        result["projects"] = projects_text[:1000] if projects_text else None

    exp_text = _extract_section(text, EXPERIENCE_SECTION, all_sections)
    if exp_text:
        result["work_experience"] = exp_text[:1000] if exp_text else None

    return result


# ── Public API ──

async def parse_resume_file(file_bytes: bytes, filename: str) -> dict:
    """Parse a resume file — tries LLM first, falls back to regex."""
    text = extract_text(file_bytes, filename)

    # Try LLM first
    api_key = _get_api_key()
    if api_key:
        try:
            return await parse_resume_with_llm(text)
        except Exception:
            # Fall through to regex
            pass

    return parse_resume_text_regex(text)


async def parse_resume_from_url(url: str) -> dict:
    """Download a resume from URL and parse it."""
    import httpx
    import urllib.parse

    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    parsed = urllib.parse.urlparse(url)
    filename = Path(parsed.path).name or "resume.pdf"
    if not Path(filename).suffix:
        ct = resp.headers.get("content-type", "")
        if "pdf" in ct:
            filename = "resume.pdf"
        else:
            filename = "resume.pdf"

    return await parse_resume_file(resp.content, filename)
