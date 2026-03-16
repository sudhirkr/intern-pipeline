# Intern Selection Pipeline — Granular Sub-Sprint Plan

## Overview
Automated intern selection pipeline for collecting resumes, building candidate personas, assigning AI-related projects, tracking submissions, and auto-grading them.

## Tech Stack
- **Backend:** Python + FastAPI + SQLAlchemy + SQLite
- **Frontend:** React + Vite + Tailwind CSS
- **Grading:** LLM (hunter-alpha via OpenRouter) + GitHub API + HTTP checks
- **Hosting:** TBD (local for dev)

## Scoring Weights
| Criteria | Weight | Method |
|---|---|---|
| Deployed Project | 40% | HTTP check → functionality, UI |
| Code Quality | 25% | LLM analyzes repo |
| AI Usage | 20% | LLM checks AI-assisted code |
| Creativity | 15% | LLM evaluates approach |

## Scale: 50-100 candidates

---

## Sprints (Granular)

### Sprint 1: Collect Resumes & Info
**Goal:** Resume upload → auto-fill → candidate submission → dashboard

#### Sprint 1.1: Backend Scaffold
**Goal:** FastAPI app + SQLite + data model + basic CRUD
- FastAPI app with CORS middleware
- SQLAlchemy + SQLite setup (`database.py`)
- Candidate model (20+ fields: name, email, phone, college, degree, year, skills, projects, experience, interests, learning_style, availability, motivation, portfolio_links, preferred_tech_stack, ai_tool_usage, challenge_solved, resume_url, persona, status)
- POST `/api/candidates` — create candidate
- GET `/api/candidates` — list all
- GET `/api/candidates/{id}` — get one
- Validation (email uniqueness, required fields)
- **Tests:** model creation, CRUD operations, validation
- **Files:** `main.py`, `models.py`, `database.py`, `api/candidates.py`, `schemas.py`

#### Sprint 1.2: Resume Parser Service
**Goal:** Extract structured data from uploaded resumes
- PDF parser using pdfplumber (extract text from PDF)
- DOCX parser using python-docx
- Resume parser service: extract name, email, phone, college, degree, year, skills, projects, work_experience
- POST `/api/candidates/parse-resume` — upload file → returns extracted JSON
- Store uploaded resume file in `data/resumes/`
- **Tests:** parsing real resumes from `data/` directory, edge cases (empty file, corrupted file)
- **Files:** `services/resume_parser.py`

#### Sprint 1.3: Frontend UI
**Goal:** Modern submission form with drag-drop + auto-fill
- React + Vite + Tailwind CSS setup (dark theme)
- Drag-drop resume upload component
- Auto-fill form from parsed resume data
- Candidate submission form (all fields)
- Candidate list table with search
- Success screen with submission token + copy button
- API client (`api/client.js`)
- **Tests:** frontend builds without errors
- **Files:** `CandidateForm.jsx`, `CandidateList.jsx`, `ApplyPage.jsx`, `App.jsx`, `main.jsx`

#### Sprint 1.4: Tests & Integration
**Goal:** Full test suite passing
- Fix any integration issues between parser, API, and frontend
- Ensure all edge cases covered
- **Target:** 23/23 tests passing
- Frontend builds clean

---

### Sprint 1.5: Auth & Roles
**Goal:** Candidate self-service + Admin dashboard

#### Sprint 1.5.1: Admin Auth
**Goal:** JWT-based admin authentication
- Admin model (email, password_hash, created_at)
- Password hashing (bcrypt via passlib)
- JWT token generation (python-jose)
- POST `/api/admin/login` — returns JWT
- Seed default admin on startup
- Auth middleware/dependency for protected routes
- **Tests:** login success/failure, token validation, expired tokens
- **Files:** `auth.py`, `api/admin.py`

#### Sprint 1.5.2: Candidate Self-Service
**Goal:** Candidates can view/edit their own application via unique link
- Generate unique `submission_token` on candidate creation
- GET `/api/candidates/by-token/{token}` — view own application
- PUT `/api/candidates/by-token/{token}` — edit own application
- Data isolation: candidates cannot see others' data
- **Tests:** token access, data isolation, invalid tokens
- **Files:** `api/candidates.py` (by-token endpoints)

