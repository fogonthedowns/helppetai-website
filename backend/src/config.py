"""
Application configuration using Pydantic Settings.
Handles environment variables and app settings.
"""

import os
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
        default="http://localhost:3000,http://localhost:3001,https://helppet.ai,https://www.helppet.ai", 
        env="CORS_ORIGINS"
    )
    cors_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", env="CORS_METHODS")
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
    
    @property
    def get_postgresql_url(self) -> str:
        """Get PostgreSQL URL - use RDS if configured, otherwise fallback to POSTGRESQL_URL"""
        if self.rds_hostname and self.rds_username and self.rds_password:
            return f"postgresql+asyncpg://{self.rds_username}:{self.rds_password}@{self.rds_hostname}:{self.rds_port}/{self.rds_db_name}"
        return self.postgresql_url
    
    @property
    def get_postgresql_sync_url(self) -> str:
        """Get PostgreSQL sync URL - use RDS if configured, otherwise fallback to POSTGRESQL_SYNC_URL"""
        if self.rds_hostname and self.rds_username and self.rds_password:
            return f"postgresql+psycopg2://{self.rds_username}:{self.rds_password}@{self.rds_hostname}:{self.rds_port}/{self.rds_db_name}"
        return self.postgresql_sync_url
    
    # MongoDB Configuration (keeping for migration)
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    database_name: str = Field(default="ai_visit_summary", env="DATABASE_NAME")
    
    # LLM Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # RAG Configuration
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="1536", env="PINECONE_INDEX_NAME")
    openai_embed_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBED_MODEL")
    
    # DynamoDB Configuration for RAG
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
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


# Global settings instance
settings = Settings()
