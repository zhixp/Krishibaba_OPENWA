"""
Configuration Management
Uses Pydantic Settings for type-safe environment variable loading
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    GEMINI_API_KEY: str
    OPENWEATHER_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""  # Hybrid geocoding: Primary (accurate), Nominatim is fallback
    
    # Admin
    ADMIN_API_KEY: str = "changeme_in_production"
    BROADCAST_ADMIN_KEY: str = "sarpanch_secret"  # Default, override in .env
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./krishi_baba.db"
    
    # CORS - Allow all localhost for development
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for development
    
    # App Settings
    DEBUG: bool = False
    TEST_MODE: bool = False  # Set to True for local pilot/testing flows
    MAX_AUDIO_SIZE_MB: int = 5
    AUDIO_UPLOAD_PATH: str = "./uploads/audio"
    
    # Prompts Configuration
    PROMPTS_PATH: str = "./app/core/prompts.yaml"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.AUDIO_UPLOAD_PATH, exist_ok=True)
