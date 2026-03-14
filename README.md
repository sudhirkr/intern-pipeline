# Intern Pipeline

Automated intern selection pipeline — collect resumes, build candidate personas, assign AI projects, track submissions, and auto-grade them.

## Tech Stack

- **Backend:** Python + FastAPI + SQLAlchemy + SQLite
- **Frontend:** React + Vite + Tailwind CSS
- **Auth:** JWT (admin) + UUID tokens (candidates)
- **Resume Parsing:** pdfplumber + python-docx

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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

### Sprint 1 & 1.5 (Current)

- **Resume Upload** — drag-drop PDF/DOCX or paste link
- **Auto-Fill** — PDF parser extracts name, email, college, skills, projects, experience
- **Candidate Submission** — form with all persona fields
- **Candidate Self-Service** — unique token link to view/edit own application
- **Admin Dashboard** — list all candidates, search, filter by status
- **Admin Auth** — JWT-based login
- **Role-Based Access** — candidates see only their data, admin sees all
- **Status Management** — submitted → reviewing → accepted → rejected

## API Endpoints

### Public

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/candidates` | Submit application |
| POST | `/api/candidates/parse-resume` | Parse resume file (PDF/DOCX) |
| GET | `/api/candidates/{id}?token=xxx` | View own application |

### Admin (JWT required)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Admin login |
| GET | `/api/admin/candidates` | List all candidates |
| GET | `/api/admin/candidates/{id}` | Get candidate details |
| PATCH | `/api/admin/candidates/{id}/status` | Update status |

### Default Admin

- **Email:** `admin@pipeline.local`
- **Password:** `admin123`

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

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
│   │   └── admin.py         # Admin endpoints
│   ├── services/
│   │   └── resume_parser.py # PDF/DOCX parser
│   └── tests/               # pytest tests
├── frontend/
│   └── src/
│       ├── components/      # React components
│       ├── api/             # API client
│       └── assets/          # Static files
└── PLAN.md                  # Sprint plan & status
```

## Sprint Roadmap

| Sprint | Status | Description |
|---|---|---|
| 1 | ✅ Complete | Candidate submission + resume parser |
| 1.5 | ✅ Complete | Auth, roles, admin dashboard |
| 2 | Not Started | Candidate persona builder (LLM) |
| 3 | Not Started | AI assignment manager |
| 4 | Not Started | Submission tracker (GitHub + deploy) |
| 5 | Not Started | Auto-grading engine |
| 6 | Not Started | Polish & integration |
| 7 | Not Started | End-to-end testing |

## License

Private
