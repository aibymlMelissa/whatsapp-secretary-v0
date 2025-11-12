# backend/services/authorization_service.py
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from database.database import SessionLocal
from database.models import PendingAuthorization, SystemConfig, Chat


class AuthorizationService:
    """
    Service to handle two-factor authentication for sensitive LLM operations

    Workflow:
    1. LLM detects request for sensitive data (DB, files, appointments)
    2. System creates pending authorization request
    3. System sends WhatsApp message to BOSS phone number
    4. BOSS replies with auth code (e.g., "AIbyML.com")
    5. System validates code and executes the original request
    6. Response is sent back to the requester
    """

    def __init__(self, whatsapp_service=None):
        self.whatsapp_service = whatsapp_service

    def get_boss_phone_number(self) -> Optional[str]:
        """Get the BOSS phone number from system config"""
        db = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == "BOSS_PHONE_NUMBER").first()
            if config and config.value:
                return config.value.strip()
            return None
        finally:
            db.close()

    def get_auth_code_phrase(self) -> str:
        """Get the authorization code phrase from system config"""
        db = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_CODE_PHRASE").first()
            if config and config.value:
                return config.value.strip()
            return "AIbyML.com"  # Default
        finally:
            db.close()

    def get_auth_timeout_minutes(self) -> int:
        """Get the authorization timeout in minutes"""
        db = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == "AUTH_TIMEOUT_MINUTES").first()
            if config and config.value:
                try:
                    return int(config.value)
                except ValueError:
                    pass
            return 5  # Default 5 minutes
        finally:
            db.close()

    async def request_authorization(
        self,
        chat_id: str,
        requester_phone: str,
        action_type: str,
        action_description: str,
        requested_data: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Create an authorization request and send it to BOSS

        Args:
            chat_id: Chat ID of the requester
            requester_phone: Phone number of the requester
            action_type: Type of action (e.g., 'database_query', 'file_access')
            action_description: Human-readable description
            requested_data: Additional data about the request

        Returns:
            request_id if successful, None otherwise
        """
        boss_phone = self.get_boss_phone_number()
        if not boss_phone:
            print("❌ BOSS phone number not configured")
            return None

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        auth_code = self.get_auth_code_phrase()
        timeout_minutes = self.get_auth_timeout_minutes()
        expires_at = datetime.now() + timedelta(minutes=timeout_minutes)

        db = SessionLocal()
        try:
            # Create pending authorization
            auth_request = PendingAuthorization(
                request_id=request_id,
                chat_id=chat_id,
                requester_phone=requester_phone,
                action_type=action_type,
                action_description=action_description,
                requested_data=json.dumps(requested_data) if requested_data else None,
                auth_code=auth_code,
                expires_at=expires_at,
                status="pending"
            )
            db.add(auth_request)
            db.commit()

            print(f"🔐 Created authorization request: {request_id}")

            # Send WhatsApp message to BOSS
            if self.whatsapp_service:
                boss_chat_id = f"{boss_phone}@c.us"
                message = (
                    f"🔐 *AUTHORIZATION REQUIRED*\n\n"
                    f"📱 From: {requester_phone}\n"
                    f"🎯 Action: {action_type}\n"
                    f"📝 Request: {action_description}\n\n"
                    f"⏰ Expires in {timeout_minutes} minutes\n\n"
                    f"To approve, reply with:\n*{auth_code}*\n\n"
                    f"Request ID: `{request_id[:8]}...`"
                )

                await self.whatsapp_service.send_message(boss_chat_id, message)
                print(f"✅ Authorization request sent to BOSS: {boss_phone}")

            return request_id

        except Exception as e:
            print(f"❌ Error creating authorization request: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    async def check_authorization_response(self, message: str, sender_phone: str) -> bool:
        """
        Check if a message is an authorization response from BOSS

        Args:
            message: The message content
            sender_phone: Phone number of the sender

        Returns:
            True if authorization was processed, False otherwise
        """
        boss_phone = self.get_boss_phone_number()
        if not boss_phone:
            return False

        # Check if sender is BOSS
        if sender_phone != boss_phone:
            return False

        # Check if message matches auth code
        auth_code = self.get_auth_code_phrase()
        if message.strip().lower() != auth_code.lower():
            return False

        # Find pending authorization
        db = SessionLocal()
        try:
            # Find the most recent pending authorization
            pending_auth = db.query(PendingAuthorization).filter(
                PendingAuthorization.status == "pending",
                PendingAuthorization.expires_at > datetime.now()
            ).order_by(PendingAuthorization.created_at.desc()).first()

            if not pending_auth:
                print("ℹ️ No pending authorization found")
                return False

            # Approve the authorization
            pending_auth.status = "approved"
            pending_auth.approved_by = sender_phone
            pending_auth.approved_at = datetime.now()
            db.commit()

            print(f"✅ Authorization approved by BOSS for request: {pending_auth.request_id}")

            # Send confirmation to BOSS
            if self.whatsapp_service:
                boss_chat_id = f"{boss_phone}@c.us"
                confirmation = (
                    f"✅ *AUTHORIZATION APPROVED*\n\n"
                    f"Request ID: `{pending_auth.request_id[:8]}...`\n"
                    f"Action: {pending_auth.action_type}\n"
                    f"Requester: {pending_auth.requester_phone}\n\n"
                    f"The request will now be processed."
                )
                await self.whatsapp_service.send_message(boss_chat_id, confirmation)

            # Execute the authorized action (this will be handled by the calling service)
            await self.execute_authorized_action(pending_auth)

            return True

        except Exception as e:
            print(f"❌ Error processing authorization response: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def execute_authorized_action(self, auth_request: PendingAuthorization):
        """Execute the action that was authorized"""
        # This will be called by specific services (LLM, appointment, etc.)
        # They will check for approved authorizations and execute accordingly
        print(f"🎯 Executing authorized action: {auth_request.action_type}")

        # The actual execution is handled by the service that created the request
        # This is just a placeholder that can be extended

    def is_action_authorized(self, request_id: str) -> bool:
        """Check if a specific request has been authorized"""
        db = SessionLocal()
        try:
            auth = db.query(PendingAuthorization).filter(
                PendingAuthorization.request_id == request_id,
                PendingAuthorization.status == "approved"
            ).first()
            return auth is not None
        finally:
            db.close()

    def cleanup_expired_authorizations(self):
        """Clean up expired authorization requests"""
        db = SessionLocal()
        try:
            expired_count = db.query(PendingAuthorization).filter(
                PendingAuthorization.status == "pending",
                PendingAuthorization.expires_at < datetime.now()
            ).update({"status": "expired"})

            db.commit()
            if expired_count > 0:
                print(f"🧹 Cleaned up {expired_count} expired authorization requests")
        except Exception as e:
            print(f"❌ Error cleaning up expired authorizations: {e}")
            db.rollback()
        finally:
            db.close()
