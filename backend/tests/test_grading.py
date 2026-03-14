"""Tests for auto-grading engine and grading endpoints."""
import json
import sys
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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
    "skills": "Python, React",
    "ai_tool_usage": "Used ChatGPT for debugging",
    "projects": "Built a chatbot",
}

SAMPLE_ASSIGNMENT = {
    "title": "Build a RAG Chatbot",
    "description": "Build a RAG chatbot",
    "tech_stack": "Python, LangChain",
    "difficulty": "medium",
    "expected_outcome": "Working chatbot deployed on a cloud platform",
}

MOCK_GITHUB_VALID = {
    "valid": True, "owner_repo": "test/rag", "stars": 5, "language": "Python",
    "description": "A RAG chatbot", "size_kb": 1024, "is_public": True,
    "topics": ["rag", "chatbot"], "error": None,
}

MOCK_DEPLOY_VALID = {
    "valid": True, "status_code": 200, "response_time_ms": 250,
    "has_content": True, "content_length": 5000, "content_type": "text/html", "error": None,
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


def _submit_work(token):
    with patch("api.assignments.check_github_repo", new_callable=AsyncMock, return_value=MOCK_GITHUB_VALID), \
         patch("api.assignments.check_deployed_url", new_callable=AsyncMock, return_value=MOCK_DEPLOY_VALID):
        r = client.post(
            f"/api/candidates/by-token/{token}/submit-work",
            json={
                "github_repo_url": "https://github.com/test/rag",
                "deployed_url": "https://rag.vercel.app",
            },
        )
    return r


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
# 1. Grade Candidate — End to End
# ══════════════════════════════════════════


@patch("api.assignments.clone_repo", return_value=False)
def test_grade_candidate_success(mock_clone):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    _submit_work(candidate["submission_token"])

    r = client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["candidate_id"] == candidate["id"]
    assert data["grade_overall"] is not None
    assert 0 <= data["grade_overall"] <= 100
    assert data["grade_deployed"] is not None
    assert data["grade_code_quality"] is not None
    assert data["grade_ai_usage"] is not None
    assert data["grade_creativity"] is not None
    assert data["graded_at"] is not None


@patch("api.assignments.clone_repo", return_value=False)
def test_grade_stores_all_categories(mock_clone):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    _submit_work(candidate["submission_token"])

    r = client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    data = r.json()

    # Each category should be 0-100
    for field in ["grade_deployed", "grade_code_quality", "grade_ai_usage", "grade_creativity"]:
        assert data[field] is not None
        assert 0 <= data[field] <= 100, f"{field}={data[field]} out of range"


@patch("api.assignments.clone_repo", return_value=False)
def test_grade_feedback_is_json(mock_clone):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    _submit_work(candidate["submission_token"])

    r = client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    feedback = json.loads(r.json()["grade_feedback"])
    assert "deployed" in feedback
    assert "code_quality" in feedback
    assert "ai_usage" in feedback
    assert "creativity" in feedback


# ══════════════════════════════════════════
# 2. Get Grade
# ══════════════════════════════════════════


@patch("api.assignments.clone_repo", return_value=False)
def test_get_grade_after_grading(mock_clone):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    _submit_work(candidate["submission_token"])

    client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())

    r = client.get(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    assert r.status_code == 200
    assert r.json()["grade_overall"] is not None


def test_get_grade_not_yet_graded():
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])

    r = client.get(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    assert r.status_code == 404


def test_get_grade_no_assignment():
    candidate = _create_candidate()
    r = client.get(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    assert r.status_code == 404


# ══════════════════════════════════════════
# 3. Grade Requires Admin
# ══════════════════════════════════════════


def test_grade_requires_admin():
    candidate = _create_candidate()
    r = client.post(f"/api/grading/candidates/{candidate['id']}/grade")
    assert r.status_code in (401, 403)


def test_get_grade_requires_admin():
    candidate = _create_candidate()
    r = client.get(f"/api/grading/candidates/{candidate['id']}/grade")
    assert r.status_code in (401, 403)


# ══════════════════════════════════════════
# 4. Grade Without Submission
# ══════════════════════════════════════════


def test_grade_candidate_no_submission():
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    # No submit_work call

    r = client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    assert r.status_code == 400


def test_grade_candidate_no_assignment():
    candidate = _create_candidate()
    r = client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())
    assert r.status_code == 404


def test_grade_nonexistent_candidate():
    r = client.post("/api/grading/candidates/9999/grade", headers=_admin_headers())
    assert r.status_code == 404


# ══════════════════════════════════════════
# 5. Grading Service Functions
# ══════════════════════════════════════════


@pytest.mark.asyncio
async def test_grade_deployed_valid():
    from services.grader import grade_deployed
    result = await grade_deployed(json.dumps(MOCK_DEPLOY_VALID))
    assert result["score"] > 50
    assert result["feedback"]


@pytest.mark.asyncio
async def test_grade_deployed_invalid():
    from services.grader import grade_deployed
    result = await grade_deployed(json.dumps({"valid": False, "error": "Connection refused"}))
    assert result["score"] == 0
    assert "not accessible" in result["feedback"].lower()


@pytest.mark.asyncio
async def test_grade_code_quality_with_tmp_repo(tmp_path):
    """Create a temp dir with files and grade it."""
    from services.grader import grade_code_quality

    # Create a basic project structure
    (tmp_path / "README.md").write_text("# My Project\nA test project.")
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn")
    (tmp_path / "main.py").write_text("print('hello')")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_main.py").write_text("def test_pass(): assert True")

    result = await grade_code_quality("{}", str(tmp_path))
    assert result["score"] > 50
    assert "README" in result["feedback"]


@pytest.mark.asyncio
async def test_grade_code_quality_empty_repo(tmp_path):
    from services.grader import grade_code_quality
    result = await grade_code_quality("{}", str(tmp_path))
    assert result["score"] < 50


@pytest.mark.asyncio
async def test_grade_creativity_with_readme(tmp_path):
    from services.grader import grade_creativity

    (tmp_path / "README.md").write_text(
        "# My Amazing Project\n\n"
        "## Features\n- Feature 1\n- Feature 2\n\n"
        "## Installation\npip install myproject\n\n"
        "## Usage\npython main.py\n\n"
        "![Demo Screenshot](screenshot.png)\n"
    )

    result = await grade_creativity({"ai_tool_usage": ""}, "{}", str(tmp_path))
    assert result["score"] > 50


def test_clone_repo_invalid_url(tmp_path):
    from services.grader import clone_repo
    target = str(tmp_path / "cloned")
    result = clone_repo("https://github.com/nonexistent/repo-xyz-123", target)
    assert result is False


def test_analyze_repo_structure(tmp_path):
    from services.grader import _analyze_repo_structure

    (tmp_path / "README.md").write_text("README")
    (tmp_path / ".gitignore").write_text("*.pyc")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "Dockerfile").write_text("FROM python:3")

    result = _analyze_repo_structure(str(tmp_path))
    assert result["has_readme"] is True
    assert result["has_gitignore"] is True
    assert result["has_docker"] is True
    assert result["num_files"] == 4


