# backend/app/routers/appointments.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from database.database import get_db
from database.models import Appointment, AppointmentStatus, Chat
from services.llm_service import LLMService

router = APIRouter()

class AppointmentCreate(BaseModel):
    chat_id: str
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    title: str
    description: Optional[str] = None
    service_type: str
    appointment_date: datetime
    duration_minutes: int = 60
    notes: Optional[str] = None
    price: Optional[float] = None

class AppointmentUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    price: Optional[float] = None

@router.post("/")
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new appointment"""
    try:
        # Check for conflicts
        conflicts = db.query(Appointment).filter(
            Appointment.appointment_date == appointment_data.appointment_date,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
        ).all()
        
        if conflicts:
            raise HTTPException(
                status_code=409, 
                detail=f"Time slot conflict. Existing appointments: {[apt.id for apt in conflicts]}"
            )
        
        # Ensure chat exists
        chat = db.query(Chat).filter(Chat.id == appointment_data.chat_id).first()
        if not chat:
            chat = Chat(
                id=appointment_data.chat_id,
                name=appointment_data.customer_name,
                phone_number=appointment_data.customer_phone
            )
            db.add(chat)
            db.commit()
        
        # Create appointment
        appointment = Appointment(
            external_id=f"apt_{int(datetime.now().timestamp())}_{appointment_data.chat_id[-4:]}",
            **appointment_data.dict()
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        return {
            "success": True,
            "appointment": {
                "id": appointment.id,
                "external_id": appointment.external_id,
                "customer_name": appointment.customer_name,
                "service_type": appointment.service_type,
                "appointment_date": appointment.appointment_date.isoformat(),
                "duration_minutes": appointment.duration_minutes,
                "status": appointment.status.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_appointments(
    chat_id: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get appointments with optional filters"""
    try:
        query = db.query(Appointment)
        
        if chat_id:
            query = query.filter(Appointment.chat_id == chat_id)
        if status:
            query = query.filter(Appointment.status == status)
        if date_from:
            query = query.filter(Appointment.appointment_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.filter(Appointment.appointment_date <= datetime.combine(date_to, datetime.max.time()))
        
        appointments = query.order_by(Appointment.appointment_date).limit(limit).all()
        
        appointment_list = []
        for apt in appointments:
            appointment_list.append({
                "id": apt.id,
                "external_id": apt.external_id,
                "chat_id": apt.chat_id,
                "customer_name": apt.customer_name,
                "customer_phone": apt.customer_phone,
                "customer_email": apt.customer_email,
                "title": apt.title,
                "description": apt.description,
                "service_type": apt.service_type,
                "appointment_date": apt.appointment_date.isoformat(),
                "duration_minutes": apt.duration_minutes,
                "status": apt.status.value,
                "notes": apt.notes,
                "price": apt.price,
                "created_at": apt.created_at.isoformat(),
                "updated_at": apt.updated_at.isoformat()
            })
        
        return {"success": True, "appointments": appointment_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """Get specific appointment"""
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "success": True,
            "appointment": {
                "id": appointment.id,
                "external_id": appointment.external_id,
                "chat_id": appointment.chat_id,
                "customer_name": appointment.customer_name,
                "customer_phone": appointment.customer_phone,
                "customer_email": appointment.customer_email,
                "title": appointment.title,
                "description": appointment.description,
                "service_type": appointment.service_type,
                "appointment_date": appointment.appointment_date.isoformat(),
                "duration_minutes": appointment.duration_minutes,
                "status": appointment.status.value,
                "notes": appointment.notes,
                "price": appointment.price,
                "created_at": appointment.created_at.isoformat(),
                "updated_at": appointment.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """Update appointment"""
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Check for conflicts if date/time is being changed
        if appointment_data.appointment_date and appointment_data.appointment_date != appointment.appointment_date:
            conflicts = db.query(Appointment).filter(
                Appointment.id != appointment_id,
                Appointment.appointment_date == appointment_data.appointment_date,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            ).all()
            
            if conflicts:
                raise HTTPException(
                    status_code=409,
                    detail=f"Time slot conflict. Existing appointments: {[apt.id for apt in conflicts]}"
                )
        
        # Update fields
        for field, value in appointment_data.dict(exclude_unset=True).items():
            setattr(appointment, field, value)
        
        appointment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(appointment)
        
        return {
            "success": True,
            "message": "Appointment updated successfully",
            "appointment": {
                "id": appointment.id,
                "external_id": appointment.external_id,
                "status": appointment.status.value,
                "updated_at": appointment.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """Cancel appointment"""
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment.status = AppointmentStatus.CANCELLED
        appointment.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Appointment cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/availability/slots")
async def get_available_slots(
    date_param: date = Query(..., alias="date"),
    duration_minutes: int = Query(60),
    db: Session = Depends(get_db)
):
    """Get available time slots for a specific date"""
    try:
        # Business hours (this could come from database configuration)
        start_hour = 9
        end_hour = 17
        slot_duration = duration_minutes
        
        # Generate all possible slots
        available_slots = []
        current_datetime = datetime.combine(date_param, datetime.min.time().replace(hour=start_hour))
        end_datetime = datetime.combine(date_param, datetime.min.time().replace(hour=end_hour))
        
        while current_datetime < end_datetime:
            # Check if slot is available
            conflicts = db.query(Appointment).filter(
                Appointment.appointment_date <= current_datetime,
                Appointment.appointment_date + timedelta(minutes=Appointment.duration_minutes) > current_datetime,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            ).count()
            
            if conflicts == 0:
                available_slots.append(current_datetime.strftime("%H:%M"))
            
            current_datetime += timedelta(minutes=slot_duration)
        
        return {
            "success": True,
            "date": date_param.isoformat(),
            "available_slots": available_slots,
            "duration_minutes": duration_minutes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-nlp")
async def process_appointment_nlp(
    request_data: dict,
    llm_service: LLMService = Depends(),
    db: Session = Depends(get_db)
):
    """Process natural language appointment request"""
    try:
        message = request_data.get("message", "")
        chat_id = request_data.get("chat_id", "")
        
        if not message or not chat_id:
            raise HTTPException(status_code=400, detail="message and chat_id are required")
        
        # Process with LLM
        appointment_data = await llm_service.process_appointment_request(message, chat_id)
        
        if not appointment_data:
            return {
                "success": False,
                "message": "Could not process appointment request"
            }
        
        return {
            "success": True,
            "parsed_data": appointment_data,
            "confidence": appointment_data.get("confidence", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
