# ConversationManagerAgent - Detailed Design

## Overview

The ConversationManagerAgent is a specialized agent responsible for database maintenance, conversation archiving, message syncing, and metadata management for the WhatsApp Secretary system.

---

## 1. Database Schema Changes

### 1.1 Messages Table - New Fields

```sql
ALTER TABLE messages ADD COLUMN:
- archived_at TIMESTAMP NULL
- archive_reason VARCHAR(255) NULL
- processed BOOLEAN DEFAULT FALSE
- read_at TIMESTAMP NULL
- metadata JSONB DEFAULT '{}'
- last_synced_at TIMESTAMP NULL
- sentiment VARCHAR(50) NULL  -- positive, neutral, negative, mixed
- category VARCHAR(100) NULL
- tags TEXT[]  -- Array of tags
```

### 1.2 Chats Table - New Fields

```sql
ALTER TABLE chats ADD COLUMN:
- archived_at TIMESTAMP NULL
- archive_reason VARCHAR(255) NULL
- last_activity_at TIMESTAMP NULL
- message_count INTEGER DEFAULT 0
- unread_count INTEGER DEFAULT 0
- metadata JSONB DEFAULT '{}'
- auto_archive_after_days INTEGER DEFAULT 90
```

### 1.3 New Table: message_archives

```sql
CREATE TABLE message_archives (
    id SERIAL PRIMARY KEY,
    original_message_id INTEGER REFERENCES messages(id),
    chat_id VARCHAR(255),
    content TEXT,
    metadata JSONB,
    archived_at TIMESTAMP DEFAULT NOW(),
    archive_reason VARCHAR(255),
    compressed BOOLEAN DEFAULT FALSE,
    storage_path VARCHAR(500)  -- For external storage if needed
);

CREATE INDEX idx_archives_chat ON message_archives(chat_id);
CREATE INDEX idx_archives_date ON message_archives(archived_at);
```

### 1.4 New Table: sync_status

```sql
CREATE TABLE sync_status (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),  -- 'message', 'chat', 'contact'
    entity_id VARCHAR(255),
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(50),  -- 'synced', 'pending', 'failed'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sync_entity ON sync_status(entity_type, entity_id);
CREATE INDEX idx_sync_status ON sync_status(sync_status);
```

---

## 2. ConversationManagerAgent Implementation

### 2.1 Agent Structure

```python
class ConversationManagerAgent(BaseAgent):
    """
    Manages conversation lifecycle, archiving, syncing, and metadata.
    """

    @property
    def agent_type(self) -> str:
        return "conversation_manager"

    async def can_handle(self, task: Task) -> bool:
        """
        Handles tasks related to:
        - CONVERSATION_ARCHIVE
        - MESSAGE_SYNC
        - DATABASE_CLEANUP
        - METADATA_UPDATE
        - STATUS_UPDATE
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

        return {"success": False, "error": "Unknown task type"}
```

### 2.2 Feature Implementations

#### Feature 1: Archive Old Conversations

```python
async def _archive_conversations(self, task: Task) -> Dict[str, Any]:
    """
    Archive conversations based on criteria:
    - Age (older than X days)
    - Inactivity (no messages in X days)
    - Manual archive request
    - Completed status
    """
    config = task.input_data.get('config', {})
    days_threshold = config.get('days_old', 90)
    include_inactive = config.get('include_inactive', True)

    # Find conversations to archive
    cutoff_date = datetime.now() - timedelta(days=days_threshold)

    query = """
        SELECT c.id, c.chat_id, COUNT(m.id) as msg_count
        FROM chats c
        LEFT JOIN messages m ON m.chat_id = c.id
        WHERE c.archived_at IS NULL
        AND (
            c.created_at < :cutoff_date
            OR c.last_activity_at < :cutoff_date
        )
        GROUP BY c.id, c.chat_id
    """

    # Archive logic:
    # 1. Move messages to message_archives table
    # 2. Compress if enabled
    # 3. Update chat.archived_at
    # 4. Optional: Delete from main table if config allows

    return {
        "success": True,
        "archived_count": archived_count,
        "compressed_count": compressed_count,
        "freed_space_mb": freed_space
    }
```

#### Feature 2: Update Message Status

