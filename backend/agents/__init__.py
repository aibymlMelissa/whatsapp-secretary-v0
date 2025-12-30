# backend/agents/__init__.py
"""
Agentic Task System

This module implements a multi-agent architecture for handling WhatsApp secretary tasks.
Each agent is specialized for specific types of tasks and can collaborate through
the orchestrator.
"""

from agents.base_agent import BaseAgent
from agents.orchestrator import OrchestratorAgent
from agents.conversation_manager import ConversationManagerAgent
from agents.document_analyzer import DocumentAnalyzerAgent

__all__ = ['BaseAgent', 'OrchestratorAgent', 'ConversationManagerAgent', 'DocumentAnalyzerAgent']

# Version info
__version__ = '1.0.0'
