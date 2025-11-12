# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "WhatsApp Secretary"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    
    # Database
    DATABASE_PATH: str = "data/whatsapp_secretary.db"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self.DATABASE_PATH}"
    
    # WhatsApp
    WHATSAPP_SESSION_PATH: str = "data/whatsapp-session"
    WHATSAPP_NODE_SCRIPT_PATH: str = "whatsapp_client/whatsapp_client.js"
    MEDIA_DOWNLOAD_PATH: str = "data/media"
    
    # LLM Settings
    # Ollama (Llama 4)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # Update when Llama 4 is available
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # OpenAI (optional fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    
    # Business settings
    BUSINESS_NAME: str = "Your Business"
    BUSINESS_HOURS_START: str = "09:00"
    BUSINESS_HOURS_END: str = "17:00"
    DEFAULT_APPOINTMENT_DURATION: int = 60  # minutes
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()

# Create data directories
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
os.makedirs(settings.WHATSAPP_SESSION_PATH, exist_ok=True)
os.makedirs(settings.MEDIA_DOWNLOAD_PATH, exist_ok=True)
os.makedirs(os.path.dirname(settings.WHATSAPP_NODE_SCRIPT_PATH), exist_ok=True)
