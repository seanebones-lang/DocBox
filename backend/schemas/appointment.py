"""
Pydantic schemas for appointment data validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from models.appointment import AppointmentStatus, AppointmentType


class AppointmentBase(BaseModel):
    """Base appointment schema."""
    
    patient_id: UUID
    provider_id: UUID
    clinic_id: UUID
    location_id: Optional[UUID] = None
    
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int = Field(30, ge=5, le=480)
    
    appointment_type: AppointmentType = AppointmentType.ROUTINE
    reason: str = Field(..., min_length=1, max_length=1000)
    chief_complaint: Optional[str] = Field(None, max_length=1000)
    
    is_telehealth: bool = False
    is_follow_up: bool = False
    parent_appointment_id: Optional[UUID] = None


class AppointmentCreate(AppointmentBase):
    """Schema for creating a new appointment."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "provider_id": "650e8400-e29b-41d4-a716-446655440000",
                "clinic_id": "750e8400-e29b-41d4-a716-446655440000",
                "scheduled_start": "2025-10-25T14:00:00Z",
                "scheduled_end": "2025-10-25T14:30:00Z",
                "duration_minutes": 30,
                "appointment_type": "routine",
                "reason": "Annual physical examination",
                "is_telehealth": False
            }
        }
    )


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""
    
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = Field(None, min_length=1, max_length=1000)
    chief_complaint: Optional[str] = Field(None, max_length=1000)
    
    provider_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    
    vitals: Optional[Dict[str, Any]] = None


class AppointmentResponse(AppointmentBase):
    """Schema for appointment response."""
    
    id: UUID
    status: AppointmentStatus
    
    # Check-in info
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None
    
    # Actual times
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    
    # Reminders
    reminder_sent_at: Optional[datetime] = None
    confirmation_sent_at: Optional[datetime] = None
    
    # Billing
    copay_amount: Optional[int] = None
    copay_paid: bool = False
    
    # Telehealth
    telehealth_url: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    can_check_in: bool = False
    is_past: bool = False
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "850e8400-e29b-41d4-a716-446655440000",
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "provider_id": "650e8400-e29b-41d4-a716-446655440000",
                "clinic_id": "750e8400-e29b-41d4-a716-446655440000",
                "scheduled_start": "2025-10-25T14:00:00Z",
                "scheduled_end": "2025-10-25T14:30:00Z",
                "status": "scheduled",
                "appointment_type": "routine",
                "reason": "Annual physical examination",
                "created_at": "2025-10-20T10:00:00Z",
                "updated_at": "2025-10-20T10:00:00Z"
            }
        }
    )


class AppointmentListResponse(BaseModel):
    """Schema for paginated appointment list."""
    
    items: list[AppointmentResponse]
    total: int
    page: int
    per_page: int
    pages: int
    
    model_config = ConfigDict(from_attributes=True)

