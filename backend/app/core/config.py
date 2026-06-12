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
    GEMINI_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""  # Hybrid geocoding: Primary (accurate), Nominatim is fallback
    
    # Admin / channel secrets. Keep empty by default so protected routes fail closed.
    ADMIN_API_KEY: str = ""
    BROADCAST_ADMIN_KEY: str = ""
    CHANNEL_GATEWAY_SECRET: str = ""
    PHONE_HASH_SALT: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./krishi_baba.db"
    
    # CORS origins as a comma-separated string. Use "*" only for local throwaway dev.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080"
    
    # App Settings
    DEBUG: bool = False
    TEST_MODE: bool = False  # Set to True for local pilot/testing flows
    MAX_AUDIO_SIZE_MB: int = 5
    MAX_IMAGE_SIZE_MB: int = 5
    AUDIO_UPLOAD_PATH: str = "./uploads/audio"
    
    # Prompts Configuration
    PROMPTS_PATH: str = "./app/core/prompts.yaml"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def cors_origins(self) -> List[str]:
        """Return normalized CORS origins from a comma-separated env value."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if not origins:
            return []

        if "*" in origins and not self.DEBUG:
            return []

        return origins


# Create global settings instance
settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.AUDIO_UPLOAD_PATH, exist_ok=True)
