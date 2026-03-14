"""Tests for work submission and GitHub/deploy validation."""
import json
import sys
import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main as main_module
from database import Base, get_db
from models import Candidate, Admin, Assignment, CandidateAssignment
from auth import hash_password

from tests.test_candidates import TestSessionLocal, override_get_db, app, client

ADMIN_EMAIL = "admin@pipeline.local"
ADMIN_PASSWORD = "admin123"

SAMPLE_CANDIDATE = {
    "name": "Test Student",
    "email": "test@example.com",
    "phone": "+91-9876543210",
    "college": "IIT Bombay",
    "degree": "B.Tech",
    "year": "3rd Year",
    "skills": "Python, React",
}

SAMPLE_ASSIGNMENT = {
    "title": "Build a RAG Chatbot",
    "description": "Build a retrieval-augmented generation chatbot.",
    "tech_stack": "Python, LangChain",
    "difficulty": "medium",
    "expected_outcome": "Working chatbot deployed on a cloud platform",
}

MOCK_GITHUB_VALID = {
    "valid": True,
    "owner_repo": "teststudent/rag-chatbot",
    "stars": 5,
    "language": "Python",
    "description": "A RAG chatbot",
    "size_kb": 1024,
    "is_public": True,
    "topics": ["rag", "chatbot"],
    "error": None,
}

MOCK_GITHUB_INVALID = {
    "valid": False,
    "owner_repo": "teststudent/nonexistent",
    "stars": 0,
    "language": "",
    "description": "",
    "size_kb": 0,
    "is_public": False,
    "topics": [],
    "error": "Repository not found or is private",
}

MOCK_DEPLOY_VALID = {
    "valid": True,
    "status_code": 200,
    "response_time_ms": 250,
    "has_content": True,
    "content_length": 5000,
    "content_type": "text/html",
    "error": None,
}

MOCK_DEPLOY_INVALID = {
    "valid": False,
    "status_code": 404,
    "response_time_ms": 100,
    "has_content": False,
    "content_length": 0,
    "content_type": "",
    "error": None,
}


def _seed_admin():
    db = TestSessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first()
        if not existing:
            db.rollback()
            admin = Admin(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD))
            db.add(admin)
            db.commit()
    finally:
        db.close()


def _get_admin_token():
    _seed_admin()
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    return r.json()["token"]


def _admin_headers():
    return {"Authorization": f"Bearer {_get_admin_token()}"}


def _create_candidate(data=None):
    r = client.post("/api/candidates", data=data or SAMPLE_CANDIDATE)
    assert r.status_code == 201
    return r.json()


def _create_assignment(data=None):
    r = client.post("/api/assignments", json=data or SAMPLE_ASSIGNMENT, headers=_admin_headers())
    assert r.status_code == 201
    return r.json()


def _assign(candidate_id, assignment_id):
    r = client.post(f"/api/assignments/{assignment_id}/assign/{candidate_id}", headers=_admin_headers())
    assert r.status_code == 201
    return r.json()


@pytest.fixture(autouse=True)
def clean_db():
    db = TestSessionLocal()
    try:
        db.query(CandidateAssignment).delete()
        db.query(Assignment).delete()
        db.query(Candidate).delete()
        db.query(Admin).delete()
        db.commit()
    finally:
        db.close()
    yield


# ══════════════════════════════════════════
# 1. Submit Work — Success
# ══════════════════════════════════════════


@patch("api.assignments.check_github_repo", new_callable=AsyncMock, return_value=MOCK_GITHUB_VALID)
@patch("api.assignments.check_deployed_url", new_callable=AsyncMock, return_value=MOCK_DEPLOY_VALID)
def test_submit_work_success(mock_deploy, mock_github):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "https://github.com/teststudent/rag-chatbot",
            "deployed_url": "https://rag-chatbot.vercel.app",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["github_valid"] is True
    assert data["deploy_valid"] is True
    assert "submitted successfully" in data["message"].lower()


@patch("api.assignments.check_github_repo", new_callable=AsyncMock, return_value=MOCK_GITHUB_VALID)
@patch("api.assignments.check_deployed_url", new_callable=AsyncMock, return_value=MOCK_DEPLOY_VALID)
def test_submit_work_updates_assignment(mock_deploy, mock_github):
    """Submit work updates the CandidateAssignment record."""
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "https://github.com/teststudent/rag-chatbot",
            "deployed_url": "https://rag-chatbot.vercel.app",
        },
    )
    assert r.status_code == 200

    # Verify via admin endpoint
    r2 = client.get(f"/api/assignments/candidate/{candidate['id']}", headers=_admin_headers())
    ca = r2.json()
    assert ca["github_repo_url"] == "https://github.com/teststudent/rag-chatbot"
    assert ca["deployed_url"] == "https://rag-chatbot.vercel.app"
    assert ca["github_valid"] == 1
    assert ca["deploy_valid"] == 1
    assert ca["status"] == "submitted"
    assert ca["submitted_at"] is not None


