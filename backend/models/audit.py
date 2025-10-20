"""
Audit logging models for HIPAA compliance.
All PHI access must be logged and retained for 7 years.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.postgres import Base


class AuditLog(Base):
    """
    Comprehensive audit log for HIPAA compliance.
    Records all access to Protected Health Information (PHI).
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Who (User identification)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        index=True
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    user_role: Mapped[Optional[str]] = mapped_column(String(50))
    
    # What (Action performed)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Actions: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, PRINT, etc.
    
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Resource types: Patient, Appointment, MedicalHistory, etc.
    
    resource_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        index=True
    )
    
    # When (Timestamp)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Where (Network information)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Location
    clinic_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        index=True
    )
    geographic_location: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Why (Reason for access - optional but recommended)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Details
    changes: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Example: {
    #     "before": {"email": "old@example.com"},
    #     "after": {"email": "new@example.com"}
    # }
    
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Additional context like API endpoint, request method, etc.
    
    # Security
    is_phi_access: Mapped[bool] = mapped_column(JSONB, default=False, index=True)
    is_suspicious: Mapped[bool] = mapped_column(JSONB, default=False, index=True)
    
    # Blockchain hash (for immutable audit trail if enabled)
    blockchain_hash: Mapped[Optional[str]] = mapped_column(String(255))
    blockchain_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status
    success: Mapped[bool] = mapped_column(JSONB, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (
        # Composite indexes for common queries
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_resource_timestamp', 'resource_type', 'resource_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_phi_timestamp', 'is_phi_access', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, resource={self.resource_type})>"
        )


class LoginAttempt(Base):
    """Track login attempts for security monitoring."""
    
    __tablename__ = "login_attempts"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # User
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        index=True
    )
    
    # Attempt details
    success: Mapped[bool] = mapped_column(JSONB, nullable=False, index=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Network
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # MFA
    mfa_used: Mapped[bool] = mapped_column(JSONB, default=False)
    mfa_success: Mapped[Optional[bool]] = mapped_column(JSONB)
    
    __table_args__ = (
        Index('idx_login_email_timestamp', 'email', 'attempted_at'),
        Index('idx_login_ip_timestamp', 'ip_address', 'attempted_at'),
    )