```python
async def _update_status(self, task: Task) -> Dict[str, Any]:
    """
    Update message/chat status:
    - Mark as read/unread
    - Mark as processed/unprocessed
    - Update delivery status
    - Batch status updates
    """
    updates = task.input_data.get('updates', [])

    # Support batch updates
    for update in updates:
        message_id = update.get('message_id')
        status_changes = update.get('changes', {})

        # Update fields like:
        # - processed = True
        # - read_at = NOW()
        # - delivery_status = 'delivered'

    return {
        "success": True,
        "updated_count": len(updates),
        "failed": failed_updates
    }
```

#### Feature 3: Sync Conversation History

```python
async def _sync_messages(self, task: Task) -> Dict[str, Any]:
    """
    Sync WhatsApp messages with database:
    - Fetch new messages from WhatsApp
    - Compare with database
    - Insert missing messages
    - Update modified messages
    - Track sync status
    """
    chat_id = task.input_data.get('chat_id')
    sync_mode = task.input_data.get('mode', 'incremental')  # 'full' or 'incremental'

    # Get last sync timestamp
    last_sync = await self._get_last_sync(chat_id)

    # Fetch messages from WhatsApp API
    # (Integration with whatsapp_service.py)
    whatsapp_messages = await self._fetch_whatsapp_messages(
        chat_id,
        since=last_sync if sync_mode == 'incremental' else None
    )

    # Compare and sync
    synced = 0
    errors = []

    for wa_msg in whatsapp_messages:
        try:
            # Check if exists in DB
            existing = await self._get_message_by_wa_id(wa_msg['id'])

            if existing:
                # Update if modified
                if self._has_changes(existing, wa_msg):
                    await self._update_message(existing, wa_msg)
                    synced += 1
            else:
                # Insert new
                await self._insert_message(wa_msg)
                synced += 1

        except Exception as e:
            errors.append({"msg_id": wa_msg['id'], "error": str(e)})

    # Update sync status
    await self._update_sync_status(chat_id, 'synced')

    return {
        "success": True,
        "synced_count": synced,
        "errors": errors,
        "sync_mode": sync_mode
    }
```

#### Feature 4: Database Cleanup & Maintenance

```python
async def _cleanup_database(self, task: Task) -> Dict[str, Any]:
    """
    Database maintenance operations:
    - Delete messages older than retention period
    - Remove orphaned records
    - Optimize tables (VACUUM)
    - Update statistics
    - Rebuild indexes
    - Compress old data
    """
    config = task.input_data.get('config', {})

    results = {
        "deleted_messages": 0,
        "deleted_archives": 0,
        "orphans_removed": 0,
        "tables_optimized": 0,
        "space_freed_mb": 0
    }

    # 1. Delete old archived messages (if retention period expired)
    retention_days = config.get('archive_retention_days', 365)
    cutoff = datetime.now() - timedelta(days=retention_days)

    deleted = await self.db.execute(
        "DELETE FROM message_archives WHERE archived_at < :cutoff",
        {"cutoff": cutoff}
    )
    results["deleted_archives"] = deleted.rowcount

    # 2. Remove orphaned messages (no parent chat)
    orphans = await self.db.execute(
        "DELETE FROM messages WHERE chat_id NOT IN (SELECT id FROM chats)"
    )
    results["orphans_removed"] = orphans.rowcount

    # 3. Compress old messages (move to compressed storage)
    compress_older_than = config.get('compress_after_days', 30)
    compressed = await self._compress_old_messages(compress_older_than)
    results["compressed_count"] = compressed

    # 4. Database optimization
    if config.get('optimize_tables', False):
        await self.db.execute("VACUUM ANALYZE messages")
        await self.db.execute("VACUUM ANALYZE chats")
        results["tables_optimized"] = 2

    # 5. Update statistics
    await self._update_chat_statistics()

    return {
        "success": True,
        **results
    }
```

#### Feature 5: Metadata Management

