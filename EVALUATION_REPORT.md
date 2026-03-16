# Project Evaluation Report — Intern Selection (March 2026)

**Evaluator:** Senior Engineering Hiring Manager  
**Methodology:** Cloned all 10 GitHub repositories, reviewed code structure, commit history, architecture, README, and deployed dashboards.  
**Criteria:** Hands-on Engineering (0–4) | Code Quality (0–2) | Completeness (0–2) | Technical Depth (0–1) | Documentation (0–1)

---

## Individual Evaluations

---

### 1. Snehash Kumar Behera — Global Ship Radar (Strait of Hormuz & Arabian Sea)

**Dashboard:** https://ship-radar-jt0j6xs7j-nongenericguys-projects.vercel.app/ (auth-gated)  
**GitHub:** https://github.com/nongenericguy/ship-radar  
**Code:** 519 lines | 8 commits | All by Snehash  
**Tech Stack:** FastAPI + WebSocket backend, React + Leaflet + MapLibreGL frontend, AIS real-time streaming

**Project Summary:**  
Real-time maritime traffic visualization using AIS (Automatic Identification System) data. Backend connects to AIS streaming API, processes ship positions, and pushes live updates via WebSocket. Frontend renders ships on an interactive map with live updates.

**Strengths:**  
• Real-time WebSocket architecture — non-trivial infrastructure, not a static dashboard  
• Proper separation: backend (ais_stream.py, websocket_server.py, ship_filter.py) + frontend (MapView.jsx, shipLayer.jsx)  
• Live AIS data integration — connects to actual maritime data feeds, not mock data  
• React frontend with MapLibreGL for high-performance map rendering  
• Clean project structure with clear module boundaries

**Weaknesses:**  
• No README — zero documentation  
• Commit messages are uninformative ("Updated_4", "Updated_3")  
• Vercel deployment is auth-gated (requires Vercel login to view)  
• Minimal frontend polish — functional but basic UI

**Score:** 7 / 10  
- Engineering: 3.5/4 | Code Quality: 1/2 | Completeness: 1.5/2 | Depth: 0.5/1 | Docs: 0/1

**Decision:** ✅ SELECTED  
**Reason:** Demonstrates genuine real-time system engineering — WebSocket, live data streaming, map rendering. This is a working system, not a tutorial. The auth-gated deployment and missing README are concerning, but the code quality is solid.

---

### 2. Radhika Dhama + Ankush Agarwal — Real-Time Satellite Tracker

**Dashboard:** https://satellite-tracker-frontend-nu.vercel.app/  
**GitHub:** https://github.com/RadhikaDhama/real-time-satellite-tracker  
**Code:** 383 lines | 25 commits | All by Radhika Dhama  
**Tech Stack:** FastAPI, Skyfield/SGP4, APScheduler, React frontend

**Project Summary:**  
Full-stack satellite visualization. Backend fetches TLE (Two-Line Element) data from public datasets, propagates orbital mechanics using SGP4/Skyfield, generates analytics (constellations, orbit distribution), and exposes REST APIs. React frontend displays satellites on a 3D globe.

**Strengths:**  
• Real orbital mechanics — uses SGP4 propagation library, not just drawing circles  
• Modular backend architecture: api/routes.py, processing/, analytics/, services/, ingestion/  
• 25 commits showing iterative development  
• Comprehensive README with architecture diagrams, setup instructions, role breakdown  
• Background scheduler for periodic TLE data refresh

**Weaknesses:**  
• All commits by Radhika — Ankush's contribution unclear from git history  
• Frontend appears to be a static shell (loads but shows placeholder data) — backend API connection may be incomplete  
• Committed `__pycache__` directories — indicates less experience with production hygiene  
• Analytics modules are relatively thin (22-56 lines each)

**Score:** 6.5 / 10  
- Engineering: 3/4 | Code Quality: 1/2 | Completeness: 1/2 | Depth: 0.5/1 | Docs: 1/1

**Decision:** ✅ SELECTED (marginal)  
**Reason:** Strong backend with real orbital mechanics and good architecture. The comprehensive README shows engineering maturity. The front-end appears incomplete, but the backend alone demonstrates solid systems thinking. Radhika clearly did the heavy lifting.

---

### 3. Sania Rawat + Bibek Rout — Satellites Over My City (Coriolis Predictor)

