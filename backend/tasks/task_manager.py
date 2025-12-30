# backend/tasks/task_manager.py
"""
Task Manager

Central service for managing tasks in the agentic system:
- Create and queue tasks
- Route tasks to appropriate agents
- Monitor task execution
- Handle task failures and retries
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from database.database import SessionLocal
from database.models import Task, TaskType, TaskStatus, TaskPriority, Message, Chat


class TaskManager:
    """
    Manages the lifecycle of tasks in the agentic system
    """

    def __init__(self):
        self.db = None
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False

    def get_db(self):
        """Get database session"""
        if not self.db:
            self.db = SessionLocal()
        return self.db

    def close_db(self):
        """Close database session"""
        if self.db:
            self.db.close()
            self.db = None

    async def create_task(
        self,
        task_type: TaskType,
        chat_id: str,
        message_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        priority: int = TaskPriority.NORMAL.value,
        deadline: Optional[datetime] = None
    ) -> Optional[Task]:
        """
        Create a new task

        Args:
            task_type: Type of task to create
            chat_id: WhatsApp chat ID
            message_id: Optional message ID that triggered this task
            input_data: Input data for the task (will be stored as JSON)
            priority: Task priority (1-10, lower is higher priority)
            deadline: Optional deadline for task completion

        Returns:
            Created Task object or None if failed
        """
        db = self.get_db()

        try:
            # Prepare input data
            input_json = json.dumps(input_data) if input_data else None

            # Create task
            task = Task(
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                chat_id=chat_id,
                message_id=message_id,
                input_data=input_json,
                deadline=deadline
            )

            db.add(task)
            db.commit()
            db.refresh(task)

            print(f"📋 Created task #{task.id}: {task_type.value} (priority: {priority})")

            # Add to queue for processing
            await self.task_queue.put(task.id)

            return task

        except Exception as e:
            print(f"❌ Failed to create task: {e}")
            db.rollback()
            return None
        finally:
            self.close_db()

    async def create_task_from_message(
        self,
        message_data: Dict[str, Any],
        task_type: TaskType = TaskType.TRIAGE,
        priority: int = TaskPriority.NORMAL.value
    ) -> Optional[Task]:
        """
        Create a task from an incoming WhatsApp message

        Args:
            message_data: Message data from WhatsApp
            task_type: Type of task (defaults to TRIAGE)
            priority: Task priority

        Returns:
            Created Task object or None
        """
        chat_id = message_data.get('chatId')
        message_id = message_data.get('id')

        if not chat_id:
            print("❌ Cannot create task: missing chat_id")
            return None

        # Build comprehensive input data
        input_data = {
            'message': message_data.get('body', ''),
            'from_me': message_data.get('fromMe', False),
            'timestamp': message_data.get('timestamp'),
            'has_media': message_data.get('hasMedia', False),
            'message_type': message_data.get('type', 'text'),
            'raw_data': message_data
        }

        return await self.create_task(
            task_type=task_type,
            chat_id=chat_id,
            message_id=message_id,
            input_data=input_data,
            priority=priority
        )

    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get a task by ID

        Args:
            task_id: Task ID

        Returns:
            Task object or None
        """
        db = self.get_db()
        try:
            return db.query(Task).filter(Task.id == task_id).first()
        finally:
            self.close_db()

    async def get_pending_tasks(
        self,
        limit: int = 10,
        task_type: Optional[TaskType] = None
    ) -> List[Task]:
        """
        Get pending tasks sorted by priority

        Args:
            limit: Maximum number of tasks to return
            task_type: Optional filter by task type

        Returns:
            List of pending tasks
        """
        db = self.get_db()
        try:
            query = db.query(Task).filter(Task.status == TaskStatus.PENDING)

            if task_type:
                query = query.filter(Task.task_type == task_type)

            tasks = query.order_by(Task.priority.asc(), Task.created_at.asc()).limit(limit).all()
            return tasks
        finally:
            self.close_db()

    async def get_tasks_by_chat(
        self,
        chat_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Task]:
        """
        Get tasks for a specific chat

        Args:
            chat_id: Chat ID
            status: Optional status filter
            limit: Maximum number of tasks

        Returns:
            List of tasks
        """
        db = self.get_db()
        try:
            query = db.query(Task).filter(Task.chat_id == chat_id)

            if status:
                query = query.filter(Task.status == status)

            tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
            return tasks
        finally:
            self.close_db()

    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update task status and output

        Args:
            task_id: Task ID
            status: New status
            output_data: Optional output data
            error_message: Optional error message

        Returns:
            True if updated successfully
        """
        db = self.get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()

            if not task:
                return False

            task.status = status

            if output_data:
                task.output_data = json.dumps(output_data)

            if error_message:
                task.error_message = error_message

            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()

            db.commit()
            return True

        except Exception as e:
            print(f"❌ Failed to update task status: {e}")
            db.rollback()
            return False
        finally:
            self.close_db()

    async def retry_failed_task(self, task_id: int) -> bool:
        """
        Retry a failed task

        Args:
            task_id: Task ID

        Returns:
            True if retry was scheduled
        """
        db = self.get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()

            if not task or task.status != TaskStatus.FAILED:
                return False

            if task.retry_count >= task.max_retries:
                print(f"⚠️ Task #{task_id} exceeded max retries ({task.max_retries})")
                return False

            # Reset task for retry
            task.status = TaskStatus.PENDING
            task.retry_count += 1
            task.error_message = None
            task.started_at = None
            task.completed_at = None

            db.commit()

            # Re-queue the task
            await self.task_queue.put(task_id)

            print(f"🔄 Retrying task #{task_id} (attempt {task.retry_count + 1}/{task.max_retries})")
            return True

        except Exception as e:
            print(f"❌ Failed to retry task: {e}")
            db.rollback()
            return False
        finally:
            self.close_db()

    async def cancel_task(self, task_id: int, reason: str = "") -> bool:
        """
        Cancel a task

        Args:
            task_id: Task ID
            reason: Cancellation reason

        Returns:
            True if cancelled successfully
        """
        db = self.get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()

            if not task:
                return False

            task.status = TaskStatus.CANCELLED
            task.error_message = f"Cancelled: {reason}" if reason else "Cancelled by user"
            task.completed_at = datetime.now()

            db.commit()

            print(f"🚫 Cancelled task #{task_id}: {reason}")
            return True

        except Exception as e:
            print(f"❌ Failed to cancel task: {e}")
            db.rollback()
            return False
        finally:
            self.close_db()

    async def get_task_stats(self) -> Dict[str, Any]:
        """
        Get task statistics

        Returns:
            Dictionary with task stats
        """
        db = self.get_db()
        try:
            total = db.query(Task).count()
            pending = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
            in_progress = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
            completed = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
            failed = db.query(Task).filter(Task.status == TaskStatus.FAILED).count()

            # Get average completion time for completed tasks
            completed_tasks = db.query(Task).filter(
                Task.status == TaskStatus.COMPLETED,
                Task.started_at.isnot(None),
                Task.completed_at.isnot(None)
            ).all()

            avg_duration = 0
            if completed_tasks:
                durations = [
                    (t.completed_at - t.started_at).total_seconds()
                    for t in completed_tasks
                ]
                avg_duration = sum(durations) / len(durations)

            return {
                'total': total,
                'pending': pending,
                'in_progress': in_progress,
                'completed': completed,
                'failed': failed,
                'cancelled': db.query(Task).filter(Task.status == TaskStatus.CANCELLED).count(),
                'avg_completion_seconds': round(avg_duration, 2),
                'queue_size': self.task_queue.qsize()
            }

        finally:
            self.close_db()

    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        Clean up old completed/failed tasks

        Args:
            days: Delete tasks older than this many days

        Returns:
            Number of tasks deleted
        """
        db = self.get_db()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            deleted = db.query(Task).filter(
                Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]),
                Task.created_at < cutoff_date
            ).delete()

            db.commit()

            print(f"🧹 Cleaned up {deleted} old tasks (older than {days} days)")
            return deleted

        except Exception as e:
            print(f"❌ Failed to cleanup tasks: {e}")
            db.rollback()
            return 0
        finally:
            self.close_db()
