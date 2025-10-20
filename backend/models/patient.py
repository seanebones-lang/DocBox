"""
Patient and medical record models.
"""

import enum
from datetime import datetime, date
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Date, DateTime, Text, Integer, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.postgres import Base


class Gender(str, enum.Enum):
    """Gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class BloodType(str, enum.Enum):
    """Blood type options."""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    UNKNOWN = "unknown"


class Patient(Base):
    """Patient demographic and health information."""
    
    __tablename__ = "patients"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Demographics (PHI - encrypted)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), default=Gender.UNKNOWN)
    
    # Contact Information (PHI - encrypted)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    country: Mapped[str] = mapped_column(String(50), default="USA")
    
    # Identifiers (PHI - encrypted)
    ssn: Mapped[Optional[str]] = mapped_column(String(255))  # Encrypted
    medical_record_number: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        index=True,
        nullable=False
    )
    
    # Insurance
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(200))
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(String(100))
    insurance_group_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Medical Information
    blood_type: Mapped[BloodType] = mapped_column(
        Enum(BloodType),
        default=BloodType.UNKNOWN
    )
    height_cm: Mapped[Optional[int]] = mapped_column(Integer)
    weight_kg: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Primary Care
    primary_doctor_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True
    )
    primary_clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id"),
        index=True,
        nullable=False
    )
    
    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    communication_preferences: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Biometric Data (for kiosk authentication)
    biometric_template: Mapped[Optional[str]] = mapped_column(Text)  # Encrypted, stored locally
    biometric_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Genomic Data (optional, HIPAA-compliant encryption)
    has_genomic_data: Mapped[bool] = mapped_column(Boolean, default=False)
    genomic_data_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    genomic_data_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # User account link
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        index=True
    )
    
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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, mrn={self.medical_record_number})>"
    
    @property
    def full_name(self) -> str:
        """Get patient's full name."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """Calculate patient's current age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class MedicalHistory(Base):
    """Patient medical history records."""
    
    __tablename__ = "medical_history"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    patient_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        index=True,
        nullable=False
    )
    
    # Diagnosis/Condition
    condition: Mapped[str] = mapped_column(String(500), nullable=False)
    icd10_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Details
    diagnosis_date: Mapped[date] = mapped_column(Date, nullable=False)
    resolution_date: Mapped[Optional[date]] = mapped_column(Date)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Provider
    diagnosed_by_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )
    
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


class Allergy(Base):
    """Patient allergies and adverse reactions."""
    
    __tablename__ = "allergies"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    patient_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        index=True,
        nullable=False
    )
    
    # Allergen
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    allergen_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # medication, food, environmental, other
    
    # Reaction
    reaction: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # mild, moderate, severe, life-threatening
    
    # Timestamps
    onset_date: Mapped[Optional[date]] = mapped_column(Date)
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

