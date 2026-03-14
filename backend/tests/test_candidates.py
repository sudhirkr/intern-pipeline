import sys
import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import main first (this imports models via the chain)
import main as main_module
from database import Base, get_db
from models import Candidate, Admin
from auth import hash_password

# Use shared in-memory SQLite for tests (StaticPool keeps one connection)
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables on the test engine (now that all models are registered)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = main_module.app
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

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
    "portfolio_links": "https://github.com/teststudent, https://teststudent.dev",
    "preferred_tech_stack": "Python, FastAPI, React, PostgreSQL",
    "ai_tool_usage": "Used ChatGPT for code review, Copilot for boilerplate",
    "challenge_solved": "Optimized database queries reducing load time by 80%",
    "resume_url": "https://drive.google.com/resume/test",
}

ADMIN_EMAIL = "admin@pipeline.local"
ADMIN_PASSWORD = "admin123"


def _seed_admin():
    """Ensure admin user exists in the test database."""
    db = TestSessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first()
        if not existing:
            admin = Admin(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


def _get_admin_token():
    """Login as admin and return JWT token."""
    _seed_admin()
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["token"]


def _admin_headers():
    """Return headers dict with admin Authorization."""
    token = _get_admin_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clean_db():
    """Clear all data between tests."""
    db = TestSessionLocal()
    try:
        db.query(Candidate).delete()
        db.query(Admin).delete()
        db.commit()
    finally:
        db.close()
    yield


# ── Health Check ──


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ── Create Candidate ──


def test_create_candidate():
    r = client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Student"
    assert data["email"] == "test@example.com"
    assert data["id"] is not None
    assert "submission_token" in data


def test_create_candidate_minimal():
    """Only name + email required."""
    r = client.post("/api/candidates", data={"name": "Minimal", "email": "min@test.com"})
    assert r.status_code == 201
    assert r.json()["name"] == "Minimal"


def test_create_candidate_duplicate_email():
    client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    r = client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


def test_create_candidate_missing_name():
    r = client.post("/api/candidates", data={"email": "noname@test.com"})
    assert r.status_code == 422


def test_create_candidate_missing_email():
    r = client.post("/api/candidates", data={"name": "No Email"})
    assert r.status_code == 422


def test_create_candidate_invalid_email():
    r = client.post("/api/candidates", data={"name": "Bad", "email": "notanemail"})
    assert r.status_code == 422


def test_create_candidate_empty_name():
    r = client.post("/api/candidates", data={"name": "  ", "email": "ok@test.com"})
    assert r.status_code == 422


# ── List Candidates ──


def test_list_candidates_empty():
    r = client.get("/api/candidates", headers=_admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["candidates"] == []


def test_list_candidates_with_data():
    client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    client.post("/api/candidates", data={"name": "Another", "email": "another@test.com"})

    r = client.get("/api/candidates", headers=_admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["candidates"]) == 2


def test_list_candidates_pagination():
    for i in range(5):
        client.post("/api/candidates", data={"name": f"Student {i}", "email": f"s{i}@test.com"})

    r = client.get("/api/candidates?skip=0&limit=3", headers=_admin_headers())
    assert r.json()["total"] == 5
    assert len(r.json()["candidates"]) == 3

    r = client.get("/api/candidates?skip=3&limit=3", headers=_admin_headers())
    assert len(r.json()["candidates"]) == 2


def test_list_candidates_search():
    client.post("/api/candidates", data={"name": "Alice Wonder", "email": "alice@test.com"})
    client.post("/api/candidates", data={"name": "Bob Builder", "email": "bob@test.com"})

    r = client.get("/api/candidates?search=alice", headers=_admin_headers())
    assert r.json()["total"] == 1
    assert r.json()["candidates"][0]["name"] == "Alice Wonder"


# ── Get Single Candidate ──


def test_get_candidate():
    create_r = client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    cid = create_r.json()["id"]

    r = client.get(f"/api/candidates/{cid}", headers=_admin_headers())
    assert r.status_code == 200
    assert r.json()["name"] == "Test Student"
    assert r.json()["college"] == "IIT Bombay"


def test_get_candidate_not_found():
    r = client.get("/api/candidates/9999", headers=_admin_headers())
    assert r.status_code == 404


# ── Database Storage ──


def test_all_fields_stored():
    r = client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    cid = r.json()["id"]

    # Verify via admin GET that all fields were stored
    r = client.get(f"/api/candidates/{cid}", headers=_admin_headers())
    assert r.status_code == 200
    data = r.json()

    assert data["phone"] == "+91-9876543210"
    assert data["degree"] == "B.Tech Computer Science"
    assert data["skills"] == "Python, React, PostgreSQL"
    assert data["learning_style"] == "hands_on"
    assert data["availability"] == "full_time"
    assert data["resume_url"] == "https://drive.google.com/resume/test"
    assert data["ai_tool_usage"] is not None
    assert data["challenge_solved"] is not None


def test_email_lowercased():
    r = client.post("/api/candidates", data={"name": "Test", "email": "TEST@EXAMPLE.COM"})
    assert r.json()["email"] == "test@example.com"


def test_enum_validation():
    r = client.post("/api/candidates", data={
        "name": "Bad Enum",
        "email": "bad@test.com",
        "learning_style": "invalid_style",
    })
    assert r.status_code == 422


def test_no_certifications_field():
    """Certifications field has been removed from the model."""
    r = client.post("/api/candidates", data=SAMPLE_CANDIDATE)
    cid = r.json()["id"]
    r = client.get(f"/api/candidates/{cid}", headers=_admin_headers())
    data = r.json()
    assert "certifications" not in data


# ── Parse Resume Endpoint ──


def test_parse_resume_no_input():
    """Must provide file or URL."""
    r = client.post("/api/candidates/parse-resume")
    assert r.status_code == 400


def test_parse_resume_unsupported_format():
    """Only PDF/DOCX supported."""
    r = client.post(
        "/api/candidates/parse-resume",
        files={"file": ("resume.txt", b"hello world", "text/plain")},
    )
    assert r.status_code == 400
    assert "Unsupported format" in r.json()["detail"]


def test_parse_resume_pdf():
    """Test PDF parsing with a minimal PDF."""
    # Create a minimal PDF with some resume-like content
    # This is a valid PDF with embedded text
    import pdfplumber
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(72, 750, "John Doe")
    c.drawString(72, 730, "Email: john.doe@example.com")
    c.drawString(72, 710, "Phone: +1-555-123-4567")
    c.drawString(72, 690, "B.Tech Computer Science, 3rd Year")
    c.drawString(72, 670, "Indian Institute of Technology Bombay")
    c.drawString(72, 640, "Skills")
    c.drawString(72, 620, "Python, JavaScript, React, SQL")
    c.drawString(72, 590, "Projects")
    c.drawString(72, 570, "Built a web app using FastAPI and React")
    c.drawString(72, 540, "Work Experience")
    c.drawString(72, 520, "Summer intern at TechCorp - developed APIs")
    c.save()
    pdf_bytes = buf.getvalue()

    r = client.post(
        "/api/candidates/parse-resume",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == "file"
    extracted = data["extracted"]
    assert extracted["email"] == "john.doe@example.com"
    assert extracted["college"] is not None
    assert "IIT" in extracted["college"] or "Institute" in extracted["college"]
    assert extracted["degree"] is not None


def test_create_candidate_with_file_upload():
    """Test candidate submission with resume file."""
    r = client.post(
        "/api/candidates",
        data={"name": "File Upload Test", "email": "file@test.com"},
        files={"resume_file": ("resume.pdf", b"%PDF-1.0 fake", "application/pdf")},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "File Upload Test"
    # Verify stored resume_url via admin GET
    r2 = client.get(f"/api/candidates/{data['id']}", headers=_admin_headers())
    assert r2.json()["resume_url"] is not None
    assert "resumes/" in r2.json()["resume_url"]
