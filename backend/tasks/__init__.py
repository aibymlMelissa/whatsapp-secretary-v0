# backend/tasks/__init__.py
"""
Task Management System

Provides task creation, queuing, scheduling, and monitoring capabilities
for the agentic task system.
"""

from tasks.task_manager import TaskManager

__all__ = ['TaskManager']
