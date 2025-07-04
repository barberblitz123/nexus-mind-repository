#!/usr/bin/env python3
"""
MANUS Continuous Work Agent - Real Implementation
Inspired by Claude's ability to maintain context and work continuously on tasks
"""

import asyncio
import json
import sqlite3
import logging
import uuid
import time
import pickle
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from queue import PriorityQueue
import subprocess
import os
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MANUS')

class TaskStatus(Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class Task:
    """Represents a unit of work for MANUS"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    action: str = ""  # Function name or command to execute
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0-100
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # Task IDs
    context: Dict[str, Any] = field(default_factory=dict)  # Preserved context
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """Enable priority queue sorting"""
        return self.priority.value < other.priority.value

class TaskPersistence:
    """Handles persistent storage of tasks and their state"""
    
    def __init__(self, db_path: str = "manus_tasks.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    action TEXT NOT NULL,
                    parameters TEXT,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    progress REAL DEFAULT 0,
                    result TEXT,
                    error TEXT,
                    dependencies TEXT,
                    context TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
    
    def save_task(self, task: Task):
        """Save or update a task in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.name,
                task.description,
                task.action,
                json.dumps(task.parameters),
                task.status.value,
                task.priority.value,
                task.created_at.isoformat(),
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.progress,
                pickle.dumps(task.result) if task.result else None,
                task.error,
                json.dumps(task.dependencies),
                json.dumps(task.context),
                task.retry_count,
                task.max_retries
            ))
    
    def load_task(self, task_id: str) -> Optional[Task]:
        """Load a task from the database"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            
            if row:
                return self._row_to_task(row)
        return None
    
    def load_all_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Load all tasks, optionally filtered by status"""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = ?", (status.value,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tasks").fetchall()
            
            return [self._row_to_task(row) for row in rows]
    
    def _row_to_task(self, row) -> Task:
        """Convert a database row to a Task object"""
        return Task(
            id=row[0],
            name=row[1],
            description=row[2],
            action=row[3],
            parameters=json.loads(row[4]),
            status=TaskStatus(row[5]),
            priority=TaskPriority(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            started_at=datetime.fromisoformat(row[8]) if row[8] else None,
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            progress=row[10],
            result=pickle.loads(row[11]) if row[11] else None,
            error=row[12],
            dependencies=json.loads(row[13]),
            context=json.loads(row[14]),
            retry_count=row[15],
            max_retries=row[16]
        )
    
    def log_task_event(self, task_id: str, level: str, message: str):
        """Log an event for a task"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO task_logs (task_id, timestamp, level, message)
                VALUES (?, ?, ?, ?)
            """, (task_id, datetime.now().isoformat(), level, message))

