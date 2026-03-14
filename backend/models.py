from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
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

    # Status tracking
    status = Column(String(50), default="submitted")  # submitted, reviewing, accepted, rejected


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
