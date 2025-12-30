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
    DATABASE_URL: str = "sqlite:///data/whatsapp_secretary.db"  # Override via environment variable
    
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
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # OpenAI (optional fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"

    # Authorization
    BOSS_PHONE_NUMBER: Optional[str] = None
    BOSS_CONTACT_NAME: Optional[str] = None
    AUTHORIZATION_PASSWORD: Optional[str] = None
    UNAUTHORIZED_MESSAGE: str = "Sorry, Mr Hung is not available at this moment, if you like leave any message or make an appointments, please let me know. We will arrange with you asap"

    # Business settings
    BUSINESS_NAME: str = "Your Business"
    BUSINESS_HOURS_START: str = "09:00"
    BUSINESS_HOURS_END: str = "17:00"
    DEFAULT_APPOINTMENT_DURATION: int = 60  # minutes

    # Conversation Manager Settings
    # Archive settings
    ARCHIVE_ENABLED: bool = True
    AUTO_ARCHIVE_AFTER_DAYS: int = 90
    ARCHIVE_INACTIVE_AFTER_DAYS: int = 60
    COMPRESS_ARCHIVES: bool = True
    ARCHIVE_RETENTION_DAYS: int = 365
    ARCHIVE_STORAGE_PATH: str = "data/archives"

    # Sync settings
    SYNC_ENABLED: bool = True
    AUTO_SYNC_INTERVAL_MINUTES: int = 30
    FULL_SYNC_INTERVAL_HOURS: int = 24
    RETRY_FAILED_SYNCS: bool = True
    MAX_SYNC_RETRIES: int = 3

    # Cleanup settings
    CLEANUP_ENABLED: bool = True
    CLEANUP_RUN_TIME: str = "02:00"  # Daily at 2 AM
    OPTIMIZE_TABLES: bool = True
    REMOVE_ORPHANS: bool = True
    COMPRESS_OLD_MESSAGES: bool = True
    COMPRESS_AFTER_DAYS: int = 30

    # Metadata settings
    AUTO_SENTIMENT_ANALYSIS: bool = True
    AUTO_CATEGORIZATION: bool = True
    AUTO_TAGGING: bool = True
    GENERATE_CHAT_SUMMARIES: bool = True
    UPDATE_METADATA_ON_RECEIVE: bool = False

    # Status update settings
    AUTO_MARK_READ: bool = False
    MARK_PROCESSED_AFTER_RESPONSE: bool = True

    model_config = {
        "env_file": "../.env",  # .env file is in parent directory
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()

# Create data directories
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
os.makedirs(settings.WHATSAPP_SESSION_PATH, exist_ok=True)
os.makedirs(settings.MEDIA_DOWNLOAD_PATH, exist_ok=True)
os.makedirs(os.path.dirname(settings.WHATSAPP_NODE_SCRIPT_PATH), exist_ok=True)
os.makedirs(settings.ARCHIVE_STORAGE_PATH, exist_ok=True)
