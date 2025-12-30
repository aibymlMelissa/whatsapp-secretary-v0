# backend/app/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, Enum, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import enum
from typing import Optional

from database.base import Base

class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"

class MessageType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    STICKER = "sticker"

class LLMProvider(enum.Enum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

# Chat Management
class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)  # WhatsApp chat ID
    name = Column(String, nullable=False)
    phone_number = Column(String)
    is_group = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    ai_enabled = Column(Boolean, default=False)  # Enable AI auto-response for this chat
    is_whitelisted = Column(Boolean, default=False)  # Only whitelisted chats can receive AI responses

    # Conversation Management
    archived_at = Column(DateTime)
    archive_reason = Column(String)
    last_activity_at = Column(DateTime, default=func.now())
    message_count = Column(Integer, default=0)
    unread_count = Column(Integer, default=0)
    extra_data = Column(JSONB, default={})
    auto_archive_after_days = Column(Integer, default=90)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="chat")
    appointments = relationship("Appointment", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)  # WhatsApp message ID
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False)
    body = Column(Text)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    from_me = Column(Boolean, default=False)
    timestamp = Column(DateTime, nullable=False)
    has_media = Column(Boolean, default=False)
    media_path = Column(String)  # Path to downloaded media
    llm_processed = Column(Boolean, default=False)
    llm_response = Column(Text)  # AI response if any

    # Conversation Management
    archived_at = Column(DateTime)
    archive_reason = Column(String)
    processed = Column(Boolean, default=False)
    read_at = Column(DateTime)
    extra_data = Column(JSONB, default={})
    last_synced_at = Column(DateTime)
    sentiment = Column(String)  # positive, neutral, negative, mixed
    category = Column(String)
    tags = Column(ARRAY(String))

    created_at = Column(DateTime, default=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="messages")

# Appointment System
class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, unique=True)  # For external references
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False)
    
    # Customer info
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String)
    customer_email = Column(String)
    
    # Appointment details
    title = Column(String, nullable=False)
    description = Column(Text)
    service_type = Column(String)
    appointment_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Status and metadata
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    notes = Column(Text)
    price = Column(Float)
    currency = Column(String, default="USD")
    
    # Reminders
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_1h_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="appointments")
    reminders = relationship("AppointmentReminder", back_populates="appointment")

class AppointmentReminder(Base):
    __tablename__ = "appointment_reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    reminder_type = Column(String, nullable=False)  # "24h", "1h", "custom"
    reminder_time = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    message_template = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    appointment = relationship("Appointment", back_populates="reminders")

# File Management
class FileRecord(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    
    # Associated with message/chat
    message_id = Column(String, ForeignKey("messages.id"))
    chat_id = Column(String, ForeignKey("chats.id"))
    
    # Metadata
    is_processed = Column(Boolean, default=False)
    processing_result = Column(Text)  # JSON string with processing results
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# User Management
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, unique=True, nullable=False)  # WhatsApp phone number
    display_name = Column(String)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    llm_settings = relationship("UserLLMSetting", back_populates="user")

# User-specific LLM Configuration
class UserLLMSetting(Base):
    __tablename__ = "user_llm_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Provider settings
    preferred_provider = Column(Enum(LLMProvider), default=LLMProvider.GEMINI)

    # OpenAI settings
    openai_api_key = Column(String)  # Encrypted
    openai_model = Column(String, default="gpt-4o-mini")

    # Anthropic settings
    anthropic_api_key = Column(String)  # Encrypted
    anthropic_model = Column(String, default="claude-3-haiku-20240307")

    # Gemini settings
    gemini_api_key = Column(String)  # Encrypted
    gemini_model = Column(String, default="gemini-1.5-flash")

    # Ollama settings
    ollama_base_url = Column(String, default="http://localhost:11434")
    ollama_model = Column(String, default="llama3.2")

    # General settings
    max_tokens = Column(Integer, default=500)
    temperature = Column(Float, default=0.7)
    use_system_default = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="llm_settings")

# LLM Configuration and History
class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    provider = Column(Enum(LLMProvider), nullable=False)
    model_name = Column(String, nullable=False)
    api_key = Column(String)  # Encrypted
    base_url = Column(String)  # For Ollama

    # Configuration
    max_tokens = Column(Integer, default=500)
    temperature = Column(Float, default=0.7)
    system_prompt = Column(Text)

    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False)
    message_id = Column(String, ForeignKey("messages.id"))
    
    # LLM interaction
    user_input = Column(Text, nullable=False)
    llm_response = Column(Text, nullable=False)
    provider = Column(Enum(LLMProvider), nullable=False)
    model_name = Column(String, nullable=False)
    
    # Performance metrics
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())

