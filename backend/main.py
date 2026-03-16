import os
import sys
import time
import uuid

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv()

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging before importing anything that uses loggers
from logging_config import setup_logging, get_logger
setup_logging()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from database import Base, engine, SessionLocal
from api import candidates
from api.admin import router as auth_router, admin_router, seed_admin
from api.assignments import router as assignment_router, candidate_assignment_router
from api.assignments import grading_router
from api.projects import router as projects_router

logger = get_logger("main")

# Ensure data directories exist before creating tables
os.makedirs("data", exist_ok=True)
os.makedirs("data/resumes", exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Seed default admin
db = SessionLocal()
try:
    seed_admin(db)
finally:
    db.close()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for traceability."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "%s %s → %d (%dms) [rid=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response


app = FastAPI(
    title="Intern Selection Pipeline",
    version="0.2.0",
    description="Candidate submission and evaluation platform",
)

# Request ID middleware (outermost)
app.add_middleware(RequestIDMiddleware)

# CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(candidates.router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(assignment_router)
app.include_router(candidate_assignment_router)
app.include_router(grading_router)
app.include_router(projects_router)


# --- Serve frontend (production) ---
import os

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")


@app.get("/")
def root():
    if os.path.isdir(FRONTEND_DIR):
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    return {"service": "Intern Selection Pipeline", "status": "running"}


@app.get("/health")
def health():
    return {"ok": True}


if os.path.isdir(FRONTEND_DIR):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    # SPA fallback: serve index.html for all non-API, non-static routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
