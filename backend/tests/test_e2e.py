"""End-to-end test: full candidate pipeline."""
import sys, os, pytest
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Candidate, Admin, Assignment, CandidateAssignment
from tests.test_candidates import TestSessionLocal, client
from auth import hash_password

ADMIN_EMAIL = "admin@pipeline.local"
ADMIN_PASS = "admin123"

MOCK_PERSONA = {
    "skill_level": "Intermediate", "strengths": ["Python", "AI interest"],
    "gaps": ["No deployment"], "learning_style": "project-based",
    "assignment_fit": "Build a chatbot", "risk_flags": [], "summary": "Good candidate"
}

async def _mock_persona(data):
    return dict(MOCK_PERSONA)

def _setup_admin():
    db = TestSessionLocal()
    try:
        if not db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first():
            db.add(Admin(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASS)))
            db.commit()
    finally:
        db.close()

def _token():
    _setup_admin()
    return client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}).json()["token"]

def _h():
    return {"Authorization": f"Bearer {_token()}"}

@pytest.fixture(autouse=True)
def clean():
    db = TestSessionLocal()
    try:
        db.query(CandidateAssignment).delete()
        db.query(Assignment).delete()
        db.query(Candidate).delete()
        db.commit()
    finally:
        db.close()
    yield

@patch("api.candidates.generate_persona", _mock_persona)
def test_full_pipeline():
    """Test: submit → persona → assign → submit work → view."""
    
    # 1. Candidate submits
    r = client.post("/api/candidates", data={
        "name": "E2E Student", "email": "e2e@test.com",
        "college": "IIT", "degree": "B.Tech", "year": "3rd",
        "skills": "Python, React"
    })
    assert r.status_code == 201
    cid = r.json()["id"]
    ctoken = r.json()["submission_token"]
    
    # 2. Admin generates persona
    r = client.post(f"/api/candidates/{cid}/generate-persona", headers=_h())
    assert r.status_code == 200
    assert r.json()["persona"]["skill_level"] == "Intermediate"
    
    # 3. Admin creates and assigns project
    r = client.post("/api/assignments", json={
        "title": "AI Chatbot", "description": "Build chatbot",
        "tech_stack": "Python", "difficulty": "medium",
        "expected_outcome": "Deployed app"
    }, headers=_h())
    assert r.status_code == 201
    aid = r.json()["id"]
    
    r = client.post(f"/api/assignments/{aid}/assign/{cid}", headers=_h())
    assert r.status_code == 201
    
    # 4. Candidate submits work
    r = client.post(f"/api/candidates/by-token/{ctoken}/submit-work", json={
        "github_repo_url": "https://github.com/test/chatbot",
        "deployed_url": "https://chatbot.vercel.app"
    })
    assert r.status_code == 200
    
    # 5. Verify data accessible
    r = client.get(f"/api/candidates/{cid}/persona", headers=_h())
    assert r.status_code == 200
    assert r.json()["persona_generated"] is True
    
    r = client.get(f"/api/candidates/{cid}/assignment", headers=_h())
    assert r.status_code == 200
