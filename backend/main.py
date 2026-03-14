import os
import sys

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, SessionLocal
from api import candidates
from api.admin import router as auth_router, admin_router, seed_admin
from api.assignments import router as assignment_router, candidate_assignment_router

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

app = FastAPI(
    title="Intern Selection Pipeline",
    version="0.2.0",
    description="Candidate submission and evaluation platform",
)

# CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates.router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(assignment_router)
app.include_router(candidate_assignment_router)


@app.get("/")
def root():
    return {"service": "Intern Selection Pipeline", "status": "running"}


@app.get("/health")
def health():
    return {"ok": True}
