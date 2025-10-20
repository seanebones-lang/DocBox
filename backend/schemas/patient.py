"""
Pydantic schemas for patient data validation.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from models.patient import Gender, BloodType


class PatientBase(BaseModel):
    """Base patient schema with common fields."""
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    gender: Gender = Gender.UNKNOWN
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: str = Field("USA", max_length=50)
    
    # Insurance
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    
    # Medical Info
    blood_type: BloodType = BloodType.UNKNOWN
    height_cm: Optional[int] = Field(None, ge=0, le=300)
    weight_kg: Optional[int] = Field(None, ge=0, le=500)
    
    # Clinic Assignment
    primary_clinic_id: UUID
    primary_doctor_id: Optional[UUID] = None
    
    # Preferences
    preferred_language: str = Field("en", max_length=10)


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""
    
    ssn: Optional[str] = Field(None, description="Social Security Number (will be encrypted)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-01-15",
                "gender": "male",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "address_line1": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "primary_clinic_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class PatientUpdate(BaseModel):
    """Schema for updating patient information."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=10)
    
    # Insurance
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    
    # Medical Info
    blood_type: Optional[BloodType] = None
    height_cm: Optional[int] = Field(None, ge=0, le=300)
    weight_kg: Optional[int] = Field(None, ge=0, le=500)
    
    # Assignments
    primary_doctor_id: Optional[UUID] = None
    preferred_language: Optional[str] = Field(None, max_length=10)


class PatientResponse(PatientBase):
    """Schema for patient response (excludes sensitive data)."""
    
    id: UUID
    medical_record_number: str
    age: int
    full_name: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "medical_record_number": "MRN-2025-001234",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "date_of_birth": "1980-01-15",
                "age": 45,
                "gender": "male",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "primary_clinic_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-10-20T10:00:00Z",
                "updated_at": "2025-10-20T10:00:00Z"
            }
        }
    )


class PatientListResponse(BaseModel):
    """Schema for paginated patient list response."""
    
    items: list[PatientResponse]
    total: int
    page: int
    per_page: int
    pages: int
    
    model_config = ConfigDict(from_attributes=True)

