"""
Clinic and location models.
"""

from datetime import datetime, time
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, Time, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.postgres import Base


class Clinic(Base):
    """Clinic location model for multi-tenant system."""
    
    __tablename__ = "clinics"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False
    )  # Unique clinic identifier (e.g., "CLINIC001")
    
    # Contact
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    fax: Mapped[Optional[str]] = mapped_column(String(20))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Address
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="USA")
    
    # Geolocation (for routing and analytics)
    latitude: Mapped[Optional[float]] = mapped_column()
    longitude: Mapped[Optional[float]] = mapped_column()
    
    # Operating Hours (stored as JSON)
    operating_hours: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Example: {
    #     "monday": {"open": "08:00", "close": "17:00", "closed": false},
    #     "tuesday": {"open": "08:00", "close": "17:00", "closed": false},
    #     ...
    # }
    
    # Capacity
    max_patients_per_day: Mapped[int] = mapped_column(Integer, default=100)
    max_patients_per_hour: Mapped[int] = mapped_column(Integer, default=10)
    
    # Services Offered
    services: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Example: ["primary_care", "urgent_care", "lab", "imaging", "pharmacy"]
    
    # Specialties
    specialties: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Example: ["family_medicine", "pediatrics", "internal_medicine"]
    
    # Configuration
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")
    language_support: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Example: ["en", "es", "fr"]
    
    # Kiosk Configuration
    has_kiosk: Mapped[bool] = mapped_column(Boolean, default=False)
    kiosk_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_accepting_new_patients: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Compliance
    npi_number: Mapped[Optional[str]] = mapped_column(String(10))  # National Provider Identifier
    tax_id: Mapped[Optional[str]] = mapped_column(String(20))
    
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
        return f"<Clinic(id={self.id}, name={self.name}, code={self.code})>"
    
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return ", ".join(parts)


class ClinicLocation(Base):
    """
    Separate locations/departments within a clinic.
    For larger clinics with multiple buildings or departments.
    """
    
    __tablename__ = "clinic_locations"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Details
    building: Mapped[Optional[str]] = mapped_column(String(50))
    floor: Mapped[Optional[str]] = mapped_column(String(20))
    room_number: Mapped[Optional[str]] = mapped_column(String(20))
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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

