"""
NEXUS Production Configuration
Environment-based configuration with secrets management and validation
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import timedelta
import hvac
from pydantic import BaseSettings, validator, Field
from dotenv import load_dotenv
import yaml

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class VaultClient:
    """HashiCorp Vault client for secrets management"""
    
    def __init__(self, vault_url: str, vault_token: str, mount_point: str = "secret"):
        self.client = hvac.Client(url=vault_url, token=vault_token)
        self.mount_point = mount_point
        
        if not self.client.is_authenticated():
            raise Exception("Vault authentication failed")
    
    def get_secret(self, path: str) -> Dict[str, Any]:
        """Retrieve secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to retrieve secret from {path}: {e}")
            raise
    
    def set_secret(self, path: str, secret: Dict[str, Any]):
        """Store secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                mount_point=self.mount_point
            )
        except Exception as e:
            logger.error(f"Failed to store secret at {path}: {e}")
            raise


class FeatureFlags:
    """Feature flags management system"""
    
    def __init__(self, config_source: str = "env"):
        self.config_source = config_source
        self._flags = {}
        self._load_flags()
    
    def _load_flags(self):
        """Load feature flags from configuration source"""
        if self.config_source == "env":
            # Load from environment variables
            for key, value in os.environ.items():
                if key.startswith("FEATURE_"):
                    flag_name = key[8:].lower()
                    self._flags[flag_name] = value.lower() in ('true', '1', 'yes', 'on')
        elif self.config_source == "file":
            # Load from file
            try:
                with open("feature_flags.json", "r") as f:
                    self._flags = json.load(f)
            except FileNotFoundError:
                logger.warning("Feature flags file not found, using defaults")
    
    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Check if feature flag is enabled"""
        return self._flags.get(flag_name, default)
    
    def set_flag(self, flag_name: str, enabled: bool):
        """Dynamically update feature flag"""
        self._flags[flag_name] = enabled
        logger.info(f"Feature flag '{flag_name}' set to {enabled}")
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self._flags.copy()


