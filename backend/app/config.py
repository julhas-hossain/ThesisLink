"""
Configuration management for ThesisLink application.
Loads settings from environment variables with validation.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "ThesisLink"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Email Configuration
    EMAIL_PROVIDER: str = "smtp"  # smtp or gmail_api
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "ThesisLink"
    
    # Gmail API
    GMAIL_CREDENTIALS_FILE: str = "credentials.json"
    GMAIL_TOKEN_FILE: str = "token.json"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: str = ".pdf,.doc,.docx,.txt"
    UPLOAD_DIR: str = "./uploads"
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def convert_file_types(cls, v):
        if isinstance(v, str):
            return v
        return v
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Batch Email
    BATCH_EMAIL_DELAY_SECONDS: int = 5
    MAX_EMAILS_PER_BATCH: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
