"""AgentForge Auth Router"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentforge.api.auth import create_access_token, get_current_user, hash_password, verify_password
from agentforge.api.models import TokenResponse, UserRegisterRequest, UserLoginRequest, UserResponse
from agentforge.config import get_config
from agentforge.database.database import get_db_session
from agentforge.database.repository import UserRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: UserRegisterRequest, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    if await repo.get_by_username(request.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if await repo.get_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await repo.create(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    user = await repo.get_by_username(request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    cfg = get_config()
    token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=cfg.auth.access_token_expire_minutes),
    )
    return TokenResponse(
        access_token=token,
        expires_in=cfg.auth.access_token_expire_minutes * 60,
        user_id=user.id,
        username=user.username,
        role=user.role,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserResponse.model_validate(current_user)
