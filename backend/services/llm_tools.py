# backend/services/llm_tools.py
"""
LLM Tools that require authorization for sensitive operations

These tools can be called by the LLM but require BOSS approval
before executing sensitive operations like database access, file access, etc.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from services.authorization_service import AuthorizationService
from database.database import SessionLocal
from database.models import Appointment, Chat, Message, SystemConfig


class SecureLLMTools:
    """LLM tools with built-in authorization for sensitive operations"""

    def __init__(self, auth_service: AuthorizationService):
        self.auth_service = auth_service

    # ==================== DATABASE TOOLS ====================

    async def get_appointments(
        self,
        chat_id: str,
        requester_phone: str,
        date_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get appointments from database (REQUIRES AUTHORIZATION)

        Args:
            chat_id: Chat ID of the requester
            requester_phone: Phone number of the requester
            date_filter: Optional date filter

        Returns:
            Dictionary with status and data/error
        """
        # Request authorization
        request_id = await self.auth_service.request_authorization(
            chat_id=chat_id,
            requester_phone=requester_phone,
            action_type="database_query",
            action_description=f"Access appointment database{' for date: ' + date_filter if date_filter else ''}",
            requested_data={"query": "appointments", "filter": date_filter}
        )

        if not request_id:
            return {
                "status": "error",
                "message": "Failed to request authorization"
            }

        return {
            "status": "pending_authorization",
            "message": "⏳ Authorization request sent to administrator. Waiting for approval...",
            "request_id": request_id
        }

    async def query_database(
        self,
        chat_id: str,
        requester_phone: str,
        query_description: str,
        table_name: str,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query database (REQUIRES AUTHORIZATION)

        Args:
            chat_id: Chat ID of the requester
            requester_phone: Phone number of the requester
            query_description: Human-readable description of what data is needed
            table_name: Database table to query
            filters: Query filters

        Returns:
            Dictionary with status and data/error
        """
        request_id = await self.auth_service.request_authorization(
            chat_id=chat_id,
            requester_phone=requester_phone,
            action_type="database_query",
            action_description=f"Query {table_name} table: {query_description}",
            requested_data={"table": table_name, "filters": filters}
        )

        if not request_id:
            return {
                "status": "error",
                "message": "Failed to request authorization"
            }

        return {
            "status": "pending_authorization",
            "message": "⏳ Authorization request sent to administrator. Waiting for approval...",
            "request_id": request_id
        }

    # ==================== FILE SYSTEM TOOLS ====================

    async def access_file(
        self,
        chat_id: str,
        requester_phone: str,
        file_path: str,
        operation: str = "read"
    ) -> Dict[str, Any]:
        """
        Access file system (REQUIRES AUTHORIZATION)

        Args:
            chat_id: Chat ID of the requester
            requester_phone: Phone number of the requester
            file_path: Path to the file
            operation: Operation type (read, write, delete)

        Returns:
            Dictionary with status and data/error
        """
        request_id = await self.auth_service.request_authorization(
            chat_id=chat_id,
            requester_phone=requester_phone,
            action_type="file_access",
            action_description=f"{operation.upper()} file: {file_path}",
            requested_data={"path": file_path, "operation": operation}
        )

        if not request_id:
            return {
                "status": "error",
                "message": "Failed to request authorization"
            }

        return {
            "status": "pending_authorization",
            "message": "⏳ Authorization request sent to administrator. Waiting for approval...",
            "request_id": request_id
        }

    # ==================== SYSTEM CONFIGURATION TOOLS ====================

    async def get_system_config(
        self,
        chat_id: str,
        requester_phone: str,
        config_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Access system configuration (REQUIRES AUTHORIZATION)

        Args:
            chat_id: Chat ID of the requester
            requester_phone: Phone number of the requester
            config_key: Optional specific config key

        Returns:
            Dictionary with status and data/error
        """
        request_id = await self.auth_service.request_authorization(
            chat_id=chat_id,
            requester_phone=requester_phone,
            action_type="system_config_access",
            action_description=f"Access system configuration{': ' + config_key if config_key else ''}",
            requested_data={"config_key": config_key}
        )

        if not request_id:
            return {
                "status": "error",
                "message": "Failed to request authorization"
            }

        return {
            "status": "pending_authorization",
            "message": "⏳ Authorization request sent to administrator. Waiting for approval...",
            "request_id": request_id
        }

    # ==================== APPOINTMENT TOOLS (NO AUTH REQUIRED FOR BOOKING) ====================

    async def create_appointment(
        self,
        chat_id: str,
        customer_name: str,
        customer_phone: str,
        service_type: str,
        appointment_date: str,
        appointment_time: str,
        duration_minutes: int = 60,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Create an appointment (NO AUTH REQUIRED - Customer-facing)

        Args:
            chat_id: Chat ID for the appointment
            customer_name: Customer's name
            customer_phone: Customer's phone number
            service_type: Type of service requested
            appointment_date: Date in YYYY-MM-DD format
            appointment_time: Time in HH:MM format
            duration_minutes: Appointment duration (default 60)
            notes: Additional notes

        Returns:
            Dictionary with status and appointment details or error
        """
        db = SessionLocal()
        try:
            # Combine date and time into datetime
            appointment_datetime = datetime.fromisoformat(f"{appointment_date}T{appointment_time}:00")

            # Check for conflicts
            from database.models import AppointmentStatus
            conflicts = db.query(Appointment).filter(
                Appointment.appointment_date == appointment_datetime,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            ).all()

            if conflicts:
                # Suggest alternative times
                return {
                    "status": "conflict",
                    "message": f"⚠️ The requested time slot is not available. Please choose a different time.",
                    "conflicting_appointments": [{"id": apt.id, "time": apt.appointment_date.isoformat()} for apt in conflicts]
                }

            # Ensure chat exists
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                chat = Chat(
                    id=chat_id,
                    name=customer_name,
                    phone_number=customer_phone
                )
                db.add(chat)
                db.flush()

            # Create appointment
            appointment = Appointment(
                external_id=f"apt_{int(datetime.now().timestamp())}_{chat_id[-4:]}",
                chat_id=chat_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                title=f"{service_type} Appointment",
                service_type=service_type,
                appointment_date=appointment_datetime,
                duration_minutes=duration_minutes,
                notes=notes,
                status=AppointmentStatus.SCHEDULED
            )

            db.add(appointment)
            db.commit()
            db.refresh(appointment)

            return {
                "status": "success",
                "message": f"✅ Appointment confirmed for {appointment_date} at {appointment_time}",
                "appointment": {
                    "id": appointment.id,
                    "external_id": appointment.external_id,
                    "service": service_type,
                    "date": appointment_date,
                    "time": appointment_time,
                    "duration": duration_minutes,
                    "customer": customer_name
                }
            }

        except ValueError as e:
            return {
                "status": "error",
                "message": f"❌ Invalid date/time format: {str(e)}"
            }
        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"❌ Failed to create appointment: {str(e)}"
            }
        finally:
            db.close()

    async def check_availability(
        self,
        date: str,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Check available time slots for a date (NO AUTH REQUIRED)

        Args:
            date: Date in YYYY-MM-DD format
            duration_minutes: Appointment duration to check

        Returns:
            Dictionary with available time slots
        """
        db = SessionLocal()
        try:
            from datetime import timedelta
            from database.models import AppointmentStatus

            # Business hours
            start_hour = 9
            end_hour = 17

            # Generate all possible slots
            available_slots = []
            date_obj = datetime.fromisoformat(date)
            current_datetime = date_obj.replace(hour=start_hour, minute=0, second=0)
            end_datetime = date_obj.replace(hour=end_hour, minute=0, second=0)

            while current_datetime < end_datetime:
                # Check if slot is available
                conflicts = db.query(Appointment).filter(
                    Appointment.appointment_date <= current_datetime,
                    Appointment.appointment_date >= current_datetime - timedelta(minutes=duration_minutes),
                    Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
                ).count()

                if conflicts == 0:
                    available_slots.append(current_datetime.strftime("%H:%M"))

                current_datetime += timedelta(minutes=duration_minutes)

            return {
                "status": "success",
                "date": date,
                "available_slots": available_slots,
                "total_slots": len(available_slots)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check availability: {str(e)}"
            }
        finally:
            db.close()

    # ==================== SAFE TOOLS (NO AUTH REQUIRED) ====================

    async def get_current_time(self) -> Dict[str, Any]:
        """Get current time (NO AUTH REQUIRED)"""
        return {
            "status": "success",
            "data": {
                "current_time": datetime.now().isoformat(),
                "timezone": "UTC"
            }
        }

    async def calculate(self, expression: str) -> Dict[str, Any]:
        """Simple calculator (NO AUTH REQUIRED)"""
        try:
            # Safe eval with limited scope
            result = eval(expression, {"__builtins__": {}}, {})
            return {
                "status": "success",
                "data": {"result": result}
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Calculation error: {str(e)}"
            }

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Get basic chat info (NO AUTH REQUIRED)"""
        db = SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return {
                    "status": "error",
                    "message": "Chat not found"
                }

            return {
                "status": "success",
                "data": {
                    "name": chat.name,
                    "phone_number": chat.phone_number,
                    "is_group": chat.is_group,
                    "ai_enabled": chat.ai_enabled,
                    "is_whitelisted": chat.is_whitelisted
                }
            }
        finally:
            db.close()


# Tool registry for LLM to discover available tools
TOOL_REGISTRY = {
    "safe_tools": [
        {
            "name": "get_current_time",
            "description": "Get current date and time",
            "requires_auth": False
        },
        {
            "name": "calculate",
            "description": "Perform simple calculations",
            "requires_auth": False,
            "parameters": ["expression"]
        },
        {
            "name": "get_chat_info",
            "description": "Get basic information about the current chat",
            "requires_auth": False,
            "parameters": ["chat_id"]
        },
        {
            "name": "create_appointment",
            "description": "Create a new appointment for a customer",
            "requires_auth": False,
            "parameters": ["chat_id", "customer_name", "customer_phone", "service_type", "appointment_date", "appointment_time", "duration_minutes?", "notes?"]
        },
        {
            "name": "check_availability",
            "description": "Check available time slots for a specific date",
            "requires_auth": False,
            "parameters": ["date", "duration_minutes?"]
        }
    ],
    "protected_tools": [
        {
            "name": "get_appointments",
            "description": "Access appointment database",
            "requires_auth": True,
            "parameters": ["chat_id", "requester_phone", "date_filter?"]
        },
        {
            "name": "query_database",
            "description": "Query any database table",
            "requires_auth": True,
            "parameters": ["chat_id", "requester_phone", "query_description", "table_name", "filters?"]
        },
        {
            "name": "access_file",
            "description": "Access files on the server",
            "requires_auth": True,
            "parameters": ["chat_id", "requester_phone", "file_path", "operation"]
        },
        {
            "name": "get_system_config",
            "description": "Access system configuration",
            "requires_auth": True,
            "parameters": ["chat_id", "requester_phone", "config_key?"]
        }
    ]
}
