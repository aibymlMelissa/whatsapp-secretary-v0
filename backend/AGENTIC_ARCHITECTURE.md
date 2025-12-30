# Agentic Task System Architecture

## Overview

The WhatsApp Secretary now uses a **multi-agent architecture** for handling tasks. This provides:

- ✅ **Specialized agents** for different task types
- ✅ **Intent-based routing** using LLM and keyword analysis
- ✅ **Task persistence** and lifecycle management
- ✅ **Workflow orchestration** for multi-step tasks
- ✅ **Performance tracking** and analytics
- ✅ **Error handling** and retry mechanisms

## Architecture Components

### 1. Task Models (`database/models.py`)

**New Database Tables:**

- `tasks` - Stores all tasks with status, priority, and metadata
- `agent_logs` - Tracks agent actions for debugging and analytics

**Key Enums:**

- `TaskType` - Types of tasks (appointment booking, inquiries, etc.)
- `TaskStatus` - Task lifecycle states (pending, in_progress, completed, etc.)
- `TaskPriority` - Priority levels (urgent, high, normal, low, background)

### 2. Base Agent (`agents/base_agent.py`)

Abstract base class that all agents inherit from:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def can_handle(self, task: Task) -> bool:
        """Determine if agent can handle this task"""
        pass

    @abstractmethod
    async def process(self, task: Task) -> Dict[str, Any]:
        """Process the task and return results"""
        pass
```

**Features:**
- Automatic error handling
- Task status management
- Logging and performance tracking
- Database session management
- Subtask creation for workflows

### 3. Orchestrator Agent (`agents/orchestrator.py`)

The main routing agent that analyzes incoming messages and delegates to specialists:

**Intent Analysis Methods:**
1. **Keyword-based** - Fast pattern matching for common intents
2. **LLM-based** - Sophisticated analysis for complex messages

**Routing Decision:**
```python
message = "I want to book an appointment for next Monday"

# Orchestrator analyzes and routes:
{
    'task_type': TaskType.APPOINTMENT_BOOKING,
    'agent_type': 'appointment_agent',
    'confidence': 0.85,
    'routed_to': 'appointment_agent'
}
```

### 4. Task Manager (`tasks/task_manager.py`)

Central service for task lifecycle management:

**Key Operations:**
- `create_task()` - Create new tasks
- `create_task_from_message()` - Create from WhatsApp messages
- `get_pending_tasks()` - Retrieve tasks by status
- `update_task_status()` - Update task lifecycle
- `retry_failed_task()` - Retry mechanism
- `get_task_stats()` - Analytics and monitoring

## Usage Examples

### Creating a Task from a Message

```python
from tasks.task_manager import TaskManager
from database.models import TaskType, TaskPriority

task_manager = TaskManager()

# Create task from WhatsApp message
task = await task_manager.create_task_from_message(
    message_data={
        'chatId': '85260552717@c.us',
        'id': 'msg_123',
        'body': 'I want to book an appointment',
        'fromMe': False
    },
    task_type=TaskType.TRIAGE,  # Will be routed by orchestrator
    priority=TaskPriority.NORMAL.value
)
```

### Using the Orchestrator

```python
from agents.orchestrator import OrchestratorAgent
from services.llm_service import LLMService

llm_service = LLMService()
orchestrator = OrchestratorAgent(llm_service=llm_service)

# Process a task
result = await orchestrator.execute(task)

# Result contains:
# - success: bool
# - response: str (message to send back)
# - data: dict (routing decision, extracted info)
```

### Building a Custom Agent

```python
from agents.base_agent import BaseAgent
from database.models import Task, TaskType

class AppointmentAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "appointment_agent"

    async def can_handle(self, task: Task) -> bool:
        return task.task_type in [
            TaskType.APPOINTMENT_BOOKING,
            TaskType.APPOINTMENT_RESCHEDULE,
            TaskType.APPOINTMENT_CANCEL
        ]

    async def process(self, task: Task) -> Dict[str, Any]:
        context = self.get_task_context(task)
        message = context.get('message', {}).get('body', '')

        # Your appointment logic here
        # ...

        return {
            'success': True,
            'response': 'Appointment booked successfully!',
            'data': {'appointment_id': 123}
        }
