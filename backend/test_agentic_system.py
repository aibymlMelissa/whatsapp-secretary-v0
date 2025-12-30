#!/usr/bin/env python3
"""
Test script for the Agentic Task System

This demonstrates how the task system works:
1. Creating tasks from messages
2. Using the Orchestrator to analyze intent
3. Routing to appropriate agents
4. Task lifecycle management
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal
from database.models import Task, TaskType, TaskStatus, TaskPriority
from tasks.task_manager import TaskManager
from agents.orchestrator import OrchestratorAgent
from services.llm_service import LLMService
import json


async def test_task_creation():
    """Test creating tasks"""
    print("\n" + "="*60)
    print("TEST 1: Task Creation")
    print("="*60)

    task_manager = TaskManager()

    # Test message data
    test_messages = [
        {
            "chatId": "test_chat_1@c.us",
            "id": "msg_001",
            "body": "Hi, I'd like to book an appointment for next Monday at 2pm",
            "fromMe": False,
            "timestamp": 1234567890
        },
        {
            "chatId": "test_chat_2@c.us",
            "id": "msg_002",
            "body": "What are your business hours?",
            "fromMe": False,
            "timestamp": 1234567891
        },
        {
            "chatId": "test_chat_3@c.us",
            "id": "msg_003",
            "body": "I need to cancel my appointment",
            "fromMe": False,
            "timestamp": 1234567892
        }
    ]

    created_tasks = []
    for msg_data in test_messages:
        task = await task_manager.create_task_from_message(
            message_data=msg_data,
            task_type=TaskType.TRIAGE,
            priority=TaskPriority.NORMAL.value
        )
        if task:
            created_tasks.append(task)
            print(f"✅ Created task #{task.id}: {msg_data['body'][:50]}...")

    print(f"\n📊 Created {len(created_tasks)} tasks")
    return created_tasks


async def test_orchestrator(tasks):
    """Test the Orchestrator agent"""
    print("\n" + "="*60)
    print("TEST 2: Orchestrator Intent Analysis")
    print("="*60)

    llm_service = LLMService()
    orchestrator = OrchestratorAgent(llm_service=llm_service)

    for task in tasks[:3]:  # Test first 3 tasks
        print(f"\n🎯 Processing Task #{task.id}")
        print(f"   Message: {json.loads(task.input_data).get('message', '')[:60]}...")

        # Process the task
        result = await orchestrator.execute(task)

        if result.get('success'):
            print(f"   ✅ Analysis complete")
            print(f"   📍 Intent: {result['data']['intent']['task_type'].value}")
            print(f"   🎯 Routed to: {result['data']['routed_to']}")
            print(f"   📊 Confidence: {result['data']['confidence']:.2f}")
            print(f"   💬 Response: {result['response'][:80]}...")
        else:
            print(f"   ❌ Failed: {result.get('error')}")


async def test_task_manager_operations():
    """Test TaskManager operations"""
    print("\n" + "="*60)
    print("TEST 3: TaskManager Operations")
    print("="*60)

    task_manager = TaskManager()

    # Get task statistics
    stats = await task_manager.get_task_stats()
    print("\n📊 Task Statistics:")
    print(f"   Total tasks: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   In Progress: {stats['in_progress']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Cancelled: {stats['cancelled']}")
    print(f"   Avg completion time: {stats['avg_completion_seconds']:.2f}s")
    print(f"   Queue size: {stats['queue_size']}")

    # Get pending tasks
    print("\n📋 Pending Tasks:")
    pending = await task_manager.get_pending_tasks(limit=5)
    for task in pending:
        input_data = json.loads(task.input_data) if task.input_data else {}
        message = input_data.get('message', 'N/A')
        print(f"   Task #{task.id}: {task.task_type.value} - {message[:40]}...")


async def test_task_lifecycle():
    """Test complete task lifecycle"""
    print("\n" + "="*60)
    print("TEST 4: Task Lifecycle Management")
    print("="*60)

    task_manager = TaskManager()

    # Create a test task
    test_task = await task_manager.create_task(
        task_type=TaskType.APPOINTMENT_BOOKING,
        chat_id="lifecycle_test@c.us",
        input_data={
            "message": "Book appointment for tomorrow",
            "customer": "Test Customer"
        },
        priority=TaskPriority.HIGH.value
    )

    print(f"\n📝 Created task #{test_task.id}")
    print(f"   Status: {test_task.status.value}")

    # Simulate task processing
    print(f"\n🔄 Simulating task processing...")

    # Update to in progress
    await task_manager.update_task_status(
        test_task.id,
        TaskStatus.IN_PROGRESS
    )
    print(f"   ✅ Status: IN_PROGRESS")

    # Complete the task
    await task_manager.update_task_status(
        test_task.id,
        TaskStatus.COMPLETED,
        output_data={"appointment_id": 123, "time": "2024-01-15 10:00"}
    )
    print(f"   ✅ Status: COMPLETED")

    # Get updated task
    updated_task = await task_manager.get_task(test_task.id)
    print(f"\n📊 Final Task State:")
    print(f"   ID: {updated_task.id}")
    print(f"   Type: {updated_task.task_type.value}")
    print(f"   Status: {updated_task.status.value}")
    print(f"   Priority: {updated_task.priority}")
    if updated_task.output_data:
        output = json.loads(updated_task.output_data)
        print(f"   Output: {output}")


async def test_keyword_routing():
    """Test keyword-based routing without LLM"""
    print("\n" + "="*60)
    print("TEST 5: Keyword-Based Intent Detection")
    print("="*60)

    orchestrator = OrchestratorAgent()

    test_cases = [
        ("I want to book an appointment for next week", "APPOINTMENT_BOOKING"),
        ("Can I reschedule my appointment?", "APPOINTMENT_RESCHEDULE"),
        ("I need to cancel my appointment", "APPOINTMENT_CANCEL"),
        ("What are your business hours?", "INFORMATION_QUERY"),
        ("Hello, how can I help you?", "GENERAL_INQUIRY"),
        ("How much does a consultation cost?", "INFORMATION_QUERY"),
    ]

    for message, expected_type in test_cases:
        analysis = orchestrator._keyword_based_routing(message.lower())
        actual_type = analysis['task_type'].value.upper()
        confidence = analysis['confidence']

        match = "✅" if expected_type.lower() in actual_type.lower() else "❌"
        print(f"\n{match} Message: \"{message[:50]}...\"")
        print(f"   Expected: {expected_type}")
        print(f"   Detected: {actual_type}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Method: {analysis['method']}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🤖 AGENTIC TASK SYSTEM TEST SUITE")
    print("="*60)

    try:
        # Test 1: Task Creation
        tasks = await test_task_creation()

        # Test 2: Orchestrator
        await test_orchestrator(tasks)

        # Test 3: TaskManager Operations
        await test_task_manager_operations()

        # Test 4: Task Lifecycle
        await test_task_lifecycle()

        # Test 5: Keyword Routing
        await test_keyword_routing()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
