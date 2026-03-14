"""Tests for persona generation — endpoints and parsing logic."""
import json
import sys
import os
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main as main_module
from database import Base, get_db
from models import Candidate, Admin
from auth import hash_password

# Share the same test engine as test_candidates.py
from tests.test_candidates import TestSessionLocal, override_get_db, app, client

ADMIN_EMAIL = "admin@pipeline.local"
ADMIN_PASSWORD = "admin123"

SAMPLE_CANDIDATE = {
    "name": "Test Student",
    "email": "test@example.com",
    "phone": "+91-9876543210",
    "college": "IIT Bombay",
    "degree": "B.Tech Computer Science",
    "year": "3rd Year",
    "skills": "Python, React, PostgreSQL",
    "projects": "Built a chatbot using GPT-4 API",
    "work_experience": "Summer intern at TechCorp",
    "interests": "AI/ML, Web Development",
    "learning_style": "hands_on",
    "availability": "full_time",
    "motivation": "Want to build AI products that help people",
    "portfolio_links": "https://github.com/teststudent",
    "preferred_tech_stack": "Python, FastAPI, React",
    "ai_tool_usage": "Used ChatGPT for code review",
    "challenge_solved": "Optimized DB queries reducing load time by 80%",
}

MOCK_PERSONA = {
    "skill_level": "Intermediate",
    "strengths": ["Strong Python skills", "Full-stack experience", "AI/ML interest with practical projects"],
    "gaps": ["Limited production deployment experience", "Needs more exposure to ML frameworks"],
    "learning_style": "project-based",
    "assignment_fit": "Build a RAG-based document Q&A system using Python and a vector database",
    "risk_flags": ["No deployed projects yet"],
    "summary": "Solid technical foundation with hands-on project experience. Shows genuine interest in AI/ML and has practical experience with LLM APIs. Would benefit from a structured project that pushes deployment skills."
}


def _seed_admin():
    db = TestSessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first()
        if not existing:
            admin = Admin(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD))
            db.add(admin)
            db.commit()
    finally:
        db.close()


def _get_admin_token():
    _seed_admin()
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    return r.json()["token"]


def _admin_headers():
    return {"Authorization": f"Bearer {_get_admin_token()}"}


def _create_candidate(data=None):
    r = client.post("/api/candidates", data=data or SAMPLE_CANDIDATE)
    assert r.status_code == 201
    return r.json()


@pytest.fixture(autouse=True)
def clean_db():
    db = TestSessionLocal()
    try:
        db.query(Candidate).delete()
        db.query(Admin).delete()
        db.commit()
    finally:
        db.close()
    yield


# ── Mock persona generation directly ──

async def _mock_generate_persona(candidate_data):
    return dict(MOCK_PERSONA)


# ══════════════════════════════════════════
# 1. Persona Generation (mocked)
# ══════════════════════════════════════════


@patch("api.candidates.generate_persona", _mock_generate_persona)
def test_generate_persona_success():
    """Test persona generation with mocked LLM."""
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]

    r = client.post(f"/api/candidates/{cid}/generate-persona", headers=_admin_headers())
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    data = r.json()
    assert data["id"] == cid
    assert data["persona_generated"] is True
    persona = data["persona"]
    assert persona["skill_level"] == "Intermediate"
    assert len(persona["strengths"]) >= 2
    assert len(persona["gaps"]) >= 1


# ══════════════════════════════════════════
# 2. Persona Persists in Database
# ══════════════════════════════════════════


@patch("api.candidates.generate_persona", _mock_generate_persona)
def test_persona_persists_in_database():
    """Test that persona is stored and retrievable."""
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]

    r = client.post(f"/api/candidates/{cid}/generate-persona", headers=_admin_headers())
    assert r.status_code == 200

    r2 = client.get(f"/api/candidates/{cid}/persona", headers=_admin_headers())
    assert r2.status_code == 200
    data = r2.json()
    assert data["persona_generated"] is True
    assert data["persona"]["skill_level"] == "Intermediate"


# ══════════════════════════════════════════
# 3. Generate Persona Requires Admin Auth
# ══════════════════════════════════════════


