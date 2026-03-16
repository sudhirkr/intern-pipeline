from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from database import Base


class Availability(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FLEXIBLE = "flexible"


class LearningStyle(str, enum.Enum):
    VISUAL = "visual"
    HANDS_ON = "hands_on"
    READING = "reading"
    MIXED = "mixed"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Auth: unique token for candidate self-service
    submission_token = Column(String(64), unique=True, index=True, nullable=True)

    # Basic info
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(20))

    # Education
    college = Column(String(300))
    degree = Column(String(200))
    year = Column(String(50))  # e.g. "3rd Year", "Final Year"

    # From resume
    skills = Column(Text)  # comma-separated or JSON string
    projects = Column(Text)  # description of projects
    work_experience = Column(Text)

    # From form
    interests = Column(Text)
    learning_style = Column(SQLEnum(LearningStyle), default=LearningStyle.MIXED)
    availability = Column(SQLEnum(Availability), default=Availability.FLEXIBLE)
    motivation = Column(Text)
    portfolio_links = Column(Text)  # comma-separated URLs
    preferred_tech_stack = Column(Text)
    ai_tool_usage = Column(Text)
    challenge_solved = Column(Text)

    # File upload
    resume_url = Column(String(500))

    # LLM-generated persona
    persona = Column(Text, nullable=True)  # JSON string with persona profile
    persona_generated_at = Column(DateTime, nullable=True)  # when persona was last generated

    # Resume caching
    resume_hash = Column(String(64), nullable=True)  # SHA-256 of uploaded file bytes
    resume_parsed = Column(Text, nullable=True)  # JSON string of LLM-extracted resume data

    # Status tracking
    status = Column(String(50), default="submitted")  # submitted, reviewing, accepted, rejected


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    SUBMITTED = "submitted"
    GRADED = "graded"


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    tech_stack = Column(Text)  # comma-separated
    difficulty = Column(SQLEnum(Difficulty), default=Difficulty.MEDIUM)
    expected_outcome = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    candidate_assignments = relationship("CandidateAssignment", back_populates="assignment")


class CandidateAssignment(Base):
    __tablename__ = "candidate_assignments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(AssignmentStatus), default=AssignmentStatus.ASSIGNED)
    github_repo_url = Column(String(500), nullable=True)
    deployed_url = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    # Submission validation results (from github.py and deploy_check.py)
    github_valid = Column(Integer, nullable=True)  # 1=valid, 0=invalid
    github_stats = Column(Text, nullable=True)  # JSON: stars, language, commits, description, size
    deploy_valid = Column(Integer, nullable=True)  # 1=valid, 0=invalid
    deploy_stats = Column(Text, nullable=True)  # JSON: status_code, response_time_ms, has_content

    # Grading results (from grader.py)
    grade_overall = Column(Integer, nullable=True)  # 0-100
    grade_deployed = Column(Integer, nullable=True)  # 0-100
    grade_code_quality = Column(Integer, nullable=True)  # 0-100
    grade_ai_usage = Column(Integer, nullable=True)  # 0-100
    grade_creativity = Column(Integer, nullable=True)  # 0-100
    grade_feedback = Column(Text, nullable=True)  # JSON string with detailed feedback
    graded_at = Column(DateTime, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="candidate_assignments")
    candidate = relationship("Candidate")
