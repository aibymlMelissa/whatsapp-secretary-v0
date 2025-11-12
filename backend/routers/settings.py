# backend/app/routers/settings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database.database import get_db
from database.models import User, UserLLMSetting, LLMProvider, SystemConfig
from core.security import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Security Settings Models
class SecuritySettingsRequest(BaseModel):
    boss_phone_number: Optional[str] = None
    auth_code_phrase: Optional[str] = None
    auth_timeout_minutes: Optional[int] = None

class SecuritySettingsResponse(BaseModel):
    boss_phone_number: Optional[str] = None
    auth_code_phrase: str
    auth_timeout_minutes: int
    has_boss_configured: bool

# Pydantic models for API
class LLMSettingsRequest(BaseModel):
    preferred_provider: str
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    max_tokens: int = 500
    temperature: float = 0.7
    use_system_default: bool = False

class LLMSettingsResponse(BaseModel):
    preferred_provider: str
    openai_model: str
    anthropic_model: str
    gemini_model: str
    ollama_base_url: str
    ollama_model: str
    max_tokens: int
    temperature: float
    use_system_default: bool
    has_openai_key: bool
    has_anthropic_key: bool
    has_gemini_key: bool

class TestConnectionRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    response_time_ms: Optional[int] = None

def get_or_create_user(phone_number: str, db: Session) -> User:
    """Get or create user by phone number"""
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        user = User(phone_number=phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_or_create_llm_settings(user_id: int, db: Session) -> UserLLMSetting:
    """Get or create LLM settings for user"""
    settings = db.query(UserLLMSetting).filter(UserLLMSetting.user_id == user_id).first()
    if not settings:
        settings = UserLLMSetting(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Get user's LLM settings"""
    try:
        user = get_or_create_user(phone_number, db)
        settings = get_or_create_llm_settings(user.id, db)

        return LLMSettingsResponse(
            preferred_provider=settings.preferred_provider.value,
            openai_model=settings.openai_model,
            anthropic_model=settings.anthropic_model,
            gemini_model=settings.gemini_model,
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            use_system_default=settings.use_system_default,
            has_openai_key=bool(settings.openai_api_key),
            has_anthropic_key=bool(settings.anthropic_api_key),
            has_gemini_key=bool(settings.gemini_api_key)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM settings: {str(e)}"
        )

@router.post("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(
    phone_number: str,
    request: LLMSettingsRequest,
    db: Session = Depends(get_db)
):
    """Update user's LLM settings"""
    try:
        user = get_or_create_user(phone_number, db)
        settings = get_or_create_llm_settings(user.id, db)

        # Update settings
        settings.preferred_provider = LLMProvider(request.preferred_provider)
        settings.openai_model = request.openai_model
        settings.anthropic_model = request.anthropic_model
        settings.gemini_model = request.gemini_model
        settings.ollama_base_url = request.ollama_base_url
        settings.ollama_model = request.ollama_model
        settings.max_tokens = request.max_tokens
        settings.temperature = request.temperature
        settings.use_system_default = request.use_system_default

        # Encrypt and store API keys if provided
        if request.openai_api_key:
            settings.openai_api_key = encrypt_api_key(request.openai_api_key)
        if request.anthropic_api_key:
            settings.anthropic_api_key = encrypt_api_key(request.anthropic_api_key)
        if request.gemini_api_key:
            settings.gemini_api_key = encrypt_api_key(request.gemini_api_key)

        db.commit()
        db.refresh(settings)

        return LLMSettingsResponse(
            preferred_provider=settings.preferred_provider.value,
            openai_model=settings.openai_model,
            anthropic_model=settings.anthropic_model,
            gemini_model=settings.gemini_model,
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            use_system_default=settings.use_system_default,
            has_openai_key=bool(settings.openai_api_key),
            has_anthropic_key=bool(settings.anthropic_api_key),
            has_gemini_key=bool(settings.gemini_api_key)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update LLM settings: {str(e)}"
        )

@router.post("/llm/test", response_model=TestConnectionResponse)
async def test_llm_connection(
    request: TestConnectionRequest
):
    """Test LLM provider connection"""
    import time
    import httpx

    start_time = time.time()

    try:
        if request.provider == "openai":
            # Test OpenAI connection
            if not request.api_key:
                return TestConnectionResponse(
                    success=False,
                    message="OpenAI API key is required"
                )

            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {request.api_key}"}
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    response_time = int((time.time() - start_time) * 1000)
                    return TestConnectionResponse(
                        success=True,
                        message="OpenAI connection successful",
                        response_time_ms=response_time
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"OpenAI API error: {response.status_code}"
                    )

        elif request.provider == "anthropic":
            # Test Anthropic connection
            if not request.api_key:
                return TestConnectionResponse(
                    success=False,
                    message="Anthropic API key is required"
                )

            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {request.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": request.model or "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                }

                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    response_time = int((time.time() - start_time) * 1000)
                    return TestConnectionResponse(
                        success=True,
                        message="Anthropic connection successful",
                        response_time_ms=response_time
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Anthropic API error: {response.status_code}"
                    )

        elif request.provider == "gemini":
            # Test Gemini connection
            if not request.api_key:
                return TestConnectionResponse(
                    success=False,
                    message="Gemini API key is required"
                )

            import google.generativeai as genai
            genai.configure(api_key=request.api_key)

            model = genai.GenerativeModel(request.model or "gemini-1.5-flash")
            response = model.generate_content("Hi")

            if response.text:
                response_time = int((time.time() - start_time) * 1000)
                return TestConnectionResponse(
                    success=True,
                    message="Gemini connection successful",
                    response_time_ms=response_time
                )
            else:
                return TestConnectionResponse(
                    success=False,
                    message="Gemini API test failed"
                )

        elif request.provider == "ollama":
            # Test Ollama connection
            base_url = request.base_url or "http://localhost:11434"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/api/tags",
                    timeout=5.0
                )

                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_name = request.model or "llama3.2"

                    if any(model.get("name", "").startswith(model_name) for model in models):
                        response_time = int((time.time() - start_time) * 1000)
                        return TestConnectionResponse(
                            success=True,
                            message=f"Ollama connection successful, {model_name} available",
                            response_time_ms=response_time
                        )
                    else:
                        return TestConnectionResponse(
                            success=False,
                            message=f"Ollama connected but {model_name} model not found"
                        )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Ollama connection failed: {response.status_code}"
                    )

        else:
            return TestConnectionResponse(
                success=False,
                message=f"Unsupported provider: {request.provider}"
            )

    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"Connection test failed: {str(e)}"
        )

