"""
Clinic management endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import (
    get_current_user,
    require_role,
    require_permission,
    PaginationParams,
    get_db
)
from models.clinic import Clinic, ClinicLocation
from models.user import User, UserRole
from schemas.clinic import ClinicCreate, ClinicUpdate, ClinicResponse, ClinicListResponse
from security.audit import audit_logger

router = APIRouter()


@router.get("", response_model=ClinicListResponse)
async def list_clinics(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name or code"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> ClinicListResponse:
    """
    List clinics with filtering and pagination.
    """

    # Build base query
    query = select(Clinic)

    # Non-admin users can only see active clinics in their state (if staff) or their assigned clinic
    if current_user.role != UserRole.ADMIN:
        query = query.where(Clinic.is_active == True)
        if current_user.role == UserRole.STAFF:
            # Staff can only see their assigned clinic
            query = query.where(Clinic.id == current_user.clinic_id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            and_(
                Clinic.name.ilike(search_term),
                Clinic.code.ilike(search_term)
            )
        )

    if state:
        query = query.where(Clinic.state == state)

    if is_active is not None:
        query = query.where(Clinic.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query)
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination and ordering
    query = query.order_by(Clinic.name).offset(pagination.offset).limit(pagination.limit)

    # Execute query
    result = await db.execute(query)
    clinics = result.scalars().all()

    # Convert to response format
    items = []
    for clinic in clinics:
        items.append(ClinicResponse.model_validate(clinic))

    return ClinicListResponse(
        items=items,
        total=total
    )


@router.post("", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    request: Request,
    clinic_data: ClinicCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ClinicResponse:
    """
    Create a new clinic (admin only).
    """

    # Check if clinic code already exists
    existing_clinic = await db.execute(
        select(Clinic).where(Clinic.code == clinic_data.code)
    )
    if existing_clinic.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clinic code already exists"
        )

    # Create clinic
    db_clinic = Clinic(**clinic_data.model_dump())
    db.add(db_clinic)
    await db.commit()
    await db.refresh(db_clinic)

    # Log audit event
    await audit_logger.log_admin_action(
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE_CLINIC",
        resource_type="clinic",
        resource_id=db_clinic.id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        metadata={
            "clinic_name": db_clinic.name,
            "clinic_code": db_clinic.code,
        }
    )

    return ClinicResponse.model_validate(db_clinic)


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    request: Request,
    clinic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicResponse:
    """
    Get clinic details by ID.
    """

    # Get clinic with access control
    query = select(Clinic).where(Clinic.id == clinic_id)

    if current_user.role != UserRole.ADMIN:
        query = query.where(Clinic.is_active == True)
        if current_user.role == UserRole.STAFF:
            query = query.where(Clinic.id == current_user.clinic_id)

    result = await db.execute(query)
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )

    # Log audit event
    await audit_logger.log_admin_action(
        user_id=current_user.id,
        user_email=current_user.email,
        action="VIEW_CLINIC",
        resource_type="clinic",
        resource_id=clinic_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        metadata={
            "clinic_name": clinic.name,
        }
    )

    return ClinicResponse.model_validate(clinic)


@router.put("/{clinic_id}", response_model=ClinicResponse)
async def update_clinic(
    request: Request,
    clinic_id: UUID,
    clinic_data: ClinicUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ClinicResponse:
    """
    Update clinic information (admin only).
    """

    # Get existing clinic
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )

    # Check if code is being changed and already exists
    if clinic_data.code and clinic_data.code != clinic.code:
        existing_clinic = await db.execute(
            select(Clinic).where(Clinic.code == clinic_data.code)
        )
        if existing_clinic.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Clinic code already exists"
            )

    # Update fields
    update_data = clinic_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clinic, field, value)

    clinic.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(clinic)

    # Log audit event
    await audit_logger.log_admin_action(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE_CLINIC",
        resource_type="clinic",
        resource_id=clinic_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        metadata={
            "clinic_name": clinic.name,
            "updated_fields": list(update_data.keys()),
        }
    )

    return ClinicResponse.model_validate(clinic)


@router.delete("/{clinic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinic(
    request: Request,
    clinic_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a clinic (admin only).
    """

    # Get clinic
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )

    # Check if clinic has active users or patients
    # In a real implementation, you might want to prevent deletion
    # or cascade the soft delete to related records

    # Soft delete
    clinic.deleted_at = datetime.utcnow()
    await db.commit()

    # Log audit event
    await audit_logger.log_admin_action(
        user_id=current_user.id,
        user_email=current_user.email,
        action="DELETE_CLINIC",
        resource_type="clinic",
        resource_id=clinic_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        metadata={
            "clinic_name": clinic.name,
            "clinic_code": clinic.code,
        }
    )


@router.get("/{clinic_id}/locations", response_model=List[dict])
async def list_clinic_locations(
    request: Request,
    clinic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    List locations within a clinic.
    """

    # Verify clinic access
    await get_clinic(request, clinic_id, current_user, db)

    # Get locations
    result = await db.execute(
        select(ClinicLocation).where(
            and_(ClinicLocation.clinic_id == clinic_id, ClinicLocation.is_active == True)
        )
    )
    locations = result.scalars().all()

    return [
        {
            "id": loc.id,
            "name": loc.name,
            "code": loc.code,
            "building": loc.building,
            "floor": loc.floor,
            "room_number": loc.room_number,
            "description": loc.description,
            "created_at": loc.created_at.isoformat(),
        }
        for loc in locations
    ]

