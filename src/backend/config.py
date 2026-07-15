"""
Configuration Management für Gen-DB

Zentrale Konfigurationshandhabung mit:
- Environment Variable Parsing
- Validation
- Default Values
- Type Conversion
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Konfigurationsfehler"""
    pass


class Config:
    """
    Zentrale Konfiguration für Gen-DB
    
    Lädt Konfiguration aus (in dieser Reihenfolge):
    1. Umgebungsvariablen
    2. .env Datei
    3. Defaults
    """
    
    # Defaults
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Subgraph Executor
    SUBGRAPH_CLI_PATH: Optional[str] = None
    SUBGRAPH_MAX_WORKERS: Optional[int] = None
    SUBGRAPH_TIMEOUT: int = 30
    
    # Database
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_NAME: str = "gendb"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_SSL_MODE: str = "disable"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    CORS_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: list = ["Content-Type", "Authorization"]
    CORS_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 300
    RATE_LIMIT_WINDOW: int = 1
    
    # Monitoring
    ENABLE_PROMETHEUS: bool = False
    PROMETHEUS_PORT: int = 9090
    ENABLE_REQUEST_TRACKING: bool = True
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # Container
    CONTAINER_ENV: str = "production"
    
    # Development
    RELOAD: bool = False
    SHOW_SQL: bool = False
    GENERATE_FAKE_DATA: bool = False
    FAKE_DATA_COUNT: int = 10
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Lädt Konfiguration aus Umgebungsvariablen und .env Datei
        
        Returns:
            Config Instanz
        """
        instance = cls()
        
        # Lade .env Datei falls vorhanden
        env_file = Path(".env")
        if env_file.exists():
            logger.info(f"Loading .env from {env_file.absolute()}")
            instance._load_env_file(env_file)
        
        # Lade Umgebungsvariablen (überschreiben .env)
        instance._load_from_env()
        
        # Validiere Konfiguration
        instance._validate()
        
        logger.info(f"Configuration loaded (ENV={instance.CONTAINER_ENV})")
        
        return instance
    
    @classmethod
    def _load_env_file(cls, env_file: Path) -> None:
        """Lade .env Datei in os.environ"""
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Ignoriere Kommentare und leere Zeilen
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
    
    def _load_from_env(self) -> None:
        """Lade Umgebungsvariablen"""
        # Boolean
        self.DEBUG = self._parse_bool("DEBUG", self.DEBUG)
        self.RELOAD = self._parse_bool("RELOAD", self.RELOAD)
        self.SHOW_SQL = self._parse_bool("SHOW_SQL", self.SHOW_SQL)
        self.GENERATE_FAKE_DATA = self._parse_bool("GENERATE_FAKE_DATA", self.GENERATE_FAKE_DATA)
        self.ENABLE_PROMETHEUS = self._parse_bool("ENABLE_PROMETHEUS", self.ENABLE_PROMETHEUS)
        self.ENABLE_REQUEST_TRACKING = self._parse_bool("ENABLE_REQUEST_TRACKING", self.ENABLE_REQUEST_TRACKING)
        self.CORS_CREDENTIALS = self._parse_bool("CORS_CREDENTIALS", self.CORS_CREDENTIALS)
        
        # String
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", self.LOG_LEVEL).upper()
        self.API_HOST = os.environ.get("API_HOST", self.API_HOST)
        self.DATABASE_HOST = os.environ.get("DATABASE_HOST", self.DATABASE_HOST)
        self.DATABASE_USER = os.environ.get("DATABASE_USER", self.DATABASE_USER)
        self.DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", self.DATABASE_PASSWORD)
        self.DATABASE_NAME = os.environ.get("DATABASE_NAME", self.DATABASE_NAME)
        self.DATABASE_SSL_MODE = os.environ.get("DATABASE_SSL_MODE", self.DATABASE_SSL_MODE)
        self.CONTAINER_ENV = os.environ.get("CONTAINER_ENV", self.CONTAINER_ENV)
        self.SECRET_KEY = os.environ.get("SECRET_KEY", self.SECRET_KEY)
        self.SUBGRAPH_CLI_PATH = os.environ.get("SUBGRAPH_CLI_PATH", self.SUBGRAPH_CLI_PATH)
        
        # Integer
        self.API_PORT = self._parse_int("API_PORT", self.API_PORT)
        self.DATABASE_PORT = self._parse_int("DATABASE_PORT", self.DATABASE_PORT)
        self.DATABASE_POOL_SIZE = self._parse_int("DATABASE_POOL_SIZE", self.DATABASE_POOL_SIZE)
        self.DATABASE_POOL_RECYCLE = self._parse_int("DATABASE_POOL_RECYCLE", self.DATABASE_POOL_RECYCLE)
        self.SUBGRAPH_MAX_WORKERS = self._parse_int("SUBGRAPH_MAX_WORKERS", self.SUBGRAPH_MAX_WORKERS)
        self.SUBGRAPH_TIMEOUT = self._parse_int("SUBGRAPH_TIMEOUT", self.SUBGRAPH_TIMEOUT)
        self.RATE_LIMIT_REQUESTS = self._parse_int("RATE_LIMIT_REQUESTS", self.RATE_LIMIT_REQUESTS)
        self.RATE_LIMIT_WINDOW = self._parse_int("RATE_LIMIT_WINDOW", self.RATE_LIMIT_WINDOW)
        self.PROMETHEUS_PORT = self._parse_int("PROMETHEUS_PORT", self.PROMETHEUS_PORT)
        self.MAX_UPLOAD_SIZE = self._parse_int("MAX_UPLOAD_SIZE", self.MAX_UPLOAD_SIZE)
        self.FAKE_DATA_COUNT = self._parse_int("FAKE_DATA_COUNT", self.FAKE_DATA_COUNT)
        
        # Lists (comma-separated)
        self.CORS_ORIGINS = self._parse_list("CORS_ORIGINS", self.CORS_ORIGINS)
        self.CORS_METHODS = self._parse_list("CORS_METHODS", self.CORS_METHODS)
        self.CORS_HEADERS = self._parse_list("CORS_HEADERS", self.CORS_HEADERS)
    
    def _validate(self) -> None:
        """Validiere Konfiguration"""
        errors = []
        
        # Database Validierung
        if not self.DATABASE_USER:
            errors.append("DATABASE_USER nicht gesetzt")
        if not self.DATABASE_PASSWORD:
            errors.append("DATABASE_PASSWORD sollte nicht leer sein")
        if self.DATABASE_PORT not in range(1, 65536):
            errors.append(f"DATABASE_PORT ungültig: {self.DATABASE_PORT}")
        
        # API Validierung
        if self.API_PORT not in range(1, 65536):
            errors.append(f"API_PORT ungültig: {self.API_PORT}")
        if self.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"LOG_LEVEL ungültig: {self.LOG_LEVEL}")
        
        # Subgraph Validierung
        if self.SUBGRAPH_TIMEOUT < 5:
            errors.append(f"SUBGRAPH_TIMEOUT sollte >= 5s sein")
        
        # Production Warnings
        if self.CONTAINER_ENV == "production":
            if self.SECRET_KEY == "change-this-in-production":
                errors.append("SECRET_KEY muss in Production geändert werden!")
            if self.DEBUG:
                logger.warning("DEBUG=True in Production ist nicht empfohlen!")
        
        if errors:
            error_msg = "\n  - ".join(errors)
            raise ConfigError(f"Konfigurationsfehler:\n  - {error_msg}")
    
    @staticmethod
    def _parse_bool(key: str, default: bool) -> bool:
        """Parse boolean value"""
        value = os.environ.get(key, "").lower()
        if value in ["true", "1", "yes", "on"]:
            return True
        elif value in ["false", "0", "no", "off"]:
            return False
        return default
    
    @staticmethod
    def _parse_int(key: str, default: Optional[int]) -> Optional[int]:
        """Parse integer value"""
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Could not parse {key}={value} as int, using default {default}")
            return default
    
    @staticmethod
    def _parse_list(key: str, default: list) -> list:
        """Parse comma-separated list"""
        value = os.environ.get(key)
        if value is None:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def get_database_url(self) -> str:
        """
        Konstruiert PostgreSQL Connection URL
        
        Returns:
            PostgreSQL URL für psycopg2/SQLAlchemy
        """
        ssl_part = f"?sslmode={self.DATABASE_SSL_MODE}" if self.DATABASE_SSL_MODE != "disable" else ""
        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}{ssl_part}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Konfiguration zu Dictionary"""
        return {
            key: getattr(self, key)
            for key in dir(self)
            if not key.startswith('_') and key.isupper()
        }
    
    def __repr__(self) -> str:
        """String representation"""
        config_dict = self.to_dict()
        # Maskiere sensitive Werte
        config_dict['DATABASE_PASSWORD'] = '***'
        config_dict['SECRET_KEY'] = '***'
        
        items = "\n  ".join(f"{k}: {v}" for k, v in sorted(config_dict.items()))
        return f"Config(\n  {items}\n)"


# Singleton Pattern
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Gibt globale Config Instanz zurück (Singleton)
    
    Returns:
        Config Instanz
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config.from_env()
    
    return _config_instance


def reload_config() -> Config:
    """
    Lädt Konfiguration neu (für Testing)
    
    Returns:
        Neue Config Instanz
    """
    global _config_instance
    _config_instance = Config.from_env()
    return _config_instance