**Dashboard:** https://web-production-2ea3c.up.railway.app/  
**GitHub:** https://github.com/saniarawat/Coriolis-satellite-predictor-app  
**Code:** 1,374 lines | 6 commits | All by saniarawat (Sania)  
**Tech Stack:** Flask, SQLite, Celestrak TLE API, Leaflet.js, Chart.js

**Project Summary:**  
Full-stack app predicting satellite passes over any city. User enters a city name, backend fetches TLE data from Celestrak, computes pass predictions using orbital propagation, and frontend displays interactive maps with ground tracks and a data dashboard with charts.

**Strengths:**  
• End-to-end working product — search → prediction → map → charts pipeline is complete  
• Proper backend architecture: routes/, services/, database/, config.py  
• Database layer for caching satellite data (SQLite)  
• Frontend includes interactive Leaflet map with animated satellite ground tracks  
• Railway deployment is live and functional  
• Demo screenshots in README  
• Production config (gunicorn, Procfile, railway.json)

**Weaknesses:**  
• Only 6 commits — less iterative history to evaluate  
• Frontend is vanilla JS (300 lines) — functional but not modern  
• Backend services are thin (pass_predictor.py ~66 lines) — the actual orbital mechanics is relatively simple  
• Second student (Bibek) has no visible contribution in git

**Score:** 7 / 10  
- Engineering: 3/4 | Code Quality: 1/2 | Completeness: 2/2 | Depth: 0.5/1 | Docs: 0.5/1

**Decision:** ✅ SELECTED  
**Reason:** A complete, working product with search, prediction, mapping, and analytics. The deployment on Railway works. This demonstrates full-stack engineering capability. The frontend is basic but the end-to-end pipeline is real.

---

### 4. Rajveer Singh + Dhruv Vasantkumar Patel — Urban Intelligence Dashboard

**Dashboard:** https://urban-intelligence-dashboard.vercel.app/  
**GitHub:** https://github.com/rsinghsssd-byte/urban-intelligence-dashboard  
**Code:** 2,223 lines | 8 commits (4 Rajveer, 4 Dhruv)  
**Tech Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion, Leaflet, Recharts, Overpass API

**Project Summary:**  
Urban infrastructure analytics dashboard for Indian cities. Fetches real OpenStreetMap data via Overpass API (hospitals, schools, traffic signals, buildings), analyzes underserved areas using Haversine distance calculations, generates AI strategy recommendations, and renders everything on an interactive map with analytics charts.

**Strengths:**  
• Production-quality UI — "Dark Mode Glassmorphism" with Framer Motion animations  
• Real data pipeline: fetch_osm_data.js pulls live data from OpenStreetMap Overpass API  
• Mathematical rigor: Haversine formula for geographic distance, grid-based underserved area detection  
• Multi-tab dashboard: Map view, Analytics charts, AI Strategy generation  
• TypeScript throughout — type safety, proper interfaces (geoUtils.ts)  
• Next.js API routes serving structured JSON data  
• AI strategy generation endpoint (generate-strategy API route) — uses LLM to generate urban planning recommendations  
• Both students contributed (clear division: Dhruv=backend/data, Rajveer=frontend)

**Weaknesses:**  
• Data appears to be pre-fetched for Bangalore only (static JSON), not truly dynamic  
• AI strategy endpoint may be template-based rather than genuine LLM integration  
• Frontend is heavy (React + Next.js) for what's essentially a data viewer

**Score:** 8 / 10  
- Engineering: 3.5/4 | Code Quality: 2/2 | Completeness: 1.5/2 | Depth: 0.5/1 | Docs: 0.5/1

**Decision:** ✅ SELECTED  
**Reason:** Best UI/UX of all projects. Modern TypeScript/Next.js stack with real data engineering. The Haversine-based underserved area detection shows mathematical thinking. Both students clearly contributed. The AI strategy generation feature adds depth.

---

### 5. Urjaswi Chakraborty + Aarcha Mukesh — Satellite Collision Risk Detector

**Dashboard:** https://satellite-collision-detector.vercel.app/  
**GitHub:** https://github.com/chakraborty-urjaswi/satellite-collision-detector  
**Code:** 1,882 lines | 4 commits (Aarcha: 3, Urjaswi: 1)  
**Tech Stack:** FastAPI, CelesTrak API, Pytest, React + Vite frontend

**Project Summary:**  
Satellite collision risk assessment engine. Backend propagates satellite orbits using TLE data, computes pairwise proximity between all active satellites, and scores collision risk based on distance, relative velocity, and object size. Includes a formal risk scoring model (RiskScorer dataclass) and physics-based tests.

**Strengths:**  
• Strongest technical depth of all projects — formal risk model with normalized scoring  
• Production-quality code patterns: dataclasses with frozen/slots, proper type hints, lifespan context manager  
• Includes pytest tests for orbital propagation (ISS altitude validation)  
• Clean engine architecture: propagator.py, proximity.py, risk_model.py  
• CelesTrak service with async/await and proper resource cleanup  
• Risk scoring model is mathematically grounded (normalization, clamping, collision probability estimation)  
• Well-structured React frontend (Vite + JSX)

**Weaknesses:**  
• Only 4 commits — very compressed development history  
• No README  
• Aarcha did 3 of 4 commits — Urjaswi's contribution unclear  
• Frontend is scaffolded but may be minimal  
• Deployment shows only "frontend" placeholder text

**Score:** 7.5 / 10  
- Engineering: 3.5/4 | Code Quality: 2/2 | Completeness: 1/2 | Depth: 1/1 | Docs: 0/1

**Decision:** ✅ SELECTED  
**Reason:** Highest code quality and technical depth among all projects. The RiskScorer with mathematical normalization, pytest tests for orbital mechanics, and proper async architecture demonstrate engineering maturity well beyond typical student work. The lack of README and sparse commits are the only weaknesses.

---

### 6. Arkaprabha Chakraborty + Swikriti Paul — Skill Intelligence Dashboard

**Dashboard:** https://skill-intelligence-dashboard-app-7dawzgmvesva35voqc7i3b.streamlit.app/  
**GitHub:** https://github.com/kriti212/Skill-Intelligence-Dashboard-App  
**Code:** 979 lines | 20 commits (Swikriti: 10, Arkaprabha: 4, kriti212 bot: 6)  
**Tech Streamlit**, Pandas, Plotly, NetworkX, spaCy (optional)

**Project Summary:**  
Streamlit-based analytics dashboard that extracts skill mentions from activity logs and visualizes them with interactive charts, treemaps, and network graphs. Processes CSV datasets to detect skill keywords, groups them into hierarchical categories, and displays distribution insights.

**Strengths:**  
• Well-documented README with architecture diagram, feature list, setup instructions  
• Modular code: data_processor.py, skill_grouper.py, backend/dataset_ingestion.py  
• Multiple visualization types: KPIs, bar charts, treemaps, NetworkX relationship graphs  
• Configurable thresholds via Streamlit sidebar  
• Dark-themed UI with custom CSS  
• 20 commits show iterative development  
• Devcontainer support

**Weaknesses:**  
• Essentially a data visualization tool — no real "engineering" system (no API, no backend service, no deployment pipeline)  
• Uses Streamlit, which is primarily for prototyping, not production  
• Skill extraction is regex-based — simple text matching, not NLP  
• The "hierarchy" is a hardcoded dictionary — no learning or adaptation  
• Two GitHub accounts involved (Swikriti Paul and kriti212) — unclear if same person  
• No backend API or service layer — just a Streamlit app

**Score:** 4 / 10  
- Engineering: 1/4 | Code Quality: 1/2 | Completeness: 1/2 | Depth: 0/1 | Docs: 1/1

**Decision:** ❌ REJECTED  
**Reason:** This is a Streamlit visualization app, not an engineering project. No backend service, no API, no deployment pipeline. Regex-based skill extraction is tutorial-level NLP. Good documentation but doesn't compensate for lack of engineering substance.

---

### 7. Sourit Mitra + Aman Ray — AI-Based Soft Skills Analyzer

**Dashboard:** https://softskillanalyser-kqmauq2z6csnfu3hesqprr.streamlit.app/  
**GitHub:** https://github.com/amanray8900-ux/Soft_Skill_Analyser  
**Code:** 554 lines | 16 commits (Aman: 13, Sourit: 3)  
**Tech Stack:** Streamlit, OpenAI Whisper (local), Librosa, Cerebras LLM, Plotly

**Project Summary:**  
Audio analysis tool that evaluates vocal patterns and communication style. Uploads audio → transcribes with Whisper → analyzes pitch, pauses, filler words with Librosa → sends text to Cerebras LLM for semantic feedback → displays radar charts and scoring cards.

