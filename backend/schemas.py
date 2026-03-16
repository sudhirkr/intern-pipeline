from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from models import Availability, LearningStyle, Difficulty, AssignmentStatus


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


# ── Persona Schemas ──

class PersonaData(BaseModel):
    skill_level: str
    strengths: list[str]
    gaps: list[str]
    learning_style: str
    assignment_fit: str
    risk_flags: list[str]
    summary: str


class PersonaResponse(BaseModel):
    id: int
    name: str
    email: str
    persona: Optional[PersonaData] = None
    persona_generated: bool = False
    persona_generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Assignment Schemas ──

class AssignmentCreate(BaseModel):
    title: str
    description: str
    tech_stack: Optional[str] = None
    difficulty: Optional[Difficulty] = Difficulty.MEDIUM
    expected_outcome: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Title is required")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Description is required")
        return v.strip()


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    expected_outcome: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: int
    title: str
    description: str
    tech_stack: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    expected_outcome: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentListResponse(BaseModel):
    total: int
    assignments: list[AssignmentResponse]


class CandidateAssignmentResponse(BaseModel):
    id: int
    candidate_id: int
    assignment_id: int
    assigned_at: datetime
    submitted_at: Optional[datetime] = None
    status: AssignmentStatus
    github_repo_url: Optional[str] = None
    deployed_url: Optional[str] = None
    github_valid: Optional[int] = None
    github_stats: Optional[str] = None
    deploy_valid: Optional[int] = None
    deploy_stats: Optional[str] = None
    grade_overall: Optional[int] = None
    grade_deployed: Optional[int] = None
    grade_code_quality: Optional[int] = None
    grade_ai_usage: Optional[int] = None
    grade_creativity: Optional[int] = None
    grade_feedback: Optional[str] = None
    graded_at: Optional[datetime] = None
    assignment: Optional[AssignmentResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ── Submission Schemas ──

class SubmitWorkRequest(BaseModel):
    github_repo_url: str
    deployed_url: str

    @field_validator("github_repo_url")
    @classmethod
    def github_url_valid(cls, v):
        if not v or not v.strip():
            raise ValueError("GitHub repo URL is required")
        v = v.strip()
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("GitHub URL must start with http:// or https://")
        return v

    @field_validator("deployed_url")
    @classmethod
    def deploy_url_valid(cls, v):
        if not v or not v.strip():
            raise ValueError("Deployed URL is required")
        v = v.strip()
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("Deployed URL must start with http:// or https://")
        return v


class SubmitWorkResponse(BaseModel):
    message: str
    github_valid: bool
    github_stats: Optional[str] = None
    deploy_valid: bool
    deploy_stats: Optional[str] = None


# ── Grade Schemas ──

class GradeResponse(BaseModel):
    id: int
    candidate_id: int
    grade_overall: Optional[int] = None
    grade_deployed: Optional[int] = None
    grade_code_quality: Optional[int] = None
    grade_ai_usage: Optional[int] = None
    grade_creativity: Optional[int] = None
    grade_feedback: Optional[str] = None
    graded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
