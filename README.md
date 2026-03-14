# Intern Pipeline

Automated intern selection pipeline — collect resumes, build candidate personas, assign AI projects, track submissions, and auto-grade them.

## Tech Stack

- **Backend:** Python + FastAPI + SQLAlchemy + SQLite
- **Frontend:** React + Vite + Tailwind CSS
- **Auth:** JWT (admin) + UUID tokens (candidates)
- **Resume Parsing:** pdfplumber + python-docx
- **Persona:** LLM via OpenRouter (hunter-alpha)
- **Grading:** GitHub API + deploy checks + LLM analysis

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
rm -f data/candidates.db   # first time only
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`, backend at `http://localhost:8000`.

## Features

### Core Pipeline

1. **Resume Upload** — drag-drop PDF/DOCX or paste link
2. **Auto-Fill** — PDF parser extracts name, email, college, skills, projects, experience
3. **Candidate Submission** — form with all persona fields + unique token for self-service
4. **Persona Generation** — LLM analyzes candidate, produces skill level, strengths, gaps, assignment fit, risk flags
5. **Assignment Manager** — CRUD for projects, assign to candidates
6. **Submission Tracker** — GitHub repo validation + deployed URL checking
7. **Auto-Grading** — weighted scoring: Deployed (40%), Code Quality (25%), AI Usage (20%), Creativity (15%)
8. **Admin Dashboard** — manage candidates, assignments, grades
9. **Role-Based Access** — candidates see only their data, admin sees all

## API Endpoints

### Public

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/candidates` | Submit application |
| POST | `/api/candidates/parse-resume` | Parse resume file (PDF/DOCX) |
| GET | `/api/candidates/{id}?token=xxx` | View own application |
| PUT | `/api/candidates/{id}` | Update own application |
| POST | `/api/candidates/by-token/{token}/submit-work` | Submit GitHub + deployed URL |
| GET | `/api/candidates/by-token/{token}/assignment` | View assigned project |

### Admin (JWT required)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Admin login |
| GET | `/api/admin/candidates` | List all candidates |
| GET | `/api/admin/candidates/{id}` | Get candidate details |
| PATCH | `/api/admin/candidates/{id}/status` | Update status |
| POST | `/api/candidates/{id}/generate-persona` | Generate LLM persona |
| GET | `/api/candidates/{id}/persona` | View persona |
| POST | `/api/assignments` | Create assignment |
| GET | `/api/assignments` | List assignments |
| PUT | `/api/assignments/{id}` | Update assignment |
| DELETE | `/api/assignments/{id}` | Delete assignment |
| POST | `/api/assignments/{id}/assign/{cid}` | Assign to candidate |
| POST | `/api/candidates/{id}/grade` | Auto-grade submission |
| GET | `/api/candidates/{id}/grade` | View grade results |

### Default Admin

- **Email:** `admin@pipeline.local`
- **Password:** `admin123`

## Running Tests

```bash
cd backend
source .venv/bin/activate
rm -f data/candidates.db
pytest tests/ -v
```

**Current: 106/106 tests passing** ✅

## Project Structure

```
intern-pipeline/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # DB connection
│   ├── auth.py              # JWT auth utilities
│   ├── api/
│   │   ├── candidates.py    # Candidate endpoints
│   │   ├── admin.py         # Admin endpoints
│   │   └── assignments.py   # Assignment + grading endpoints
│   ├── services/
│   │   ├── resume_parser.py # PDF/DOCX parser
│   │   ├── persona.py       # LLM persona generation
│   │   ├── github.py        # GitHub repo validation
│   │   ├── deploy_check.py  # Deployed URL checker
│   │   └── grader.py        # Auto-grading engine
│   └── tests/               # pytest tests (106 tests)
│       ├── test_candidates.py
│       ├── test_persona.py
│       ├── test_assignments.py
│       ├── test_submissions.py
│       ├── test_grading.py
│       └── test_e2e.py
├── frontend/
│   └── src/
│       ├── components/      # React components
│       │   ├── CandidateForm.jsx
│       │   ├── ApplicationView.jsx
│       │   ├── AdminDashboard.jsx
│       │   ├── AssignmentManager.jsx
│       │   ├── AssignmentView.jsx
│       │   ├── LoginPage.jsx
│       │   └── PersonaCard.jsx
│       ├── api/             # API client
│       └── App.jsx          # Routing
└── PLAN.md                  # Sprint plan & status
```

## Sprint Roadmap

| Sprint | Status | Description |
|---|---|---|
| 1 | ✅ Complete | Candidate submission + resume parser |
| 1.5 | ✅ Complete | Auth, roles, admin dashboard |
| 2 | ✅ Complete | Candidate persona builder (LLM) |
| 3 | ✅ Complete | AI assignment manager |
| 4 | ✅ Complete | Submission tracker (GitHub + deploy) |
| 5 | ✅ Complete | Auto-grading engine |
| 6 | ✅ Complete | Polish & integration |
| 7 | ✅ Complete | End-to-end tests |

## License

Private