**Strengths:**  
• Multi-modal pipeline: audio → transcription → NLP → visualization — genuinely interesting architecture  
• Local Whisper transcription (not API-dependent)  
• Librosa audio analysis for pitch variation, pause detection — real signal processing  
• Cerebras LLM integration for semantic coaching feedback  
• Modular structure: transcription.py, audio_processing.py, text_analysis.py, scoring_engine.py, visual_components.py  
• Scoring formula with weighted metrics (pacing, clarity, engagement, content)  
• 16 commits with meaningful progression (from initial build through refinements)

**Weaknesses:**  
• Streamlit again — not a production architecture  
• Aman authored 13 of 16 commits — Sourit's contribution minimal  
• LLM analysis depends on Cerebras API — external dependency  
• Scoring weights are heuristic (tuned by feel, not validated)

**Score:** 5.5 / 10  
- Engineering: 2/4 | Code Quality: 1.5/2 | Completeness: 1/2 | Depth: 0.5/1 | Docs: 0.5/1

**Decision:** ❌ REJECTED  
**Reason:** Interesting multi-modal concept but Streamlit prototype, not a production system. The audio pipeline shows ambition but the overall engineering is prototype-level. Aman clearly did nearly all the work. Borderline, but the lack of proper backend/frontend architecture puts it below the threshold.

---

### 8. Aarushi Kumar + Kanshiya Uday — Hands-On Persona Analyzer

**Dashboard:** https://ai-based-hands-on-skill-analyzer-production.up.railway.app/  
**GitHub:** https://github.com/Uday-Kanshiya/AI-Based-Hands-On-Skill-Analyzer  
**Code:** 1,630 lines | 11 commits (Uday: 4, "Your Name"/Aarushi: 7)  
**Tech Stack:** FastAPI, Streamlit frontend, PyGithub, pdfplumber, yt-dlp, OpenAI Whisper, Chart.js

**Project Summary:**  
Full-stack system for evaluating a developer's "hands-on persona" from their GitHub profile, resume, and demo videos. Collects GitHub repos/languages/stars via PyGithub, parses resumes with pdfplumber, validates deployment URLs, transcribes demo videos with Whisper, and generates a composite engineering score.

**Strengths:**  
• Multi-signal evaluation pipeline — genuinely novel concept  
• GitHub API integration with PyGithub (repos, stars, languages, commit frequency)  
• Resume parsing with pdfplumber + NLP keyword extraction  
• Video transcription pipeline (yt-dlp + Whisper)  
• Heuristic scoring engine (scorer.py) with weighted categories  
• FastAPI backend with proper API endpoints  
• Dockerfile for deployment  
• Both students contributed (clear split: Aarushi=frontend/UI, Uday=backend/pipeline)  
• Railway deployment works

**Weaknesses:**  
• The app evaluates OTHER developers — it's a tool, not a demonstration of their own engineering  
• Scoring algorithm is heuristic and may not correlate with actual engineering quality  
• Frontend is Streamlit (despite having a FastAPI backend)  
• Some commit messages say "Your Name" — suggests template usage  
• Link validation is basic HTTP status check

**Score:** 6 / 10  
- Engineering: 2.5/4 | Code Quality: 1.5/2 | Completeness: 1.5/2 | Depth: 0.5/1 | Docs: 0/1

**Decision:** ❌ REJECTED  
**Reason:** While architecturally interesting (multi-signal evaluation), this is meta — a tool that evaluates developers rather than a demonstration of building something meaningful. The scoring algorithm is arbitrary. Streamlit frontend with a FastAPI backend is inconsistent architecture. Borderline, but the other candidates have stronger signals of hands-on engineering.

---

### 9. Aryan Chauhan + Nandini Agarwal — Stratos Intel Dashboard (Coriolis)

**Dashboard:** https://stratos-intel-dashboard.onrender.com/  
**GitHub:** https://github.com/Aryanchauhan08/stratos-intel-dashboard  
**Code:** 5,176 lines | 51 commits (nikhil1770: ~45, Aryanchauhan08: 2, Nandini: 1, merge commits)  
**Tech Stack:** FastAPI, SQLAlchemy, spaCy NER, VADER Sentiment, Nominatim Geocoder, SQLite, Mastodon API, RSS feeds, GDELT

**Project Summary:**  
Real-time global intelligence platform that aggregates social signals from Mastodon, RSS news feeds, and GDELT geopolitical events. Processes content through NLP pipeline (spaCy NER → Nominatim geocoding → VADER sentiment) and displays geo-tagged data on an interactive world map.