def test_generate_persona_requires_admin():
    """Generate persona endpoint requires admin JWT."""
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]

    r = client.post(f"/api/candidates/{cid}/generate-persona")
    assert r.status_code in (401, 403)

    r = client.post(
        f"/api/candidates/{cid}/generate-persona",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert r.status_code == 401


# ══════════════════════════════════════════
# 4. Candidate Can View Own Persona with Token
# ══════════════════════════════════════════


@patch("api.candidates.generate_persona", _mock_generate_persona)
def test_candidate_can_view_own_persona():
    """Candidate can view their own persona with submission token."""
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]
    token = candidate["submission_token"]

    client.post(f"/api/candidates/{cid}/generate-persona", headers=_admin_headers())

    r = client.get(f"/api/candidates/{cid}/persona?token={token}")
    assert r.status_code == 200
    data = r.json()
    assert data["persona_generated"] is True

    r = client.get(f"/api/candidates/{cid}/persona", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


# ══════════════════════════════════════════
# 5. Candidate Cannot View Other's Persona
# ══════════════════════════════════════════


@patch("api.candidates.generate_persona", _mock_generate_persona)
def test_candidate_cannot_view_other_persona():
    """Candidate token cannot view another's persona."""
    c1 = _create_candidate(SAMPLE_CANDIDATE)
    c2 = _create_candidate({"name": "Other", "email": "other@test.com"})

    client.post(f"/api/candidates/{c1['id']}/generate-persona", headers=_admin_headers())

    r = client.get(f"/api/candidates/{c1['id']}/persona?token={c2['submission_token']}")
    assert r.status_code == 403


# ══════════════════════════════════════════
# 6. Invalid Candidate ID
# ══════════════════════════════════════════


def test_generate_persona_invalid_candidate_id():
    r = client.post("/api/candidates/9999/generate-persona", headers=_admin_headers())
    assert r.status_code == 404


def test_get_persona_invalid_candidate_id():
    r = client.get("/api/candidates/9999/persona", headers=_admin_headers())
    assert r.status_code == 404


# ══════════════════════════════════════════
# 7. Persona Not Yet Generated
# ══════════════════════════════════════════


def test_persona_not_generated():
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]

    r = client.get(f"/api/candidates/{cid}/persona", headers=_admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["persona_generated"] is False
    assert data["persona"] is None


# ══════════════════════════════════════════
# 8. Persona Parsing Logic
# ══════════════════════════════════════════


def test_parse_persona_json():
    from services.persona import _parse_persona_response
    result = _parse_persona_response(json.dumps(MOCK_PERSONA))
    assert result["skill_level"] == "Intermediate"
    assert isinstance(result["strengths"], list)


def test_parse_persona_with_markdown_fence():
    from services.persona import _parse_persona_response
    result = _parse_persona_response(f"```json\n{json.dumps(MOCK_PERSONA)}\n```")
    assert result["skill_level"] == "Intermediate"


def test_parse_persona_with_plain_fence():
    from services.persona import _parse_persona_response
    result = _parse_persona_response(f"```\n{json.dumps(MOCK_PERSONA)}\n```")
    assert result["skill_level"] == "Intermediate"


def test_parse_persona_validates_skill_level():
    from services.persona import _parse_persona_response
    data = dict(MOCK_PERSONA)
    data["skill_level"] = "Expert"
    result = _parse_persona_response(json.dumps(data))
    assert result["skill_level"] == "Intermediate"


def test_parse_persona_validates_learning_style():
    from services.persona import _parse_persona_response
    data = dict(MOCK_PERSONA)
    data["learning_style"] = "online"
    result = _parse_persona_response(json.dumps(data))
    assert result["learning_style"] == "project-based"


def test_parse_persona_wraps_non_lists():
    from services.persona import _parse_persona_response
    data = dict(MOCK_PERSONA)
    data["strengths"] = "Just one strength"
    data["gaps"] = "One gap"
    data["risk_flags"] = "One flag"
    result = _parse_persona_response(json.dumps(data))
    assert isinstance(result["strengths"], list)
    assert isinstance(result["gaps"], list)
    assert isinstance(result["risk_flags"], list)


def test_parse_persona_missing_field():
    from services.persona import _parse_persona_response
    with pytest.raises(ValueError, match="Missing required field"):
        _parse_persona_response(json.dumps({"skill_level": "Beginner"}))


def test_parse_persona_with_extra_text():
    from services.persona import _parse_persona_response
    result = _parse_persona_response(f"Here is the analysis:\n\n{json.dumps(MOCK_PERSONA)}\n\nHope this helps!")
    assert result["skill_level"] == "Intermediate"


# ══════════════════════════════════════════
# 9. Candidate to Dict Conversion
# ══════════════════════════════════════════


def test_candidate_to_dict():
    from services.persona import candidate_to_dict
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]

    db = TestSessionLocal()
    try:
        c = db.query(Candidate).filter(Candidate.id == cid).first()
        d = candidate_to_dict(c)
        assert d["name"] == "Test Student"
        assert d["skills"] == "Python, React, PostgreSQL"
    finally:
        db.close()


# ══════════════════════════════════════════
# 10. Persona in Admin Candidate Detail
# ══════════════════════════════════════════


@patch("api.candidates.generate_persona", _mock_generate_persona)
def test_persona_in_admin_candidate_detail():
    """Persona accessible via persona endpoint after generation."""
    candidate = _create_candidate(SAMPLE_CANDIDATE)
    cid = candidate["id"]

    client.post(f"/api/candidates/{cid}/generate-persona", headers=_admin_headers())

    r = client.get(f"/api/candidates/{cid}/persona", headers=_admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["persona_generated"] is True
    assert data["persona"]["skill_level"] == "Intermediate"
