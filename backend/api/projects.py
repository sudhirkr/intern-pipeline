"""Google Sheet Projects API — fetch and serve student project data."""
import csv
import io
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_admin
from models import Admin

router = APIRouter(prefix="/api/admin/projects", tags=["projects"])

# Google Sheet constants
SHEET_ID = "19g7AKy2h_3t3shnfMLGYNpeHVmbOdjgw"
MODIFIED_GROUPS_GID = 39892379

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MODIFIED_GROUPS_GID}"

# Simple in-memory cache: (timestamp, data)
_cache: tuple[float, list[dict]] | None = None
CACHE_TTL_SECONDS = 300  # 5 minutes


def _normalize_header(h: str) -> str:
    """Convert header like 'Student Name' -> 'student_name'."""
    return h.strip().lower().replace(" ", "_").replace("-", "_")


def _fetch_and_parse() -> list[dict]:
    """Fetch CSV from Google Sheet, skip note row, parse headers."""
    resp = httpx.get(SHEET_URL, timeout=30.0, follow_redirects=True)
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
    data = []
    for row in rows[2:]:  # skip note + header
        if not any(cell.strip() for cell in row):
            continue
        record = {}
        for i, h in enumerate(headers):
            record[h] = row[i].strip() if i < len(row) else ""
        data.append(record)

    return data


@router.get("/sheet")
def get_projects_sheet(
    admin: Admin = Depends(get_current_admin),
):
    """Fetch Modified_Groups tab and return parsed JSON array."""
    global _cache
    now = time.time()

    # Check cache
    if _cache is not None and (now - _cache[0]) < CACHE_TTL_SECONDS:
        return _cache[1]

    try:
        data = _fetch_and_parse()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Google Sheet: {e}")

    _cache = (now, data)
    return data
