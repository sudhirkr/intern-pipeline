"""Authentication and authorization utilities."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import Admin, Candidate

# ── Config ──
SECRET_KEY = "intern-pipeline-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def generate_submission_token() -> str:
    """Generate a unique candidate submission token."""
    return uuid.uuid4().hex


# ── Dependencies ──

async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Admin:
    """Require a valid admin JWT. Returns the Admin object."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    admin_id = payload.get("sub")
    admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin


async def get_optional_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[Admin]:
    """Return admin if valid JWT present, else None (no error)."""
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("role") != "admin":
            return None
        admin_id = payload.get("sub")
        return db.query(Admin).filter(Admin.id == int(admin_id)).first()
    except HTTPException:
        return None


def get_candidate_from_token(
    request: Request,
    token: Optional[str] = None,
) -> Optional[str]:
    """Extract submission_token from query param or Authorization header."""
    if token:
        return token
    # Try Authorization header (Bearer <token>)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def require_candidate_token(
    request: Request,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Candidate:
    """Require a valid candidate submission token. Returns the Candidate."""
    sub_token = get_candidate_from_token(request, token)
    if not sub_token:
        raise HTTPException(status_code=401, detail="Submission token required")
    candidate = db.query(Candidate).filter(Candidate.submission_token == sub_token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid submission token")
    return candidate
