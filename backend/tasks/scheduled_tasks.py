# backend/tasks/scheduled_tasks.py
"""
Scheduled Tasks for Conversation Manager

Manages periodic background tasks:
- Auto-archive old conversations
- Auto-sync messages with WhatsApp
- Database cleanup and maintenance
- Metadata updates
"""

import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from tasks.task_manager import TaskManager
from database.models import TaskType, TaskPriority
from core.config import settings


class ScheduledTasksManager:
    """
    Manages scheduled background tasks for the conversation manager
    """

    def __init__(self, task_manager: TaskManager = None):
        self.task_manager = task_manager or TaskManager()
        self.scheduler = AsyncIOScheduler()
        self._started = False

    def start(self):
        """Start the scheduler with all configured tasks"""
        if self._started:
            print("⚠️ Scheduler already started")
            return

        print("🕐 Starting scheduled tasks manager...")

        # Register all scheduled jobs
        self._register_archive_task()
        self._register_sync_task()
        self._register_cleanup_task()
        self._register_metadata_task()

        # Start the scheduler
        self.scheduler.start()
        self._started = True

        print("✅ Scheduled tasks manager started")
        print(f"📋 Active jobs: {len(self.scheduler.get_jobs())}")

    def stop(self):
        """Stop the scheduler"""
        if not self._started:
            return

        print("🛑 Stopping scheduled tasks manager...")
        self.scheduler.shutdown(wait=False)
        self._started = False
        print("✅ Scheduled tasks manager stopped")

    def _register_archive_task(self):
        """Register auto-archive task"""
        if not settings.ARCHIVE_ENABLED:
            print("ℹ️ Auto-archive is disabled")
            return

        # Parse cleanup run time (HH:MM format)
        try:
            hour, minute = map(int, settings.CLEANUP_RUN_TIME.split(':'))
        except:
            hour, minute = 3, 0  # Default to 3 AM

        # Run daily at specified time
        self.scheduler.add_job(
            self.auto_archive_conversations,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='auto_archive',
            name='Auto-archive old conversations',
            replace_existing=True
        )

        print(f"📦 Auto-archive scheduled: Daily at {hour:02d}:{minute:02d}")

    def _register_sync_task(self):
        """Register auto-sync task"""
        if not settings.SYNC_ENABLED:
            print("ℹ️ Auto-sync is disabled")
            return

        # Run at specified interval
        interval_minutes = settings.AUTO_SYNC_INTERVAL_MINUTES

        self.scheduler.add_job(
            self.auto_sync_messages,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='auto_sync',
            name='Auto-sync messages',
            replace_existing=True
        )

        print(f"🔄 Auto-sync scheduled: Every {interval_minutes} minutes")

    def _register_cleanup_task(self):
        """Register database cleanup task"""
        if not settings.CLEANUP_ENABLED:
            print("ℹ️ Database cleanup is disabled")
            return

        # Parse cleanup run time (HH:MM format)
        try:
            hour, minute = map(int, settings.CLEANUP_RUN_TIME.split(':'))
            # Offset by 1 hour before archive time
            hour = (hour - 1) % 24
        except:
            hour, minute = 2, 0  # Default to 2 AM

        # Run daily at specified time
        self.scheduler.add_job(
            self.auto_cleanup_database,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='auto_cleanup',
            name='Database cleanup',
            replace_existing=True
        )

        print(f"🧹 Database cleanup scheduled: Daily at {hour:02d}:{minute:02d}")

    def _register_metadata_task(self):
        """Register metadata update task"""
        if not settings.AUTO_SENTIMENT_ANALYSIS and not settings.AUTO_CATEGORIZATION:
            print("ℹ️ Auto-metadata updates are disabled")
            return

        # Run weekly on Sunday at 4 AM
        self.scheduler.add_job(
            self.auto_update_metadata,
            trigger=CronTrigger(day_of_week='sun', hour=4, minute=0),
            id='auto_metadata',
            name='Auto-update metadata',
            replace_existing=True
        )

        print("🏷️ Metadata updates scheduled: Weekly on Sunday at 04:00")

    # ==================== Scheduled Task Handlers ====================

    async def auto_archive_conversations(self):
        """
        Scheduled task: Archive old conversations
        """
        print(f"\n📦 [SCHEDULED] Running auto-archive task at {datetime.now()}")

        try:
            # Create archive task
            task = await self.task_manager.create_task(
                task_type=TaskType.CONVERSATION_ARCHIVE,
                chat_id="system",  # System task, not tied to specific chat
                input_data={
                    "config": {
                        "days_old": settings.AUTO_ARCHIVE_AFTER_DAYS,
                        "include_inactive": True,
                        "compress": settings.COMPRESS_ARCHIVES,
                        "reason": "Scheduled auto-archive"
                    }
                },
                priority=TaskPriority.BACKGROUND.value
            )

            if task:
                print(f"✅ [SCHEDULED] Archive task created: #{task.id}")
            else:
                print("❌ [SCHEDULED] Failed to create archive task")

        except Exception as e:
            print(f"❌ [SCHEDULED] Auto-archive error: {e}")

    async def auto_sync_messages(self):
        """
        Scheduled task: Sync messages with WhatsApp
        """
        print(f"\n🔄 [SCHEDULED] Running auto-sync task at {datetime.now()}")

        try:
            # Create sync task for all chats
            task = await self.task_manager.create_task(
                task_type=TaskType.MESSAGE_SYNC,
                chat_id="system",
                input_data={
                    "chat_id": None,  # Sync all chats
                    "mode": "incremental"
                },
                priority=TaskPriority.NORMAL.value
            )

            if task:
                print(f"✅ [SCHEDULED] Sync task created: #{task.id}")
            else:
                print("❌ [SCHEDULED] Failed to create sync task")

        except Exception as e:
            print(f"❌ [SCHEDULED] Auto-sync error: {e}")

    async def auto_cleanup_database(self):
        """
        Scheduled task: Database cleanup and maintenance
        """
        print(f"\n🧹 [SCHEDULED] Running database cleanup at {datetime.now()}")

        try:
            # Create cleanup task
            task = await self.task_manager.create_task(
                task_type=TaskType.DATABASE_CLEANUP,
                chat_id="system",
                input_data={
                    "config": {
                        "archive_retention_days": settings.ARCHIVE_RETENTION_DAYS,
                        "compress_after_days": settings.COMPRESS_AFTER_DAYS,
                        "optimize_tables": settings.OPTIMIZE_TABLES
                    }
                },
                priority=TaskPriority.BACKGROUND.value
            )

            if task:
                print(f"✅ [SCHEDULED] Cleanup task created: #{task.id}")
            else:
                print("❌ [SCHEDULED] Failed to create cleanup task")

        except Exception as e:
            print(f"❌ [SCHEDULED] Database cleanup error: {e}")

    async def auto_update_metadata(self):
        """
        Scheduled task: Update message/chat metadata
        """
        print(f"\n🏷️ [SCHEDULED] Running metadata update at {datetime.now()}")

        try:
            # Create metadata update task
            # Note: This will process messages in batches
            task = await self.task_manager.create_task(
                task_type=TaskType.METADATA_UPDATE,
                chat_id="system",
                input_data={
                    "entity_type": "message",
                    "auto_analyze": True,
                    "batch_mode": True
                },
                priority=TaskPriority.LOW.value
            )

            if task:
                print(f"✅ [SCHEDULED] Metadata update task created: #{task.id}")
            else:
                print("❌ [SCHEDULED] Failed to create metadata update task")

        except Exception as e:
            print(f"❌ [SCHEDULED] Metadata update error: {e}")

    def get_next_run_times(self):
        """Get next run times for all scheduled jobs"""
        jobs_info = []

        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time

            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': next_run.isoformat() if next_run else None
            })

        return jobs_info

    def trigger_job(self, job_id: str):
        """Manually trigger a scheduled job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                print(f"✅ Triggered job: {job_id}")
                return True
            else:
                print(f"❌ Job not found: {job_id}")
                return False
        except Exception as e:
            print(f"❌ Failed to trigger job {job_id}: {e}")
            return False


# Global instance
scheduled_tasks_manager = ScheduledTasksManager()


def start_scheduled_tasks():
    """Start the scheduled tasks manager (call this on app startup)"""
    scheduled_tasks_manager.start()


def stop_scheduled_tasks():
    """Stop the scheduled tasks manager (call this on app shutdown)"""
    scheduled_tasks_manager.stop()
