"""
Application configuration management.
Loads environment variables and provides typed configuration objects.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DocBox"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "v1"
    secret_key: str

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    web_app_url: str = "http://localhost:3000"
    kiosk_app_url: str = "http://localhost:3001"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "docbox"
    postgres_user: str
    postgres_password: str
    database_url: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        """Construct database URL if not provided."""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_url: Optional[str] = None

    @property
    def get_redis_url(self) -> str:
        """Construct Redis URL."""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Qdrant Vector Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "medical_knowledge"

    # LLM Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    cohere_api_key: Optional[str] = None

    # Authentication
    auth_provider: str = "auth0"
    auth0_domain: Optional[str] = None
    auth0_client_id: Optional[str] = None
    auth0_client_secret: Optional[str] = None
    auth0_audience: Optional[str] = None

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Encryption
    encryption_key: str
    field_encryption_key: str

    # Blockchain
    blockchain_enabled: bool = False
    hyperledger_peer_url: Optional[str] = None
    hyperledger_orderer_url: Optional[str] = None
    hyperledger_channel: str = "healthcare-channel"
    hyperledger_chaincode: str = "audit-trail"

    # FHIR
    fhir_base_url: str = "https://fhir.docbox.health"
    fhir_version: str = "R5"

    # IoT
    iot_enabled: bool = False
    iot_hub_connection_string: Optional[str] = None
    wearable_api_keys: dict = {}

    # Payment
    stripe_api_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    payment_gateway: str = "stripe"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "DocBox <noreply@docbox.health>"

    # SMS
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # Storage
    storage_provider: str = "s3"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_region: str = "us-east-1"

    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    enable_metrics: bool = True
    prometheus_port: int = 9090

    # Security
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    allowed_hosts: str = "localhost,127.0.0.1"

    @property
    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def get_allowed_hosts(self) -> list[str]:
        """Parse allowed hosts from comma-separated string."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    # Compliance
    hipaa_audit_enabled: bool = True
    audit_log_retention_years: int = 7
    gdpr_enabled: bool = True
    auto_session_timeout_minutes: int = 30

    # Feature Flags
    enable_biometric_auth: bool = True
    enable_blockchain_audit: bool = False
    enable_iot_monitoring: bool = False
    enable_genomic_data: bool = False
    enable_ar_features: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


settings = get_settings()

