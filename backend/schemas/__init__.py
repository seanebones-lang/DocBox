"""
Pydantic schemas for request/response validation.
"""

from schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from schemas.clinic import ClinicCreate, ClinicUpdate, ClinicResponse

__all__ = [
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "ClinicCreate",
    "ClinicUpdate",
    "ClinicResponse",
]