#### Sprint 1.5.3: Admin Dashboard API
**Goal:** Admin endpoints for managing candidates
- GET `/api/admin/candidates` — list all with filtering (status, search by name/email/college)
- GET `/api/admin/candidates/{id}` — detail view
- PUT `/api/admin/candidates/{id}/status` — update status (submitted/reviewing/accepted/rejected)
- Role-based access control middleware
- **Tests:** admin access, filtering, status updates, non-admin blocked
- **Files:** `api/admin.py`

#### Sprint 1.5.4: Frontend Auth & Dashboard
**Goal:** Login page + admin dashboard + candidate view in frontend
- `/login` route — admin login form (email + password), stores JWT in localStorage
- `/admin` route — admin dashboard with candidate table, search, filter, status updates
- `/application/:token` route — candidate self-service view (read-only + edit mode)
- Protected routes (redirect to /login if unauthenticated)
- **Tests:** 44/44 tests passing, frontend builds clean
- **Files:** `LoginPage.jsx`, `AdminDashboard.jsx`, `ApplicationView.jsx`

---

### Sprint 2: Build Candidate Persona
**Goal:** Resume → LLM-generated candidate profile

#### Sprint 2.1: LLM Persona Service
**Goal:** Generate candidate persona using LLM
- Persona generation prompt (structured output: skill_level, strengths, gaps, assignment_fit, risk_flags)
- OpenRouter API integration (hunter-alpha model)
- Persona service: takes candidate data → returns structured persona JSON
- Validate LLM output (required fields, sensible values)
- **Tests:** persona generation, field extraction, edge cases
- **Files:** `services/persona.py`

#### Sprint 2.2: Persona API & Frontend
**Goal:** Expose persona generation + display in UI
- POST `/api/candidates/{id}/generate-persona` — trigger persona generation
- GET `/api/candidates/{id}/persona` — fetch generated persona
- PersonaCard component (display persona in candidate detail view)
- Persona stored as JSON string in candidate.persona field
- **Tests:** API endpoints, persona persistence
- **Files:** `api/candidates.py` (persona endpoints), `PersonaCard.jsx`

---

### Sprint 3: Assign AI Assignments
**Goal:** Manage project list + assign to candidates

#### Sprint 3.1: Assignment CRUD
**Goal:** Full CRUD for assignments/projects
- Assignment model (title, description, tech_stack, difficulty, expected_outcome)
- POST `/api/assignments` — create
- GET `/api/assignments` — list all
- GET `/api/assignments/{id}` — get one
- PUT `/api/assignments/{id}` — update
- DELETE `/api/assignments/{id}` — delete
- **Tests:** CRUD operations, validation
- **Files:** `api/assignments.py`

#### Sprint 3.2: Assignment Allocation
**Goal:** Assign projects to candidates + status tracking
- CandidateAssignment model (candidate_id, assignment_id, status, assigned_at)
- POST `/api/assignments/{id}/assign` — assign to candidate
- GET `/api/candidates/{id}/assignments` — candidate's assignments
- Assignment status: assigned → submitted → graded
- **Tests:** allocation, status transitions, duplicate prevention
- **Files:** `api/assignments.py`

