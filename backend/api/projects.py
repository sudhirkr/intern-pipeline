"""Google Sheet Projects API — fetch and serve student project data."""
import csv
import io
import re
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_admin
from models import Admin

router = APIRouter(prefix="/api/admin/projects", tags=["projects"])

# Default Google Sheet constants
SHEET_ID = "19g7AKy2h_3t3shnfMLGYNpeHVmbOdjgw"
MODIFIED_GROUPS_GID = 39892379

DEFAULT_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MODIFIED_GROUPS_GID}"

# In-memory caches: keyed by sheet URL
_cache: dict[str, tuple[float, list[dict]]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _normalize_header(h: str) -> str:
    """Convert header like 'Student Name' -> 'student_name'."""
    return h.strip().lower().replace(" ", "_").replace("-", "_")


def _extract_sheet_url(user_url: str) -> str:
    """Convert a Google Sheet view URL to a CSV export URL.

    Accepts:
      - Full CSV export URL (passthrough)
      - View/edit URL like https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=GID
    """
    if "export?format=csv" in user_url:
        return user_url

    match = re.search(
        r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)", user_url
    )
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid Google Sheet URL. Must be a docs.google.com/spreadsheets/ link.",
        )

    sheet_id = match.group(1)

    # Try to extract gid from URL hash
    gid_match = re.search(r"[#&]gid=(\d+)", user_url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def _fetch_and_parse(sheet_url: str) -> list[dict]:
    """Fetch CSV from Google Sheet, skip note row, parse headers."""
    resp = httpx.get(sheet_url, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()

    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)

    if len(rows) < 2:
        return []

    # Row 0 = note (skip), Row 1 = headers
    headers = [_normalize_header(h) for h in rows[1]]
    # Fix known typos in headers
    typo_map = {"attendence": "attendance"}
    headers = [typo_map.get(h, h) for h in headers]
    raw = []
    for row in rows[2:]:  # skip note + header
        if not any(cell.strip() for cell in row):
            continue
        record = {}
        for i, h in enumerate(headers):
            record[h] = row[i].strip() if i < len(row) else ""
        raw.append(record)

    return _group_into_projects(raw)


def _group_into_projects(raw: list[dict]) -> list[dict]:
    """Group flat student rows into project cards (2 students each).

    Rules:
      - First row with a project_name starts a new project group.
      - Subsequent rows with empty project_name join the previous group.
      - Each project collects its students into a 'students' list.
    """
    projects = []
    current = None

    for row in raw:
        has_project = bool(row.get("project_name", "").strip())
        has_student = bool(row.get("student_name", "").strip())

        if has_project:
            # Start a new project group
            current = {
                "project_name": row["project_name"],
                "project_link": row.get("project_link", ""),
                "students": [],
                # Aggregate links — take the first non-empty value across students
                "dashboard_link": row.get("dashboard_link", ""),
                "github_repo_link": row.get("github_repo_link", ""),
            }
            if has_student:
                current["students"].append({
                    "student_name": row["student_name"],
                    "email": row.get("email", ""),
                    "attendance": row.get("attendance", ""),
                })
            projects.append(current)
        elif current is not None:
            # Continuation of previous project
            if has_student:
                current["students"].append({
                    "student_name": row["student_name"],
                    "email": row.get("email", ""),
                    "attendance": row.get("attendance", ""),
                })
            # Merge links from continuation rows (first non-empty wins)
            if not current["dashboard_link"] and row.get("dashboard_link", ""):
                current["dashboard_link"] = row["dashboard_link"]
            if not current["github_repo_link"] and row.get("github_repo_link", ""):
                current["github_repo_link"] = row["github_repo_link"]

    return projects


@router.get("/sheet")
def get_projects_sheet(
    sheet_url: str = Query(None, description="Custom Google Sheet URL (view or export link)"),
    admin: Admin = Depends(get_current_admin),
):
    """Fetch project data from a Google Sheet and return grouped JSON.

    If sheet_url is provided, uses that sheet; otherwise uses the default.
    """
    now = time.time()

    # Resolve CSV export URL
    csv_url = _extract_sheet_url(sheet_url) if sheet_url else DEFAULT_SHEET_URL

    # Check cache
    if csv_url in _cache and (now - _cache[csv_url][0]) < CACHE_TTL_SECONDS:
        return _cache[csv_url][1]

    try:
        data = _fetch_and_parse(csv_url)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Google Sheet: {e}")

    _cache[csv_url] = (now, data)
    return data
