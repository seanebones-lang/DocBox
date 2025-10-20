"""
Authentication endpoints.
Handles login, registration, MFA, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres import get_db
from models.user import User, UserRole
from security.auth import (
    password_manager,
    jwt_manager,
    mfa_manager,
)
from security.audit import audit_logger

router = APIRouter()
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class MFAVerifyRequest(BaseModel):
    token: str
    mfa_code: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.PATIENT


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user with email and password.
    Returns access and refresh tokens.
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    # Find user by email
    query = select(User).where(User.email == login_data.email, User.deleted_at == None)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Log failed attempt
        await audit_logger.log_login_attempt(
            email=login_data.email,
            user_id=None,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            failure_reason="User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not password_manager.verify_password(login_data.password, user.hashed_password):
        # Log failed attempt
        await audit_logger.log_login_attempt(
            email=login_data.email,
            user_id=user.id,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            failure_reason="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # If MFA is enabled, return temporary token
    if user.mfa_enabled:
        # TODO: Implement MFA flow
        pass
    
    # Generate tokens
    access_token = jwt_manager.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        clinic_id=user.clinic_id
    )
    
    refresh_token = jwt_manager.create_refresh_token(
        user_id=user.id,
        email=user.email
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Log successful login
    await audit_logger.log_login_attempt(
        email=user.email,
        user_id=user.id,
        success=True,
        ip_address=client_ip,
        user_agent=user_agent,
        mfa_used=user.mfa_enabled
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "mfa_enabled": user.mfa_enabled
        }
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Register a new user account.
    """
    # Check if email already exists
    query = select(User).where(User.email == register_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = password_manager.hash_password(register_data.password)
    
    new_user = User(
        email=register_data.email,
        hashed_password=hashed_password,
        first_name=register_data.first_name,
        last_name=register_data.last_name,
        phone=register_data.phone,
        role=register_data.role,
        is_active=True,
        is_verified=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "user_id": str(new_user.id),
        "email": new_user.email
    }


@router.post("/refresh")
async def refresh_token(
    token_data: RefreshTokenRequest
) -> dict:
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    payload = jwt_manager.verify_token(token_data.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Generate new access token
    # Note: In production, you should fetch user from DB to ensure they're still active
    access_token = jwt_manager.create_access_token(
        user_id=payload["sub"],
        email=payload["email"],
        role=payload.get("role", UserRole.PATIENT)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Logout user (invalidate token).
    Note: In production, implement token blacklisting in Redis.
    """
    # TODO: Add token to blacklist in Redis
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get current authenticated user information.
    """
    # Verify token
    payload = jwt_manager.verify_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user from database
    query = select(User).where(User.id == payload["sub"])
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "clinic_id": str(user.clinic_id) if user.clinic_id else None,
        "mfa_enabled": user.mfa_enabled
    }

