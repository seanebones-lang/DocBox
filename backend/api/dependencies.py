"""
FastAPI dependencies for authentication, authorization, and common functionality.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.postgres import get_db
from models.user import User, UserRole
from security.auth import jwt_manager, rbac_manager
from security.audit import audit_logger

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token
    payload = jwt_manager.verify_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("sub")
    query = select(User).where(User.id == user_id, User.deleted_at == None)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Store user in request state for logging
    request.state.current_user = user
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    Alias for get_current_user with explicit active check.
    """
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin/users")
        async def list_users(
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    
    Args:
        *allowed_roles: Allowed user roles
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    
    return role_checker


def require_permission(resource: str, action: str):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.post("/patients")
        async def create_patient(
            current_user: User = Depends(require_permission("patients", "create"))
        ):
            ...
    
    Args:
        resource: Resource type
        action: Action to perform
        
    Returns:
        Dependency function
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not rbac_manager.has_permission(current_user.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {action} on {resource}"
            )
        return current_user
    
    return permission_checker


async def verify_clinic_access(
    clinic_id: UUID,
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Verify user has access to specific clinic.
    
    Args:
        clinic_id: Clinic ID to check
        current_user: Current user
        
    Returns:
        True if user has access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    # Admins have access to all clinics
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Staff can only access their assigned clinic
    if not rbac_manager.can_access_clinic(current_user.clinic_id, clinic_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this clinic"
        )
    
    return True


async def log_request(
    request: Request,
    current_user: Optional[User] = None
) -> None:
    """
    Log API request for audit trail.
    
    Args:
        request: FastAPI request
        current_user: Current user (if authenticated)
    """
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    # Determine if this is PHI access
    is_phi = any(path in str(request.url.path) for path in [
        "/patients",
        "/appointments",
        "/medical-history"
    ])
    
    # Log the request
    if current_user and is_phi:
        await audit_logger.log_phi_access(
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            action=request.method,
            resource_type=request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else "unknown",
            resource_id=None,  # Will be updated by endpoint if needed
            ip_address=client_ip,
            user_agent=user_agent,
            clinic_id=current_user.clinic_id,
            metadata={
                "endpoint": str(request.url.path),
                "method": request.method
            }
        )


class PaginationParams:
    """
    Common pagination parameters.
    
    Usage:
        @router.get("/patients")
        async def list_patients(
            pagination: PaginationParams = Depends()
        ):
            offset = pagination.skip
            limit = pagination.limit
    """
    
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ):
        """
        Initialize pagination parameters.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            max_per_page: Maximum items per page
        """
        self.page = max(1, page)
        self.per_page = min(max(1, per_page), max_per_page)
        self.skip = (self.page - 1) * self.per_page
        self.limit = self.per_page
    
    @property
    def offset(self) -> int:
        """Get offset for database query."""
        return self.skip


