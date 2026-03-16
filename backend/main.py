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
from starlette.middleware.base import BaseHTTPMiddleware
from database import Base, engine, SessionLocal
from api import candidates
from api.admin import router as auth_router, admin_router, seed_admin
from api.assignments import router as assignment_router, candidate_assignment_router
from api.assignments import grading_router

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


@app.get("/")
def root():
    return {"service": "Intern Selection Pipeline", "status": "running"}


@app.get("/health")
def health():
    return {"ok": True}