```

## Task Lifecycle

```
PENDING → IN_PROGRESS → COMPLETED
    ↓          ↓             ↓
CANCELLED  FAILED      (success)
               ↓
           RETRY (if within max_retries)
```

## Integration with WhatsApp Service

### Current Integration

In `services/whatsapp_service.py`, update `process_new_message()`:

```python
async def process_new_message(self, message_data: dict):
    """Process message with agentic system"""
    # Create task
    task = await self.task_manager.create_task_from_message(
        message_data=message_data,
        task_type=TaskType.TRIAGE
    )

    # Orchestrator will analyze and route
    result = await self.orchestrator.execute(task)

    # Send response if available
    if result.get('success') and result.get('response'):
        await self.send_message(
            chat_id=message_data['chatId'],
            message=result['response']
        )
```

## Monitoring and Analytics

### Get Task Statistics

```python
task_manager = TaskManager()
stats = await task_manager.get_task_stats()

# Returns:
{
    'total': 150,
    'pending': 5,
    'in_progress': 2,
    'completed': 140,
    'failed': 3,
    'cancelled': 0,
    'avg_completion_seconds': 2.5,
    'queue_size': 5
}
```

### Agent Performance Logs

Query `agent_logs` table to see:
- Which agents are most active
- Average task processing time per agent
- Error patterns and failure rates

## Testing

Run the test suite:

```bash
cd backend
python3 test_agentic_system.py
```

Tests include:
1. Task creation from messages
2. Orchestrator intent analysis
3. TaskManager operations
4. Complete task lifecycle
5. Keyword-based routing

## Phase 2 Roadmap

Future specialized agents to implement:

1. **TriageAgent** - First contact, greetings, simple Q&A
2. **AppointmentAgent** - Full appointment management
3. **InquiryAgent** - Business info, FAQs, services
4. **FileAgent** - Document processing and extraction
5. **ReminderAgent** - Proactive notifications and follow-ups

## Best Practices

1. **Always use TaskManager** - Don't create Task objects directly
2. **Log agent actions** - Use `self.log_action()` for debugging
3. **Handle errors gracefully** - Return error info in result dict
4. **Set appropriate priorities** - Use TaskPriority enum
5. **Monitor task stats** - Regularly check for failed/stuck tasks
6. **Clean up old tasks** - Use `task_manager.cleanup_old_tasks()`

## Database Schema

### tasks table
```sql
- id: PRIMARY KEY
- task_type: ENUM (appointment_booking, inquiry, etc.)
- status: ENUM (pending, in_progress, completed, etc.)
- priority: INTEGER (1-10)
- chat_id: STRING (WhatsApp chat ID)
- message_id: STRING (WhatsApp message ID)
- assigned_agent: STRING (agent handling this task)
- input_data: JSON (message, context, parameters)
- output_data: JSON (results, responses)
- metadata: JSON (agent notes, internal state)
- parent_task_id: INTEGER (for subtasks)
- created_at, started_at, completed_at: TIMESTAMP
- retry_count, max_retries: INTEGER
```

### agent_logs table
```sql
- id: PRIMARY KEY
- task_id: FOREIGN KEY (tasks)
- agent_name: STRING
- action: STRING (created, processed, delegated, completed, failed)
- details: JSON
- duration_ms: INTEGER
- created_at: TIMESTAMP
```

## API Endpoints (Future)

Planned endpoints for task management:

- `GET /api/tasks` - List tasks
- `GET /api/tasks/{id}` - Get task details
- `POST /api/tasks` - Create manual task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Cancel task
- `GET /api/tasks/stats` - Get statistics
- `GET /api/agents/logs` - Get agent activity logs

---

**Version:** 1.0.0
**Last Updated:** 2024-12-30
**Author:** Claude Code
