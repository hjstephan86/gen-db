"""
Configuration Management für Gen-DB

Zentrale Konfigurationshandhabung mit:
- Environment Variable Parsing (via Pydantic)
- Validation (via Pydantic validators)
- Default Values
- Type Conversion
"""

import logging
from typing import Optional, List, Any, Dict
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Konfigurationsfehler"""
    pass


class Config(BaseSettings):
    """
    Zentrale Konfiguration für Gen-DB
    
    Lädt Konfiguration aus (in dieser Reihenfolge):
    1. Umgebungsvariablen
    2. .env Datei (automatisch via Pydantic)
    3. Defaults
    """
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # === API Configuration ===
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    reload: bool = Field(default=False, description="Enable auto-reload")
    show_sql: bool = Field(default=False, description="Show SQL queries")
    
    # === Subgraph Executor ===
    subgraph_cli_path: Optional[str] = Field(default=None, description="Path to Subgraph CLI")
    subgraph_max_workers: Optional[int] = Field(default=None, ge=1, description="Max workers for Subgraph")
    subgraph_timeout: int = Field(default=30, ge=5, description="Subgraph timeout in seconds")
    
    # === Database Configuration ===
    database_host: str = Field(default="localhost", description="Database host")
    database_port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    database_user: str = Field(default="postgres", description="Database user")
    database_password: str = Field(default="postgres", description="Database password")
    database_name: str = Field(default="gendb", description="Database name")
    database_pool_size: int = Field(default=10, ge=1, description="Connection pool size")
    database_pool_recycle: int = Field(default=3600, ge=1, description="Connection pool recycle time")
    database_ssl_mode: str = Field(default="disable", description="SSL mode")
    
    # === CORS Configuration ===
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods"
    )
    cors_headers: List[str] = Field(
        default=["Content-Type", "Authorization"],
        description="CORS allowed headers"
    )
    cors_credentials: bool = Field(default=True, description="CORS credentials")
    
    # === Rate Limiting ===
    rate_limit_requests: int = Field(default=300, ge=1, description="Rate limit requests")
    rate_limit_window: int = Field(default=1, ge=1, description="Rate limit window in seconds")
    
    # === Monitoring ===
    enable_prometheus: bool = Field(default=False, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, ge=1, le=65535, description="Prometheus port")
    enable_request_tracking: bool = Field(default=True, description="Enable request tracking")
    
    # === Security ===
    secret_key: str = Field(default="change-this-in-production", description="Secret key for security")
    max_upload_size: int = Field(default=10485760, ge=1, description="Max upload size in bytes")
    
    # === Container & Environment ===
    container_env: str = Field(default="production", description="Container environment")
    
    # === Development ===
    generate_fake_data: bool = Field(default=False, description="Generate fake data on startup")
    fake_data_count: int = Field(default=10, ge=1, description="Number of fake data records")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {v}")
        return v_upper
    
    @field_validator('database_ssl_mode')
    @classmethod
    def validate_database_ssl_mode(cls, v: str) -> str:
        """Validate database SSL mode"""
        valid_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if v.lower() not in valid_modes:
            raise ValueError(f"DATABASE_SSL_MODE must be one of {valid_modes}, got {v}")
        return v.lower()
    
    @field_validator('container_env')
    @classmethod
    def validate_container_env(cls, v: str) -> str:
        """Validate container environment"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            logger.warning(f"CONTAINER_ENV '{v}' is not a standard environment")
        return v.lower()
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate secret key in production"""
        if info.data.get('container_env') == "production":
            if v == "change-this-in-production":
                raise ValueError("SECRET_KEY must be changed in production environment!")
        return v
    
    def get_database_url(self) -> str:
        """
        Konstruiert PostgreSQL Connection URL
        
        Returns:
            PostgreSQL URL für psycopg2/SQLAlchemy
        """
        ssl_part = f"?sslmode={self.database_ssl_mode}" if self.database_ssl_mode != "disable" else ""
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}{ssl_part}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Konfiguration zu Dictionary"""
        return self.model_dump()
    
    def __repr__(self) -> str:
        """String representation"""
        config_dict = self.model_dump()
        # Maskiere sensitive Werte
        config_dict['database_password'] = '***'
        config_dict['secret_key'] = '***'
        
        items = "\n  ".join(f"{k}: {v}" for k, v in sorted(config_dict.items()))
        return f"Config(\n  {items}\n)"


# Singleton Pattern für Backward Compatibility
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Gibt globale Config Instanz zurück (Singleton)
    
    Returns:
        Config Instanz
    """
    global _config_instance
    
    if _config_instance is None:
        try:
            _config_instance = Config()
            logger.info(f"Configuration loaded (ENV={_config_instance.container_env})")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigError(f"Konfigurationsfehler: {e}") from e
    
    return _config_instance


def reload_config() -> Config:
    """
    Lädt Konfiguration neu (für Testing)
    
    Returns:
        Neue Config Instanz
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance
