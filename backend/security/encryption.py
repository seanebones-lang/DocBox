"""
PHI (Protected Health Information) encryption module.
Provides AES-256 encryption for sensitive patient data (HIPAA compliant).
"""

import base64
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

from config import settings


class EncryptionService:
    """
    Service for encrypting and decrypting PHI using AES-256.
    Uses Fernet (symmetric encryption) for field-level encryption.
    """
    
    def __init__(self, encryption_key: Optional[str] = None) -> None:
        """
        Initialize encryption service with key.
        
        Args:
            encryption_key: Base64-encoded encryption key. Uses settings key if not provided.
        """
        key = encryption_key or settings.encryption_key
        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted_bytes).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt encrypted string.
        
        Args:
            ciphertext: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
        
        encrypted_bytes = base64.b64decode(ciphertext.encode())
        decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    
    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data
            fields: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        encrypted_data = data.copy()
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        decrypted_data = data.copy()
        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
        return decrypted_data


class FieldEncryption:
    """
    Field-level encryption for highly sensitive data (SSN, genomic data).
    Uses separate encryption key for additional security layer.
    """
    
    def __init__(self, field_key: Optional[str] = None) -> None:
        """Initialize field encryption with dedicated key."""
        key = field_key or settings.field_encryption_key
        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt_ssn(self, ssn: str) -> str:
        """Encrypt Social Security Number with additional security."""
        if not ssn:
            return ""
        # Remove any formatting
        clean_ssn = ssn.replace("-", "").replace(" ", "")
        encrypted = self.fernet.encrypt(clean_ssn.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_ssn(self, encrypted_ssn: str) -> str:
        """Decrypt Social Security Number."""
        if not encrypted_ssn:
            return ""
        encrypted_bytes = base64.b64decode(encrypted_ssn.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        ssn = decrypted.decode()
        # Format as XXX-XX-XXXX
        return f"{ssn[:3]}-{ssn[3:5]}-{ssn[5:]}" if len(ssn) == 9 else ssn
    
    def encrypt_genomic_data(self, data: bytes) -> str:
        """Encrypt genomic data (typically large binary files)."""
        encrypted = self.fernet.encrypt(data)
        return base64.b64encode(encrypted).decode()
    
    def decrypt_genomic_data(self, encrypted_data: str) -> bytes:
        """Decrypt genomic data."""
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        return self.fernet.decrypt(encrypted_bytes)


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    Use this for initial setup or key rotation.
    
    Returns:
        Base64-encoded encryption key
    """
    return Fernet.generate_key().decode()


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive encryption key from password using PBKDF2.
    
    Args:
        password: User password
        salt: Random salt (should be stored with encrypted data)
        
    Returns:
        Derived encryption key
    """
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,  # OWASP recommendation for 2025
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# Global instances for convenience
encryption_service = EncryptionService()
field_encryption = FieldEncryption()

