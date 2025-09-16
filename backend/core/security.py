# backend/app/core/security.py
from cryptography.fernet import Fernet
from core.config import settings
import base64
import hashlib

def get_encryption_key() -> bytes:
    """Generate encryption key from secret key"""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    if not api_key:
        return None

    f = Fernet(get_encryption_key())
    encrypted_key = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted_key).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key from storage"""
    if not encrypted_key:
        return None

    try:
        f = Fernet(get_encryption_key())
        decoded_key = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted_key = f.decrypt(decoded_key)
        return decrypted_key.decode()
    except Exception:
        return None