# backend/app/routers/whatsapp.py
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from database.database import get_db
from services.whatsapp_service import WhatsAppService
from database.models import Chat, Message

router = APIRouter()

# This will be injected from main.py
whatsapp_service: WhatsAppService = None

class PhoneNumberRequest(BaseModel):
    phone_number: str

def get_whatsapp_service():
    global whatsapp_service
    if not whatsapp_service:
        raise HTTPException(status_code=500, detail="WhatsApp service not initialized")
    return whatsapp_service

@router.post("/connect")
async def connect_whatsapp(service: WhatsAppService = Depends(get_whatsapp_service)):
    """Initialize WhatsApp connection"""
    try:
        success = await service.initialize()
        if success:
            return {"success": True, "message": "WhatsApp connection initiated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize WhatsApp service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
async def disconnect_whatsapp(service: WhatsAppService = Depends(get_whatsapp_service)):
    """Disconnect WhatsApp"""
    try:
        await service.disconnect()
        return {"success": True, "message": "WhatsApp disconnected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-session")
async def reset_session(service: WhatsAppService = Depends(get_whatsapp_service)):
    """Reset WhatsApp session to generate new QR code"""
    try:
        import shutil
        from pathlib import Path
        from core.config import settings

        # Disconnect first
        await service.disconnect()

        # Clear session files
        session_path = Path(settings.WHATSAPP_SESSION_PATH)
        if session_path.exists():
            shutil.rmtree(session_path)
            print(f"✅ Session cleared: {session_path}")

        # Clear status and QR files in whatsapp_client directory
        qr_file = Path("backend/whatsapp_client/qr_code.txt")
        status_file = Path("backend/whatsapp_client/status.json")
        if qr_file.exists():
            qr_file.unlink()
        if status_file.exists():
            status_file.unlink()

        # Wait a moment then reconnect
        import asyncio
        await asyncio.sleep(1)

        # Reinitialize to get new QR code
        await service.initialize()

        return {"success": True, "message": "Session reset. New QR code will be generated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_whatsapp_status(service: WhatsAppService = Depends(get_whatsapp_service)):
    """Get WhatsApp connection status"""
    try:
        status = await service.get_status()
        return {"success": True, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr")
async def get_qr_code(service: WhatsAppService = Depends(get_whatsapp_service)):
    """Get current QR code for authentication"""
    try:
        # Check for QR code from file
        await service.check_qr_file()
        qr_code = service.qr_code

        # Also check Node.js status file for QR code
        node_status = await service.read_status_file()
        if not qr_code and node_status.get("qr_code"):
            qr_code = node_status["qr_code"]
            service.qr_code = qr_code

        return {
            "success": True,
            "qr_code": qr_code,
            "has_qr": qr_code is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Pairing code functionality removed - using QR code only for now

@router.post("/callback")
async def whatsapp_callback(request: Request, service: WhatsAppService = Depends(get_whatsapp_service)):
    """Handle callbacks from Node.js WhatsApp client"""
    try:
        data = await request.json()
        event = data.get("event")
        event_data = data.get("data", {})

        print(f"📞 Callback received - Event: {event}, Data keys: {list(event_data.keys()) if event_data else []}")

        await service.handle_callback(event, event_data)
        return {"success": True}

    except Exception as e:
        import traceback
        print(f"❌ Callback error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@router.post("/send-message")
async def send_message(
    message_data: Dict[str, Any],
    service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Send message via WhatsApp"""
    try:
        chat_id = message_data.get("chat_id")
        message = message_data.get("message")
        media_path = message_data.get("media_path")
        
        if not chat_id or not message:
            raise HTTPException(status_code=400, detail="chat_id and message are required")
        
        result = await service.send_message(chat_id, message, media_path)
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats")
async def get_chats(
    db: Session = Depends(get_db),
    fetch_from_whatsapp: bool = False
):
    """Get all chats - optionally fetch fresh data from WhatsApp"""
    try:
        if fetch_from_whatsapp:
            # Fetch fresh data from WhatsApp client (requires service)
            service = get_whatsapp_service()
            await service.fetch_chats_from_whatsapp()

        # Get from database
        db_chats = db.query(Chat).filter(Chat.is_active == True).all()

        chats = []
        for chat in db_chats:
            # Get last message
            last_message = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.timestamp.desc()).first()

            # Get unread count (messages not from me, created after last read)
            unread_count = db.query(Message).filter(
                Message.chat_id == chat.id,
                Message.from_me == False,
                Message.llm_processed == False
            ).count()

            chat_data = {
                "id": chat.id,
                "name": chat.name,
                "phone_number": chat.phone_number,
                "is_group": chat.is_group,
                "ai_enabled": chat.ai_enabled,
                "is_whitelisted": chat.is_whitelisted,
                "unread_count": unread_count,
                "last_message": {
                    "body": last_message.body if last_message else None,
                    "timestamp": last_message.timestamp.isoformat() if last_message else None,
                    "from_me": last_message.from_me if last_message else False
                } if last_message else None,
                "updated_at": chat.updated_at.isoformat()
            }
            chats.append(chat_data)

        return {"success": True, "chats": chats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats/{chat_id}/toggle-ai")
async def toggle_ai_for_chat(
    chat_id: str,
    enabled: bool,
    db: Session = Depends(get_db)
):
    """Toggle AI auto-response for a specific chat"""
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        chat.ai_enabled = enabled
        db.commit()

        return {
            "success": True,
            "chat_id": chat_id,
            "ai_enabled": enabled,
            "message": f"AI assistant {'enabled' if enabled else 'disabled'} for this chat"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats/{chat_id}/toggle-whitelist")
async def toggle_whitelist_for_chat(
    chat_id: str,
    whitelisted: bool,
    db: Session = Depends(get_db)
):
    """Toggle whitelist status for a specific chat"""
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        chat.is_whitelisted = whitelisted
        db.commit()

        return {
            "success": True,
            "chat_id": chat_id,
            "is_whitelisted": whitelisted,
            "message": f"Chat {'added to' if whitelisted else 'removed from'} whitelist"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    fetch_from_whatsapp: bool = False,
    db: Session = Depends(get_db),
    service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get messages from a specific chat - optionally fetch fresh data from WhatsApp"""
    try:
        if fetch_from_whatsapp:
            # Fetch fresh message history from WhatsApp client
            await service.fetch_chat_messages(chat_id, limit)

        messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).limit(limit).all()

        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "chat_id": msg.chat_id,
                "body": msg.body,
                "message_type": msg.message_type.value if msg.message_type else "text",
                "from_me": msg.from_me,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                "has_media": msg.has_media,
                "media_path": msg.media_path,
                "llm_processed": msg.llm_processed,
                "llm_response": msg.llm_response
            })

        return {"success": True, "messages": list(reversed(message_list))}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get quick statistics for dashboard"""
    try:
        from datetime import datetime, timedelta
        from database.models import Appointment

        # Count active chats
        active_chats = db.query(Chat).filter(Chat.is_active == True).count()

        # Count messages today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = db.query(Message).filter(Message.timestamp >= today).count()

        # Count upcoming appointments
        now = datetime.now()
        upcoming_appointments = db.query(Appointment).filter(
            Appointment.appointment_date >= now,
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).count()

        # Count total files
        from database.models import FileRecord
        total_files = db.query(FileRecord).count()

        # Count AI-enabled chats
        ai_enabled_chats = db.query(Chat).filter(
            Chat.is_active == True,
            Chat.ai_enabled == True
        ).count()

        return {
            "success": True,
            "stats": {
                "active_chats": active_chats,
                "messages_today": messages_today,
                "upcoming_appointments": upcoming_appointments,
                "total_files": total_files,
                "ai_enabled_chats": ai_enabled_chats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


