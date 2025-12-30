# backend/routers/conversations.py
"""
Conversation Management API Endpoints

Provides REST API endpoints for:
- Archiving and unarchiving conversations
- Syncing messages
- Database cleanup operations
- Metadata management
- Scheduled task management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from database.database import get_db
from database.models import (
    Chat, Message, MessageArchive, SyncStatus,
    Task, TaskType, TaskStatus, TaskPriority
)
from tasks.task_manager import TaskManager
from tasks.scheduled_tasks import scheduled_tasks_manager


router = APIRouter(prefix="/api/conversations", tags=["conversations"])
task_manager = TaskManager()


# ==================== Request/Response Models ====================

class ArchiveRequest(BaseModel):
    chat_ids: List[str]
    reason: Optional[str] = "Manual archive"
    compress: bool = True


class UnarchiveRequest(BaseModel):
    chat_id: str


class SyncRequest(BaseModel):
    chat_id: Optional[str] = None  # None = sync all chats
    mode: str = "incremental"  # "incremental" or "full"


class CleanupRequest(BaseModel):
    archive_retention_days: int = 365
    optimize_tables: bool = True
    compress_after_days: int = 30


class MetadataUpdateRequest(BaseModel):
    entity_type: str  # "message" or "chat"
    entity_id: str
    metadata: Dict[str, Any]
    auto_analyze: bool = False


class StatusUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]]


class ArchiveResponse(BaseModel):
    success: bool
    task_id: int
    message: str


class SyncStatusResponse(BaseModel):
    entity_id: str
    last_sync_at: Optional[datetime]
    status: str
    error_message: Optional[str]


class DatabaseStatsResponse(BaseModel):
    total_chats: int
    total_messages: int
    archived_chats: int
    archived_messages: int
    database_size_mb: float
    oldest_message: Optional[datetime]
    newest_message: Optional[datetime]


# ==================== Archive Endpoints ====================

@router.post("/archive", response_model=ArchiveResponse)
async def archive_conversations(
    request: ArchiveRequest,
    db: Session = Depends(get_db)
):
    """
    Archive specific conversations

    Archives the specified conversations and their messages.
    Creates a background task to perform the archival.
    """
    try:
        # Validate chat IDs exist
        existing_chats = db.query(Chat).filter(Chat.id.in_(request.chat_ids)).all()

        if len(existing_chats) != len(request.chat_ids):
            found_ids = [chat.id for chat in existing_chats]
            missing_ids = [cid for cid in request.chat_ids if cid not in found_ids]
            raise HTTPException(
                status_code=404,
                detail=f"Chats not found: {', '.join(missing_ids)}"
            )

        # Create archive task
        task = await task_manager.create_task(
            task_type=TaskType.CONVERSATION_ARCHIVE,
            chat_id="manual",  # Manual operation
            input_data={
                "chat_ids": request.chat_ids,
                "config": {
                    "reason": request.reason,
                    "compress": request.compress
                }
            },
            priority=TaskPriority.HIGH.value
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create archive task")

        return ArchiveResponse(
            success=True,
            task_id=task.id,
            message=f"Archive task created for {len(request.chat_ids)} conversation(s)"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unarchive")
async def unarchive_conversation(
    request: UnarchiveRequest,
    db: Session = Depends(get_db)
):
    """
    Unarchive a conversation

    Restores an archived conversation to active status.
    """
    try:
        chat = db.query(Chat).filter(Chat.id == request.chat_id).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        if not chat.archived_at:
            return {"success": True, "message": "Chat is not archived"}

        # Unarchive chat
        chat.archived_at = None
        chat.archive_reason = None

        # Unarchive messages
        messages = db.query(Message).filter(
            Message.chat_id == chat.id,
            Message.archived_at.isnot(None)
        ).all()

        for message in messages:
            message.archived_at = None
            message.archive_reason = None

        db.commit()

        return {
            "success": True,
            "message": f"Unarchived conversation with {len(messages)} messages"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/archives")
async def get_archived_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of archived conversations
    """
    try:
        offset = (page - 1) * limit

        archived_chats = db.query(Chat).filter(
            Chat.archived_at.isnot(None)
        ).order_by(Chat.archived_at.desc()).offset(offset).limit(limit).all()

        total = db.query(Chat).filter(Chat.archived_at.isnot(None)).count()

        return {
            "success": True,
            "data": [
                {
                    "id": chat.id,
                    "name": chat.name,
                    "archived_at": chat.archived_at.isoformat() if chat.archived_at else None,
                    "archive_reason": chat.archive_reason,
                    "message_count": chat.message_count
                }
                for chat in archived_chats
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Sync Endpoints ====================

@router.post("/sync")
async def sync_messages(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    Sync messages with WhatsApp

    Creates a background task to synchronize messages.
    """
    try:
        # Create sync task
        task = await task_manager.create_task(
            task_type=TaskType.MESSAGE_SYNC,
            chat_id=request.chat_id or "all",
            input_data={
                "chat_id": request.chat_id,
                "mode": request.mode
            },
            priority=TaskPriority.NORMAL.value
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create sync task")

        return {
            "success": True,
            "task_id": task.id,
            "message": f"Sync task created for {request.chat_id or 'all chats'}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status", response_model=List[SyncStatusResponse])
async def get_sync_status(
    chat_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get synchronization status for chats
    """
    try:
        query = db.query(SyncStatus).filter(SyncStatus.entity_type == 'message')

        if chat_id:
            query = query.filter(SyncStatus.entity_id == chat_id)

        sync_records = query.order_by(SyncStatus.last_sync_at.desc()).limit(100).all()

        return [
            SyncStatusResponse(
                entity_id=record.entity_id,
                last_sync_at=record.last_sync_at,
                status=record.sync_status,
                error_message=record.error_message
            )
            for record in sync_records
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Database Cleanup ====================

@router.post("/cleanup")
async def cleanup_database(
    request: CleanupRequest,
    db: Session = Depends(get_db)
):
    """
    Perform database cleanup and maintenance

    Creates a background task to clean up old data and optimize tables.
    """
    try:
        task = await task_manager.create_task(
            task_type=TaskType.DATABASE_CLEANUP,
            chat_id="system",
            input_data={
                "config": {
                    "archive_retention_days": request.archive_retention_days,
                    "optimize_tables": request.optimize_tables,
                    "compress_after_days": request.compress_after_days
                }
            },
            priority=TaskPriority.BACKGROUND.value
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create cleanup task")

        return {
            "success": True,
            "task_id": task.id,
            "message": "Database cleanup task created"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Get database statistics
    """
    try:
        total_chats = db.query(Chat).count()
        total_messages = db.query(Message).count()
        archived_chats = db.query(Chat).filter(Chat.archived_at.isnot(None)).count()
        archived_messages = db.query(Message).filter(Message.archived_at.isnot(None)).count()

        # Get oldest and newest messages
        oldest_msg = db.query(Message).order_by(Message.timestamp.asc()).first()
        newest_msg = db.query(Message).order_by(Message.timestamp.desc()).first()

        # Estimate database size (simplified)
        # In production, you'd query the actual database size
        estimated_size_mb = (total_messages * 1.5 + archived_messages * 0.5) / 1000  # Rough estimate

        return DatabaseStatsResponse(
            total_chats=total_chats,
            total_messages=total_messages,
            archived_chats=archived_chats,
            archived_messages=archived_messages,
            database_size_mb=round(estimated_size_mb, 2),
            oldest_message=oldest_msg.timestamp if oldest_msg else None,
            newest_message=newest_msg.timestamp if newest_msg else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Metadata Management ====================

@router.post("/metadata")
async def update_metadata(
    request: MetadataUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update metadata for a message or chat
    """
    try:
        task = await task_manager.create_task(
            task_type=TaskType.METADATA_UPDATE,
            chat_id="manual",
            input_data={
                "entity_type": request.entity_type,
                "entity_id": request.entity_id,
                "metadata": request.metadata,
                "auto_analyze": request.auto_analyze
            },
            priority=TaskPriority.NORMAL.value
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create metadata update task")

        return {
            "success": True,
            "task_id": task.id,
            "message": f"Metadata update task created for {request.entity_type} {request.entity_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/analyze")
async def analyze_message(
    message_id: str,
    db: Session = Depends(get_db)
):
    """
    Auto-analyze a message (sentiment, category, tags)
    """
    try:
        message = db.query(Message).filter(Message.id == message_id).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        task = await task_manager.create_task(
            task_type=TaskType.METADATA_UPDATE,
            chat_id=message.chat_id,
            message_id=message_id,
            input_data={
                "entity_type": "message",
                "entity_id": message_id,
                "metadata": {},
                "auto_analyze": True
            },
            priority=TaskPriority.NORMAL.value
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create analysis task")

        return {
            "success": True,
            "task_id": task.id,
            "message": "Message analysis task created"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Scheduled Tasks Management ====================

@router.get("/scheduled-tasks")
async def get_scheduled_tasks():
    """
    Get information about scheduled tasks
    """
    try:
        jobs_info = scheduled_tasks_manager.get_next_run_times()

        return {
            "success": True,
            "jobs": jobs_info,
            "scheduler_running": scheduled_tasks_manager._started
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduled-tasks/{job_id}/trigger")
async def trigger_scheduled_task(job_id: str):
    """
    Manually trigger a scheduled task
    """
    try:
        success = scheduled_tasks_manager.trigger_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        return {
            "success": True,
            "message": f"Triggered job: {job_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Task Status ====================

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Get status of a conversation management task
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        import json

        return {
            "success": True,
            "task": {
                "id": task.id,
                "type": task.task_type.value,
                "status": task.status.value,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "output_data": json.loads(task.output_data) if task.output_data else None,
                "error_message": task.error_message
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
