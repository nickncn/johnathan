"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://risk_user:risk_pass@localhost:5432/risk_dashboard",
        description="Database connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Security
    JWT_SECRET: str = Field(
        default="change-this-secret-key",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # LLM Configuration
    LLM_PROVIDER: str = Field(default="anthropic", description="LLM provider")
    LLM_API_KEY: str = Field(default="", description="LLM API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    LLM_MAX_TOKENS: int = Field(default=1000, description="Max LLM response tokens")
    LLM_TEMPERATURE: float = Field(default=0.1, description="LLM temperature")
    
    # Risk Parameters
    DEFAULT_VAR_ALPHA: float = Field(default=0.99, description="Default VaR alpha")
    DEFAULT_VAR_LOOKBACK: int = Field(
        default=250, description="Default VaR lookback days"
    )
    VAR_ALERT_THRESHOLD: float = Field(
        default=1000000.0, description="VaR alert threshold"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()