#### Sprint 3.3: Assignment Frontend
**Goal:** Assignment management UI
- AssignmentManager component (CRUD for projects)
- AssignmentView component (candidate's assigned projects)
- Admin can assign projects from dashboard
- **Tests:** frontend builds clean
- **Files:** `AssignmentManager.jsx`, `AssignmentView.jsx`

---

### Sprint 4: Track Submissions
**Goal:** GitHub repo + deployed URL validation

#### Sprint 4.1: GitHub Checker
**Goal:** Validate GitHub repo existence and stats
- GitHub API integration (check repo exists, is accessible)
- Extract repo stats: stars, language, commits, description, size
- POST `/api/candidates/{id}/assignments/{aid}/check-github` — validate repo
- Store results in CandidateAssignment (github_valid, github_stats JSON)
- **Tests:** valid repo, invalid repo, private repo, API errors
- **Files:** `services/github.py`

#### Sprint 4.2: Deploy Checker
**Goal:** Validate deployed URL
- HTTP check: status code, response time, has content
- POST `/api/candidates/{id}/assignments/{aid}/check-deploy` — validate URL
- Store results in CandidateAssignment (deploy_valid, deploy_stats JSON)
- **Tests:** live URL, dead URL, slow response, redirects
- **Files:** `services/deploy_check.py`

#### Sprint 4.3: Submission Frontend
**Goal:** Submission form + status dashboard
- Submission form (GitHub repo URL + deployed URL)
- Submission status display (GitHub valid ✓/✗, Deploy valid ✓/✗)
- Status dashboard for admin (all submissions overview)
- **Tests:** frontend builds clean
- **Files:** `AssignmentView.jsx`, `AdminDashboard.jsx`

---

### Sprint 5: Auto-Grade
**Goal:** Automated grading with weighted scores + feedback

#### Sprint 5.1: Code Analysis Engine
**Goal:** Clone repo + LLM code review
- Git clone candidate's repo to temp directory
- LLM-based code analysis (prompt for quality, structure, best practices)
- Score code quality 0-100
- Score AI usage 0-100 (check for AI-assisted patterns)
- Score creativity 0-100
- **Tests:** scoring accuracy, different repo sizes
- **Files:** `services/grader.py` (code analysis)

#### Sprint 5.2: Deployed App Tester
**Goal:** Test deployed app functionality
- HTTP-based testing (check key pages, API endpoints)
- LLM-based evaluation (if content is scraped)
- Score deployed project 0-100
- **Tests:** various deployed app scenarios
- **Files:** `services/grader.py` (deploy testing)

#### Sprint 5.3: Grading API + Reports
**Goal:** Weighted scoring + feedback reports
- Weighted score calculation: deploy(40%) + code_quality(25%) + ai_usage(20%) + creativity(15%)
- POST `/api/candidates/{id}/assignments/{aid}/grade` — trigger grading
- GET `/api/candidates/{id}/assignments/{aid}/grade` — get results
- Feedback report generation (JSON with detailed feedback per criterion)
- Store all grade fields in CandidateAssignment
- **Tests:** weight calculation, report generation, edge cases
- **Files:** `api/assignments.py` (grading endpoints), `services/grader.py`

---

### Sprint 6: Polish & Integrate
**Goal:** Full flow works end-to-end

#### Sprint 6.1: Error Handling & Loading States
**Goal:** Production-quality error handling
- Global error handler in backend
- Loading states in frontend (spinners, skeleton screens)
- Error boundaries in React
- Toast notifications for success/failure
- Form validation (client + server side)
- **Tests:** error scenarios, loading states
- **Files:** All frontend components, `main.py`

#### Sprint 6.2: Performance & Security
**Goal:** Optimize and secure
- Database query optimization (indexes, eager loading)
- CORS configuration for production
- Input sanitization
- Rate limiting on auth endpoints
- Password policy enforcement
- **Tests:** performance benchmarks, security tests

#### Sprint 6.3: Deployment Setup
**Goal:** Ready for deployment
- Environment configuration (.env support)
- Production database config
- Static file serving for frontend build
- Docker setup (optional)
- Deployment documentation
- **Tests:** deployment smoke tests

---

### Sprint 7: End-to-End Testing
**Goal:** Full pipeline validated

#### Sprint 7.1: API Integration Tests
**Goal:** All API flows tested end-to-end
- Full candidate flow: submit → persona → assign → submit work → grade
- Admin flow: login → manage candidates → assign projects → review grades
- Auth flow: login → token refresh → logout
- Error flows: invalid data, unauthorized access, missing resources
- **Target:** All integration tests passing

#### Sprint 7.2: Browser Automation Tests
**Goal:** Full UI flow tested with browser automation
- Candidate submission flow (upload resume → auto-fill → submit → get token)
- Admin dashboard flow (login → view candidates → update status)
- Candidate self-service flow (access via token → view/edit application)
- Assignment flow (admin assigns → candidate views → submits work)
- **Target:** All browser tests passing

#### Sprint 7.3: Load Testing & Bug Fixes
**Goal:** System handles 50-100 candidates
- Load test with 50 candidate submissions
- Concurrent admin operations
- Database performance under load
- Fix any bugs found during testing
- Final demo preparation
- **Target:** System stable under load, 106/106 tests passing

---

## Current Status
- ✅ All sprints complete (106/106 tests)
- ✅ Frontend builds clean
- ✅ Full pipeline: submit → persona → assign → submit work → grade
