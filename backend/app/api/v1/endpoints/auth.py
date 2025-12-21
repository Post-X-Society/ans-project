"""
Authentication endpoints for user registration, login, and token management
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    RefreshTokenRequest,
    Token,
    TokenWithUser,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.token_blacklist import TokenBlacklistService

security = HTTPBearer()

router = APIRouter()


@router.post("/register", response_model=TokenWithUser, status_code=status.HTTP_200_OK)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)) -> TokenWithUser:
    """
    Register a new user with email and password.

    Default role is 'submitter'. Returns access and refresh tokens with user data.
    """
    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create new user with default role 'submitter'
    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
        role=UserRole.SUBMITTER,
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate tokens
    token_data = {
        "sub": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role.value,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenWithUser(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenWithUser, status_code=status.HTTP_200_OK)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenWithUser:
    """
    Login with email and password.

    Returns access and refresh tokens with user data on success.
    """
    # Find user by email
    stmt = select(User).where(User.email == credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenWithUser(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> Token:
    """
    Refresh access token using a valid refresh token.

    Security: Checks if refresh token is blacklisted before issuing new tokens.
    Returns new access and refresh tokens.
    """
    # Decode and verify refresh token
    payload = decode_token(refresh_data.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if refresh token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklist_service = TokenBlacklistService(redis)
        is_blacklisted = await blacklist_service.is_token_blacklisted(jti)
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been blacklisted (logged out)",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Verify token type is 'refresh'
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    from uuid import UUID

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    refresh_data: RefreshTokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    redis: Any = Depends(get_redis),
) -> Dict[str, str]:
    """
    Logout user by blacklisting both access and refresh tokens.

    Tokens are added to Redis blacklist and cannot be used after logout.
    Security improvement: Prevents compromised tokens from being used.
    """
    blacklist_service = TokenBlacklistService(redis)

    # Get access token from Authorization header
    access_token = credentials.credentials

    # Decode both tokens to get JTI and expiration
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_data.refresh_token)

    # Blacklist access token if valid
    if access_payload and access_payload.get("jti"):
        # Calculate remaining TTL (time until natural expiration)
        exp_timestamp = access_payload.get("exp", 0)
        current_timestamp = datetime.utcnow().timestamp()
        ttl_seconds = max(int(exp_timestamp - current_timestamp), 60)  # Min 60s TTL

        await blacklist_service.blacklist_token(access_payload["jti"], ttl_seconds)

    # Blacklist refresh token if valid
    if refresh_payload and refresh_payload.get("jti"):
        exp_timestamp = refresh_payload.get("exp", 0)
        current_timestamp = datetime.utcnow().timestamp()
        ttl_seconds = max(int(exp_timestamp - current_timestamp), 60)

        await blacklist_service.blacklist_token(refresh_payload["jti"], ttl_seconds)

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Returns the user's information including email, role, and active status.
    Requires a valid JWT access token.
    """
    return UserResponse.model_validate(current_user)
