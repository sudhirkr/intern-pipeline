from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from models import Availability, LearningStyle


class CandidateCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    work_experience: Optional[str] = None
    interests: Optional[str] = None
    learning_style: Optional[LearningStyle] = LearningStyle.MIXED
    availability: Optional[Availability] = Availability.FLEXIBLE
    motivation: Optional[str] = None
    portfolio_links: Optional[str] = None
    preferred_tech_stack: Optional[str] = None
    ai_tool_usage: Optional[str] = None
    challenge_solved: Optional[str] = None
    resume_url: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name is required")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        if not v or "@" not in v or "." not in v:
            raise ValueError("Valid email is required")
        return v.strip().lower()


class CandidateUpdate(BaseModel):
    """Fields a candidate can update via self-service."""
    name: Optional[str] = None
    phone: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    work_experience: Optional[str] = None
    interests: Optional[str] = None
    learning_style: Optional[LearningStyle] = None
    availability: Optional[Availability] = None
    motivation: Optional[str] = None
    portfolio_links: Optional[str] = None
    preferred_tech_stack: Optional[str] = None
    ai_tool_usage: Optional[str] = None
    challenge_solved: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    submission_token: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    work_experience: Optional[str] = None
    interests: Optional[str] = None
    learning_style: Optional[LearningStyle] = None
    availability: Optional[Availability] = None
    motivation: Optional[str] = None
    portfolio_links: Optional[str] = None
    preferred_tech_stack: Optional[str] = None
    ai_tool_usage: Optional[str] = None
    challenge_solved: Optional[str] = None
    resume_url: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateListResponse(BaseModel):
    total: int
    candidates: list[CandidateResponse]


# ── Auth Schemas ──

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    email: str


class CandidateSubmissionResponse(BaseModel):
    """Returned after candidate submits — includes their self-service token."""
    id: int
    name: str
    email: str
    submission_token: str
    message: str = "Application submitted successfully. Save your link to view/edit your application."
