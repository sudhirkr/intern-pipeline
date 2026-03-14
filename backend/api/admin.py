"""Admin authentication and dashboard API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from auth import hash_password, verify_password, create_access_token, get_current_admin
from models import Admin, Candidate
from schemas import LoginRequest, LoginResponse, CandidateResponse, CandidateListResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Seed default admin on first import
DEFAULT_ADMIN_EMAIL = "admin@pipeline.local"
DEFAULT_ADMIN_PASSWORD = "admin123"


def seed_admin(db: Session):
    """Create the default admin if not exists."""
    existing = db.query(Admin).filter(Admin.email == DEFAULT_ADMIN_EMAIL).first()
    if not existing:
        db.rollback()  # ensure clean state
        admin = Admin(
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        )
        db.add(admin)
        db.commit()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Admin login — returns JWT token."""
    # Ensure default admin exists
    seed_admin(db)

    admin = db.query(Admin).filter(Admin.email == body.email).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(admin.id), "role": "admin", "email": admin.email})
    return LoginResponse(token=token, email=admin.email)


# ── Admin Dashboard API ──

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


@admin_router.get("/candidates", response_model=CandidateListResponse)
def admin_list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Admin: list all candidates with search, filter, and pagination."""
    query = db.query(Candidate)

    if search:
        term = f"%{search}%"
        query = query.filter(
            Candidate.name.ilike(term) | Candidate.email.ilike(term) | Candidate.college.ilike(term)
        )

    if status:
        query = query.filter(Candidate.status == status)

    total = query.count()
    candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()

    return CandidateListResponse(total=total, candidates=candidates)


@admin_router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def admin_get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Admin: get full candidate details."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@admin_router.patch("/candidates/{candidate_id}/status")
def admin_update_status(
    candidate_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Admin: update candidate status (submitted/reviewing/accepted/rejected)."""
    valid_statuses = ["submitted", "reviewing", "accepted", "rejected"]
    new_status = body.get("status")
    if new_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {valid_statuses}")

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = new_status
    db.commit()
    db.refresh(candidate)
    return {"id": candidate.id, "status": candidate.status}
