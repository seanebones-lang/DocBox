"""
Patient management endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_permission,
    verify_clinic_access,
    PaginationParams,
    get_db
)
from database.postgres import get_db
from models.patient import Patient, MedicalHistory, Allergy, Gender, BloodType
from models.user import User, UserRole
from schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListResponse
from security.audit import audit_logger
from security.encryption import encrypt_field, decrypt_field

router = APIRouter()


@router.get("", response_model=PatientListResponse)
async def list_patients(
    request: Request,
    current_user: User = Depends(require_permission("patients", "read")),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name, MRN, or email"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic"),
    gender: Optional[Gender] = Query(None, description="Filter by gender"),
    age_min: Optional[int] = Query(None, ge=0, le=150, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=150, description="Maximum age"),
) -> PatientListResponse:
    """
    List patients with filtering and pagination.

    Supports filtering by:
    - Search query (name, MRN, email)
    - Clinic assignment
    - Gender
    - Age range
    """

    # Build base query
    query = select(Patient).where(Patient.deleted_at == None)

    # Apply clinic access control
    if current_user.role != UserRole.ADMIN:
        query = query.where(Patient.primary_clinic_id == current_user.clinic_id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.medical_record_number.ilike(search_term),
                Patient.email.ilike(search_term),
            )
        )

    if clinic_id:
        await verify_clinic_access(clinic_id, current_user)
        query = query.where(Patient.primary_clinic_id == clinic_id)

    if gender:
        query = query.where(Patient.gender == gender)

    if age_min is not None or age_max is not None:
        # Calculate age using SQL
        age_expr = func.extract('year', func.age(Patient.date_of_birth))

        if age_min is not None:
            query = query.where(age_expr >= age_min)
        if age_max is not None:
            query = query.where(age_expr <= age_max)

    # Get total count
    count_query = select(func.count()).select_from(query)
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    query = query.offset(pagination.offset).limit(pagination.limit)

    # Execute query
    result = await db.execute(query)
    patients = result.scalars().all()

    # Convert to response format
    items = []
    for patient in patients:
        items.append(PatientResponse.model_validate(patient))

    return PatientListResponse(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=(total + pagination.per_page - 1) // pagination.per_page
    )


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_data: PatientCreate,
    current_user: User = Depends(require_permission("patients", "create")),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """
    Create a new patient record.
    """

    # Verify clinic access
    await verify_clinic_access(patient_data.primary_clinic_id, current_user)

    # Check if MRN already exists
    existing_patient = await db.execute(
        select(Patient).where(Patient.medical_record_number == patient_data.medical_record_number)
    )
    if existing_patient.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medical record number already exists"
        )

    # Check if email already exists (if provided)
    if patient_data.email:
        existing_patient = await db.execute(
            select(Patient).where(Patient.email == patient_data.email)
        )
        if existing_patient.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient with this email already exists"
            )

    # Generate medical record number if not provided
    if not hasattr(patient_data, 'medical_record_number') or not patient_data.medical_record_number:
        # Generate MRN based on clinic and timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        clinic_prefix = f"CLINIC-{patient_data.primary_clinic_id}"[:8]
        mrn_suffix = str(uuid4())[:8]
        patient_data.medical_record_number = f"MRN-{timestamp}-{clinic_prefix}-{mrn_suffix}"

    # Encrypt sensitive fields
    encrypted_ssn = encrypt_field(patient_data.ssn) if patient_data.ssn else None

    # Create patient
    db_patient = Patient(
        **patient_data.model_dump(exclude={'ssn'}),
        ssn=encrypted_ssn,
        created_by_id=current_user.id,
    )

    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CREATE",
        resource_type="patient",
        resource_id=db_patient.id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_mrn": db_patient.medical_record_number,
            "patient_name": db_patient.full_name,
        }
    )

    return PatientResponse.model_validate(db_patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_permission("patients", "read")),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """
    Get patient details by ID.
    """

    # Get patient with clinic access check
    query = select(Patient).where(
        and_(Patient.id == patient_id, Patient.deleted_at == None)
    )

    # Apply clinic access control
    if current_user.role != UserRole.ADMIN:
        query = query.where(Patient.primary_clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="READ",
        resource_type="patient",
        resource_id=patient_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_mrn": patient.medical_record_number,
            "patient_name": patient.full_name,
        }
    )

    return PatientResponse.model_validate(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    request: Request,
    patient_id: UUID,
    patient_data: PatientUpdate,
    current_user: User = Depends(require_permission("patients", "update")),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """
    Update patient information.
    """

    # Get existing patient
    query = select(Patient).where(
        and_(Patient.id == patient_id, Patient.deleted_at == None)
    )

    # Apply clinic access control
    if current_user.role != UserRole.ADMIN:
        query = query.where(Patient.primary_clinic_id == current_user.clinic_id)

    result = await db.execute(query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check if email is being changed and already exists
    if patient_data.email and patient_data.email != patient.email:
        existing_patient = await db.execute(
            select(Patient).where(Patient.email == patient_data.email)
        )
        if existing_patient.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient with this email already exists"
            )

    # Verify clinic access if clinic is being changed
    if patient_data.primary_clinic_id and patient_data.primary_clinic_id != patient.primary_clinic_id:
        await verify_clinic_access(patient_data.primary_clinic_id, current_user)

    # Update fields
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    patient.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(patient)

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="UPDATE",
        resource_type="patient",
        resource_id=patient_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_mrn": patient.medical_record_number,
            "patient_name": patient.full_name,
            "updated_fields": list(update_data.keys()),
        }
    )

    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a patient record (admin only).
    """

    # Get patient
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Soft delete
    patient.deleted_at = datetime.utcnow()
    await db.commit()

    # Log audit event
    await audit_logger.log_phi_access(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="DELETE",
        resource_type="patient",
        resource_id=patient_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        clinic_id=current_user.clinic_id,
        metadata={
            "patient_mrn": patient.medical_record_number,
            "patient_name": patient.full_name,
        }
    )


@router.get("/{patient_id}/history", response_model=List[dict])
async def get_patient_history(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_permission("patients", "read")),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get patient's medical history.
    """

    # Verify patient exists and user has access
    await get_patient(request, patient_id, current_user, db)

    # Get medical history
    result = await db.execute(
        select(MedicalHistory).where(MedicalHistory.patient_id == patient_id)
    )
    history = result.scalars().all()

    # Get allergies
    result = await db.execute(
        select(Allergy).where(Allergy.patient_id == patient_id)
    )
    allergies = result.scalars().all()

    return {
        "medical_history": [
            {
                "id": h.id,
                "condition": h.condition,
                "icd10_code": h.icd10_code,
                "diagnosis_date": h.diagnosis_date.isoformat(),
                "resolution_date": h.resolution_date.isoformat() if h.resolution_date else None,
                "is_chronic": h.is_chronic,
                "notes": h.notes,
                "created_at": h.created_at.isoformat(),
            }
            for h in history
        ],
        "allergies": [
            {
                "id": a.id,
                "allergen": a.allergen,
                "allergen_type": a.allergen_type,
                "reaction": a.reaction,
                "severity": a.severity,
                "onset_date": a.onset_date.isoformat() if a.onset_date else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in allergies
        ]
    }