def test_analyze_repo_structure_nonexistent():
    from services.grader import _analyze_repo_structure
    result = _analyze_repo_structure("/nonexistent/path")
    assert result["num_files"] == 0


# ══════════════════════════════════════════
# 6. Weighted Score Calculation
# ══════════════════════════════════════════


@pytest.mark.asyncio
async def test_calculate_overall_grade_weights():
    from services.grader import calculate_overall_grade

    results = await calculate_overall_grade(
        deploy_stats=json.dumps(MOCK_DEPLOY_VALID),
        github_stats=json.dumps(MOCK_GITHUB_VALID),
        candidate_data={"name": "Test", "ai_tool_usage": ""},
        repo_path=None,
    )

    # Overall should be a weighted average
    expected = int(
        results["deployed"]["score"] * 0.40 +
        results["code_quality"]["score"] * 0.25 +
        results["ai_usage"]["score"] * 0.20 +
        results["creativity"]["score"] * 0.15
    )
    assert results["overall"] == expected
    assert 0 <= results["overall"] <= 100


# ══════════════════════════════════════════
# 7. Grade Updates Assignment Status
# ══════════════════════════════════════════


@patch("api.assignments.clone_repo", return_value=False)
def test_grade_updates_status_to_graded(mock_clone):
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    _submit_work(candidate["submission_token"])

    client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())

    # Check status via assignment endpoint
    r = client.get(f"/api/assignments/candidate/{candidate['id']}", headers=_admin_headers())
    assert r.json()["status"] == "graded"


@patch("api.assignments.clone_repo", return_value=False)
def test_grade_stores_via_assignment_response(mock_clone):
    """Graded fields are visible in CandidateAssignmentResponse."""
    candidate = _create_candidate()
    assignment = _create_assignment()
    _assign(candidate["id"], assignment["id"])
    _submit_work(candidate["submission_token"])

    client.post(f"/api/grading/candidates/{candidate['id']}/grade", headers=_admin_headers())

    r = client.get(f"/api/assignments/candidate/{candidate['id']}", headers=_admin_headers())
    ca = r.json()
    assert ca["grade_overall"] is not None
    assert ca["grade_deployed"] is not None
    assert ca["grade_feedback"] is not None
