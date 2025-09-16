# backend/app/services/user_service.py
from sqlalchemy.orm import Session
from typing import Optional

from database.models import User, UserLLMSetting, LLMProvider
from database.database import get_db
from core.security import decrypt_api_key


class UserService:
    """Service for managing user settings and preferences"""

    @staticmethod
    def get_user_by_phone(phone_number: str, db: Session) -> Optional[User]:
        """Get user by phone number"""
        return db.query(User).filter(User.phone_number == phone_number).first()

    @staticmethod
    def get_or_create_user(phone_number: str, db: Session) -> User:
        """Get or create user by phone number"""
        user = UserService.get_user_by_phone(phone_number, db)
        if not user:
            user = User(phone_number=phone_number)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_user_llm_settings(phone_number: str, db: Session) -> Optional[UserLLMSetting]:
        """Get user's LLM settings"""
        user = UserService.get_user_by_phone(phone_number, db)
        if not user:
            return None

        settings = db.query(UserLLMSetting).filter(UserLLMSetting.user_id == user.id).first()
        return settings

    @staticmethod
    def get_user_llm_config(phone_number: str, db: Session) -> Optional[dict]:
        """Get decrypted LLM configuration for a user"""
        settings = UserService.get_user_llm_settings(phone_number, db)

        if not settings or settings.use_system_default:
            return None

        config = {
            'preferred_provider': settings.preferred_provider.value,
            'max_tokens': settings.max_tokens,
            'temperature': settings.temperature,
        }

        # Decrypt API keys and add provider-specific configs
        if settings.preferred_provider == LLMProvider.OPENAI and settings.openai_api_key:
            config.update({
                'openai_api_key': decrypt_api_key(settings.openai_api_key),
                'openai_model': settings.openai_model,
            })
        elif settings.preferred_provider == LLMProvider.ANTHROPIC and settings.anthropic_api_key:
            config.update({
                'anthropic_api_key': decrypt_api_key(settings.anthropic_api_key),
                'anthropic_model': settings.anthropic_model,
            })
        elif settings.preferred_provider == LLMProvider.GEMINI and settings.gemini_api_key:
            config.update({
                'gemini_api_key': decrypt_api_key(settings.gemini_api_key),
                'gemini_model': settings.gemini_model,
            })
        elif settings.preferred_provider == LLMProvider.OLLAMA:
            config.update({
                'ollama_base_url': settings.ollama_base_url,
                'ollama_model': settings.ollama_model,
            })

        return config