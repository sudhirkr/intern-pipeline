"""
Resume parser service — extracts structured data from PDF/DOCX resumes.
Uses pdfplumber for PDF and python-docx for DOCX.
"""
import re
import tempfile
from typing import Optional
from pathlib import Path


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


# ── Regex patterns for extraction ──

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"[\+]?[\d\-\s\(\)]{8,15}")

# Common degree patterns
DEGREE_PATTERN = re.compile(
    r"(B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|B\.?E|M\.?E|B\.?A|M\.?A|"
    r"B\.?Com|M\.?Com|BCA|MCA|MBA|PhD|BBA|LLB|MBBS)",
    re.IGNORECASE,
)

# Year patterns (1st/2nd/3rd/4th year, etc.)
YEAR_PATTERN = re.compile(
    r"((?:1st|2nd|3rd|4th|5th|first|second|third|fourth|final)\s+year)",
    re.IGNORECASE,
)

# Section headers
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
    # Find the next section header after this one
    end_pos = len(text)
    for pattern in next_patterns:
        for match in pattern.finditer(text[start_pos + 1:]):
            candidate = start_pos + 1 + match.start()
            if candidate < end_pos:
                end_pos = candidate

    section_text = text[start_pos:end_pos].strip()
    # Remove the header line
    lines = section_text.split("\n")
    if lines:
        lines = lines[1:]
    return "\n".join(lines).strip()


def _extract_name(text: str) -> Optional[str]:
    """Try to extract the candidate's name from the first few lines."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return None

    # Usually the name is the first non-empty line, and it's short
    for line in lines[:5]:
        # Skip lines that look like email, phone, or section headers
        if EMAIL_PATTERN.search(line):
            continue
        if PHONE_PATTERN.search(line) and len(line) < 20:
            continue
        if any(kw in line.lower() for kw in ["resume", "cv", "curriculum", "profile", "objective", "summary"]):
            continue
        # Names are usually 2-5 words, all alphabetic (with spaces)
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
            # Clean up the line
            college = line.strip()
            if len(college) < 200:
                return college
    return None


def parse_resume_text(text: str) -> dict:
    """Parse resume text and extract structured fields."""
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

    # Email
    email_match = EMAIL_PATTERN.search(text)
    if email_match:
        result["email"] = email_match.group(0).lower()

    # Phone
    phone_match = PHONE_PATTERN.search(text)
    if phone_match:
        result["phone"] = phone_match.group(0).strip()

    # Name
    result["name"] = _extract_name(text)

    # Degree
    degree_match = DEGREE_PATTERN.search(text)
    if degree_match:
        result["degree"] = degree_match.group(0)

    # Year
    year_match = YEAR_PATTERN.search(text)
    if year_match:
        result["year"] = year_match.group(0).title()

    # College
    result["college"] = _extract_college(text)

    # All section patterns (for boundary detection)
    all_sections = [SKILLS_SECTION, PROJECTS_SECTION, EXPERIENCE_SECTION, EDUCATION_SECTION]

    # Skills
    skills_text = _extract_section(text, SKILLS_SECTION, all_sections)
    if skills_text:
        # Clean up skills: join lines, deduplicate
        skills = []
        for line in skills_text.split("\n"):
            line = line.strip().rstrip(",").strip()
            if line and len(line) < 100:
                # Remove bullet points and markers
                line = re.sub(r"^[\•\-\*\·\▸\▹\◦\▪\‣]\s*", "", line)
                if line:
                    skills.append(line)
        result["skills"] = ", ".join(skills[:20]) if skills else None

    # Projects
    projects_text = _extract_section(text, PROJECTS_SECTION, all_sections)
    if projects_text:
        result["projects"] = projects_text[:1000] if projects_text else None

    # Work Experience
    exp_text = _extract_section(text, EXPERIENCE_SECTION, all_sections)
    if exp_text:
        result["work_experience"] = exp_text[:1000] if exp_text else None

    return result


def parse_resume_file(file_bytes: bytes, filename: str) -> dict:
    """Parse a resume file (PDF/DOCX) and return extracted data."""
    text = extract_text(file_bytes, filename)
    return parse_resume_text(text)


def parse_resume_from_url(url: str) -> dict:
    """Download a resume from URL and parse it."""
    import httpx
    import urllib.parse

    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    # Determine filename from URL or content-type
    parsed = urllib.parse.urlparse(url)
    filename = Path(parsed.path).name or "resume.pdf"
    if not Path(filename).suffix:
        ct = resp.headers.get("content-type", "")
        if "pdf" in ct:
            filename = "resume.pdf"
        else:
            filename = "resume.pdf"  # default

    return parse_resume_file(resp.content, filename)
