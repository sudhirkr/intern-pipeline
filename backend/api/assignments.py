"""Assignment CRUD and candidate-assignment linking API."""
import os
import shutil
import tempfile
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from database import get_db
from models import Assignment, CandidateAssignment, Candidate, AssignmentStatus
from schemas import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentListResponse, CandidateAssignmentResponse,
)
from auth import get_current_admin, get_optional_admin, get_candidate_from_token, decode_access_token

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentResponse, status_code=201)
def create_assignment(
    body: AssignmentCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Create a new assignment (admin only)."""
    assignment = Assignment(
        title=body.title,
        description=body.description,
        tech_stack=body.tech_stack,
        difficulty=body.difficulty,
        expected_outcome=body.expected_outcome,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("", response_model=AssignmentListResponse)
def list_assignments(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List all assignments (admin only)."""
    assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).all()
    return AssignmentListResponse(total=len(assignments), assignments=assignments)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Get a single assignment (admin only)."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    body: AssignmentUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Update an assignment (admin only)."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(assignment, field):
            setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Delete an assignment (admin only)."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Also delete all candidate-assignment links
    db.query(CandidateAssignment).filter(CandidateAssignment.assignment_id == assignment_id).delete()
    db.delete(assignment)
    db.commit()


@router.post("/{assignment_id}/assign/{candidate_id}", response_model=CandidateAssignmentResponse, status_code=201)
def assign_to_candidate(
    assignment_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Assign a project to a candidate (admin only)."""
    # Check assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check candidate exists
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Check if already assigned
    existing = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Candidate already has an assignment")

    candidate_assignment = CandidateAssignment(
        candidate_id=candidate_id,
        assignment_id=assignment_id,
        status=AssignmentStatus.ASSIGNED,
    )
    db.add(candidate_assignment)
    try:
        db.commit()
        db.refresh(candidate_assignment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Candidate already has an assignment")

    return candidate_assignment


@router.get("/candidate/{candidate_id}", response_model=CandidateAssignmentResponse)
def get_candidate_assignment(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Get a candidate's assigned project (admin only)."""
    ca = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate_id
    ).first()
    if not ca:
        raise HTTPException(status_code=404, detail="No assignment found for this candidate")
    return ca


# ── Candidate-facing endpoint (via token) ──

candidate_assignment_router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@candidate_assignment_router.get("/{candidate_id}/assignment", response_model=CandidateAssignmentResponse)
def get_my_assignment(
    candidate_id: int,
    token: str | None = None,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Get candidate's assignment. Candidate can view their own via token, or admin via JWT."""
    # Check if admin
    is_admin = False
    try:
        auth_header = request.headers.get("Authorization", "") if request else ""
        if auth_header.startswith("Bearer "):
            payload = decode_access_token(auth_header[7:])
            if payload.get("role") == "admin":
                is_admin = True
    except Exception:
        pass

    if not is_admin:
        # Validate candidate token matches
        sub_token = token
        if not sub_token and request:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                sub_token = auth_header[7:]

        if not sub_token:
            raise HTTPException(status_code=401, detail="Admin JWT or candidate submission token required")

        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if candidate.submission_token != sub_token:
            raise HTTPException(status_code=403, detail="Access denied. Token does not match this candidate.")

    ca = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate_id
    ).first()
    if not ca:
        raise HTTPException(status_code=404, detail="No assignment found for this candidate")
    return ca


# Also expose candidate's assignment via by-token convenience
@candidate_assignment_router.get("/by-token/{token}/assignment", response_model=CandidateAssignmentResponse)
def get_assignment_by_token(
    token: str,
    db: Session = Depends(get_db),
):
    """Get candidate's assignment using their submission token."""
    candidate = db.query(Candidate).filter(Candidate.submission_token == token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid submission token")

    ca = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate.id
    ).first()
    if not ca:
        raise HTTPException(status_code=404, detail="No assignment found for this candidate")
    return ca


# ── Work Submission (candidate via token) ──

from schemas import SubmitWorkRequest, SubmitWorkResponse, GradeResponse
from services.github import check_github_repo
from services.deploy_check import check_deployed_url
from services.grader import calculate_overall_grade, clone_repo


