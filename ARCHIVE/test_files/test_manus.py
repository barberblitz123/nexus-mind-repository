#!/usr/bin/env python3
"""
Test script for MANUS continuous work agent
Demonstrates Claude-like task processing capabilities
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manus_continuous_agent import (
    MANUSContinuousAgent, Task, TaskStatus, TaskPriority
)

async def test_manus():
    """Test MANUS functionality"""
    print("🤖 Testing MANUS Continuous Work Agent...")
    print("=" * 50)
    
    # Create MANUS agent
    agent = MANUSContinuousAgent(db_path="test_manus.db", max_workers=2)
    
    # Start agent in background
    agent_task = asyncio.create_task(agent.start())
    
    print("\n✓ MANUS agent started")
    
    # Test 1: Simple shell command
    print("\n📋 Test 1: Shell command execution")
    task1 = Task(
        name="System check",
        description="Check system information",
        action="shell_command",
        parameters={"command": "echo 'MANUS is operational' && date"},
        priority=TaskPriority.HIGH
    )
    task1_id = await agent.add_task(task1)
    print(f"   Added task: {task1.name} (ID: {task1_id})")
    
    # Test 2: Python script execution
    print("\n📋 Test 2: Python script execution")
    task2 = Task(
        name="Calculate fibonacci",
        description="Calculate fibonacci sequence",
        action="python_script",
        parameters={
            "script": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(10)]
print(f"Fibonacci sequence: {result}")
"""
        },
        priority=TaskPriority.MEDIUM
    )
    task2_id = await agent.add_task(task2)
    print(f"   Added task: {task2.name} (ID: {task2_id})")
    
    # Test 3: Task with dependencies
    print("\n📋 Test 3: Task with dependencies")
    task3 = Task(
        name="Dependent task",
        description="This task depends on previous tasks",
        action="shell_command",
        parameters={"command": "echo 'Previous tasks completed successfully!'"},
        priority=TaskPriority.LOW,
        dependencies=[task1_id, task2_id]
    )
    task3_id = await agent.add_task(task3)
    print(f"   Added task: {task3.name} (ID: {task3_id})")
    print(f"   Dependencies: {task3.dependencies}")
    
    # Test 4: File operation
    print("\n📋 Test 4: File operation")
    task4 = Task(
        name="Write test file",
        description="Create a test file",
        action="file_operation",
        parameters={
            "operation": "write",
            "path": "manus_test_output.txt",
            "content": "MANUS continuous work agent is operational!\nWorking like Claude with persistent task execution."
        },
        priority=TaskPriority.MEDIUM
    )
    task4_id = await agent.add_task(task4)
    print(f"   Added task: {task4.name} (ID: {task4_id})")
    
    # Monitor progress
    print("\n⏳ Monitoring task progress...")
    all_tasks = [task1_id, task2_id, task3_id, task4_id]
    completed = set()
    
    for i in range(30):  # Monitor for up to 30 seconds
        stats = agent.get_statistics()
        print(f"\r   Active: {stats['in_progress']}, Pending: {stats['pending']}, "
              f"Completed: {stats['completed']}, Failed: {stats['failed']}", end="")
        
        # Check individual task status
        for task_id in all_tasks:
            if task_id not in completed:
                task = await agent.get_task_status(task_id)
                if task and task.status == TaskStatus.COMPLETED:
                    completed.add(task_id)
                    print(f"\n   ✓ Task completed: {task.name}")
                elif task and task.status == TaskStatus.FAILED:
                    completed.add(task_id)
                    print(f"\n   ✗ Task failed: {task.name} - {task.error}")
        
        if len(completed) == len(all_tasks):
            break
        
        await asyncio.sleep(1)
    
    print("\n\n📊 Final Statistics:")
    final_stats = agent.get_statistics()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")
    
    # Display results
    print("\n📝 Task Results:")
    for task_id in all_tasks:
        task = await agent.get_task_status(task_id)
        if task:
            print(f"\n   Task: {task.name}")
            print(f"   Status: {task.status.value}")
            print(f"   Progress: {task.progress}%")
            if task.result:
                print(f"   Result: {task.result}")
            if task.error:
                print(f"   Error: {task.error}")
    
    # Test context preservation
    print("\n💾 Testing context preservation...")
    context_task = Task(
        name="Context test",
        description="Test context memory",
        action="python_script",
        parameters={
            "script": """
# Store data in context
context['test_data'] = {'timestamp': '2024-01-01', 'value': 42}
context['calculation'] = 2 + 2
result = f"Context stored: {context}"
"""
        },
        context={"initial": "test"}
    )
    context_id = await agent.add_task(context_task)
    
    # Wait for completion
    await asyncio.sleep(2)
    
    # Check if context was preserved
    context_result = await agent.get_task_status(context_id)
    if context_result and context_result.status == TaskStatus.COMPLETED:
        print(f"   ✓ Context preserved: {context_result.context}")
    
    # Cleanup
    print("\n🛑 Stopping MANUS agent...")
    await agent.stop()
    agent_task.cancel()
    
    print("\n✅ MANUS test completed successfully!")
    
    # Check if test file was created
    if os.path.exists("manus_test_output.txt"):
        print("\n📄 Test file content:")
        with open("manus_test_output.txt", "r") as f:
            print(f"   {f.read()}")
        os.remove("manus_test_output.txt")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║           MANUS Continuous Work Agent Test                 ║
║                Claude-like Task Processing                 ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_manus())