class ProductionConfig(BaseSettings):
    """Production configuration with validation"""
    
    # Application settings
    APP_NAME: str = Field(default="NEXUS", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    WORKER_CLASS: str = Field(default="uvicorn.workers.UvicornWorker", env="WORKER_CLASS")
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    DB_ECHO: bool = Field(default=False, env="DB_ECHO")
    DB_MAX_CONNECTIONS: int = Field(default=100, env="DB_MAX_CONNECTIONS")
    DB_READ_REPLICAS: List[str] = Field(default_factory=list, env="DB_READ_REPLICAS")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_POOL_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_POOL_MAX_CONNECTIONS")
    REDIS_SENTINELS: Optional[List[tuple]] = Field(default=None, env="REDIS_SENTINELS")
    REDIS_MASTER_NAME: str = Field(default="mymaster", env="REDIS_MASTER_NAME")
    
    # RabbitMQ settings
    RABBITMQ_HOST: str = Field(default="localhost", env="RABBITMQ_HOST")
    RABBITMQ_PORT: int = Field(default=5672, env="RABBITMQ_PORT")
    RABBITMQ_USER: str = Field(default="guest", env="RABBITMQ_USER")
    RABBITMQ_PASSWORD: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    RABBITMQ_VHOST: str = Field(default="/", env="RABBITMQ_VHOST")
    
    # Celery settings
    CELERY_BROKER_URL: str = Field(default="amqp://guest:guest@localhost:5672//", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_TIME_LIMIT: int = Field(default=3600, env="CELERY_TASK_TIME_LIMIT")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=3300, env="CELERY_TASK_SOFT_TIME_LIMIT")
    
    # Monitoring settings
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    OTLP_ENDPOINT: str = Field(default="localhost:4317", env="OTLP_ENDPOINT")
    OTLP_INSECURE: bool = Field(default=True, env="OTLP_INSECURE")
    
    # Security settings
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    CORS_CREDENTIALS: bool = Field(default=True, env="CORS_CREDENTIALS")
    CORS_METHODS: List[str] = Field(default=["*"], env="CORS_METHODS")
    CORS_HEADERS: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Vault settings (optional)
    VAULT_ENABLED: bool = Field(default=False, env="VAULT_ENABLED")
    VAULT_URL: Optional[str] = Field(default=None, env="VAULT_URL")
    VAULT_TOKEN: Optional[str] = Field(default=None, env="VAULT_TOKEN")
    VAULT_MOUNT_POINT: str = Field(default="secret", env="VAULT_MOUNT_POINT")
    
    # Feature flags
    FEATURE_FLAGS_ENABLED: bool = Field(default=True, env="FEATURE_FLAGS_ENABLED")
    FEATURE_FLAGS_SOURCE: str = Field(default="env", env="FEATURE_FLAGS_SOURCE")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # External services
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Storage
    STORAGE_TYPE: str = Field(default="local", env="STORAGE_TYPE")
    STORAGE_PATH: str = Field(default="/data", env="STORAGE_PATH")
    S3_BUCKET: Optional[str] = Field(default=None, env="S3_BUCKET")
    S3_REGION: Optional[str] = Field(default=None, env="S3_REGION")
    S3_ACCESS_KEY: Optional[str] = Field(default=None, env="S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = Field(default=None, env="S3_SECRET_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @validator("DB_READ_REPLICAS", pre=True)
    def parse_read_replicas(cls, v):
        """Parse read replicas from string"""
        if isinstance(v, str):
            return [url.strip() for url in v.split(",") if url.strip()]
        return v or []
    
    @validator("REDIS_SENTINELS", pre=True)
    def parse_redis_sentinels(cls, v):
        """Parse Redis sentinels from string"""
        if isinstance(v, str) and v:
            sentinels = []
            for sentinel in v.split(","):
                host, port = sentinel.strip().split(":")
                sentinels.append((host, int(port)))
            return sentinels
        return v
    
    @validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", pre=True)
    def parse_list_from_string(cls, v):
        """Parse list from comma-separated string"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._vault_client = None
        self._feature_flags = None
        
        # Initialize Vault client if enabled
        if self.VAULT_ENABLED and self.VAULT_URL and self.VAULT_TOKEN:
            self._vault_client = VaultClient(
                self.VAULT_URL,
                self.VAULT_TOKEN,
                self.VAULT_MOUNT_POINT
            )
            self._load_secrets_from_vault()
        
        # Initialize feature flags
        if self.FEATURE_FLAGS_ENABLED:
            self._feature_flags = FeatureFlags(self.FEATURE_FLAGS_SOURCE)
    
    def _load_secrets_from_vault(self):
        """Load secrets from Vault and override configuration"""
        try:
            # Load database credentials
            db_secrets = self._vault_client.get_secret("database/credentials")
            if db_secrets:
                self.DATABASE_URL = self._build_database_url(db_secrets)
            
            # Load API keys
            api_keys = self._vault_client.get_secret("api/keys")
            if api_keys:
                self.OPENAI_API_KEY = api_keys.get("openai")
                self.ANTHROPIC_API_KEY = api_keys.get("anthropic")
            
            # Load JWT secret
            jwt_secret = self._vault_client.get_secret("jwt/secret")
            if jwt_secret:
                self.JWT_SECRET_KEY = jwt_secret.get("key")
            
            logger.info("Secrets loaded from Vault successfully")
        except Exception as e:
            logger.error(f"Failed to load secrets from Vault: {e}")
            if self.ENVIRONMENT == "production":
                raise
    
    def _build_database_url(self, credentials: Dict[str, str]) -> str:
        """Build database URL from credentials"""
        return (
            f"postgresql+asyncpg://{credentials['username']}:{credentials['password']}"
            f"@{credentials['host']}:{credentials.get('port', 5432)}/{credentials['database']}"
        )
    
    def get_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Get secret from Vault"""
        if self._vault_client:
            return self._vault_client.get_secret(path)
        return None
    
    def is_feature_enabled(self, feature_name: str, default: bool = False) -> bool:
        """Check if feature is enabled"""
        if self._feature_flags:
            return self._feature_flags.is_enabled(feature_name, default)
        return default
    
    def get_all_features(self) -> Dict[str, bool]:
        """Get all feature flags"""
        if self._feature_flags:
            return self._feature_flags.get_all_flags()
        return {}
    
    def update_feature(self, feature_name: str, enabled: bool):
        """Update feature flag dynamically"""
        if self._feature_flags:
            self._feature_flags.set_flag(feature_name, enabled)
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert config to dictionary"""
        data = self.dict()
        
        if not include_secrets:
            # Remove sensitive fields
            sensitive_fields = [
                'SECRET_KEY', 'DATABASE_URL', 'JWT_SECRET_KEY',
                'RABBITMQ_PASSWORD', 'VAULT_TOKEN', 'OPENAI_API_KEY',
                'ANTHROPIC_API_KEY', 'S3_ACCESS_KEY', 'S3_SECRET_KEY'
            ]
            for field in sensitive_fields:
                if field in data:
                    data[field] = '***REDACTED***'
        
        return data
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required fields
        if not self.SECRET_KEY:
            issues.append("SECRET_KEY is required")
        
        if not self.DATABASE_URL:
            issues.append("DATABASE_URL is required")
        
        if not self.JWT_SECRET_KEY:
            issues.append("JWT_SECRET_KEY is required")
        
        # Check database connection
        if self.DATABASE_URL and not self.DATABASE_URL.startswith("postgresql"):
            issues.append("Only PostgreSQL is supported")
        
        # Check Redis sentinels configuration
        if self.REDIS_SENTINELS and not self.REDIS_MASTER_NAME:
            issues.append("REDIS_MASTER_NAME is required when using sentinels")
        
        # Validate feature flags
        if self.FEATURE_FLAGS_ENABLED and self.FEATURE_FLAGS_SOURCE not in ["env", "file"]:
            issues.append("Invalid FEATURE_FLAGS_SOURCE")
        
        return issues
    
    def save_to_file(self, filepath: str, format: str = "yaml"):
        """Save configuration to file"""
        config_data = self.to_dict(include_secrets=False)
        
        if format == "yaml":
            with open(filepath, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        elif format == "json":
            with open(filepath, "w") as f:
                json.dump(config_data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "ProductionConfig":
        """Load configuration from file"""
        if filepath.endswith(".yaml") or filepath.endswith(".yml"):
            with open(filepath, "r") as f:
                data = yaml.safe_load(f)
        elif filepath.endswith(".json"):
            with open(filepath, "r") as f:
                data = json.load(f)
        else:
            raise ValueError("Unsupported file format")
        
        return cls(**data)


# Configuration profiles
class ConfigurationProfiles:
    """Predefined configuration profiles"""
    
    @staticmethod
    def development() -> Dict[str, Any]:
        """Development profile"""
        return {
            "ENVIRONMENT": "development",
            "DEBUG": True,
            "DB_ECHO": True,
            "WORKERS": 1,
            "LOG_LEVEL": "DEBUG",
            "RATE_LIMIT_ENABLED": False
        }
    
    @staticmethod
    def staging() -> Dict[str, Any]:
        """Staging profile"""
        return {
            "ENVIRONMENT": "staging",
            "DEBUG": False,
            "DB_ECHO": False,
            "WORKERS": 2,
            "LOG_LEVEL": "INFO",
            "RATE_LIMIT_ENABLED": True
        }
    
    @staticmethod
    def production() -> Dict[str, Any]:
        """Production profile"""
        return {
            "ENVIRONMENT": "production",
            "DEBUG": False,
            "DB_ECHO": False,
            "WORKERS": 4,
            "LOG_LEVEL": "WARNING",
            "RATE_LIMIT_ENABLED": True,
            "VAULT_ENABLED": True
        }


# Helper function to get configuration
def get_config(profile: Optional[str] = None) -> ProductionConfig:
    """Get configuration based on profile"""
    base_config = {}
    
    if profile:
        profiles = ConfigurationProfiles()
        if hasattr(profiles, profile):
            base_config = getattr(profiles, profile)()
    
    # Override with environment variables
    config = ProductionConfig(**base_config)
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        logger.warning(f"Configuration issues found: {issues}")
    
    return config