```python
async def _update_metadata(self, task: Task) -> Dict[str, Any]:
    """
    Update message/chat metadata:
    - Add/update tags
    - Set categories
    - Sentiment analysis
    - AI-generated summaries
    - Custom metadata fields
    """
    entity_type = task.input_data.get('entity_type')  # 'message' or 'chat'
    entity_id = task.input_data.get('entity_id')
    metadata_updates = task.input_data.get('metadata', {})

    # Auto-generate metadata if requested
    if metadata_updates.get('auto_analyze', False):
        content = await self._get_entity_content(entity_type, entity_id)

        # Sentiment analysis
        sentiment = await self._analyze_sentiment(content)
        metadata_updates['sentiment'] = sentiment

        # Category classification
        category = await self._classify_category(content)
        metadata_updates['category'] = category

        # Auto-tagging
        tags = await self._extract_tags(content)
        metadata_updates['tags'] = tags

        # Summary (for chats)
        if entity_type == 'chat':
            summary = await self._generate_summary(content)
            metadata_updates['summary'] = summary

    # Update metadata JSON field
    await self._update_entity_metadata(entity_type, entity_id, metadata_updates)

    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metadata": metadata_updates
    }

async def _analyze_sentiment(self, text: str) -> str:
    """Use LLM to analyze sentiment"""
    # Integration with llm_service.py
    # Returns: 'positive', 'negative', 'neutral', 'mixed'
    pass

async def _classify_category(self, text: str) -> str:
    """Classify message category"""
    # Categories: appointment, inquiry, complaint, feedback, general
    pass

async def _extract_tags(self, text: str) -> List[str]:
    """Extract relevant tags from content"""
    # Returns: ['urgent', 'appointment', 'price_inquiry', etc.]
    pass
```

---

## 3. Configuration & Settings

### 3.1 Configuration File: `config/conversation_manager.yaml`

```yaml
conversation_manager:
  # Archive settings
  archive:
    enabled: true
    auto_archive_after_days: 90
    archive_inactive_after_days: 60
    compress_archives: true
    compression_format: "gzip"
    retention_days: 365  # Delete archives after 1 year

  # Sync settings
  sync:
    enabled: true
    auto_sync_interval_minutes: 30
    full_sync_interval_hours: 24
    retry_failed_syncs: true
    max_retries: 3

  # Cleanup settings
  cleanup:
    enabled: true
    run_daily_at: "02:00"  # 2 AM
    optimize_tables: true
    remove_orphans: true
    compress_old_messages: true
    compress_after_days: 30

  # Metadata settings
  metadata:
    auto_sentiment_analysis: true
    auto_categorization: true
    auto_tagging: true
    generate_chat_summaries: true
    update_on_message_received: false  # Only manual or scheduled

  # Status updates
  status:
    auto_mark_read: false
    mark_processed_after_response: true
```

### 3.2 Environment Variables

```bash
# Archive Storage
ARCHIVE_STORAGE_TYPE=local  # or 's3', 'azure'
ARCHIVE_STORAGE_PATH=/data/archives
ARCHIVE_COMPRESSION_ENABLED=true

# Sync Settings
SYNC_ENABLED=true
SYNC_INTERVAL_MINUTES=30

# Cleanup Settings
CLEANUP_ENABLED=true
CLEANUP_SCHEDULE="0 2 * * *"  # Cron format
```

---

## 4. Scheduled Tasks

### 4.1 Cron Jobs - `tasks/scheduled_tasks.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks.task_manager import TaskManager
from database.models import TaskType, TaskPriority

scheduler = AsyncIOScheduler()
task_manager = TaskManager()

# Auto-archive daily at 3 AM
@scheduler.scheduled_job('cron', hour=3, minute=0)
async def auto_archive_old_conversations():
    await task_manager.create_task(
        task_type=TaskType.CONVERSATION_ARCHIVE,
        priority=TaskPriority.BACKGROUND.value,
        input_data={
            "config": {
                "days_old": 90,
                "include_inactive": True,
                "compress": True
            }
        }
    )

# Auto-sync every 30 minutes
@scheduler.scheduled_job('interval', minutes=30)
async def auto_sync_conversations():
    await task_manager.create_task(
        task_type=TaskType.MESSAGE_SYNC,
        priority=TaskPriority.NORMAL.value,
        input_data={
            "mode": "incremental",
            "chat_id": None  # Sync all chats
        }
    )

# Database cleanup daily at 2 AM
@scheduler.scheduled_job('cron', hour=2, minute=0)
async def auto_cleanup_database():
    await task_manager.create_task(
        task_type=TaskType.DATABASE_CLEANUP,
        priority=TaskPriority.BACKGROUND.value,
        input_data={
            "config": {
                "archive_retention_days": 365,
                "compress_after_days": 30,
                "optimize_tables": True
            }
        }
    )

# Update metadata weekly
@scheduler.scheduled_job('cron', day_of_week='sun', hour=4, minute=0)
async def auto_update_metadata():
    await task_manager.create_task(
        task_type=TaskType.METADATA_UPDATE,
        priority=TaskPriority.LOW.value,
        input_data={
            "entity_type": "chat",
            "auto_analyze": True
        }
    )
