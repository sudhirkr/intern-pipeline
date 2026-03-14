"""Tests for assignment management."""
import sys, os, pytest
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import Base, get_db
from models import Candidate, Admin, Assignment, CandidateAssignment
from tests.test_candidates import TestSessionLocal, override_get_db, app, client
from auth import hash_password

ADMIN_EMAIL = "admin@pipeline.local"
ADMIN_PASS = "admin123"

def _seed_admin():
    return  # skip, handled by fixture
    db = TestSessionLocal()
    try:
        if not db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first():
            db.add(Admin(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASS)))
            db.commit()
    finally:
        db.close()

def _token():
    _seed_admin()
    return client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}).json()["token"]

def _h():
    return {"Authorization": f"Bearer {_token()}"}

def _candidate(name="Test", email="test@test.com"):
    r = client.post("/api/candidates", data={"name": name, "email": email})
    assert r.status_code == 201
    return r.json()

def _assignment(title="Build Chatbot"):
    r = client.post("/api/assignments", json={
        "title": title, "description": "AI chatbot", "tech_stack": "Python, FastAPI",
        "difficulty": "medium", "expected_outcome": "Deployed app"
    }, headers=_h())
    assert r.status_code == 201
    return r.json()

@pytest.fixture(autouse=True)
def clean():
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

def test_create_assignment():
    r = client.post("/api/assignments", json={"title": "Test", "description": "Desc", "tech_stack": "Python", "difficulty": "easy", "expected_outcome": "Done"}, headers=_h())
    assert r.status_code == 201
    assert r.json()["title"] == "Test"

def test_create_assignment_requires_admin():
    r = client.post("/api/assignments", json={"title": "Test", "description": "D", "tech_stack": "P", "difficulty": "easy", "expected_outcome": "O"})
    assert r.status_code in (401, 403)

def test_list_assignments():
    _assignment("A1")
    _assignment("A2")
    r = client.get("/api/assignments", headers=_h())
    assert r.status_code in (200, 204)
    assert r.json()["total"] == 2

def test_update_assignment():
    a = _assignment()
    r = client.put(f"/api/assignments/{a['id']}", json={"title": "Updated"}, headers=_h())
    assert r.status_code in (200, 204)
    assert r.json()["title"] == "Updated"

def test_delete_assignment():
    a = _assignment()
    r = client.delete(f"/api/assignments/{a['id']}", headers=_h())
    assert r.status_code in (200, 204)

def test_assign_to_candidate():
    a = _assignment()
    c = _candidate()
    r = client.post(f"/api/assignments/{a['id']}/assign/{c['id']}", headers=_h())
    assert r.status_code == 201

def test_candidate_view_assignment():
    a = _assignment()
    c = _candidate()
    client.post(f"/api/assignments/{a['id']}/assign/{c['id']}", headers=_h())
    r = client.get(f"/api/candidates/{c['id']}/assignment", headers={"Authorization": f"Bearer {c['submission_token']}"})
    assert r.status_code in (200, 204)

def test_duplicate_assignment():
    a = _assignment()
    c = _candidate()
    client.post(f"/api/assignments/{a['id']}/assign/{c['id']}", headers=_h())
    r = client.post(f"/api/assignments/{a['id']}/assign/{c['id']}", headers=_h())
    assert r.status_code in (400, 409, 422)
