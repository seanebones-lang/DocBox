"""
Pydantic schemas for clinic data validation.
"""

from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ClinicBase(BaseModel):
    """Base clinic schema."""
    
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20, pattern="^[A-Z0-9_-]+$")
    
    # Contact
    phone: str = Field(..., max_length=20)
    email: Optional[EmailStr] = None
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    
    # Address
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=50)
    zip_code: str = Field(..., max_length=10)
    country: str = Field("USA", max_length=50)
    
    # Geolocation
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    # Operating hours
    operating_hours: Dict[str, Dict[str, any]] = Field(
        ...,
        description="Operating hours by day of week"
    )
    
    # Capacity
    max_patients_per_day: int = Field(100, ge=1, le=1000)
    max_patients_per_hour: int = Field(10, ge=1, le=100)
    
    # Services and specialties
    services: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    
    # Configuration
    timezone: str = Field("America/New_York", max_length=50)
    language_support: Optional[List[str]] = Field(["en"], description="Supported languages")
    
    # Kiosk
    has_kiosk: bool = False
    kiosk_config: Optional[Dict[str, any]] = None
    
    # Status
    is_active: bool = True
    is_accepting_new_patients: bool = True
    
    # Compliance
    npi_number: Optional[str] = Field(None, max_length=10)
    tax_id: Optional[str] = Field(None, max_length=20)


class ClinicCreate(ClinicBase):
    """Schema for creating a new clinic."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Downtown Medical Center",
                "code": "CLINIC001",
                "phone": "+1-555-100-2000",
                "email": "info@downtown-med.com",
                "address_line1": "456 Health Plaza",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "operating_hours": {
                    "monday": {"open": "08:00", "close": "17:00", "closed": False},
                    "tuesday": {"open": "08:00", "close": "17:00", "closed": False},
                    "wednesday": {"open": "08:00", "close": "17:00", "closed": False},
                    "thursday": {"open": "08:00", "close": "17:00", "closed": False},
                    "friday": {"open": "08:00", "close": "17:00", "closed": False},
                    "saturday": {"open": "09:00", "close": "13:00", "closed": False},
                    "sunday": {"closed": True}
                },
                "services": ["primary_care", "urgent_care", "lab", "imaging"],
                "specialties": ["family_medicine", "internal_medicine"],
                "has_kiosk": True
            }
        }
    )


class ClinicUpdate(BaseModel):
    """Schema for updating clinic information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    
    operating_hours: Optional[Dict[str, Dict[str, any]]] = None
    max_patients_per_day: Optional[int] = Field(None, ge=1, le=1000)
    max_patients_per_hour: Optional[int] = Field(None, ge=1, le=100)
    
    services: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    
    is_active: Optional[bool] = None
    is_accepting_new_patients: Optional[bool] = None


class ClinicResponse(ClinicBase):
    """Schema for clinic response."""
    
    id: UUID
    full_address: str
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ClinicListResponse(BaseModel):
    """Schema for clinic list response."""
    
    items: list[ClinicResponse]
    total: int
    
    model_config = ConfigDict(from_attributes=True)

