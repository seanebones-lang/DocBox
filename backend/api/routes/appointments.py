"""
Appointment management endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import (
    get_current_user,
    require_role,
    require_permission,
    verify_clinic_access,
    PaginationParams,
    get_db
)
from models.appointment import Appointment, AppointmentStatus, AppointmentType
from models.user import User, UserRole
from models.patient import Patient
from schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentListResponse
from security.audit import audit_logger

router = APIRouter()


@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    request: Request,
    current_user: User = Depends(require_permission("appointments", "read")),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
    appointment_type: Optional[AppointmentType] = Query(None, description="Filter by type"),
    date_from: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
) -> AppointmentListResponse:
    """
    List appointments with filtering and pagination.
    """

    # Build base query
    query = select(Appointment).where(Appointment.deleted_at == None)

    # Apply clinic access control
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    # Apply filters
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)

    if provider_id:
        if current_user.role == UserRole.STAFF:
            # Staff can only see appointments for their providers
            query = query.where(Appointment.provider_id.in_(
                select(User.id).where(User.clinic_id == current_user.clinic_id)
            ))
        query = query.where(Appointment.provider_id == provider_id)

    if clinic_id:
        await verify_clinic_access(clinic_id, current_user)
        query = query.where(Appointment.clinic_id == clinic_id)

    if status:
        query = query.where(Appointment.status == status)

    if appointment_type:
        query = query.where(Appointment.appointment_type == appointment_type)

    if date_from:
        query = query.where(Appointment.scheduled_start >= date_from)
    if date_to:
        query = query.where(Appointment.scheduled_end <= date_to)

    # Get total count
    count_query = select(func.count()).select_from(query)
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination and ordering
    query = query.order_by(Appointment.scheduled_start).offset(pagination.offset).limit(pagination.limit)

    # Execute query
    result = await db.execute(query)
    appointments = result.scalars().all()

    # Convert to response format
    items = []
    for appointment in appointments:
        # Add computed properties
        appointment_dict = appointment.__dict__.copy()
        appointment_dict['can_check_in'] = appointment.can_check_in
        appointment_dict['is_past'] = appointment.is_past
        items.append(AppointmentResponse.model_validate(appointment_dict))

    return AppointmentListResponse(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=(total + pagination.per_page - 1) // pagination.per_page
    )


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    request: Request,
    appointment_data: AppointmentCreate,
    current_user: User = Depends(require_permission("appointments", "create")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    """
    Create a new appointment.
    """

    # Verify clinic access
    await verify_clinic_access(appointment_data.clinic_id, current_user)

    # Verify patient exists and user has access
    patient_result = await db.execute(
        select(Patient).where(
            and_(Patient.id == appointment_data.patient_id, Patient.deleted_at == None)
        )
    )
    if current_user.role != UserRole.ADMIN:
        patient_result = patient_result.where(Patient.primary_clinic_id == current_user.clinic_id)

    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or access denied"
        )

    # Verify provider exists and has access to clinic
    provider_result = await db.execute(
        select(User).where(
            and_(User.id == appointment_data.provider_id, User.deleted_at == None)
        )
    )
    if current_user.role != UserRole.ADMIN:
        provider_result = provider_result.where(User.clinic_id == current_user.clinic_id)

    provider = provider_result.scalar_one_or_none()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found or access denied"
        )

    # Check for scheduling conflicts
    conflict_query = select(Appointment).where(
        and_(
            Appointment.provider_id == appointment_data.provider_id,
            Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.CHECKED_IN,
                AppointmentStatus.IN_PROGRESS
            ]),
            Appointment.scheduled_start < appointment_data.scheduled_end,
            Appointment.scheduled_end > appointment_data.scheduled_start,
            Appointment.deleted_at == None
        )
    )
    conflict_result = await db.execute(conflict_query)
    if conflict_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scheduling conflict: Provider has another appointment at this time"
        )

    # Create appointment
    db_appointment = Appointment(**appointment_data.model_dump())
    db.add(db_appointment)
    await db.commit()
    await db.refresh(db_appointment)

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CREATE",
        resource_type="appointment",
        resource_id=db_appointment.id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment_data.patient_id),
            "provider_id": str(appointment_data.provider_id),
            "scheduled_start": appointment_data.scheduled_start.isoformat(),
            "appointment_type": appointment_data.appointment_type.value,
        }
    )

    return AppointmentResponse.model_validate(db_appointment)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    request: Request,
    appointment_id: UUID,
    current_user: User = Depends(require_permission("appointments", "read")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    """
    Get appointment details by ID.
    """

    # Get appointment with access control
    query = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.deleted_at == None)
    )

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="READ",
        resource_type="appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment.patient_id),
            "provider_id": str(appointment.provider_id),
        }
    )

    appointment_dict = appointment.__dict__.copy()
    appointment_dict['can_check_in'] = appointment.can_check_in
    appointment_dict['is_past'] = appointment.is_past

    return AppointmentResponse.model_validate(appointment_dict)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    request: Request,
    appointment_id: UUID,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(require_permission("appointments", "update")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    """
    Update appointment information.
    """

    # Get existing appointment
    query = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.deleted_at == None)
    )

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check for conflicts if time is being changed
    if appointment_data.scheduled_start or appointment_data.scheduled_end:
        new_start = appointment_data.scheduled_start or appointment.scheduled_start
        new_end = appointment_data.scheduled_end or appointment.scheduled_end

        conflict_query = select(Appointment).where(
            and_(
                Appointment.provider_id == appointment.provider_id,
                Appointment.id != appointment_id,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS
                ]),
                Appointment.scheduled_start < new_end,
                Appointment.scheduled_end > new_start,
                Appointment.deleted_at == None
            )
        )
        conflict_result = await db.execute(conflict_query)
        if conflict_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Scheduling conflict: Provider has another appointment at this time"
            )

    # Update fields
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    appointment.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(appointment)

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="UPDATE",
        resource_type="appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment.patient_id),
            "updated_fields": list(update_data.keys()),
        }
    )

    appointment_dict = appointment.__dict__.copy()
    appointment_dict['can_check_in'] = appointment.can_check_in
    appointment_dict['is_past'] = appointment.is_past

    return AppointmentResponse.model_validate(appointment_dict)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    request: Request,
    appointment_id: UUID,
    current_user: User = Depends(require_permission("appointments", "update")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Cancel an appointment.
    """

    # Get appointment
    query = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.deleted_at == None)
    )

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Cancel appointment
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = datetime.utcnow()
    appointment.cancelled_by_id = current_user.id
    appointment.updated_at = datetime.utcnow()

    await db.commit()

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CANCEL",
        resource_type="appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment.patient_id),
            "original_status": appointment.status.value,
        }
    )