**Strengths:**  
• Most architecturally complex project — multi-source data ingestion, NLP processing pipeline, real-time streaming  
• Multiple data sources: Mastodon streaming API, RSS feeds, GDELT Global Knowledge Graph  
• Full NLP pipeline: spaCy NER for location extraction, Nominatim for geocoding, VADER for sentiment  
• Background processing workers with proper status tracking (pending → processed → error)  
• Content-based deduplication logic  
• SQLAlchemy with proper ORM models (SocialActivity, ProcessedActivity)  
• REST API serving GeoJSON for the map frontend  
• 51 commits show extensive iterative development  
• Production deployment on Render with continuous pipeline

**Weaknesses:**  
• CRITICAL: GitHub username "nikhil1770" authored ~45 of 51 commits. This is NEITHER Aryan Chauhan nor Nandini Agarwal. The actual contributor is not listed in the project team.  
• Aryan Chauhan only has 2 commits (1 merge, 1 initial)  
• Nandini has 1 commit (fixing duplicates)  
• The deployed dashboard shows "Awaiting intercept packets..." — data pipeline may not be actively running  
• Database reset scripts suggest reliability issues  
• `rss_ingest.log` and `api.log` committed to repo — debugging artifacts

**Score:** 3 / 10  
- Engineering: 3/4 (the code is genuinely impressive) | Code Quality: 1/2 | Completeness: 0/2 | Depth: 1/1 | Docs: 0/1  
- **PENALTY: -2 for apparent third-party authorship**

**Decision:** ❌ REJECTED  
**Reason:** The code is genuinely impressive — this is the most complex system of all submissions. However, the actual engineering work was done by "nikhil1770," who is NOT listed as a team member. Aryan's and Nandini's commit history shows minimal contribution. This is either a borrowed/template project or an unlisted collaborator did the work. Cannot select based on work that isn't demonstrably the student's own.

---

### 10. Agnivesh + Anupam — Project Assignment System

**Dashboard:** https://project-assignment-system-fpez5p826b5xwwjfxs2nbg-silver-frost.streamlit.app/  
**GitHub:** https://github.com/agnivesh-chatterjee/Project-assignment-system  
**Code:** 1,236 lines | 68 commits (Agnivesh: ~60, Anupam/Archer-Frost: ~8)  
**Tech Stack:** FastAPI, Streamlit dashboard, Pandas, team formation algorithm, match scoring

**Project Summary:**  
System for matching students to projects based on skill profiles and project requirements. Uses a scoring algorithm to compute compatibility scores, forms teams, and provides a Streamlit dashboard for visualization and management.

**Strengths:**  
• 68 commits — most active development of any project  
• FastAPI REST backend with CRUD endpoints (students, projects, teams)  
• Match scoring algorithm (matchscore_generator.py) — considers skill alignment  
• Team formation logic (team_formation.py) — considers student preferences and project requirements  
• Streamlit dashboard with tabs: Students, Projects, Match Scores, Teams  
• CSV data persistence (students.csv, projects.csv, scores.csv, teams.csv)  
• Both students contributed (Agnivesh: backend/algorithms, Anupam: dashboard/UI)  
• Production deployment on Streamlit Cloud  
• Database directory with seed data and documentation

**Weaknesses:**  
• The system is a meta-tool (assigning projects to students) — similar to project #8, it's a tool about the internship process rather than a technical demonstration  
• Streamlit frontend — limited UI sophistication  
• Match scoring algorithm is simple weighted scoring — not sophisticated  
• No real data pipeline or external API integration  
• CSV persistence instead of proper database

**Score:** 5 / 10  
- Engineering: 2/4 | Code Quality: 1/2 | Completeness: 1.5/2 | Depth: 0/1 | Docs: 0.5/1

**Decision:** ❌ REJECTED  
**Reason:** Functional but meta — a student project assignment tool doesn't demonstrate deep engineering capability. The match scoring is simple weighted matching. Both students contributed but the project lacks the technical depth seen in the top selections.

---

## Final Selection

### Top 5 Selected Students

