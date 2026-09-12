"""
AgentForge JWT Authentication.

JWT token creation, validation, and FastAPI dependencies.
Uses python-jose + passlib[bcrypt].
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agentforge.config import get_config
from agentforge.database.database import get_db_session
from agentforge.database.models import User
from agentforge.database.repository import UserRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)

try:
    from jose import JWTError, jwt
    _JOSE_AVAILABLE = True
except ImportError:
    _JOSE_AVAILABLE = False
    logger.warning("python-jose not installed. JWT auth disabled.")

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _PASSLIB_AVAILABLE = True
except ImportError:
    _PASSLIB_AVAILABLE = False
    logger.warning("passlib not installed. Password hashing disabled.")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if not _PASSLIB_AVAILABLE:
        return password  # Fallback (development only)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    if not _PASSLIB_AVAILABLE:
        return plain_password == hashed_password
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if not _JOSE_AVAILABLE:
        return "dev-token-no-jose"

    cfg = get_config()
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=cfg.auth.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, cfg.auth.secret_key, algorithm=cfg.auth.algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    if not _JOSE_AVAILABLE:
        return {"sub": "dev-user", "role": "admin"}

    cfg = get_config()
    try:
        payload = jwt.decode(token, cfg.auth.secret_key, algorithms=[cfg.auth.algorithm])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session=Depends(get_db_session),
) -> Optional[User]:
    """
    FastAPI dependency — get the authenticated user from JWT token.

    If auth is disabled (AUTH_ENABLE_AUTH=false), returns None (anonymous access).
    """
    cfg = get_config()

    # Auth disabled — anonymous access
    if not cfg.auth.enable_auth:
        return None

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


async def get_current_user_or_none(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session=Depends(get_db_session),
) -> Optional[User]:
    """Same as get_current_user but returns None instead of raising on missing token."""
    cfg = get_config()
    if not cfg.auth.enable_auth:
        return None
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