@router.post("/{appointment_id}/check-in", status_code=status.HTTP_200_OK)
async def check_in_appointment(
    request: Request,
    appointment_id: UUID,
    current_user: User = Depends(require_permission("appointments", "update")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check in a patient for their appointment.
    """

    # Get appointment
    query = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.deleted_at == None)
    )

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check if appointment can be checked in
    if not appointment.can_check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment cannot be checked in at this time"
        )

    # Update appointment status
    appointment.status = AppointmentStatus.CHECKED_IN
    appointment.checked_in_at = datetime.utcnow()
    appointment.checked_in_by = f"staff:{current_user.id}"
    appointment.updated_at = datetime.utcnow()

    await db.commit()

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CHECK_IN",
        resource_type="appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment.patient_id),
            "check_in_method": "staff",
        }
    )

    return {
        "message": "Patient checked in successfully",
        "appointment_id": str(appointment_id),
        "status": appointment.status.value,
        "checked_in_at": appointment.checked_in_at.isoformat()
    }


@router.post("/{appointment_id}/start", status_code=status.HTTP_200_OK)
async def start_appointment(
    request: Request,
    appointment_id: UUID,
    current_user: User = Depends(require_permission("appointments", "update")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Start an appointment (provider action).
    """

    # Get appointment
    query = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.deleted_at == None)
    )

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check if provider is authorized
    if appointment.provider_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned provider can start this appointment"
        )

    # Update appointment status
    appointment.status = AppointmentStatus.IN_PROGRESS
    appointment.actual_start = datetime.utcnow()
    appointment.updated_at = datetime.utcnow()

    await db.commit()

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="START",
        resource_type="appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment.patient_id),
        }
    )

    return {
        "message": "Appointment started",
        "appointment_id": str(appointment_id),
        "status": appointment.status.value,
        "actual_start": appointment.actual_start.isoformat()
    }


@router.post("/{appointment_id}/complete", status_code=status.HTTP_200_OK)
async def complete_appointment(
    request: Request,
    appointment_id: UUID,
    current_user: User = Depends(require_permission("appointments", "update")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Complete an appointment (provider action).
    """

    # Get appointment
    query = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.deleted_at == None)
    )

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        query = query.where(Appointment.clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check if provider is authorized
    if appointment.provider_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned provider can complete this appointment"
        )

    # Update appointment status
    appointment.status = AppointmentStatus.COMPLETED
    appointment.actual_end = datetime.utcnow()
    appointment.updated_at = datetime.utcnow()

    await db.commit()

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="COMPLETE",
        resource_type="appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_id": str(appointment.patient_id),
        }
    )

    return {
        "message": "Appointment completed",
        "appointment_id": str(appointment_id),
        "status": appointment.status.value,
        "actual_end": appointment.actual_end.isoformat()
    }

