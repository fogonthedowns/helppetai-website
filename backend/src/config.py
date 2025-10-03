"""
Application configuration using Pydantic Settings.
Handles environment variables and app settings.
"""

import os
import sys
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # App Configuration
    app_name: str = Field(default="AI Visit Summary Portal", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    docs_url: str = Field(default="/docs", env="DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="REDOC_URL")
    
    # Security Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://host.docker.internal:3000,https://helppet.ai,https://www.helppet.ai,null,file://", 
        env="CORS_ORIGINS"
    )
    cors_methods: str = Field(default="GET,POST,PUT,PATCH,DELETE,OPTIONS", env="CORS_METHODS")
    cors_headers: str = Field(default="*", env="CORS_HEADERS")
    
    # Production URLs
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    api_url: str = Field(default="http://localhost:8000", env="API_URL")
    
    # Database Configuration
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # PostgreSQL Configuration (RDS Support)
    postgresql_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/helppet_dev", 
        env="POSTGRESQL_URL"
    )
    postgresql_sync_url: str = Field(
        default="postgresql+psycopg2://postgres:password@localhost:5432/helppet_dev",
        env="POSTGRESQL_SYNC_URL"
    )
    
    # RDS specific configuration
    rds_hostname: Optional[str] = Field(default=None, env="RDS_HOSTNAME")
    rds_port: int = Field(default=5432, env="RDS_PORT")
    rds_db_name: str = Field(default="helppet_prod", env="RDS_DB_NAME")
    rds_username: Optional[str] = Field(default=None, env="RDS_USERNAME")
    rds_password: Optional[str] = Field(default=None, env="RDS_PASSWORD")
    rds_ssl_mode: str = Field(default="require", env="RDS_SSL_MODE")
    
    @property
    def get_postgresql_url(self) -> str:
        """Get PostgreSQL URL - use RDS if configured, otherwise fallback to POSTGRESQL_URL"""
        if self.rds_hostname and self.rds_username and self.rds_password:
            return f"postgresql+asyncpg://{self.rds_username}:{self.rds_password}@{self.rds_hostname}:{self.rds_port}/{self.rds_db_name}?ssl={self.rds_ssl_mode}"
        return self.postgresql_url
    
    @property
    def get_postgresql_sync_url(self) -> str:
        """Get PostgreSQL sync URL - use RDS if configured, otherwise fallback to POSTGRESQL_SYNC_URL"""
        if self.rds_hostname and self.rds_username and self.rds_password:
            return f"postgresql+psycopg2://{self.rds_username}:{self.rds_password}@{self.rds_hostname}:{self.rds_port}/{self.rds_db_name}?sslmode={self.rds_ssl_mode}"
        return self.postgresql_sync_url
    
    # MongoDB Configuration - REMOVED (using PostgreSQL only)
    
    # LLM Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # RAG Configuration
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="1536", env="PINECONE_INDEX_NAME")
    openai_embed_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBED_MODEL")
    
    # AWS Configuration
    aws_region: str = Field(default="us-west-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # S3 Configuration for Audio Uploads
    s3_bucket_name: str = Field(default="helppet-audio-recordings", env="S3_BUCKET_NAME")
    s3_recordings_prefix: str = Field(default="recordings/", env="S3_RECORDINGS_PREFIX")
    s3_presigned_url_expiration: int = Field(default=3600, env="S3_PRESIGNED_URL_EXPIRATION")  # 1 hour
    
    # DynamoDB Configuration for RAG
    dynamodb_vector_table: str = Field(default="rag_vector_index", env="DYNAMODB_VECTOR_TABLE")
    rag_sources_table: str = Field(default="rag_content_sources", env="RAG_SOURCES_TABLE")
    
    # JWT Authentication Configuration
    jwt_secret_key: str = Field(default="your-super-secret-jwt-key-change-in-production", env="JWT_SECRET_KEY")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


def validate_environment():
    """Validate critical environment variables and fail fast if missing."""
    
    # Check if we're in Docker (by checking if we're running as 'appuser' or in container)
    is_docker = (os.getenv('USER') == 'appuser' or 
                 os.path.exists('/.dockerenv') or 
                 os.getenv('ENVIRONMENT') and not os.path.exists('/Users'))
    
    # Check if .env file exists (required for local, should be copied into Docker)
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_file_path):
        if is_docker:
            print("❌ DOCKER ERROR: .env file not found in container!")
            print("💡 Solution: Rebuild the Docker image - .env file should be copied during build")
            print("   1. Make sure .env exists on host: cp env.template .env")
            print("   2. Rebuild: make build")
            print("   3. Run: make run")
        else:
            print("❌ STARTUP ERROR: .env file not found!")
            print("💡 Solution:")
            print("   1. Copy the template: cp env.template .env")
            print("   2. Edit .env with your PostgreSQL connection details")
            print("   3. For your local setup, use:")
            print("      POSTGRESQL_URL=postgresql+asyncpg://justinzollars@localhost:5432/helppet_dev")
            print("      POSTGRESQL_SYNC_URL=postgresql+psycopg2://justinzollars@localhost:5432/helppet_dev")
            print("")
            print("⚠️  IMPORTANT: Make sure you're running the PostgreSQL version:")
            print("   uvicorn src.main_pg:app --host 0.0.0.0 --port 8000 --reload")
            print("   NOT: uvicorn src.main:app ...")
        sys.exit(1)
    
    # Test database connection string format
    test_settings = Settings()
    
    # Check PostgreSQL URL format
    if not test_settings.postgresql_url.startswith(('postgresql+asyncpg://', 'postgresql://')):
        print("❌ STARTUP ERROR: Invalid POSTGRESQL_URL format!")
        print(f"   Current: {test_settings.postgresql_url}")
        print("💡 Expected format: postgresql+asyncpg://user@host:port/database")
        print("   For your local setup: postgresql+asyncpg://justinzollars@localhost:5432/helppet_dev")
        sys.exit(1)
    
    # Check if required database fields are present
    if 'localhost' in test_settings.postgresql_url and 'justinzollars' not in test_settings.postgresql_url:
        print("❌ STARTUP ERROR: PostgreSQL connection uses wrong username!")
        print(f"   Current: {test_settings.postgresql_url}")
        print("💡 For your local setup, change to:")
        print("   POSTGRESQL_URL=postgresql+asyncpg://justinzollars@localhost:5432/helppet_dev")
        print("   POSTGRESQL_SYNC_URL=postgresql+psycopg2://justinzollars@localhost:5432/helppet_dev")
        sys.exit(1)
    
    print("✅ Environment validation passed")
    print(f"✅ Using PostgreSQL: {test_settings.postgresql_url}")
    return test_settings


# Validate environment on import and create settings
validate_environment()
settings = Settings()