class WorkerPool:
    """Manages a pool of workers for parallel task execution"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.workers: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def submit_task(self, task: Task, processor: Callable):
        """Submit a task to the worker pool"""
        async with self.semaphore:
            worker = asyncio.create_task(processor(task))
            self.workers[task.id] = worker
            try:
                await worker
            finally:
                del self.workers[task.id]
    
    def get_active_count(self) -> int:
        """Get the number of active workers"""
        return len(self.workers)
    
    async def shutdown(self):
        """Cancel all active workers"""
        for worker in self.workers.values():
            worker.cancel()
        
        if self.workers:
            await asyncio.gather(*self.workers.values(), return_exceptions=True)

class TaskExecutor:
    """Executes different types of tasks"""
    
    def __init__(self):
        self.action_registry: Dict[str, Callable] = {
            'shell_command': self._execute_shell_command,
            'python_script': self._execute_python_script,
            'http_request': self._execute_http_request,
            'file_operation': self._execute_file_operation,
            'nexus_integration': self._execute_nexus_integration,
            # Enhanced MANUS actions
            'generate_project': self._execute_generate_project,
            'detect_bugs': self._execute_detect_bugs,
            'scan_security': self._execute_scan_security,
            'analyze_performance': self._execute_analyze_performance,
            'generate_docs': self._execute_generate_docs,
        }
    
    async def execute(self, task: Task) -> Any:
        """Execute a task based on its action type"""
        action_handler = self.action_registry.get(task.action)
        if not action_handler:
            raise ValueError(f"Unknown action type: {task.action}")
        
        return await action_handler(task)
    
    async def _execute_shell_command(self, task: Task) -> Dict[str, Any]:
        """Execute a shell command"""
        command = task.parameters.get('command', '')
        timeout = task.parameters.get('timeout', 300)
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            
            return {
                'stdout': stdout.decode(),
                'stderr': stderr.decode(),
                'returncode': process.returncode,
                'success': process.returncode == 0
            }
        except asyncio.TimeoutError:
            if process:
                process.terminate()
            raise TimeoutError(f"Command timed out after {timeout} seconds")
    
    async def _execute_python_script(self, task: Task) -> Any:
        """Execute a Python script or code"""
        script = task.parameters.get('script', '')
        context = task.context.copy()
        
        # Create a restricted execution environment
        exec_globals = {
            '__builtins__': __builtins__,
            'context': context,
            'parameters': task.parameters,
        }
        
        # Use globals as locals to enable function definitions
        try:
            exec(script, exec_globals, exec_globals)
            # Try to get result from globals first, then look for specific variable
            return exec_globals.get('result', exec_globals)
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {str(e)}")
    
    async def _execute_http_request(self, task: Task) -> Dict[str, Any]:
        """Execute an HTTP request"""
        import aiohttp
        
        url = task.parameters.get('url', '')
        method = task.parameters.get('method', 'GET')
        headers = task.parameters.get('headers', {})
        data = task.parameters.get('data', None)
        timeout = task.parameters.get('timeout', 30)
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=headers, json=data, timeout=timeout
            ) as response:
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': await response.text(),
                    'success': 200 <= response.status < 300
                }
    
    async def _execute_file_operation(self, task: Task) -> Dict[str, Any]:
        """Execute file operations"""
        operation = task.parameters.get('operation', '')
        path = task.parameters.get('path', '')
        
        if operation == 'read':
            with open(path, 'r') as f:
                return {'content': f.read(), 'success': True}
        elif operation == 'write':
            content = task.parameters.get('content', '')
            with open(path, 'w') as f:
                f.write(content)
            return {'success': True}
        elif operation == 'delete':
            os.remove(path)
            return {'success': True}
        else:
            raise ValueError(f"Unknown file operation: {operation}")
    
    async def _execute_nexus_integration(self, task: Task) -> Dict[str, Any]:
        """Execute NEXUS-specific integrations"""
        integration_type = task.parameters.get('type', '')
        
        if integration_type == 'consciousness_sync':
            # Integrate with NEXUS consciousness core
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'http://localhost:8000/consciousness/sync',
                    json={'task_id': task.id, 'context': task.context}
                ) as response:
                    return await response.json()
        
        elif integration_type == 'memory_store':
            # Store task memory in NEXUS
            memory_data = {
                'task_id': task.id,
                'memory': task.parameters.get('memory', {}),
                'timestamp': datetime.now().isoformat()
            }
            # Implementation would connect to NEXUS memory system
            return {'stored': True, 'memory_id': str(uuid.uuid4())}
        
        else:
            raise ValueError(f"Unknown integration type: {integration_type}")
    
    async def _execute_generate_project(self, task: Task) -> Dict[str, Any]:
        """Generate a complete project from description"""
        try:
            from nexus_enhanced_manus import EnhancedMANUSOmnipotent
            enhanced_manus = EnhancedMANUSOmnipotent()
            
            result = await enhanced_manus.execute_specialty({
                'command': 'generate_project',
                'description': task.parameters.get('description'),
                'type': task.parameters.get('type', 'auto'),
                'output_dir': task.parameters.get('output_dir', './generated_project')
            })
            
            return result
        except Exception as e:
            logger.error(f"Project generation failed: {e}")
            raise
    
    async def _execute_detect_bugs(self, task: Task) -> Dict[str, Any]:
        """Detect bugs in a project"""
        try:
            from nexus_bug_detector import BugDetectorOmnipotent
            detector = BugDetectorOmnipotent()
            
            directory = task.parameters.get('directory', '.')
            bugs = await detector.scan_project(directory)
            report = detector.generate_report()
            
            return {
                'bugs': bugs,
                'report': detector.export_report(report, 'json'),
                'total_bugs': len(bugs)
            }
        except Exception as e:
            logger.error(f"Bug detection failed: {e}")
            raise
    
    async def _execute_scan_security(self, task: Task) -> Dict[str, Any]:
        """Scan for security vulnerabilities"""
        try:
            from nexus_security_scanner import SecurityScannerOmnipotent
            scanner = SecurityScannerOmnipotent()
            
            directory = task.parameters.get('directory', '.')
            report = scanner.scan_for_vulnerabilities(directory)
            risk_score = scanner.calculate_risk_score(report)
            
            return {
                'report': report.dict(),
                'risk_score': risk_score,
                'vulnerabilities': len(report.vulnerabilities)
            }
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            raise
    
    async def _execute_analyze_performance(self, task: Task) -> Dict[str, Any]:
        """Analyze code performance"""
        try:
            from nexus_performance_analyzer import PerformanceAnalyzerOmnipotent
            analyzer = PerformanceAnalyzerOmnipotent()
            
            code = task.parameters.get('code', '')
            file_path = task.parameters.get('file_path')
            
            if file_path:
                with open(file_path, 'r') as f:
                    code = f.read()
            
            complexity = analyzer.analyze_complexity(code)
            metrics = await analyzer.profile_execution(code, {})
            suggestions = analyzer.suggest_optimizations(code, metrics)
            
            return {
                'complexity': complexity.dict() if complexity else None,
                'metrics': metrics.dict() if metrics else None,
                'suggestions': [s.dict() for s in suggestions]
            }
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            raise
    
    async def _execute_generate_docs(self, task: Task) -> Dict[str, Any]:
        """Generate documentation for a project"""
        try:
            from nexus_doc_generator import DocGeneratorOmnipotent
            generator = DocGeneratorOmnipotent()
            
            directory = task.parameters.get('directory', '.')
            output_dir = task.parameters.get('output_dir', './docs')
            
            result = await generator.sync_documentation(directory, output_dir)
            
            return result
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            raise

class MANUSContinuousAgent:
    """
    Main MANUS continuous work agent - inspired by Claude's architecture
    Provides persistent, intelligent task execution with context preservation
    """
    
    def __init__(self, db_path: str = "manus_tasks.db", max_workers: int = 4):
        self.persistence = TaskPersistence(db_path)
        self.worker_pool = WorkerPool(max_workers)
        self.executor = TaskExecutor()
        self.task_queue = asyncio.Queue()
        self.running = False
        self.context_memory: Dict[str, Any] = {}
        self._load_context_memory()
    
    def _load_context_memory(self):
        """Load preserved context from previous sessions"""
        memory_file = "manus_context_memory.json"
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                self.context_memory = json.load(f)
    
    def _save_context_memory(self):
        """Save context memory for future sessions"""
        with open("manus_context_memory.json", 'w') as f:
            json.dump(self.context_memory, f, indent=2)
    
    async def start(self):
        """Start the continuous work agent"""
        self.running = True
        logger.info("MANUS Continuous Agent starting...")
        
        # Load incomplete tasks from previous session
        await self._restore_incomplete_tasks()
        
        # Start the main work loop
        await asyncio.gather(
            self._main_work_loop(),
            self._progress_monitor(),
            self._dependency_resolver()
        )
    
    async def stop(self):
        """Gracefully stop the agent"""
        logger.info("MANUS Continuous Agent stopping...")
        self.running = False
        await self.worker_pool.shutdown()
        self._save_context_memory()
    
    async def _restore_incomplete_tasks(self):
        """Restore tasks that were incomplete from previous session"""
        incomplete_tasks = self.persistence.load_all_tasks(TaskStatus.IN_PROGRESS)
        pending_tasks = self.persistence.load_all_tasks(TaskStatus.PENDING)
        
        # Reset in-progress tasks to pending
        for task in incomplete_tasks:
            task.status = TaskStatus.PENDING
            self.persistence.save_task(task)
            pending_tasks.append(task)
        
        # Re-queue all pending tasks
        for task in sorted(pending_tasks, key=lambda t: t.priority.value):
            await self.task_queue.put(task)
        
        logger.info(f"Restored {len(pending_tasks)} incomplete tasks")
    
    async def _main_work_loop(self):
        """Main loop that continuously processes tasks"""
        while self.running:
            try:
                # Get next task with timeout to allow checking running status
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Check dependencies
                if await self._check_dependencies(task):
                    # Submit to worker pool
                    asyncio.create_task(
                        self.worker_pool.submit_task(task, self._process_task)
                    )
                else:
                    # Re-queue if dependencies not met
                    await self.task_queue.put(task)
                    await asyncio.sleep(5)  # Wait before rechecking
                    
            except asyncio.TimeoutError:
                # No tasks available, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in main work loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task: Task):
        """Process a single task with full lifecycle management"""
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            self.persistence.save_task(task)
            self.persistence.log_task_event(task.id, "INFO", f"Task started: {task.name}")
            
            # Restore task context
            task.context.update(self.context_memory.get(task.id, {}))
            
            # Execute the task
            logger.info(f"Executing task: {task.name} (ID: {task.id})")
            result = await self.executor.execute(task)
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0
            task.result = result
            
            # Save context for future use
            self.context_memory[task.id] = task.context
            self._save_context_memory()
            
            self.persistence.save_task(task)
            self.persistence.log_task_event(task.id, "INFO", f"Task completed successfully")
            logger.info(f"Task completed: {task.name}")
            
        except Exception as e:
            # Handle task failure
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                # Retry the task
                task.status = TaskStatus.PENDING
                await self.task_queue.put(task)
                logger.warning(f"Task failed, retrying ({task.retry_count}/{task.max_retries}): {task.name}")
                self.persistence.log_task_event(task.id, "WARNING", f"Task failed, retrying: {e}")
            else:
                # Mark as failed after max retries
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(f"Task failed permanently: {task.name} - {e}")
                self.persistence.log_task_event(task.id, "ERROR", f"Task failed permanently: {e}")
            
            self.persistence.save_task(task)
    
    async def _check_dependencies(self, task: Task) -> bool:
        """Check if all task dependencies are completed"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self.persistence.load_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _progress_monitor(self):
        """Monitor and update task progress"""
        while self.running:
            try:
                # Get all in-progress tasks
                in_progress = self.persistence.load_all_tasks(TaskStatus.IN_PROGRESS)
                
                for task in in_progress:
                    # Update progress based on task type and execution time
                    if task.started_at:
                        elapsed = (datetime.now() - task.started_at).total_seconds()
                        
                        # Simple progress estimation (can be enhanced)
                        if task.action == 'shell_command':
                            estimated_duration = task.parameters.get('estimated_duration', 60)
                            task.progress = min(100, (elapsed / estimated_duration) * 100)
                        
                        self.persistence.save_task(task)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in progress monitor: {e}")
                await asyncio.sleep(5)
    
    async def _dependency_resolver(self):
        """Resolve and manage task dependencies"""
        while self.running:
            try:
                # Check for tasks with resolved dependencies
                pending_tasks = self.persistence.load_all_tasks(TaskStatus.PENDING)
                
                for task in pending_tasks:
                    if task.dependencies and await self._check_dependencies(task):
                        # Dependencies resolved, move to queue
                        await self.task_queue.put(task)
                        self.persistence.log_task_event(
                            task.id, "INFO", "Dependencies resolved, task queued"
                        )
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in dependency resolver: {e}")
                await asyncio.sleep(10)
    
    # Public API methods
    
    async def add_task(self, task: Task) -> str:
        """Add a new task to the queue"""
        self.persistence.save_task(task)
        await self.task_queue.put(task)
        logger.info(f"Added task: {task.name} (ID: {task.id})")
        return task.id
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get the current status of a task"""
        return self.persistence.load_task(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or in-progress task"""
        task = self.persistence.load_task(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self.persistence.save_task(task)
            self.persistence.log_task_event(task.id, "INFO", "Task cancelled by user")
            return True
        return False
    
    async def pause_task(self, task_id: str) -> bool:
        """Pause an in-progress task"""
        task = self.persistence.load_task(task_id)
        if task and task.status == TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.PAUSED
            self.persistence.save_task(task)
            self.persistence.log_task_event(task.id, "INFO", "Task paused by user")
            return True
        return False
    
    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        task = self.persistence.load_task(task_id)
        if task and task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.PENDING
            self.persistence.save_task(task)
            await self.task_queue.put(task)
            self.persistence.log_task_event(task.id, "INFO", "Task resumed by user")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        all_tasks = self.persistence.load_all_tasks()
        
        stats = {
            'total_tasks': len(all_tasks),
            'pending': len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
            'in_progress': len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]),
            'completed': len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
            'failed': len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
            'active_workers': self.worker_pool.get_active_count(),
            'context_memory_size': len(self.context_memory)
        }
        
        return stats


# Example usage and test
async def main():
    """Example of how to use MANUS"""
    agent = MANUSContinuousAgent()
    
    # Start the agent
    agent_task = asyncio.create_task(agent.start())
    
    # Add some example tasks
    task1 = Task(
        name="Check system status",
        description="Run system diagnostics",
        action="shell_command",
        parameters={"command": "uname -a && uptime"},
        priority=TaskPriority.HIGH
    )
    
    task2 = Task(
        name="Process data",
        description="Run data processing script",
        action="python_script",
        parameters={
            "script": """
import time
# Simulate processing
for i in range(5):
    print(f"Processing step {i+1}/5")
    time.sleep(1)
result = {'processed_items': 100, 'status': 'success'}
"""
        },
        priority=TaskPriority.MEDIUM,
        dependencies=[task1.id]  # Depends on task1
    )
    
    # Add tasks
    await agent.add_task(task1)
    await agent.add_task(task2)
    
    # Let it run for a bit
    await asyncio.sleep(10)
    
    # Check statistics
    stats = agent.get_statistics()
    print(f"Agent statistics: {json.dumps(stats, indent=2)}")
    
    # Stop the agent
    await agent.stop()
    agent_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())