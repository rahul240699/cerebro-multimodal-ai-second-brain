"""
Configuration Management
Centralized settings for the application using Pydantic
"""

from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )
    
    # Application
    APP_NAME: str = "Cerebro"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cerebro"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OpenAI API
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Anthropic API
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Audio Processing
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    MAX_AUDIO_SIZE_MB: int = 50
    
    # Document Processing
    MAX_DOCUMENT_SIZE_MB: int = 20
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Retrieval
    TOP_K_RESULTS: int = 20
    RERANK_TOP_N: int = 10
    
    # Storage
    UPLOAD_DIR: str = "uploads"
    KEEP_AUDIO_FILES: bool = False  # Privacy: delete after transcription
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]


# Global settings instance
settings = Settings()