@candidate_assignment_router.post("/by-token/{token}/submit-work", response_model=SubmitWorkResponse)
async def submit_work(
    token: str,
    body: SubmitWorkRequest,
    db: Session = Depends(get_db),
):
    """Candidate submits their work (GitHub repo + deployed URL) using their submission token."""
    candidate = db.query(Candidate).filter(Candidate.submission_token == token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid submission token")

    # Must have an assignment
    ca = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate.id
    ).first()
    if not ca:
        raise HTTPException(status_code=404, detail="No assignment found for this candidate")

    # Validate GitHub repo
    github_result = await check_github_repo(body.github_repo_url)

    # Validate deployed URL
    deploy_result = await check_deployed_url(body.deployed_url)

    # Update the candidate assignment
    ca.github_repo_url = body.github_repo_url
    ca.deployed_url = body.deployed_url
    ca.github_valid = 1 if github_result["valid"] else 0
    ca.github_stats = json.dumps(github_result)
    ca.deploy_valid = 1 if deploy_result["valid"] else 0
    ca.deploy_stats = json.dumps(deploy_result)
    ca.submitted_at = datetime.now(timezone.utc)

    # Update status
    if github_result["valid"] or deploy_result["valid"]:
        ca.status = AssignmentStatus.SUBMITTED

    db.commit()
    db.refresh(ca)

    return SubmitWorkResponse(
        message="Work submitted successfully" if (github_result["valid"] or deploy_result["valid"]) else "Work submitted but validation found issues. Please check the URLs.",
        github_valid=github_result["valid"],
        github_stats=json.dumps(github_result),
        deploy_valid=deploy_result["valid"],
        deploy_stats=json.dumps(deploy_result),
    )


# ── Grading Endpoints (admin) ──

grading_router = APIRouter(prefix="/api/grading", tags=["grading"])


@grading_router.post("/candidates/{candidate_id}/grade", response_model=GradeResponse)
async def grade_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin: trigger grading for a candidate's submission.

    Requires the candidate to have submitted work (GitHub + deploy URLs).
    Clones the repo, analyzes code quality, scores all categories.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    ca = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate_id
    ).first()
    if not ca:
        raise HTTPException(status_code=404, detail="No assignment found for this candidate")

    if not ca.github_repo_url and not ca.deployed_url:
        raise HTTPException(status_code=400, detail="Candidate has not submitted any work yet")

    # Clone repo for analysis
    repo_path = None
    if ca.github_repo_url:
        repo_path = tempfile.mkdtemp(prefix="grade_")
        clone_success = clone_repo(ca.github_repo_url, repo_path)
        if not clone_success:
            repo_path = None

    # Build candidate data for AI usage and creativity grading
    candidate_data = {
        "name": candidate.name,
        "skills": candidate.skills,
        "ai_tool_usage": candidate.ai_tool_usage,
        "projects": candidate.projects,
        "challenge_solved": candidate.challenge_solved,
    }

    # Calculate grades
    try:
        results = await calculate_overall_grade(
            deploy_stats=ca.deploy_stats or '{}',
            github_stats=ca.github_stats or '{}',
            candidate_data=candidate_data,
            repo_path=repo_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")

    # Clean up cloned repo
    if repo_path and os.path.exists(repo_path):
        try:
            shutil.rmtree(repo_path)
        except Exception:
            pass

    # Store results
    ca.grade_overall = results["overall"]
    ca.grade_deployed = results["deployed"]["score"]
    ca.grade_code_quality = results["code_quality"]["score"]
    ca.grade_ai_usage = results["ai_usage"]["score"]
    ca.grade_creativity = results["creativity"]["score"]

    feedback = {
        "deployed": results["deployed"]["feedback"],
        "code_quality": results["code_quality"]["feedback"],
        "ai_usage": results["ai_usage"]["feedback"],
        "creativity": results["creativity"]["feedback"],
    }
    ca.grade_feedback = json.dumps(feedback)
    ca.graded_at = datetime.now(timezone.utc)

    if ca.status != AssignmentStatus.GRADED:
        ca.status = AssignmentStatus.GRADED

    db.commit()
    db.refresh(ca)

    return GradeResponse(
        id=ca.id,
        candidate_id=ca.candidate_id,
        grade_overall=ca.grade_overall,
        grade_deployed=ca.grade_deployed,
        grade_code_quality=ca.grade_code_quality,
        grade_ai_usage=ca.grade_ai_usage,
        grade_creativity=ca.grade_creativity,
        grade_feedback=ca.grade_feedback,
        graded_at=ca.graded_at,
    )


@grading_router.get("/candidates/{candidate_id}/grade", response_model=GradeResponse)
async def get_candidate_grade(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin: get grade results for a candidate."""
    ca = db.query(CandidateAssignment).filter(
        CandidateAssignment.candidate_id == candidate_id
    ).first()
    if not ca:
        raise HTTPException(status_code=404, detail="No assignment found for this candidate")

    if ca.grade_overall is None:
        raise HTTPException(status_code=404, detail="Candidate has not been graded yet")

    return GradeResponse(
        id=ca.id,
        candidate_id=ca.candidate_id,
        grade_overall=ca.grade_overall,
        grade_deployed=ca.grade_deployed,
        grade_code_quality=ca.grade_code_quality,
        grade_ai_usage=ca.grade_ai_usage,
        grade_creativity=ca.grade_creativity,
        grade_feedback=ca.grade_feedback,
        graded_at=ca.graded_at,
    )
