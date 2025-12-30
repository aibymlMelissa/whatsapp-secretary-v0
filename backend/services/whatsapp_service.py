# backend/app/services/whatsapp_service.py
import asyncio
import json
import subprocess
import os
import signal
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
from pathlib import Path

from core.config import settings
from database.models import Chat, Message, MessageType
from database.database import get_db
from services.llm_service import LLMService
from services.authorization_service import AuthorizationService

class WhatsAppService:
    """
    WhatsApp service that manages a Node.js subprocess running whatsapp-web.js with file-based communication

    Architecture Overview:
    - Uses simple_bridge.js for reliable Node.js ↔ Python communication
    - File-based IPC: status.json for state, qr_code.txt for QR codes
    - Polling-based monitoring instead of stdin/stdout pipes
    - QR-code only authentication (pairing codes removed for simplicity)
    - Real-time status updates via WebSocket to frontend
    """

    def __init__(self, connection_manager=None):
        self.process: Optional[subprocess.Popen] = None
        self.is_connected = False
        self.is_connecting = False
        self.qr_code = None
        self.session_path = settings.WHATSAPP_SESSION_PATH
        self.node_script_path = settings.WHATSAPP_NODE_SCRIPT_PATH
        self.llm_service = None  # Will be injected
        self.connection_manager = connection_manager  # WebSocket manager
        self.auth_service = AuthorizationService(whatsapp_service=self)  # Authorization service

        # File-based communication paths
        self.whatsapp_client_dir = Path(__file__).parent.parent / "whatsapp_client"
        self.qr_file = self.whatsapp_client_dir / "qr_code.txt"
        self.status_file = self.whatsapp_client_dir / "status.json"
        self.bridge_script = self.whatsapp_client_dir / "simple_bridge.js"

        # WhatsApp bridge port (configurable via env var)
        self.bridge_port = os.getenv('WHATSAPP_BRIDGE_PORT', os.getenv('BRIDGE_PORT', '8002'))

        # Ensure directories exist
        Path(self.session_path).mkdir(parents=True, exist_ok=True)
        Path(settings.MEDIA_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
        self.whatsapp_client_dir.mkdir(parents=True, exist_ok=True)
    
    def set_llm_service(self, llm_service: LLMService):
        """Set LLM service reference"""
        self.llm_service = llm_service
    
    async def initialize(self) -> bool:
        """Initialize WhatsApp service using file-based communication"""
        if self.process and self.process.poll() is None:
            print("WhatsApp process already running")
            return True

        try:
            print("🚀 Starting WhatsApp Node.js bridge process...")
            bridge_script = self.whatsapp_client_dir / "simple_bridge.js"

            if not bridge_script.exists():
                print(f"❌ Bridge script not found at {bridge_script}")
                return False

            self.is_connecting = True

            # Broadcast connecting status
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connecting": True, "connected": False}
                })

            # Start Node.js bridge process with environment variables
            # Use the same port as the API server for callbacks
            api_port = os.getenv('PORT', os.getenv('API_PORT', '8001'))
            # WhatsApp bridge port (separate from API port for local communication)
            bridge_port = os.getenv('WHATSAPP_BRIDGE_PORT', os.getenv('BRIDGE_PORT', '8002'))
            # Use 127.0.0.1 instead of localhost to avoid IPv6 resolution issues
            callback_url = f"http://127.0.0.1:{api_port}/api/whatsapp/callback"

            # Pass environment variables to the Node.js process
            env = os.environ.copy()
            env['PYTHON_CALLBACK_URL'] = callback_url
            env['WHATSAPP_BRIDGE_PORT'] = bridge_port

            print(f"🔗 Setting callback URL: {callback_url}")
            print(f"🔗 WhatsApp bridge will listen on port: {bridge_port}")

            self.process = subprocess.Popen(
                ['node', str(bridge_script)],
                cwd=str(self.whatsapp_client_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            print(f"✅ WhatsApp bridge process started with PID: {self.process.pid}")

            # Start monitoring the process and files
            asyncio.create_task(self.monitor_file_based_process())

            return True

        except Exception as e:
            print(f"❌ Failed to start WhatsApp process: {e}")
            self.is_connecting = False
            return False
    
    async def create_node_script(self):
        """Create the Node.js WhatsApp integration script - Skip if it already exists"""
        # Check if our updated script already exists
        if os.path.exists(self.node_script_path):
            print(f"✅ WhatsApp client script already exists at {self.node_script_path}")
            return

        print(f"⚠️ WhatsApp client script not found at {self.node_script_path}")
        print("Please ensure the whatsapp_client.js exists in the whatsapp_client directory")
    
    async def monitor_file_based_process(self):
        """Monitor the Node.js process using file-based communication"""
        if not self.process:
            return

        try:
            last_status = None
            last_qr_check = 0
            check_interval = 1.0  # Check every second

            while self.process.poll() is None:
                current_time = asyncio.get_event_loop().time()

                # Read status from file
                node_status = await self.read_status_file()

                # Check if status changed
                if node_status != last_status:
                    print(f"📊 Status update: {node_status}")

                    # Update our internal state
                    self.is_connected = node_status.get("connected", False)
                    self.is_connecting = node_status.get("connecting", False)

                    # Broadcast status changes
                    if self.connection_manager:
                        await self.connection_manager.broadcast({
                            "type": "whatsapp_status",
                            "data": {
                                "connected": self.is_connected,
                                "connecting": self.is_connecting,
                                "ready": node_status.get("ready", False)
                            }
                        })

                    # Handle ready state
                    if node_status.get("ready") and not last_status.get("ready", False) if last_status else True:
                        print("✅ WhatsApp connected and ready")

                    last_status = node_status.copy()

                # Check for QR code periodically
                if current_time - last_qr_check > 2.0:  # Check QR every 2 seconds
                    await self.check_qr_file()
                    last_qr_check = current_time

                # Read any process output
                if self.process.stdout:
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            print(f"WhatsApp: {line.strip()}")
                    except:
                        pass

                await asyncio.sleep(check_interval)

        except Exception as e:
            print(f"Error monitoring WhatsApp process: {e}")

        # Process ended
        if self.process:
            exit_code = self.process.poll()
            if exit_code != 0:
                try:
                    stderr_output = self.process.stderr.read() if self.process.stderr else ""
                    print(f"❌ WhatsApp process ended with exit code {exit_code}")
                    if stderr_output:
                        print(f"❌ Error output: {stderr_output}")
                except:
                    pass
            else:
                print("WhatsApp process ended normally")

        self.is_connected = False
        self.is_connecting = False

        # Broadcast status update
        if self.connection_manager:
            await self.connection_manager.broadcast({
                "type": "whatsapp_status",
                "data": {"connected": False, "connecting": False, "error": "Process ended"}
            })
    
    async def send_command(self, action: str, data: dict = None) -> dict:
        """Send command to Node.js process (simplified for file-based communication)"""
        if not self.process or self.process.poll() is not None:
            raise Exception("WhatsApp process not running")

        # For the file-based bridge, most commands are handled automatically
        # This method is kept for compatibility but simplified
        command_id = f"{action}_{datetime.now().timestamp()}"
        print(f"📤 Command sent: {action} (ID: {command_id})")

        return {"success": True, "command_id": command_id}
    
    async def send_message(self, chat_id: str, message: str, media_path: str = None) -> dict:
        """Send message via WhatsApp"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://127.0.0.1:{self.bridge_port}/send",
                    json={"chatId": chat_id, "message": message},
                    timeout=10.0
                )

                if response.status_code == 200:
                    print(f"✅ Message sent to {chat_id}: {message[:50]}...")
                    return {"success": True, "data": response.json()}
                else:
                    print(f"❌ Failed to send message: {response.status_code}")
                    return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_chats(self) -> List[dict]:
        """Get all chats"""
        result = await self.send_command("get_chats")
        # In real implementation, parse the response
        return []
    
    async def get_chat_messages(self, chat_id: str, limit: int = 50) -> List[dict]:
        """Get messages from a specific chat"""
        result = await self.send_command("get_chat_messages", {
            "chatId": chat_id,
            "limit": limit
        })
        return []

    async def request_pairing_code(self, phone_number: str) -> dict:
        """Request a pairing code for phone number authentication"""
        try:
            # Ensure WhatsApp service is initialized
            if not self.process or self.process.poll() is not None:
                print("⚠️ WhatsApp process not running, initializing...")
                success = await self.initialize()
                if not success:
                    raise Exception("Failed to initialize WhatsApp service")

                # Wait longer for the process to be ready and check status
                print("⏳ Waiting for WhatsApp client to initialize...")
                max_wait_time = 15  # 15 seconds
                wait_time = 0
                while wait_time < max_wait_time:
                    await asyncio.sleep(1)
                    wait_time += 1

                    # Check if process is still running
                    if not self.process or self.process.poll() is not None:
                        raise Exception("WhatsApp process ended during initialization")

                    # Check if we have any initialization feedback
                    if wait_time >= 3:  # After 3 seconds, we should have some output
                        print(f"⏳ Still waiting... ({wait_time}/{max_wait_time}s)")

            # Double-check process is running before sending command
            if not self.process or self.process.poll() is not None:
                raise Exception("WhatsApp process not running")

            self.pairing_phone_number = phone_number
            result = await self.send_command("request_pairing_code", {
                "phoneNumber": phone_number
            })

            print(f"📱 Pairing code requested for {phone_number}")
            return result

        except Exception as e:
            print(f"❌ Error requesting pairing code: {e}")
            raise Exception(f"Failed to request pairing code: {str(e)}")

    async def get_pairing_code(self) -> dict:
        """Get current pairing code"""
        return {
            "pairing_code": self.pairing_code,
            "phone_number": self.pairing_phone_number,
            "has_code": self.pairing_code is not None
        }

    async def handle_callback(self, event: str, data: dict):
        """Handle callbacks from Node.js process"""
        print(f"WhatsApp callback: {event}")

        if event == "qr_code":
            self.qr_code = data.get("qr")
            # Broadcast QR code to connected clients
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "qr_code",
                    "data": {"qr": self.qr_code}
                })

        elif event == "ready":
            self.is_connected = True
            self.is_connecting = False
            print("✅ WhatsApp connected and ready")

            # Fetch chats from WhatsApp to populate the database
            print("📥 Fetching chats from WhatsApp...")
            asyncio.create_task(self.fetch_chats_from_whatsapp())

            # Broadcast status update
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connected": True, "connecting": False}
                })

        elif event == "authenticated":
            print("✅ WhatsApp authenticated")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"authenticated": True}
                })

        elif event == "auth_failure":
            self.is_connecting = False
            print(f"❌ WhatsApp authentication failed: {data.get('message')}")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connected": False, "connecting": False, "error": data.get('message')}
                })

        elif event == "disconnected":
            self.is_connected = False
            self.is_connecting = False
            print(f"📱 WhatsApp disconnected: {data.get('reason')}")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connected": False, "connecting": False, "disconnected_reason": data.get('reason')}
                })

        elif event == "pairing_code":
            self.pairing_code = data.get("code")
            self.pairing_phone_number = data.get("phoneNumber")
            print(f"📱 WhatsApp pairing code received: {self.pairing_code}")
            # Broadcast pairing code to connected clients
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "pairing_code",
                    "data": {
                        "code": self.pairing_code,
                        "phoneNumber": self.pairing_phone_number
                    }
                })

        elif event == "chats_loaded":
            # Handle chats loaded from WhatsApp
            await self.process_chats_loaded(data)

        elif event == "new_message":
            await self.process_new_message(data)
            # Broadcast new message with enhanced data
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "new_message",
                    "data": {
                        "chatId": data.get("chatId"),
                        "messageId": data.get("id"),
                        "body": data.get("body"),
                        "fromMe": data.get("fromMe", False),
                        "timestamp": data.get("timestamp"),
                        "hasMedia": data.get("hasMedia", False),
                        "isGroup": data.get("isGroup", False)
                    }
                })

        elif event == "message_sent":
            print(f"✅ Message sent to {data.get('chatId')}")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "message_sent",
                    "data": {
                        "chatId": data.get("chatId"),
                        "messageId": data.get("id"),
                        "message": data.get("body"),
                        "timestamp": data.get("timestamp")
                    }
                })

    async def process_chats_loaded(self, data: dict):
        """Process chats loaded from WhatsApp and save to database"""
        try:
            chats = data.get("chats", [])
            print(f"📥 Processing {len(chats)} chats from WhatsApp...")

            from database.database import SessionLocal
            from database.models import Chat

            db = SessionLocal()
            try:
                saved_count = 0
                for chat_data in chats:
                    chat_id = chat_data.get("id")
                    if not chat_id:
                        continue

                    # Check if chat already exists
                    existing_chat = db.query(Chat).filter(Chat.id == chat_id).first()

                    if existing_chat:
                        # Update existing chat
                        existing_chat.name = chat_data.get("name", "Unknown")
                        existing_chat.is_group = chat_data.get("isGroup", False)
                        existing_chat.updated_at = datetime.now()
                    else:
                        # Create new chat
                        # Extract phone number from chat ID
                        phone_number = chat_id.replace("@c.us", "").replace("@g.us", "")

                        new_chat = Chat(
                            id=chat_id,
                            name=chat_data.get("name", "Unknown"),
                            phone_number=phone_number,
                            is_group=chat_data.get("isGroup", False),
                            is_active=True,
                            ai_enabled=True,  # Auto-enable AI for new chats
                            is_whitelisted=False
                        )
                        db.add(new_chat)
                        saved_count += 1

                db.commit()
                print(f"✅ Saved/updated {saved_count} new chats to database")

                # Broadcast chats_updated event to connected clients
                if self.connection_manager:
                    await self.connection_manager.broadcast({
                        "type": "chats_updated",
                        "data": {"count": len(chats)}
                    })

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error processing chats: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")

    async def process_new_message(self, message_data: dict):
        """Process new incoming message"""
        try:
            print(f"📨 Processing message from {message_data.get('chatId', 'unknown')}: {message_data.get('body', 'no text')[:50]}...")

            # Save message to database
            await self.save_message_to_database(message_data)

            print(f"✅ Message processed and saved successfully")

            # Extract phone number from chatId
            chat_id = message_data.get("chatId", "")
            sender_phone = chat_id.replace("@c.us", "") if "@c.us" in chat_id else chat_id

            # Check if this is an authorization response from BOSS
            if not message_data.get("fromMe", False):
                message_body = message_data.get("body", "").strip()
                if await self.auth_service.check_authorization_response(message_body, sender_phone):
                    print("🔐 Authorization response processed")
                    return  # Don't process as normal message

            # Process ALL incoming messages with AI (auto-enabled for everyone)
            if not message_data.get("fromMe", False) and self.llm_service:
                from database.database import SessionLocal
                db = SessionLocal()
                try:
                    chat = db.query(Chat).filter(Chat.id == message_data.get("chatId")).first()
                    if chat:
                        # Auto-enable AI for all chats if not already set
                        if not chat.ai_enabled:
                            print(f"🤖 Auto-enabling AI for chat {chat.name or chat.phone_number}")
                            chat.ai_enabled = True
                            db.commit()

                        print(f"🤖 Processing message with AI for {chat.name or chat.phone_number}...")
                        await self.process_message_with_llm(message_data)
                    else:
                        print(f"⚠️ Chat not found in database")
                finally:
                    db.close()

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")

    async def save_message_to_database(self, message_data: dict):
        """Save message and chat to database"""
        try:
            from database.database import SessionLocal
            from database.models import Chat, Message, MessageType
            from datetime import datetime
            import traceback

            # Use SessionLocal directly for synchronous database operations
            db = SessionLocal()
            try:
                chat_id = message_data.get("chatId")
                if not chat_id:
                    print("❌ Missing chatId in message data")
                    return

                phone_number = chat_id.replace("@c.us", "") if "@c.us" in chat_id else chat_id

                # Check if chat exists
                chat = db.query(Chat).filter(Chat.id == chat_id).first()

                if not chat:
                    # Create new chat
                    chat = Chat(
                        id=chat_id,  # Use the WhatsApp chat ID
                        phone_number=phone_number,
                        name=f"Contact {phone_number[-4:]}",  # Use last 4 digits as default name
                        is_group=message_data.get("isGroup", False),
                        is_active=True,
                        ai_enabled=True  # Auto-enable AI for new chats
                    )
                    db.add(chat)
                    db.flush()  # Get the chat ID
                    print(f"💾 Created new chat for {phone_number}")

                # Check if message already exists to avoid duplicates
                message_id = message_data.get("id")
                if message_id:
                    existing_message = db.query(Message).filter(Message.id == message_id).first()
                    if existing_message:
                        print(f"📨 Message {message_id} already exists, skipping")
                        return

                # Safely convert timestamp
                timestamp = datetime.now()
                try:
                    if "timestamp" in message_data and message_data["timestamp"]:
                        timestamp = datetime.fromtimestamp(float(message_data["timestamp"]))
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Invalid timestamp {message_data.get('timestamp')}, using current time")

                # Create message
                message = Message(
                    id=message_id,  # Use the WhatsApp message ID
                    chat_id=chat.id,
                    body=message_data.get("body", ""),
                    message_type=MessageType.TEXT,
                    from_me=message_data.get("fromMe", False),
                    timestamp=timestamp,
                    has_media=message_data.get("hasMedia", False),
                    llm_processed=False
                )

                db.add(message)
                db.commit()
                print(f"💾 Message saved to database: {message_data.get('body', '')[:30]}...")

            except Exception as e:
                print(f"❌ Database error: {e}")
                print(f"❌ Traceback: {traceback.format_exc()}")
                db.rollback()
            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error saving message to database: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")

    async def fetch_chats_from_whatsapp(self):
        """Fetch chats directly from WhatsApp client and sync with database"""
        try:
            if not self.process or not self.is_connected:
                print("⚠️ WhatsApp not connected, cannot fetch chats")
                return []

            # Send command to Node.js process to fetch chats
            command = {"action": "getChats"}
            await self.send_command_to_process(command)

            # The response will come through the callback mechanism
            # For now, return what we have in database
            from database.database import SessionLocal
            from database.models import Chat

            db = SessionLocal()
            try:
                chats = db.query(Chat).filter(Chat.is_active == True).all()
                return [
                    {
                        "id": chat.id,
                        "name": chat.name,
                        "phone_number": chat.phone_number,
                        "is_group": chat.is_group,
                        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None
                    }
                    for chat in chats
                ]
            finally:
                db.close()

            return []
        except Exception as e:
            print(f"❌ Error fetching chats from WhatsApp: {e}")
            return []

    async def fetch_chat_messages(self, chat_id: str, limit: int = 50):
        """Fetch messages for a specific chat from WhatsApp client"""
        try:
            if not self.process or not self.is_connected:
                print("⚠️ WhatsApp not connected, cannot fetch messages")
                return []

            # Send command to Node.js process to fetch messages
            command = {
                "action": "getChatMessages",
                "chatId": chat_id,
                "limit": limit
            }
            await self.send_command_to_process(command)

            # For now, return what we have in database
            from database.database import SessionLocal
            from database.models import Message

            db = SessionLocal()
            try:
                messages = db.query(Message).filter(
                    Message.chat_id == chat_id
                ).order_by(Message.timestamp.desc()).limit(limit).all()

                return [
                    {
                        "id": msg.id,
                        "chat_id": msg.chat_id,
                        "body": msg.body,
                        "message_type": msg.message_type.value if msg.message_type else "text",
                        "from_me": msg.from_me,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                        "has_media": msg.has_media,
                        "llm_processed": msg.llm_processed,
                        "llm_response": msg.llm_response
                    }
                    for msg in messages
                ]
            finally:
                db.close()

            return []
        except Exception as e:
            print(f"❌ Error fetching messages for chat {chat_id}: {e}")
            return []

    async def send_command_to_process(self, command: dict):
        """Send command to Node.js WhatsApp process"""
        try:
            if not self.process or not self.process.stdin:
                return False

            command_json = json.dumps(command) + "\n"
            self.process.stdin.write(command_json.encode())
            await self.process.stdin.drain()
            return True
        except Exception as e:
            print(f"❌ Error sending command to process: {e}")
            return False

    async def process_message_with_llm(self, message_data: dict):
        """Process message with LLM and potentially respond"""
        try:
            message_body = message_data.get("body", "").strip()
            chat_id = message_data["chatId"]

            if not message_body:
                return

            # Extract phone number from chat_id
            sender_phone = chat_id.replace("@c.us", "") if "@c.us" in chat_id else chat_id

            # Get chat info from database for additional context
            from database.database import SessionLocal
            db = SessionLocal()
            try:
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                contact_name = chat.name if chat else None
            finally:
                db.close()

            # Build context with phone number for authorization
            context = {
                "phone_number": sender_phone,
                "customer_name": contact_name,
                "business_hours": "Monday-Thursday, 9:00 AM - 3:00 PM",
                "services": ["Consultation", "Meeting", "Service Call", "Checkup"]
            }

            # Check if this looks like an appointment request
            appointment_keywords = [
                "appointment", "book", "schedule", "reserve", "meeting",
                "available", "time", "date", "calendar"
            ]

            if any(keyword in message_body.lower() for keyword in appointment_keywords):
                # Process as appointment request
                appointment_data = await self.llm_service.process_appointment_request(message_body, chat_id)

                if appointment_data and appointment_data.get("confidence", 0) > 0.7:
                    intent = appointment_data.get("intent")

                    # Import appointment tools
                    from services.llm_tools import SecureLLMTools
                    from services.authorization_service import AuthorizationService
                    tools = SecureLLMTools(AuthorizationService())

                    if intent == "check_availability" and appointment_data.get("preferred_date"):
                        # Check availability
                        result = await tools.check_availability(
                            date=appointment_data["preferred_date"],
                            duration_minutes=60
                        )

                        if result["status"] == "success":
                            slots = result["available_slots"]
                            if slots:
                                response = f"📅 Available time slots for {appointment_data['preferred_date']}:\n\n"
                                response += "\n".join([f"⏰ {slot}" for slot in slots[:10]])
                                if len(slots) > 10:
                                    response += f"\n\n... and {len(slots) - 10} more slots"
                                response += "\n\nPlease let me know which time works best for you!"
                            else:
                                response = f"😔 Sorry, no available slots on {appointment_data['preferred_date']}. Would you like to try a different date?"
                        else:
                            response = "❌ Sorry, I couldn't check availability. Please try again."

                        await self.send_message(chat_id, response)
                        return

                    elif intent == "book_appointment" and appointment_data.get("preferred_date") and appointment_data.get("preferred_time"):
                        # Get chat info for customer details
                        db = next(get_db())
                        chat = db.query(Chat).filter(Chat.id == chat_id).first()

                        customer_name = appointment_data.get("customer_name") or (chat.name if chat else "Customer")
                        customer_phone = appointment_data.get("customer_phone") or (chat.phone_number if chat else "")
                        service_type = appointment_data.get("service") or "General"

                        # Create appointment
                        result = await tools.create_appointment(
                            chat_id=chat_id,
                            customer_name=customer_name,
                            customer_phone=customer_phone,
                            service_type=service_type,
                            appointment_date=appointment_data["preferred_date"],
                            appointment_time=appointment_data["preferred_time"],
                            duration_minutes=60,
                            notes=appointment_data.get("notes")
                        )

                        if result["status"] == "success":
                            apt = result["appointment"]
                            response = f"""✅ **Appointment Confirmed!**

📋 Service: {apt['service']}
📅 Date: {apt['date']}
⏰ Time: {apt['time']}
⏱️ Duration: {apt['duration']} minutes
👤 Customer: {apt['customer']}
🔖 Confirmation: {apt['external_id']}

You'll receive reminders:
• 24 hours before
• 1 hour before

Thank you for booking with us! 🙏"""
                        elif result["status"] == "conflict":
                            response = f"""{result['message']}

Would you like me to show you available time slots for that day?"""
                        else:
                            response = f"❌ {result.get('message', 'Failed to create appointment. Please try again.')}"

                        await self.send_message(chat_id, response)
                        return

            # Generate general response with authorization context
            llm_response = await self.llm_service.generate_response(
                message_body,
                chat_id,
                provider="auto",
                context=context,
                phone_number=sender_phone
            )

            if llm_response and llm_response.get("response"):
                await self.send_message(chat_id, llm_response["response"])

        except Exception as e:
            print(f"Error processing message with LLM: {e}")
    
    async def get_status(self) -> dict:
        """Get WhatsApp service status"""
        # Read current status from file for most up-to-date info
        node_status = await self.read_status_file()

        return {
            "connected": node_status.get("connected", self.is_connected),
            "connecting": node_status.get("connecting", self.is_connecting),
            "process_running": self.process is not None and self.process.poll() is None,
            "has_qr_code": self.qr_code is not None or node_status.get("qr_code") is not None,
            "session_exists": os.path.exists(self.session_path),
            "ready": node_status.get("ready", False)
        }
    
    async def disconnect(self):
        """Disconnect WhatsApp"""
        if self.process:
            try:
                self.process.send_signal(signal.SIGTERM)
                await asyncio.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                print(f"Error terminating WhatsApp process: {e}")
            
            self.process = None
        
        self.is_connected = False
        self.is_connecting = False
        self.qr_code = None
    
    async def check_qr_file(self):
        """Check for QR code file and read it"""
        try:
            # Check in the whatsapp_client directory for QR code
            qr_file_path = self.whatsapp_client_dir / "qr_code.txt"
            if qr_file_path.exists():
                with open(qr_file_path, 'r') as f:
                    qr_code = f.read().strip()

                if qr_code and qr_code != self.qr_code:
                    self.qr_code = qr_code
                    print(f"✅ QR Code loaded from file: {qr_code[:50]}...")

                    # Broadcast QR code to connected clients
                    if self.connection_manager:
                        await self.connection_manager.broadcast({
                            "type": "qr_code",
                            "data": {"qr": self.qr_code}
                        })

        except Exception as e:
            print(f"❌ Error reading QR code file: {e}")

    async def read_status_file(self) -> dict:
        """Read status from Node.js bridge file"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Error reading status file: {e}")

        return {
            "connected": False,
            "connecting": False,
            "qr_code": None,
            "ready": False
        }

    async def cleanup(self):
        """Cleanup WhatsApp service"""
        await self.disconnect()
        print("📱 WhatsApp service cleaned up")