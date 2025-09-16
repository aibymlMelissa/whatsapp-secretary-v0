# backend/app/routers/whatsapp.py
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import json

from database.database import get_db
from services.whatsapp_service import WhatsAppService
from database.models import Chat, Message

router = APIRouter()

# This will be injected from main.py
whatsapp_service: WhatsAppService = None

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
            raise HTTPException(status_code=500, detail="Failed to initialize WhatsApp")
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
        qr_code = service.qr_code
        return {
            "success": True, 
            "qr_code": qr_code,
            "has_qr": qr_code is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def whatsapp_callback(request: Request, service: WhatsAppService = Depends(get_whatsapp_service)):
    """Handle callbacks from Node.js WhatsApp client"""
    try:
        data = await request.json()
        event = data.get("event")
        event_data = data.get("data", {})
        
        await service.handle_callback(event, event_data)
        return {"success": True}
        
    except Exception as e:
        print(f"Callback error: {e}")
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
    db: AsyncSession = Depends(get_db),
    service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get all chats"""
    try:
        # Get from database
        result = await db.execute(select(Chat).filter(Chat.is_active == True))
        db_chats = result.scalars().all()

        chats = []
        for chat in db_chats:
            # Get last message
            last_message_result = await db.execute(
                select(Message).filter(Message.chat_id == chat.id).order_by(Message.timestamp.desc())
            )
            last_message = last_message_result.scalars().first()
            
            chat_data = {
                "id": chat.id,
                "name": chat.name,
                "phone_number": chat.phone_number,
                "is_group": chat.is_group,
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

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get messages from a specific chat"""
    try:
        result = await db.execute(
            select(Message).filter(Message.chat_id == chat_id)
            .order_by(Message.timestamp.desc()).limit(limit)
        )
        messages = result.scalars().all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "chat_id": msg.chat_id,
                "body": msg.body,
                "message_type": msg.message_type.value if msg.message_type else "text",
                "from_me": msg.from_me,
                "timestamp": msg.timestamp.isoformat(),
                "has_media": msg.has_media,
                "media_path": msg.media_path,
                "llm_processed": msg.llm_processed,
                "llm_response": msg.llm_response
            })
        
        return {"success": True, "messages": list(reversed(message_list))}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


