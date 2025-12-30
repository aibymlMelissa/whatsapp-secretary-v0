# backend/services/agent_service.py
"""
Agent Service

Central service for managing and routing tasks to appropriate agents.
Coordinates between TaskManager and specialized agents.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.orchestrator import OrchestratorAgent
from agents.conversation_manager import ConversationManagerAgent
from database.models import Task, TaskType, TaskStatus
from services.llm_service import LLMService


class AgentService:
    """
    Manages agent registration and task routing
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service
        self.agents: List[BaseAgent] = []
        self._processing = False
        self._register_agents()

    def _register_agents(self):
        """Register all available agents"""
        print("🤖 Registering agents...")

        # Register specialized agents
        self.agents.append(OrchestratorAgent(self.llm_service))
        self.agents.append(ConversationManagerAgent(self.llm_service))

        print(f"✅ Registered {len(self.agents)} agents:")
        for agent in self.agents:
            print(f"   - {agent.agent_type}")

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task by routing it to the appropriate agent

        Args:
            task: Task to process

        Returns:
            Processing result
        """
        # Find agent that can handle this task
        agent = await self._find_agent_for_task(task)

        if not agent:
            error_msg = f"No agent available to handle task type: {task.task_type.value}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "response": "Unable to process this type of request"
            }

        # Execute task with agent
        try:
            print(f"🎯 Routing task #{task.id} to {agent.agent_type}")
            result = await agent.execute(task)
            return result

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "response": f"An error occurred while processing: {str(e)}"
            }

    async def _find_agent_for_task(self, task: Task) -> Optional[BaseAgent]:
        """
        Find the appropriate agent for a task

        Args:
            task: Task to find agent for

        Returns:
            Agent that can handle the task, or None
        """
        for agent in self.agents:
            if await agent.can_handle(task):
                return agent

        return None

    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent types"""
        return [agent.agent_type for agent in self.agents]

    async def start_processing(self, task_manager):
        """
        Start processing tasks from the task queue

        Args:
            task_manager: TaskManager instance to get tasks from
        """
        if self._processing:
            print("⚠️ Agent service already processing tasks")
            return

        self._processing = True
        print("🚀 Agent service started processing tasks")

        while self._processing:
            try:
                # Get task ID from queue (with timeout)
                try:
                    task_id = await asyncio.wait_for(
                        task_manager.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Get task from database
                task = await task_manager.get_task(task_id)

                if not task:
                    print(f"⚠️ Task #{task_id} not found")
                    continue

                if task.status != TaskStatus.PENDING:
                    print(f"⚠️ Task #{task_id} is not pending (status: {task.status.value})")
                    continue

                # Process the task
                await self.process_task(task)

            except Exception as e:
                print(f"❌ Error in task processing loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)  # Brief pause before retry

    def stop_processing(self):
        """Stop processing tasks"""
        self._processing = False
        print("🛑 Agent service stopped processing tasks")


# Global instance (will be initialized with LLM service on startup)
agent_service: Optional[AgentService] = None


def get_agent_service() -> Optional[AgentService]:
    """Get the global agent service instance"""
    return agent_service


def initialize_agent_service(llm_service: Optional[LLMService] = None):
    """
    Initialize the global agent service

    Args:
        llm_service: LLM service to inject into agents
    """
    global agent_service
    agent_service = AgentService(llm_service)
    return agent_service