@router.delete("/llm/api-key/{provider}")
async def remove_api_key(
    provider: str,
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Remove API key for a specific provider"""
    try:
        user = get_or_create_user(phone_number, db)
        settings = get_or_create_llm_settings(user.id, db)

        if provider == "openai":
            settings.openai_api_key = None
        elif provider == "anthropic":
            settings.anthropic_api_key = None
        elif provider == "gemini":
            settings.gemini_api_key = None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: {provider}"
            )

        db.commit()

        return {"message": f"API key for {provider} removed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove API key: {str(e)}"
        )

# Security Settings Endpoints

@router.get("/security", response_model=SecuritySettingsResponse)
async def get_security_settings(db: Session = Depends(get_db)):
    """Get security settings (BOSS phone number, auth code, etc.)"""
    try:
        boss_phone = db.query(SystemConfig).filter(SystemConfig.key == "BOSS_PHONE_NUMBER").first()
        auth_code = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_CODE_PHRASE").first()
        auth_timeout = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_TIMEOUT_MINUTES").first()

        return SecuritySettingsResponse(
            boss_phone_number=boss_phone.value if boss_phone else None,
            auth_code_phrase=auth_code.value if auth_code else "AIbyML.com",
            auth_timeout_minutes=int(auth_timeout.value) if auth_timeout else 5,
            has_boss_configured=bool(boss_phone and boss_phone.value)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security settings: {str(e)}"
        )

@router.post("/security", response_model=SecuritySettingsResponse)
async def update_security_settings(
    request: SecuritySettingsRequest,
    db: Session = Depends(get_db)
):
    """Update security settings"""
    try:
        # Update BOSS phone number
        if request.boss_phone_number is not None:
            boss_phone = db.query(SystemConfig).filter(SystemConfig.key == "BOSS_PHONE_NUMBER").first()
            if boss_phone:
                boss_phone.value = request.boss_phone_number
            else:
                boss_phone = SystemConfig(
                    key="BOSS_PHONE_NUMBER",
                    value=request.boss_phone_number,
                    description="Phone number of the BOSS who authorizes sensitive operations"
                )
                db.add(boss_phone)

        # Update auth code phrase
        if request.auth_code_phrase is not None:
            auth_code = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_CODE_PHRASE").first()
            if auth_code:
                auth_code.value = request.auth_code_phrase
            else:
                auth_code = SystemConfig(
                    key="AUTH_CODE_PHRASE",
                    value=request.auth_code_phrase,
                    description="Secret phrase BOSS must send to authorize requests"
                )
                db.add(auth_code)

        # Update auth timeout
        if request.auth_timeout_minutes is not None:
            auth_timeout = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_TIMEOUT_MINUTES").first()
            if auth_timeout:
                auth_timeout.value = str(request.auth_timeout_minutes)
            else:
                auth_timeout = SystemConfig(
                    key="AUTH_TIMEOUT_MINUTES",
                    value=str(request.auth_timeout_minutes),
                    description="Minutes before authorization request expires"
                )
                db.add(auth_timeout)

        db.commit()

        # Fetch and return updated settings
        boss_phone = db.query(SystemConfig).filter(SystemConfig.key == "BOSS_PHONE_NUMBER").first()
        auth_code = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_CODE_PHRASE").first()
        auth_timeout = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_TIMEOUT_MINUTES").first()

        return SecuritySettingsResponse(
            boss_phone_number=boss_phone.value if boss_phone else None,
            auth_code_phrase=auth_code.value if auth_code else "AIbyML.com",
            auth_timeout_minutes=int(auth_timeout.value) if auth_timeout else 5,
            has_boss_configured=bool(boss_phone and boss_phone.value)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update security settings: {str(e)}"
        )