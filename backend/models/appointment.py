"""
Appointment scheduling models.
"""

import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, Integer, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.postgres import Base


class AppointmentStatus(str, enum.Enum):
    """Appointment status options."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, enum.Enum):
    """Type of appointment."""
    ROUTINE = "routine"
    FOLLOW_UP = "follow_up"
    URGENT = "urgent"
    ANNUAL_PHYSICAL = "annual_physical"
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    TELEHEALTH = "telehealth"


class Appointment(Base):
    """Patient appointment scheduling."""
    
    __tablename__ = "appointments"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Patient and Provider
    patient_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        index=True,
        nullable=False
    )
    provider_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )
    
    # Location
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id"),
        index=True,
        nullable=False
    )
    location_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinic_locations.id")
    )
    
    # Scheduling
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # Appointment Details
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType),
        default=AppointmentType.ROUTINE
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        index=True
    )
    
    # Reason
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text)
    
    # Notes
    provider_notes: Mapped[Optional[str]] = mapped_column(Text)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Check-in Information
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    checked_in_by: Mapped[Optional[str]] = mapped_column(String(50))  # kiosk, staff, etc.
    
    # Actual Times
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Reminders
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    confirmation_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Telehealth
    is_telehealth: Mapped[bool] = mapped_column(Boolean, default=False)
    telehealth_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Follow-up
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_appointment_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id")
    )
    
    # Billing
    copay_amount: Mapped[Optional[int]] = mapped_column(Integer)  # in cents
    copay_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    copay_paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Additional Data
    intake_form_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    vitals: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Example vitals: {
    #     "blood_pressure_systolic": 120,
    #     "blood_pressure_diastolic": 80,
    #     "heart_rate": 72,
    #     "temperature": 98.6,
    #     "weight_kg": 70
    # }
    
    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_by_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, status={self.status})>"
    
    @property
    def is_past(self) -> bool:
        """Check if appointment is in the past."""
        return self.scheduled_start < datetime.utcnow()
    
    @property
    def can_check_in(self) -> bool:
        """Check if appointment can be checked in (within 30 minutes of start)."""
        if self.status != AppointmentStatus.SCHEDULED:
            return False
        now = datetime.utcnow()
        minutes_until = (self.scheduled_start - now).total_seconds() / 60
        return -5 <= minutes_until <= 30  # 30 minutes before to 5 minutes after

