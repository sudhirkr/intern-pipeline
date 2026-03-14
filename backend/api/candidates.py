import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Candidate, Availability, LearningStyle
from schemas import (
    CandidateCreate, CandidateResponse, CandidateListResponse,
    CandidateUpdate, CandidateSubmissionResponse,
)
from auth import (
    generate_submission_token, require_candidate_token,
    get_optional_admin,
)
from services.resume_parser import parse_resume_file, parse_resume_from_url


def _validate_enum(value: str | None, enum_cls, field_name: str) -> str | None:
    """Validate a string value against an enum class. Returns the value if valid."""
    if value is None:
        return None
    valid_values = [e.value for e in enum_cls]
    if value not in valid_values:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: '{value}'. Must be one of: {', '.join(valid_values)}"
        )
    return value

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

RESUME_DIR = Path("data/resumes")


@router.post("/parse-resume", status_code=200)
async def parse_resume(
    file: UploadFile | None = File(None),
    resume_url: str | None = Form(None),
):
    """Parse a resume PDF/DOCX and return extracted data.

    Accept either a file upload OR a resume URL.
    Returns extracted fields — does NOT save to database.
    """
    if not file and not resume_url:
        raise HTTPException(status_code=400, detail="Provide either a file upload or resume_url")

    if file:
        ext = Path(file.filename).suffix.lower()
        if ext not in (".pdf", ".docx", ".doc"):
            raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}. Use PDF or DOCX.")

        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        try:
            data = parse_resume_file(content, file.filename)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

        return {"source": "file", "filename": file.filename, "extracted": data}

    elif resume_url:
        try:
            data = parse_resume_from_url(resume_url)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to fetch/parse resume: {str(e)}")

        return {"source": "url", "url": resume_url, "extracted": data}


def _save_resume_file(file: UploadFile) -> str:
    """Save uploaded resume file and return the stored path."""
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = RESUME_DIR / unique_name

    file.file.seek(0)
    with open(dest, "wb") as f:
        while chunk := file.file.read(8192):
            f.write(chunk)

    return str(dest)


@router.post("", response_model=CandidateSubmissionResponse, status_code=201)
async def create_candidate(
    name: str = Form(...),
    email: str = Form(...),
    phone: str | None = Form(None),
    college: str | None = Form(None),
    degree: str | None = Form(None),
    year: str | None = Form(None),
    skills: str | None = Form(None),
    projects: str | None = Form(None),
    work_experience: str | None = Form(None),
    interests: str | None = Form(None),
    learning_style: str | None = Form("mixed"),
    availability: str | None = Form("flexible"),
    motivation: str | None = Form(None),
    portfolio_links: str | None = Form(None),
    preferred_tech_stack: str | None = Form(None),
    ai_tool_usage: str | None = Form(None),
    challenge_solved: str | None = Form(None),
    resume_url: str | None = Form(None),
    resume_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Submit a new candidate application.

    Accepts form data (multipart) with optional resume file upload.
    Returns submission_token for candidate self-service.
    """
    # Validate name/email
    if not name or not name.strip():
        raise HTTPException(status_code=422, detail="Name is required")
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=422, detail="Valid email is required")

    name = name.strip()
    email = email.strip().lower()

    # Validate enums
    learning_style = _validate_enum(learning_style, LearningStyle, "learning_style")
    availability = _validate_enum(availability, Availability, "availability")

    # Handle resume file upload
    stored_resume_url = resume_url
    if resume_file and resume_file.filename:
        stored_resume_url = _save_resume_file(resume_file)

    # Check for duplicate email
    existing = db.query(Candidate).filter(Candidate.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Candidate with email {email} already exists")

    # Generate submission token
    token = generate_submission_token()

    candidate = Candidate(
        submission_token=token,
        name=name,
        email=email,
        phone=phone,
        college=college,
        degree=degree,
        year=year,
        skills=skills,
        projects=projects,
        work_experience=work_experience,
        interests=interests,
        learning_style=learning_style,
        availability=availability,
        motivation=motivation,
        portfolio_links=portfolio_links,
        preferred_tech_stack=preferred_tech_stack,
        ai_tool_usage=ai_tool_usage,
        challenge_solved=challenge_solved,
        resume_url=stored_resume_url,
    )
    db.add(candidate)
    try:
        db.commit()
        db.refresh(candidate)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate entry")

    return CandidateSubmissionResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        submission_token=token,
    )


@router.get("", response_model=CandidateListResponse)
def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = None,
    db: Session = Depends(get_db),
    admin=Depends(get_optional_admin),
):
    """List all candidates. Admin sees all; non-admin sees none (requires admin auth for listing)."""
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required to list candidates")

    query = db.query(Candidate)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Candidate.name.ilike(search_term) | Candidate.email.ilike(search_term)
        )

    total = query.count()
    candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()
    return CandidateListResponse(total=total, candidates=candidates)


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Get a single candidate by ID. Requires either admin JWT or candidate submission token."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Check if admin
    try:
        auth_header = request.headers.get("Authorization", "") if request else ""
        if auth_header.startswith("Bearer "):
            from auth import decode_access_token
            payload = decode_access_token(auth_header[7:])
            if payload.get("role") == "admin":
                return candidate
    except Exception:
        pass

    # Check candidate token
    sub_token = token
    if not sub_token and request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            sub_token = auth_header[7:]

    if not sub_token or candidate.submission_token != sub_token:
        raise HTTPException(status_code=403, detail="Access denied. Provide a valid submission token.")

    return candidate


@router.get("/by-token/{token}", response_model=CandidateResponse)
def get_candidate_by_token(
    token: str,
    db: Session = Depends(get_db),
):
    """Get candidate data by their submission token. For candidate self-service."""
    candidate = db.query(Candidate).filter(Candidate.submission_token == token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid submission token")
    return candidate


@router.put("/by-token/{token}", response_model=CandidateResponse)
def update_candidate_by_token(
    token: str,
    body: CandidateUpdate,
    db: Session = Depends(get_db),
):
    """Candidate updates their own data using their submission token."""
    candidate = db.query(Candidate).filter(Candidate.submission_token == token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid submission token")

    # Update only provided fields (email cannot be changed)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "email":
            continue  # Email is immutable
        if hasattr(candidate, field):
            setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)
    return candidate