| Rank | Student Name | Project | Score | Key Signal |
|------|-------------|---------|-------|------------|
| 1 | **Rajveer Singh** | Urban Intelligence Dashboard | 8/10 | Best UI/UX, TypeScript, real OSM data, AI strategy generation |
| 2 | **Urjaswi Chakraborty** | Satellite Collision Risk Detector | 7.5/10 | Highest code quality, formal risk model, pytest tests |
| 3 | **Snehash Kumar Behera** | Ship Radar | 7/10 | Real-time WebSocket, live AIS data, map rendering |
| 4 | **Sania Rawat** | Satellites Over My City | 7/10 | Complete working product, search→predict→map→charts pipeline |
| 5 | **Radhika Dhama** | Real-Time Satellite Tracker | 6.5/10 | Orbital mechanics (SGP4), modular backend, comprehensive docs |

### Why These 5 Stand Out

**Rajveer Singh** — Demonstrated the most polished engineering. The Urban Intelligence Dashboard uses a modern TypeScript/Next.js stack with real OpenStreetMap data integration, Haversine-based geographic analysis, and an AI strategy generation endpoint. The UI quality (Glassmorphism, Framer Motion, multi-tab layout) is professional-grade. Both students contributed meaningfully.

**Urjaswi Chakraborty** — The Satellite Collision Risk Detector has the highest code quality of all submissions. The RiskScorer dataclass with mathematical normalization, pytest tests for orbital propagation validation, and proper async architecture with lifespan management show engineering maturity well beyond typical student work. Even though the frontend is minimal, the backend is production-quality.

**Snehash Kumar Behera** — Built a genuine real-time system with WebSocket communication and live AIS maritime data streaming. This isn't a static dashboard — it's a live data pipeline with React frontend rendering. The architecture (ais_stream.py → websocket_server.py → ship_filter.py → React) shows understanding of real-time systems.

**Sania Rawat** — Built the most complete end-to-end product. The Satellites Over My City app works: enter a city, get satellite pass predictions, view ground tracks on a map, explore analytics charts. Production deployment on Railway with proper gunicorn configuration. The complete pipeline (Celestrak → prediction → SQLite cache → Leaflet map → Chart.js dashboard) demonstrates full-stack capability.

**Radhika Dhama** — Demonstrated genuine understanding of orbital mechanics using SGP4/Skyfield propagation libraries. The modular backend architecture (analytics/, processing/, ingestion/, services/) and comprehensive README with architecture diagrams show engineering discipline. The frontend is incomplete but the backend alone demonstrates solid systems thinking.

---

### Why Others Were Rejected

**Arkaprabha Chakraborty (4/10)** — Streamlit visualization app, not an engineering project. Regex-based skill extraction is tutorial-level. Good documentation doesn't compensate for lack of engineering substance.

**Sourit Mitra (5.5/10)** — Ambitious multi-modal concept (audio → NLP → visualization) but Streamlit prototype with Aman doing nearly all the work. Interesting but prototype-level.

**Aarushi Kumar (6/10)** — The "Persona Analyzer" is meta — a tool that evaluates developers rather than a demonstration of building something meaningful. Streamlit + FastAPI inconsistency. Borderline but weaker signals than selected candidates.

**Aryan Chauhan (3/10, adjusted)** — The Stratos Intel Dashboard is the most architecturally complex project, BUT the actual work (45/51 commits) was done by "nikhil1770," who is not a listed team member. Aryan and Nandini contributed minimally. Cannot select based on someone else's work.

**Agnivesh (5/10)** — Functional student-project matching tool but meta (about the internship process itself) and lacks technical depth. Simple weighted scoring, CSV storage, Streamlit UI.

---

### Final Hiring Manager Commentary

The strongest signal across all selected students was **building working systems, not just prototypes**. Rajveer built a multi-tab urban analytics platform with real geographic data. Urjaswi built a physics-based risk scoring engine with formal tests. Snehash built a live WebSocket data pipeline. Sania built a complete search-to-visualization satellite prediction app. Radhika built a backend with real orbital mechanics.

The rejected projects fell into predictable patterns: Streamlit prototypes without backend architecture (#6, #7, #8), meta-tools that evaluate others rather than demonstrating their own engineering (#8, #10), or projects where the actual contributor isn't the student (#9).

Common weakness across ALL projects: commit messages are generally poor ("Updated", "fix", "Update README.md"). This suggests students are still learning version control best practices — an area for mentorship.

The top 5 students show they can design systems, write modular code, integrate external APIs, deploy to production, and (in some cases) write tests. These are the signals that predict successful internship performance.
