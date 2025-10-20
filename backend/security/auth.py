"""
Authentication and authorization module.
Handles JWT tokens, password hashing, MFA, and RBAC.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings
from models.user import UserRole


# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for 2025 security standards
)


class PasswordManager:
    """Manage password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password hash needs to be updated.
        
        Args:
            hashed_password: Current password hash
            
        Returns:
            True if hash should be updated
        """
        return pwd_context.needs_update(hashed_password)


class JWTManager:
    """Manage JWT token creation and validation."""
    
    @staticmethod
    def create_access_token(
        user_id: UUID,
        email: str,
        role: UserRole,
        clinic_id: Optional[UUID] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            role: User's role for RBAC
            clinic_id: Optional clinic ID for multi-tenant access
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.jwt_access_token_expire_minutes
            )
        
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role.value if isinstance(role, UserRole) else role,
            "clinic_id": str(clinic_id) if clinic_id else None,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        user_id: UUID,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token for obtaining new access tokens.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.jwt_refresh_token_expire_days
            )
        
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify token and check type.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = JWTManager.decode_token(token)
            if payload.get("type") != token_type:
                return None
            return payload
        except ValueError:
            return None


class MFAManager:
    """Manage Multi-Factor Authentication (Time-based OTP)."""
    
    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new TOTP secret for a user.
        
        Returns:
            Base32-encoded secret
        """
        return pyotp.random_base32()
    
    @staticmethod
    def get_provisioning_uri(
        secret: str,
        email: str,
        issuer: str = "DocBox"
    ) -> str:
        """
        Generate provisioning URI for QR code.
        
        Args:
            secret: User's TOTP secret
            email: User's email address
            issuer: Application name
            
        Returns:
            Provisioning URI for authenticator apps
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """
        Verify TOTP token.
        
        Args:
            secret: User's TOTP secret
            token: 6-digit code from authenticator app
            
        Returns:
            True if token is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 1 time step tolerance


class RBACManager:
    """Role-Based Access Control manager."""
    
    # Define role hierarchies and permissions
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            "patients": ["create", "read", "update", "delete"],
            "appointments": ["create", "read", "update", "delete"],
            "users": ["create", "read", "update", "delete"],
            "clinics": ["create", "read", "update", "delete"],
            "reports": ["read", "export"],
            "audit_logs": ["read"],
        },
        UserRole.DOCTOR: {
            "patients": ["create", "read", "update"],
            "appointments": ["create", "read", "update"],
            "medical_records": ["create", "read", "update"],
            "prescriptions": ["create", "read", "update"],
        },
        UserRole.NURSE: {
            "patients": ["read", "update"],
            "appointments": ["read", "update"],
            "medical_records": ["read", "update"],
            "vitals": ["create", "read", "update"],
        },
        UserRole.RECEPTIONIST: {
            "patients": ["create", "read", "update"],
            "appointments": ["create", "read", "update", "delete"],
            "billing": ["read", "update"],
        },
        UserRole.PATIENT: {
            "own_records": ["read"],
            "appointments": ["create", "read"],
            "messages": ["create", "read"],
        },
        UserRole.KIOSK: {
            "check_in": ["create"],
            "forms": ["create"],
            "payments": ["create"],
        },
    }
    
    @staticmethod
    def has_permission(role: UserRole, resource: str, action: str) -> bool:
        """
        Check if role has permission for action on resource.
        
        Args:
            role: User's role
            resource: Resource being accessed
            action: Action being performed (create, read, update, delete)
            
        Returns:
            True if user has permission, False otherwise
        """
        permissions = RBACManager.ROLE_PERMISSIONS.get(role, {})
        resource_permissions = permissions.get(resource, [])
        return action in resource_permissions
    
    @staticmethod
    def can_access_clinic(user_clinic_id: Optional[UUID], resource_clinic_id: UUID) -> bool:
        """
        Check if user can access resource from specific clinic.
        
        Args:
            user_clinic_id: User's assigned clinic
            resource_clinic_id: Clinic ID of the resource
            
        Returns:
            True if user can access, False otherwise
        """
        # Admins can access all clinics
        if user_clinic_id is None:
            return True
        
        # Staff can only access their assigned clinic
        return str(user_clinic_id) == str(resource_clinic_id)


# Global instances
password_manager = PasswordManager()
jwt_manager = JWTManager()
mfa_manager = MFAManager()
rbac_manager = RBACManager()

