# backend/agents/base_agent.py
"""
Base Agent Class

All specialized agents inherit from this base class which provides:
- Task management integration
- Logging capabilities
- Common agent operations
- Error handling
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time

from database.database import SessionLocal
from database.models import Task, TaskStatus, AgentLog


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system

    Each agent must implement:
    - can_handle(): Determine if agent can handle a task
    - process(): Execute the task
    """

    def __init__(self, name: str):
        self.name = name
        self.db = None

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the type/name of this agent"""
        pass

    @abstractmethod
    async def can_handle(self, task: Task) -> bool:
        """
        Determine if this agent can handle the given task

        Args:
            task: Task object to evaluate

        Returns:
            True if this agent can handle the task
        """
        pass

    @abstractmethod
    async def process(self, task: Task) -> Dict[str, Any]:
        """
        Process the task and return results

        Args:
            task: Task object to process

        Returns:
            Dictionary with results:
            {
                'success': bool,
                'response': str,
                'data': dict,
                'next_action': str (optional)
            }
        """
        pass

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

    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute the task with proper error handling and logging

        Args:
            task: Task to execute

        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        db = self.get_db()

        try:
            # Update task status to in_progress
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            task.assigned_agent = self.agent_type
            db.commit()

            # Log agent action
            self.log_action(task.id, 'started', {'message': 'Task processing started'})

            print(f"🤖 [{self.agent_type}] Processing task #{task.id} - {task.task_type.value}")

            # Process the task
            result = await self.process(task)

            # Update task with results
            task.output_data = json.dumps(result.get('data', {}))

            if result.get('success'):
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                self.log_action(task.id, 'completed', result)
                print(f"✅ [{self.agent_type}] Task #{task.id} completed successfully")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = result.get('error', 'Unknown error')
                self.log_action(task.id, 'failed', result)
                print(f"❌ [{self.agent_type}] Task #{task.id} failed: {task.error_message}")

            db.commit()

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_action(task.id, 'duration', {'duration_ms': duration_ms})

            return result

        except Exception as e:
            # Handle unexpected errors
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()

            self.log_action(task.id, 'error', {'error': str(e)})
            print(f"❌ [{self.agent_type}] Task #{task.id} error: {e}")

            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e),
                'response': f"An error occurred while processing your request: {str(e)}"
            }
        finally:
            self.close_db()

    def log_action(self, task_id: int, action: str, details: Dict[str, Any]):
        """
        Log an agent action

        Args:
            task_id: Task ID
            action: Action performed
            details: Additional details
        """
        try:
            db = self.get_db()

            log_entry = AgentLog(
                task_id=task_id,
                agent_name=self.agent_type,
                action=action,
                details=json.dumps(details),
                duration_ms=details.get('duration_ms')
            )

            db.add(log_entry)
            db.commit()
        except Exception as e:
            print(f"Failed to log action: {e}")

    def parse_input_data(self, task: Task) -> Dict[str, Any]:
        """
        Parse task input data from JSON string

        Args:
            task: Task object

        Returns:
            Parsed input data dictionary
        """
        try:
            if task.input_data:
                return json.loads(task.input_data)
            return {}
        except json.JSONDecodeError:
            return {}

    def get_task_context(self, task: Task) -> Dict[str, Any]:
        """
        Get full context for a task including chat and message info

        Args:
            task: Task object

        Returns:
            Context dictionary
        """
        db = self.get_db()
        context = self.parse_input_data(task)

        # Add chat information if available
        if task.chat_id:
            from database.models import Chat
            chat = db.query(Chat).filter(Chat.id == task.chat_id).first()
            if chat:
                context['chat'] = {
                    'id': chat.id,
                    'name': chat.name,
                    'phone_number': chat.phone_number,
                    'is_group': chat.is_group
                }

        # Add message information if available
        if task.message_id:
            from database.models import Message
            message = db.query(Message).filter(Message.id == task.message_id).first()
            if message:
                context['message'] = {
                    'id': message.id,
                    'body': message.body,
                    'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                    'from_me': message.from_me
                }

        return context

    async def delegate_to_agent(self, task: Task, agent_type: str) -> Dict[str, Any]:
        """
        Delegate task to another agent

        Args:
            task: Task to delegate
            agent_type: Type of agent to delegate to

        Returns:
            Delegation result
        """
        task.assigned_agent = agent_type
        db = self.get_db()
        db.commit()

        self.log_action(task.id, 'delegated', {'to_agent': agent_type})
        print(f"↪️ [{self.agent_type}] Delegating task #{task.id} to {agent_type}")

        return {
            'success': True,
            'delegated': True,
            'to_agent': agent_type
        }

    async def create_subtask(
        self,
        parent_task: Task,
        task_type,
        input_data: Dict[str, Any],
        priority: int = 5
    ) -> Optional[Task]:
        """
        Create a subtask for multi-step workflows

        Args:
            parent_task: Parent task
            task_type: Type of subtask
            input_data: Input data for subtask
            priority: Task priority

        Returns:
            Created subtask or None
        """
        db = self.get_db()

        try:
            subtask = Task(
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                chat_id=parent_task.chat_id,
                message_id=parent_task.message_id,
                input_data=json.dumps(input_data),
                parent_task_id=parent_task.id,
                step_number=parent_task.step_number + 1,
                total_steps=parent_task.total_steps
            )

            db.add(subtask)
            db.commit()
            db.refresh(subtask)

            self.log_action(parent_task.id, 'subtask_created', {'subtask_id': subtask.id})
            print(f"➕ [{self.agent_type}] Created subtask #{subtask.id} for task #{parent_task.id}")

            return subtask
        except Exception as e:
            print(f"Failed to create subtask: {e}")
            return None