# System Configuration
class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    description = Column(String)
    config_type = Column(String, default="string")  # string, int, float, bool, json
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Business Hours and Availability
class BusinessHours(Base):
    __tablename__ = "business_hours"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    is_open = Column(Boolean, default=True)
    open_time = Column(String)  # HH:MM format
    close_time = Column(String)  # HH:MM format
    
    # Break times
    break_start = Column(String)  # HH:MM format
    break_end = Column(String)  # HH:MM format
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ServiceType(Base):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=60)
    price = Column(Float)
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)

    # Booking rules
    advance_booking_hours = Column(Integer, default=24)  # Minimum advance booking
    max_advance_booking_days = Column(Integer, default=30)  # Maximum advance booking

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Security: Authorization System
class PendingAuthorization(Base):
    __tablename__ = "pending_authorizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, unique=True, nullable=False)  # Unique request identifier
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False)  # Who requested
    requester_phone = Column(String, nullable=False)

    # What is being requested
    action_type = Column(String, nullable=False)  # 'database_query', 'file_access', 'appointment_access', etc.
    action_description = Column(Text)  # Human-readable description
    requested_data = Column(Text)  # JSON string of what data is requested

    # Authorization status
    status = Column(String, default="pending")  # pending, approved, denied, expired
    auth_code = Column(String)  # The code BOSS needs to send (e.g., "AIbyML.com")

    # Approval tracking
    approved_by = Column(String)  # Phone number of approver
    approved_at = Column(DateTime)
    expires_at = Column(DateTime)  # Auto-expire after X minutes

    # Response handling
    response_data = Column(Text)  # Cached response to send after approval
    response_sent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Agentic Task System
class TaskType(enum.Enum):
    APPOINTMENT_BOOKING = "appointment_booking"
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"
    APPOINTMENT_CANCEL = "appointment_cancel"
    INFORMATION_QUERY = "information_query"
    FILE_PROCESSING = "file_processing"
    AUTHORIZATION_REQUEST = "authorization_request"
    REMINDER = "reminder"
    GENERAL_INQUIRY = "general_inquiry"
    TRIAGE = "triage"

    # Conversation Management
    CONVERSATION_ARCHIVE = "conversation_archive"
    MESSAGE_SYNC = "message_sync"
    DATABASE_CLEANUP = "database_cleanup"
    METADATA_UPDATE = "metadata_update"
    STATUS_UPDATE = "status_update"

    # Document and Image Analysis
    DOCUMENT_ANALYSIS = "document_analysis"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    URGENT = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7
    BACKGROUND = 9

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Integer, default=5)  # 1-10, lower is higher priority

    # Context
    chat_id = Column(String, ForeignKey("chats.id"))
    message_id = Column(String, ForeignKey("messages.id"))
    assigned_agent = Column(String)  # Which agent is handling this task

    # Task data (stored as JSON)
    input_data = Column(Text)  # JSON: original message, context, parameters
    output_data = Column(Text)  # JSON: results, responses, generated data
    extra_data = Column(Text)  # JSON: agent notes, steps completed, internal state
    error_message = Column(Text)  # Error details if failed

    # Workflow support for multi-step tasks
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    step_number = Column(Integer, default=1)
    total_steps = Column(Integer, default=1)

    # Timing and scheduling
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    deadline = Column(DateTime)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Relationships
    subtasks = relationship("Task", backref=backref("parent", remote_side=[id]))

class AgentLog(Base):
    """Log of agent actions for debugging and analytics"""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)  # 'created', 'processed', 'delegated', 'completed', 'failed'
    details = Column(Text)  # JSON: additional information
    duration_ms = Column(Integer)  # How long the action took

    created_at = Column(DateTime, default=func.now())

# Conversation Management Tables
class MessageArchive(Base):
    """Archive storage for old messages"""
    __tablename__ = "message_archives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_message_id = Column(String, index=True)
    chat_id = Column(String, index=True, nullable=False)
    content = Column(Text)
    extra_data = Column(JSONB, default={})
    archived_at = Column(DateTime, default=func.now(), index=True)
    archive_reason = Column(String)
    compressed = Column(Boolean, default=False)
    storage_path = Column(String)  # For external storage if needed

    created_at = Column(DateTime, default=func.now())

class SyncStatus(Base):
    """Track synchronization status between WhatsApp and Database"""
    __tablename__ = "sync_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False, index=True)  # 'message', 'chat', 'contact'
    entity_id = Column(String, nullable=False, index=True)
    last_sync_at = Column(DateTime)
    sync_status = Column(String, index=True)  # 'synced', 'pending', 'failed'
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