# ══════════════════════════════════════════
# 2. Submit Work — Validation Failures
# ══════════════════════════════════════════


@patch("api.assignments.check_github_repo", new_callable=AsyncMock, return_value=MOCK_GITHUB_INVALID)
@patch("api.assignments.check_deployed_url", new_callable=AsyncMock, return_value=MOCK_DEPLOY_VALID)
def test_submit_work_invalid_github(mock_deploy, mock_github):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "https://github.com/teststudent/nonexistent",
            "deployed_url": "https://valid.vercel.app",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["github_valid"] is False
    assert data["deploy_valid"] is True


@patch("api.assignments.check_github_repo", new_callable=AsyncMock, return_value=MOCK_GITHUB_VALID)
@patch("api.assignments.check_deployed_url", new_callable=AsyncMock, return_value=MOCK_DEPLOY_INVALID)
def test_submit_work_invalid_deploy(mock_github, mock_deploy):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "https://github.com/teststudent/valid-repo",
            "deployed_url": "https://broken.example.com",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["github_valid"] is True
    assert data["deploy_valid"] is False


# ══════════════════════════════════════════
# 3. Submit Work — Auth / Validation
# ══════════════════════════════════════════


def test_submit_work_invalid_token():
    r = client.post(
        "/api/candidates/by-token/invalid-token/submit-work",
        json={
            "github_repo_url": "https://github.com/test/repo",
            "deployed_url": "https://example.com",
        },
    )
    assert r.status_code == 404


def test_submit_work_no_assignment():
    candidate = _create_candidate()
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "https://github.com/test/repo",
            "deployed_url": "https://example.com",
        },
    )
    assert r.status_code == 404


def test_submit_work_missing_github_url():
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={"deployed_url": "https://example.com"},
    )
    assert r.status_code == 422


def test_submit_work_missing_deploy_url():
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={"github_repo_url": "https://github.com/test/repo"},
    )
    assert r.status_code == 422


def test_submit_work_invalid_url_scheme():
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    r = client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "not-a-url",
            "deployed_url": "https://example.com",
        },
    )
    assert r.status_code == 422


# ══════════════════════════════════════════
# 4. Submit Work — Stats stored correctly
# ══════════════════════════════════════════


@patch("api.assignments.check_github_repo", new_callable=AsyncMock, return_value=MOCK_GITHUB_VALID)
@patch("api.assignments.check_deployed_url", new_callable=AsyncMock, return_value=MOCK_DEPLOY_VALID)
def test_submit_work_stores_github_stats(mock_deploy, mock_github):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    token = candidate["submission_token"]

    client.post(
        f"/api/candidates/by-token/{token}/submit-work",
        json={
            "github_repo_url": "https://github.com/teststudent/rag-chatbot",
            "deployed_url": "https://rag-chatbot.vercel.app",
        },
    )

    r = client.get(f"/api/assignments/candidate/{candidate['id']}", headers=_admin_headers())
    ca = r.json()
    stats = json.loads(ca["github_stats"])
    assert stats["stars"] == 5
    assert stats["language"] == "Python"
    assert stats["valid"] is True

    deploy_stats = json.loads(ca["deploy_stats"])
    assert deploy_stats["status_code"] == 200
    assert deploy_stats["has_content"] is True


# ══════════════════════════════════════════
# 5. GitHub URL Normalization
# ══════════════════════════════════════════


def test_github_url_normalization():
    from services.github import _normalize_github_url

    assert _normalize_github_url("https://github.com/user/repo") == "user/repo"
    assert _normalize_github_url("https://github.com/user/repo.git") == "user/repo"
    assert _normalize_github_url("http://github.com/user/repo/") == "user/repo"
    assert _normalize_github_url("github.com/user/repo") == "user/repo"
    assert _normalize_github_url("user/repo") == "user/repo"


# ══════════════════════════════════════════
# 6. GitHub API Response Handling
# ══════════════════════════════════════════


@pytest.mark.asyncio
async def test_github_check_404():
    from services.github import check_github_repo

    mock_response = AsyncMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await check_github_repo("https://github.com/nonexistent/repo")
    assert result["valid"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_deploy_check_timeout():
    import httpx
    from services.deploy_check import check_deployed_url

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("timeout")):
        result = await check_deployed_url("https://slow.example.com")
    assert result["valid"] is False
    assert "timed out" in result["error"].lower()
