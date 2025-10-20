"""
HIPAA-compliant audit logging system.
Tracks all access to Protected Health Information (PHI).
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit import AuditLog, LoginAttempt
from database.postgres import AsyncSessionLocal


class AuditLogger:
    """
    HIPAA-compliant audit logger.
    Records who accessed what, when, where, and why.
    """
    
    @staticmethod
    async def log_phi_access(
        user_id: Optional[UUID],
        user_email: Optional[str],
        user_role: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[UUID],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        clinic_id: Optional[UUID] = None,
        reason: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> UUID:
        """
        Log access to Protected Health Information.
        
        Args:
            user_id: User's unique identifier
            user_email: User's email address
            user_role: User's role
            action: Action performed (CREATE, READ, UPDATE, DELETE, etc.)
            resource_type: Type of resource accessed
            resource_id: Resource's unique identifier
            ip_address: User's IP address
            user_agent: Browser user agent
            session_id: Session identifier
            clinic_id: Clinic where action occurred
            reason: Reason for access (optional but recommended)
            changes: Dict of before/after values for updates
            metadata: Additional context
            success: Whether action succeeded
            error_message: Error message if action failed
            
        Returns:
            UUID of created audit log entry
        """
        async with AsyncSessionLocal() as session:
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                clinic_id=clinic_id,
                reason=reason,
                changes=changes,
                metadata=metadata,
                is_phi_access=True,  # Mark as PHI access
                success=success,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            session.add(audit_log)
            await session.commit()
            await session.refresh(audit_log)
            
            return audit_log.id
    
    @staticmethod
    async def log_action(
        user_id: Optional[UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        is_phi: bool = False,
        **kwargs: Any
    ) -> UUID:
        """
        General-purpose action logging.
        
        Args:
            user_id: User performing action
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource identifier
            is_phi: Whether this involves PHI
            **kwargs: Additional fields
            
        Returns:
            UUID of audit log entry
        """
        async with AsyncSessionLocal() as session:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                is_phi_access=is_phi,
                timestamp=datetime.utcnow(),
                **kwargs
            )
            
            session.add(audit_log)
            await session.commit()
            await session.refresh(audit_log)
            
            return audit_log.id
    
    @staticmethod
    async def log_login_attempt(
        email: str,
        user_id: Optional[UUID],
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        mfa_used: bool = False,
        mfa_success: Optional[bool] = None
    ) -> UUID:
        """
        Log login attempt for security monitoring.
        
        Args:
            email: Email used for login
            user_id: User ID if login successful
            success: Whether login succeeded
            ip_address: IP address of login attempt
            user_agent: Browser user agent
            failure_reason: Reason for failure
            mfa_used: Whether MFA was used
            mfa_success: Whether MFA verification succeeded
            
        Returns:
            UUID of login attempt record
        """
        async with AsyncSessionLocal() as session:
            login_attempt = LoginAttempt(
                email=email,
                user_id=user_id,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason,
                mfa_used=mfa_used,
                mfa_success=mfa_success,
                attempted_at=datetime.utcnow()
            )
            
            session.add(login_attempt)
            await session.commit()
            await session.refresh(login_attempt)
            
            return login_attempt.id
    
    @staticmethod
    async def get_user_audit_trail(
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """
        Get audit trail for specific user.
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of records
            offset: Offset for pagination
            
        Returns:
            List of audit log entries
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(AuditLog)
                .where(AuditLog.user_id == user_id)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_resource_audit_trail(
        resource_type: str,
        resource_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """
        Get audit trail for specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource's unique identifier
            limit: Maximum number of records
            offset: Offset for pagination
            
        Returns:
            List of audit log entries
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(AuditLog)
                .where(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id
                )
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_failed_login_attempts(
        email: str,
        since: datetime,
        limit: int = 10
    ) -> list[LoginAttempt]:
        """
        Get failed login attempts for an email since a specific time.
        Useful for detecting brute force attacks.
        
        Args:
            email: Email address
            since: Start datetime
            limit: Maximum number of records
            
        Returns:
            List of failed login attempts
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(LoginAttempt)
                .where(
                    LoginAttempt.email == email,
                    LoginAttempt.success == False,
                    LoginAttempt.attempted_at >= since
                )
                .order_by(LoginAttempt.attempted_at.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def detect_suspicious_activity(
        user_id: UUID,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Detect suspicious activity patterns for a user.
        
        Args:
            user_id: User's unique identifier
            time_window_minutes: Time window to analyze
            
        Returns:
            Dict with suspicious activity indicators
        """
        async with AsyncSessionLocal() as session:
            since = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            # Get recent audit logs
            query = (
                select(AuditLog)
                .where(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= since
                )
                .order_by(AuditLog.timestamp.desc())
            )
            result = await session.execute(query)
            logs = list(result.scalars().all())
            
            # Analyze patterns
            phi_accesses = sum(1 for log in logs if log.is_phi_access)
            failed_actions = sum(1 for log in logs if not log.success)
            unique_ips = len(set(log.ip_address for log in logs if log.ip_address))
            unique_resources = len(set(log.resource_id for log in logs if log.resource_id))
            
            # Define thresholds for suspicious activity
            is_suspicious = (
                phi_accesses > 50 or  # Excessive PHI access
                failed_actions > 10 or  # Many failed attempts
                unique_ips > 3 or  # Access from multiple IPs
                unique_resources > 100  # Accessing many resources
            )
            
            return {
                "is_suspicious": is_suspicious,
                "phi_accesses": phi_accesses,
                "failed_actions": failed_actions,
                "unique_ips": unique_ips,
                "unique_resources": unique_resources,
                "time_window_minutes": time_window_minutes,
                "total_actions": len(logs)
            }


# Global audit logger instance
audit_logger = AuditLogger()

