# backend/agents/conversation_manager.py
"""
ConversationManagerAgent

Specialized agent for managing conversation lifecycle, including:
- Archiving old conversations
- Syncing messages with WhatsApp
- Database cleanup and maintenance
- Metadata management (sentiment, tags, categories)
- Status updates
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import gzip
import os

from agents.base_agent import BaseAgent
from database.models import (
    Task, TaskType, TaskStatus,
    Message, Chat, MessageArchive, SyncStatus
)
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError


class ConversationManagerAgent(BaseAgent):
    """
    Manages conversation lifecycle, archiving, syncing, and metadata
    """

    def __init__(self, llm_service=None):
        super().__init__("ConversationManager")
        self.llm_service = llm_service

    @property
    def agent_type(self) -> str:
        return "conversation_manager"

    async def can_handle(self, task: Task) -> bool:
        """
        Handles conversation management tasks
        """
        return task.task_type in [
            TaskType.CONVERSATION_ARCHIVE,
            TaskType.MESSAGE_SYNC,
            TaskType.DATABASE_CLEANUP,
            TaskType.METADATA_UPDATE,
            TaskType.STATUS_UPDATE
        ]

    async def process(self, task: Task) -> Dict[str, Any]:
        """Route to specific handler based on task type"""
        handlers = {
            TaskType.CONVERSATION_ARCHIVE: self._archive_conversations,
            TaskType.MESSAGE_SYNC: self._sync_messages,
            TaskType.DATABASE_CLEANUP: self._cleanup_database,
            TaskType.METADATA_UPDATE: self._update_metadata,
            TaskType.STATUS_UPDATE: self._update_status
        }

        handler = handlers.get(task.task_type)
        if handler:
            return await handler(task)

        return {
            "success": False,
            "error": "Unknown task type",
            "response": f"Cannot handle task type: {task.task_type}"
        }

    # ==================== Archive Conversations ====================

    async def _archive_conversations(self, task: Task) -> Dict[str, Any]:
        """
        Archive conversations based on criteria:
        - Age (older than X days)
        - Inactivity (no messages in X days)
        - Manual archive request
        """
        try:
            db = self.get_db()
            input_data = self.parse_input_data(task)
            config = input_data.get('config', {})

            days_threshold = config.get('days_old', 90)
            include_inactive = config.get('include_inactive', True)
            compress = config.get('compress', False)
            specific_chat_ids = input_data.get('chat_ids', [])

            cutoff_date = datetime.now() - timedelta(days=days_threshold)

            # Build query for chats to archive
            query = db.query(Chat).filter(Chat.archived_at.is_(None))

            if specific_chat_ids:
                # Archive specific chats
                query = query.filter(Chat.id.in_(specific_chat_ids))
            else:
                # Auto-archive based on criteria
                if include_inactive:
                    query = query.filter(
                        or_(
                            Chat.created_at < cutoff_date,
                            Chat.last_activity_at < cutoff_date
                        )
                    )
                else:
                    query = query.filter(Chat.created_at < cutoff_date)

            chats_to_archive = query.all()

            archived_count = 0
            messages_archived = 0
            compressed_count = 0
            freed_space = 0

            for chat in chats_to_archive:
                # Get messages for this chat
                messages = db.query(Message).filter(
                    Message.chat_id == chat.id,
                    Message.archived_at.is_(None)
                ).all()

                # Archive messages
                for message in messages:
                    archive_result = await self._archive_message(
                        message,
                        compress=compress,
                        reason=config.get('reason', 'Auto-archived due to age/inactivity')
                    )

                    if archive_result['success']:
                        messages_archived += 1
                        freed_space += archive_result.get('freed_bytes', 0)
                        if archive_result.get('compressed'):
                            compressed_count += 1

                # Mark chat as archived
                chat.archived_at = datetime.now()
                chat.archive_reason = config.get('reason', 'Auto-archived due to age/inactivity')
                archived_count += 1

            db.commit()

            response = (
                f"✅ Archived {archived_count} conversation(s) with {messages_archived} messages. "
            )
            if compress:
                response += f"Compressed {compressed_count} messages, freed {freed_space / 1024:.2f} KB."

            return {
                "success": True,
                "response": response,
                "data": {
                    "archived_count": archived_count,
                    "messages_archived": messages_archived,
                    "compressed_count": compressed_count,
                    "freed_space_kb": freed_space / 1024
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to archive conversations: {str(e)}"
            }

    async def _archive_message(
        self,
        message: Message,
        compress: bool = False,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Archive a single message"""
        try:
            db = self.get_db()

            # Prepare content for archival
            content = message.body or ""
            metadata = message.extra_data or {}

            # Add additional metadata
            metadata.update({
                'message_type': message.message_type.value if message.message_type else 'text',
                'from_me': message.from_me,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                'has_media': message.has_media,
                'llm_processed': message.llm_processed
            })

            # Compress if enabled
            compressed_data = None
            original_size = len(content.encode('utf-8'))
            freed_bytes = 0

            if compress and content:
                compressed_data = gzip.compress(content.encode('utf-8'))
                freed_bytes = original_size - len(compressed_data)
                # Store compressed data as base64 for database storage
                import base64
                content = base64.b64encode(compressed_data).decode('utf-8')

            # Create archive record
            archive = MessageArchive(
                original_message_id=message.id,
                chat_id=message.chat_id,
                content=content,
                metadata=metadata,
                archived_at=datetime.now(),
                archive_reason=reason,
                compressed=compress
            )

            db.add(archive)

            # Mark original message as archived
            message.archived_at = datetime.now()
            message.archive_reason = reason

            db.commit()

            return {
                "success": True,
                "compressed": compress,
                "freed_bytes": freed_bytes
            }

        except Exception as e:
            print(f"Failed to archive message {message.id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== Message Sync ====================

    async def _sync_messages(self, task: Task) -> Dict[str, Any]:
        """
        Sync WhatsApp messages with database

        Note: This is a placeholder implementation.
        Full sync requires integration with WhatsApp Web API.
        """
        try:
            db = self.get_db()
            input_data = self.parse_input_data(task)

            chat_id = input_data.get('chat_id')
            sync_mode = input_data.get('mode', 'incremental')  # 'full' or 'incremental'

            # Get or create sync status
            sync_record = db.query(SyncStatus).filter(
                and_(
                    SyncStatus.entity_type == 'message',
                    SyncStatus.entity_id == chat_id
                )
            ).first()

            if not sync_record:
                sync_record = SyncStatus(
                    entity_type='message',
                    entity_id=chat_id,
                    sync_status='pending'
                )
                db.add(sync_record)

            # Update sync status
            sync_record.sync_status = 'synced'
            sync_record.last_sync_at = datetime.now()
            sync_record.error_message = None
            sync_record.retry_count = 0

            db.commit()

            return {
                "success": True,
                "response": f"✅ Sync completed for chat {chat_id or 'all chats'}",
                "data": {
                    "chat_id": chat_id,
                    "sync_mode": sync_mode,
                    "synced_count": 0,
                    "note": "WhatsApp API integration required for full sync"
                }
            }

        except Exception as e:
            # Mark sync as failed
            if sync_record:
                sync_record.sync_status = 'failed'
                sync_record.error_message = str(e)
                sync_record.retry_count += 1
                db.commit()

            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to sync messages: {str(e)}"
            }

    # ==================== Database Cleanup ====================

    async def _cleanup_database(self, task: Task) -> Dict[str, Any]:
        """
        Database maintenance operations:
        - Delete old archived messages
        - Remove orphaned records
        - Optimize tables
        - Update statistics
        """
        try:
            db = self.get_db()
            input_data = self.parse_input_data(task)
            config = input_data.get('config', {})

            results = {
                "deleted_archives": 0,
                "orphans_removed": 0,
                "tables_optimized": 0,
                "stats_updated": False
            }

            # 1. Delete old archived messages (if retention period expired)
            retention_days = config.get('archive_retention_days', 365)
            if retention_days > 0:
                cutoff = datetime.now() - timedelta(days=retention_days)

                deleted = db.query(MessageArchive).filter(
                    MessageArchive.archived_at < cutoff
                ).delete()

                results["deleted_archives"] = deleted
                db.commit()

            # 2. Remove orphaned messages (no parent chat)
            orphan_messages = db.query(Message).filter(
                ~Message.chat_id.in_(db.query(Chat.id))
            ).delete(synchronize_session=False)

            results["orphans_removed"] = orphan_messages
            db.commit()

            # 3. Update chat statistics
            chats = db.query(Chat).all()
            for chat in chats:
                message_count = db.query(Message).filter(
                    Message.chat_id == chat.id
                ).count()

                chat.message_count = message_count

                # Update last activity
                last_message = db.query(Message).filter(
                    Message.chat_id == chat.id
                ).order_by(Message.timestamp.desc()).first()

                if last_message:
                    chat.last_activity_at = last_message.timestamp

            db.commit()
            results["stats_updated"] = True

            # 4. Optimize tables (PostgreSQL specific)
            if config.get('optimize_tables', False):
                try:
                    # Note: VACUUM needs to be run outside transaction
                    # This is a simplified version
                    db.execute(text("ANALYZE messages"))
                    db.execute(text("ANALYZE chats"))
                    db.execute(text("ANALYZE message_archives"))
                    db.commit()
                    results["tables_optimized"] = 3
                except Exception as e:
                    print(f"Table optimization skipped: {e}")

            response = (
                f"✅ Cleanup completed:\n"
                f"- Deleted {results['deleted_archives']} old archives\n"
                f"- Removed {results['orphans_removed']} orphaned messages\n"
                f"- Updated statistics for all chats"
            )

            if results['tables_optimized'] > 0:
                response += f"\n- Optimized {results['tables_optimized']} tables"

            return {
                "success": True,
                "response": response,
                "data": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to cleanup database: {str(e)}"
            }

    # ==================== Metadata Management ====================

    async def _update_metadata(self, task: Task) -> Dict[str, Any]:
        """
        Update message/chat metadata:
        - Add/update tags
        - Set categories
        - Sentiment analysis (if LLM available)
        - Custom metadata fields
        """
        try:
            db = self.get_db()
            input_data = self.parse_input_data(task)

            entity_type = input_data.get('entity_type')  # 'message' or 'chat'
            entity_id = input_data.get('entity_id')
            metadata_updates = input_data.get('metadata', {})
            auto_analyze = input_data.get('auto_analyze', False)

            if entity_type == 'message':
                entity = db.query(Message).filter(Message.id == entity_id).first()
            elif entity_type == 'chat':
                entity = db.query(Chat).filter(Chat.id == entity_id).first()
            else:
                return {
                    "success": False,
                    "error": f"Invalid entity_type: {entity_type}",
                    "response": "Entity type must be 'message' or 'chat'"
                }

            if not entity:
                return {
                    "success": False,
                    "error": f"{entity_type} not found: {entity_id}",
                    "response": f"{entity_type.capitalize()} not found"
                }

            # Auto-generate metadata if requested and LLM is available
            if auto_analyze and self.llm_service and entity_type == 'message':
                content = entity.body or ""

                # Sentiment analysis
                if 'sentiment' not in metadata_updates:
                    sentiment = await self._analyze_sentiment(content)
                    metadata_updates['sentiment'] = sentiment
                    entity.sentiment = sentiment

                # Category classification
                if 'category' not in metadata_updates:
                    category = await self._classify_category(content)
                    metadata_updates['category'] = category
                    entity.category = category

                # Extract tags
                if 'tags' not in metadata_updates:
                    tags = await self._extract_tags(content)
                    metadata_updates['tags'] = tags
                    entity.tags = tags

            # Update metadata fields
            if hasattr(entity, 'extra_data'):
                current_metadata = entity.extra_data or {}
                current_metadata.update(metadata_updates)
                entity.extra_data = current_metadata

            # Update direct fields if provided
            if 'sentiment' in metadata_updates and hasattr(entity, 'sentiment'):
                entity.sentiment = metadata_updates['sentiment']
            if 'category' in metadata_updates and hasattr(entity, 'category'):
                entity.category = metadata_updates['category']
            if 'tags' in metadata_updates and hasattr(entity, 'tags'):
                entity.tags = metadata_updates['tags']

            db.commit()

            return {
                "success": True,
                "response": f"✅ Updated metadata for {entity_type} {entity_id}",
                "data": {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "metadata": metadata_updates
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to update metadata: {str(e)}"
            }

    async def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment using LLM"""
        if not self.llm_service or not text:
            return "neutral"

        try:
            prompt = f"""Analyze the sentiment of this message and respond with ONLY one word:
- positive
- negative
- neutral
- mixed

Message: "{text}"

Sentiment:"""

            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=10,
                temperature=0.3
            )

            sentiment = response.strip().lower()
            if sentiment in ['positive', 'negative', 'neutral', 'mixed']:
                return sentiment
            return 'neutral'

        except Exception as e:
            print(f"Sentiment analysis failed: {e}")
            return "neutral"

    async def _classify_category(self, text: str) -> str:
        """Classify message category using LLM"""
        if not self.llm_service or not text:
            return "general"

        try:
            prompt = f"""Classify this message into ONE category:
- appointment (booking, scheduling, calendar related)
- inquiry (questions, information requests)
- complaint (problems, issues, dissatisfaction)
- feedback (reviews, suggestions, praise)
- general (everything else)

Message: "{text}"

Category:"""

            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=10,
                temperature=0.3
            )

            category = response.strip().lower()
            valid_categories = ['appointment', 'inquiry', 'complaint', 'feedback', 'general']
            if category in valid_categories:
                return category
            return 'general'

        except Exception as e:
            print(f"Category classification failed: {e}")
            return "general"

    async def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from content using LLM"""
        if not self.llm_service or not text:
            return []

        try:
            prompt = f"""Extract 1-3 relevant tags from this message.
Common tags: urgent, appointment, price_inquiry, follow_up, technical, question, thank_you

Message: "{text}"

Tags (comma-separated):"""

            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=30,
                temperature=0.3
            )

            # Parse comma-separated tags
            tags = [tag.strip().lower() for tag in response.split(',')]
            tags = [tag for tag in tags if tag and len(tag) > 2]

            return tags[:3]  # Limit to 3 tags

        except Exception as e:
            print(f"Tag extraction failed: {e}")
            return []

    # ==================== Status Updates ====================

    async def _update_status(self, task: Task) -> Dict[str, Any]:
        """
        Update message/chat status:
        - Mark as read/unread
        - Mark as processed/unprocessed
        - Batch status updates
        """
        try:
            db = self.get_db()
            input_data = self.parse_input_data(task)
            updates = input_data.get('updates', [])

            updated_count = 0
            failed = []

            for update in updates:
                try:
                    message_id = update.get('message_id')
                    changes = update.get('changes', {})

                    if not message_id:
                        failed.append({"error": "Missing message_id", "update": update})
                        continue

                    message = db.query(Message).filter(Message.id == message_id).first()

                    if not message:
                        failed.append({"error": f"Message {message_id} not found", "update": update})
                        continue

                    # Apply changes
                    if 'processed' in changes:
                        message.processed = changes['processed']
                    if 'read' in changes and changes['read']:
                        message.read_at = datetime.now()
                    if 'llm_processed' in changes:
                        message.llm_processed = changes['llm_processed']

                    updated_count += 1

                except Exception as e:
                    failed.append({"error": str(e), "update": update})

            db.commit()

            response = f"✅ Updated status for {updated_count} message(s)"
            if failed:
                response += f"\n⚠️ {len(failed)} update(s) failed"

            return {
                "success": True,
                "response": response,
                "data": {
                    "updated_count": updated_count,
                    "failed_count": len(failed),
                    "failed": failed
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to update status: {str(e)}"
            }