```

---

## 5. API Endpoints

### 5.1 Archive Endpoints

```python
# POST /api/conversations/archive
{
  "chat_ids": ["123@c.us", "456@c.us"],
  "reason": "Completed",
  "compress": true
}

# GET /api/conversations/archives?page=1&limit=50
# Returns archived conversations

# POST /api/conversations/unarchive
{
  "chat_id": "123@c.us"
}
```

### 5.2 Sync Endpoints

```python
# POST /api/conversations/sync
{
  "chat_id": "123@c.us",  # Optional, null = all chats
  "mode": "incremental"   # or "full"
}

# GET /api/conversations/sync-status
# Returns sync status for all chats
```

### 5.3 Cleanup Endpoints

```python
# POST /api/database/cleanup
{
  "config": {
    "delete_archives_older_than_days": 365,
    "optimize_tables": true
  }
}

# GET /api/database/stats
# Returns database statistics
```

### 5.4 Metadata Endpoints

```python
# POST /api/messages/{message_id}/metadata
{
  "tags": ["urgent", "appointment"],
  "category": "booking",
  "custom_field": "value"
}

# POST /api/messages/{message_id}/analyze
# Auto-generates sentiment, category, tags
```

---

## 6. Integration Points

### 6.1 With WhatsApp Service

```python
# In whatsapp_service.py
async def on_message_received(self, message_data):
    # Existing message processing...

    # Update sync status
    await conversation_manager.mark_synced(message_data['id'])

    # Update chat last_activity
    await conversation_manager.update_last_activity(message_data['chatId'])
```

### 6.2 With LLM Service

```python
# Use LLM for metadata generation
async def _analyze_sentiment(self, text: str):
    prompt = f"Analyze sentiment of this message: {text}"
    result = await self.llm_service.generate(prompt)
    return result
```

### 6.3 With Orchestrator

```python
# Orchestrator can delegate to ConversationManager
if intent == "archive_conversation":
    task = await task_manager.create_task(
        task_type=TaskType.CONVERSATION_ARCHIVE,
        chat_id=chat_id
    )
```

---

## 7. Performance Considerations

### 7.1 Indexing Strategy

```sql
-- Critical indexes for performance
CREATE INDEX idx_messages_chat_created ON messages(chat_id, created_at);
CREATE INDEX idx_messages_archived ON messages(archived_at) WHERE archived_at IS NOT NULL;
CREATE INDEX idx_chats_last_activity ON chats(last_activity_at);
CREATE INDEX idx_metadata_tags ON messages USING GIN(tags);
CREATE INDEX idx_sync_pending ON sync_status(sync_status) WHERE sync_status = 'pending';
```

### 7.2 Batch Processing

- Archive/cleanup operations process in batches of 1000 records
- Use cursor-based pagination for large datasets
- Implement rate limiting for API calls

### 7.3 Caching

- Cache frequently accessed metadata
- Use Redis for sync status tracking
- Cache conversation statistics

---

## 8. Monitoring & Logging

### 8.1 Metrics to Track

```python
metrics = {
    "archives_per_day": 0,
    "sync_success_rate": 0.0,
    "cleanup_freed_space_mb": 0,
    "metadata_update_count": 0,
    "average_sync_duration_seconds": 0.0
}
```

### 8.2 Alerts

- Alert if sync fails for > 3 consecutive attempts
- Alert if database size exceeds threshold
- Alert if archiving takes > 1 hour

---

## 9. Migration Plan

### Phase 1: Database Schema
1. Add new columns to existing tables
2. Create new tables
3. Add indexes
4. Test on staging

### Phase 2: Agent Implementation
1. Create ConversationManagerAgent
2. Implement core features
3. Unit tests

### Phase 3: Scheduled Tasks
1. Set up cron jobs
2. Test scheduling
3. Monitor execution

### Phase 4: API & Integration
1. Add API endpoints
2. Integrate with existing services
3. Update documentation

---

## 10. Testing Strategy

### Unit Tests
- Test each feature independently
- Mock database calls
- Test error handling

### Integration Tests
- Test full archive workflow
- Test sync with mock WhatsApp API
- Test cleanup operations

### Performance Tests
- Archive 10,000+ messages
- Sync large chat histories
- Cleanup with GB of data

---

## Next Steps

1. **Review this design** - Any changes needed?
2. **Database migration** - Should I create migration scripts?
3. **Implementation priority** - Which feature to build first?
4. **Configuration** - Any custom settings needed?

What would you like to adjust or proceed with?
