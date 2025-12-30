# backend/agents/orchestrator.py
"""
Orchestrator Agent

The orchestrator is responsible for:
1. Receiving incoming messages/tasks
2. Analyzing intent and context
3. Routing to appropriate specialized agents
4. Coordinating multi-agent workflows
5. Managing task priorities and delegation
"""

from typing import Dict, Any, Optional, List
import re
import json

from agents.base_agent import BaseAgent
from database.models import Task, TaskType, TaskStatus
from services.llm_service import LLMService


class OrchestratorAgent(BaseAgent):
    """
    Main orchestrator that routes tasks to specialized agents

    The orchestrator uses LLM-based intent recognition to determine
    which agent should handle each task.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__("Orchestrator")
        self.llm_service = llm_service

    @property
    def agent_type(self) -> str:
        return "orchestrator"

    async def can_handle(self, task: Task) -> bool:
        """
        The orchestrator can handle TRIAGE tasks
        """
        return task.task_type == TaskType.TRIAGE

    async def process(self, task: Task) -> Dict[str, Any]:
        """
        Process a triage task by analyzing intent and routing to appropriate agent

        Args:
            task: Task to process

        Returns:
            Processing result with routing decision
        """
        context = self.get_task_context(task)
        message = context.get('message', {}).get('body', '').strip()

        if not message:
            return {
                'success': False,
                'error': 'No message content to process',
                'response': 'I received an empty message. How can I help you?'
            }

        print(f"🎯 [Orchestrator] Analyzing message: '{message[:50]}...'")

        # Analyze intent using multiple strategies
        intent_analysis = await self.analyze_intent(message, context)

        # Determine which agent should handle this
        agent_type = intent_analysis.get('agent_type', 'general')
        confidence = intent_analysis.get('confidence', 0.5)
        task_type = intent_analysis.get('task_type', TaskType.GENERAL_INQUIRY)

        print(f"📊 [Orchestrator] Intent: {task_type.value}, Agent: {agent_type}, Confidence: {confidence:.2f}")

        # For now, return routing decision
        # In Phase 2, we'll actually create and delegate to specialized agents
        return {
            'success': True,
            'response': self._generate_response(intent_analysis, message),
            'data': {
                'intent': intent_analysis,
                'routed_to': agent_type,
                'task_type': task_type.value,
                'confidence': confidence
            }
        }

    async def analyze_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze message intent using keyword matching and LLM

        Args:
            message: Message text
            context: Task context

        Returns:
            Intent analysis with agent routing decision
        """
        message_lower = message.lower()

        # Quick keyword-based routing for common cases
        keyword_analysis = self._keyword_based_routing(message_lower)

        if keyword_analysis.get('confidence', 0) > 0.8:
            # High confidence keyword match, use it
            return keyword_analysis

        # For lower confidence or ambiguous cases, use LLM
        if self.llm_service:
            llm_analysis = await self._llm_based_routing(message, context)
            if llm_analysis:
                return llm_analysis

        # Fallback to keyword analysis
        return keyword_analysis

    def _keyword_based_routing(self, message: str) -> Dict[str, Any]:
        """
        Fast keyword-based intent detection

        Args:
            message: Lowercase message text

        Returns:
            Intent analysis
        """
        # Appointment-related keywords
        appointment_keywords = [
            'appointment', 'book', 'schedule', 'reserve', 'meeting',
            'reschedule', 'cancel', 'change', 'available', 'availability',
            'time slot', 'calendar', 'when can', 'free time'
        ]

        # Reschedule-specific
        reschedule_keywords = ['reschedule', 'change', 'move', 'different time', 'different date']

        # Cancel-specific
        cancel_keywords = ['cancel', 'delete', 'remove appointment']

        # Information query keywords
        info_keywords = [
            'what is', 'how much', 'price', 'cost', 'hours', 'open',
            'location', 'address', 'where', 'services', 'what do you',
            'tell me about', 'information', 'details'
        ]

        # Greetings
        greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']

        # File/document keywords
        file_keywords = ['send', 'file', 'document', 'photo', 'image', 'picture', 'attachment']

        # Count keyword matches
        appointment_score = sum(1 for kw in appointment_keywords if kw in message)
        reschedule_score = sum(1 for kw in reschedule_keywords if kw in message)
        cancel_score = sum(1 for kw in cancel_keywords if kw in message)
        info_score = sum(1 for kw in info_keywords if kw in message)
        greeting_score = sum(1 for kw in greeting_keywords if kw in message)
        file_score = sum(1 for kw in file_keywords if kw in message)

        # Determine intent based on scores
        if cancel_score > 0 and appointment_score > 0:
            return {
                'task_type': TaskType.APPOINTMENT_CANCEL,
                'agent_type': 'appointment_agent',
                'confidence': min(0.9, 0.7 + (cancel_score * 0.1)),
                'keywords_matched': cancel_score + appointment_score,
                'method': 'keyword'
            }

        if reschedule_score > 0 and appointment_score > 0:
            return {
                'task_type': TaskType.APPOINTMENT_RESCHEDULE,
                'agent_type': 'appointment_agent',
                'confidence': min(0.9, 0.7 + (reschedule_score * 0.1)),
                'keywords_matched': reschedule_score + appointment_score,
                'method': 'keyword'
            }

        if appointment_score >= 2:
            return {
                'task_type': TaskType.APPOINTMENT_BOOKING,
                'agent_type': 'appointment_agent',
                'confidence': min(0.9, 0.6 + (appointment_score * 0.1)),
                'keywords_matched': appointment_score,
                'method': 'keyword'
            }

        if info_score >= 2:
            return {
                'task_type': TaskType.INFORMATION_QUERY,
                'agent_type': 'inquiry_agent',
                'confidence': min(0.8, 0.6 + (info_score * 0.1)),
                'keywords_matched': info_score,
                'method': 'keyword'
            }

        if file_score >= 1:
            return {
                'task_type': TaskType.FILE_PROCESSING,
                'agent_type': 'file_agent',
                'confidence': 0.7,
                'keywords_matched': file_score,
                'method': 'keyword'
            }

        if greeting_score >= 1:
            return {
                'task_type': TaskType.GENERAL_INQUIRY,
                'agent_type': 'triage_agent',
                'confidence': 0.8,
                'keywords_matched': greeting_score,
                'method': 'keyword'
            }

        # Default: general inquiry
        return {
            'task_type': TaskType.GENERAL_INQUIRY,
            'agent_type': 'inquiry_agent',
            'confidence': 0.4,
            'keywords_matched': 0,
            'method': 'fallback'
        }

    async def _llm_based_routing(self, message: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use LLM to analyze intent for complex or ambiguous messages

        Args:
            message: Message text
            context: Task context

        Returns:
            LLM-based intent analysis or None
        """
        if not self.llm_service:
            return None

        try:
            prompt = f"""
            Analyze this customer message and determine the intent and appropriate agent:

            Message: "{message}"

            Customer Context:
            - Name: {context.get('chat', {}).get('name', 'Unknown')}
            - Phone: {context.get('chat', {}).get('phone_number', 'Unknown')}

            Classify this into ONE of these categories:
            1. APPOINTMENT_BOOKING - Customer wants to book a new appointment
            2. APPOINTMENT_RESCHEDULE - Customer wants to change an existing appointment
            3. APPOINTMENT_CANCEL - Customer wants to cancel an appointment
            4. INFORMATION_QUERY - Customer asking about services, hours, pricing, location
            5. FILE_PROCESSING - Customer sent or asking about a document/file
            6. GENERAL_INQUIRY - General question or greeting

            Respond with ONLY a JSON object in this exact format:
            {{
                "task_type": "TASK_TYPE_NAME",
                "agent_type": "agent_name",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation",
                "extracted_info": {{}}
            }}

            Agent types: appointment_agent, inquiry_agent, file_agent, triage_agent
            """

            # Use LLM to analyze (preferably a fast model like Gemini Flash)
            response = await self.llm_service.generate_response(
                message=prompt,
                chat_id=context.get('chat', {}).get('id', 'orchestrator'),
                provider="gemini"
            )

            if response and response.get('response'):
                # Parse JSON from LLM response
                json_str = response['response'].strip()

                # Remove markdown code blocks if present
                if json_str.startswith('```'):
                    json_str = re.sub(r'```json?\s*|\s*```', '', json_str).strip()

                analysis = json.loads(json_str)

                # Convert task_type string to enum
                task_type_str = analysis.get('task_type', 'GENERAL_INQUIRY')
                try:
                    task_type = TaskType[task_type_str]
                except KeyError:
                    task_type = TaskType.GENERAL_INQUIRY

                analysis['task_type'] = task_type
                analysis['method'] = 'llm'

                return analysis

        except Exception as e:
            print(f"❌ [Orchestrator] LLM routing failed: {e}")
            return None

    def _generate_response(self, intent: Dict[str, Any], message: str) -> str:
        """
        Generate an appropriate response based on intent

        Args:
            intent: Intent analysis
            message: Original message

        Returns:
            Response message
        """
        task_type = intent.get('task_type')
        confidence = intent.get('confidence', 0.5)

        # For Phase 1, just acknowledge the message
        responses = {
            TaskType.APPOINTMENT_BOOKING: "I'll help you book an appointment. Our appointment agent will assist you shortly.",
            TaskType.APPOINTMENT_RESCHEDULE: "I'll help you reschedule your appointment. Let me check the available times.",
            TaskType.APPOINTMENT_CANCEL: "I understand you want to cancel an appointment. Our system will process this request.",
            TaskType.INFORMATION_QUERY: "Let me get that information for you.",
            TaskType.FILE_PROCESSING: "I received your file and will process it shortly.",
            TaskType.GENERAL_INQUIRY: "Thank you for your message. How can I assist you today?"
        }

        return responses.get(task_type, "I'm analyzing your message and will respond shortly.")

    async def route_task(self, task: Task, to_agent: str, new_task_type: TaskType) -> bool:
        """
        Route a task to a specific agent

        Args:
            task: Task to route
            to_agent: Agent type to route to
            new_task_type: New task type

        Returns:
            True if routed successfully
        """
        db = self.get_db()

        try:
            # Update task type and assignment
            task.task_type = new_task_type
            task.assigned_agent = to_agent
            task.status = TaskStatus.PENDING

            db.commit()

            self.log_action(task.id, 'routed', {
                'to_agent': to_agent,
                'task_type': new_task_type.value
            })

            print(f"↪️ [Orchestrator] Routed task #{task.id} to {to_agent} ({new_task_type.value})")
            return True

        except Exception as e:
            print(f"❌ [Orchestrator] Failed to route task: {e}")
            db.rollback()
            return False
        finally:
            self.close_db()
