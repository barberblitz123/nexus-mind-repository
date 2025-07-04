#!/usr/bin/env python3
"""
NEXUS Advanced Agent Orchestrator
Production-grade orchestration system with dynamic scaling, fault tolerance, and distributed coordination
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import multiprocessing
import psutil
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import threading
import logging
from collections import defaultdict, deque
import heapq
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class ResourceLimits:
    """Resource limits for agents"""
    cpu_percent: float = 80.0
    memory_mb: int = 1024
    max_tasks: int = 10
    timeout_seconds: int = 300


@dataclass
class AgentHealth:
    """Agent health metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_latency: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    health_score: float = 100.0


@dataclass
class Task:
    """Task definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 60
    dependencies: List[str] = field(default_factory=list)
    
    def __lt__(self, other):
        """Priority comparison for heap operations"""
        return self.priority.value < other.priority.value


class Agent:
    """Base agent class with health monitoring and resource management"""
    
    def __init__(self, agent_id: str, capabilities: List[str], resource_limits: ResourceLimits):
        self.id = agent_id
        self.capabilities = set(capabilities)
        self.resource_limits = resource_limits
        self.status = AgentStatus.INITIALIZING
        self.health = AgentHealth()
        self.task_queue: queue.Queue = queue.Queue(maxsize=resource_limits.max_tasks)
        self.current_tasks: Dict[str, Task] = {}
        self.process = None
        self.thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
    def can_handle_task(self, task: Task) -> bool:
        """Check if agent can handle a specific task"""
        return (
            task.type in self.capabilities and
            self.status in [AgentStatus.READY, AgentStatus.BUSY] and
            len(self.current_tasks) < self.resource_limits.max_tasks and
            self.health.health_score > 20
        )
    
    def update_health(self):
        """Update agent health metrics"""
        if self.process and self.process.is_alive():
            try:
                proc = psutil.Process(self.process.pid)
                self.health.cpu_usage = proc.cpu_percent(interval=0.1)
                self.health.memory_usage = proc.memory_info().rss / 1024 / 1024  # MB
                self.health.active_tasks = len(self.current_tasks)
                self.health.last_heartbeat = datetime.now()
                
                # Calculate health score
                cpu_score = max(0, 100 - self.health.cpu_usage)
                memory_score = max(0, 100 - (self.health.memory_usage / self.resource_limits.memory_mb * 100))
                task_score = max(0, 100 - (self.health.active_tasks / self.resource_limits.max_tasks * 100))
                failure_penalty = min(50, self.health.consecutive_failures * 10)
                
                self.health.health_score = max(0, (cpu_score + memory_score + task_score) / 3 - failure_penalty)
                
                # Update status based on health
                if self.health.health_score < 20:
                    self.status = AgentStatus.UNHEALTHY
                elif self.health.active_tasks >= self.resource_limits.max_tasks * 0.8:
                    self.status = AgentStatus.OVERLOADED
                elif self.health.active_tasks > 0:
                    self.status = AgentStatus.BUSY
                else:
                    self.status = AgentStatus.READY
                    
            except Exception as e:
                logger.error(f"Error updating health for agent {self.id}: {e}")
                self.status = AgentStatus.UNHEALTHY


class AdvancedOrchestrator:
    """Advanced agent orchestration with dynamic scaling and fault tolerance"""
    
    def __init__(self, max_agents: int = 10, min_agents: int = 2):
        self.agents: Dict[str, Agent] = {}
        self.max_agents = max_agents
        self.min_agents = min_agents
        self.task_queue = []  # Priority queue
        self.completed_tasks: deque = deque(maxlen=1000)
        self.failed_tasks: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Load balancing
        self.agent_loads: Dict[str, float] = defaultdict(float)
        self.task_routing: Dict[str, List[str]] = defaultdict(list)  # task_type -> agent_ids
        
        # Monitoring
        self.metrics = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_retried': 0,
            'average_latency': 0.0,
            'agent_spawns': 0,
            'agent_failures': 0
        }
        
        # Communication mesh
        self.agent_mesh: Dict[str, List[str]] = defaultdict(list)
        self.message_bus = queue.Queue()
        
        # Start background tasks
        self.executor = ThreadPoolExecutor(max_workers=20)
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring and management tasks"""
        self.executor.submit(self._health_monitor_loop)
        self.executor.submit(self._task_scheduler_loop)
        self.executor.submit(self._auto_scaler_loop)
        self.executor.submit(self._fault_detector_loop)
        self.executor.submit(self._message_router_loop)
    
    async def spawn_agent(self, agent_type: str, capabilities: List[str], 
                         resource_limits: Optional[ResourceLimits] = None) -> Agent:
        """Dynamically spawn a new agent"""
        if len(self.agents) >= self.max_agents:
            raise RuntimeError("Maximum agent limit reached")
        
        agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        limits = resource_limits or ResourceLimits()
        
        agent = Agent(agent_id, capabilities, limits)
        
        # Start agent process
        agent.process = multiprocessing.Process(
            target=self._run_agent_process,
            args=(agent_id, capabilities, limits)
        )
        agent.process.start()
        
        # Register agent
        with self._lock:
            self.agents[agent_id] = agent
            for capability in capabilities:
                self.task_routing[capability].append(agent_id)
            
            self.metrics['agent_spawns'] += 1
        
        logger.info(f"Spawned agent {agent_id} with capabilities {capabilities}")
        return agent
    
    def _run_agent_process(self, agent_id: str, capabilities: List[str], limits: ResourceLimits):
        """Agent process main loop"""
        signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
        
        logger.info(f"Agent {agent_id} process started")
        
        while True:
            try:
                # Simulate agent work
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task to the orchestrator"""
        with self._lock:
            heapq.heappush(self.task_queue, task)
            self.metrics['tasks_submitted'] += 1
        
        logger.info(f"Task {task.id} submitted with priority {task.priority.name}")
        return task.id
    
    def _select_agent_for_task(self, task: Task) -> Optional[Agent]:
        """Select the best agent for a task using load balancing"""
        eligible_agents = []
        
        with self._lock:
            for agent_id in self.task_routing.get(task.type, []):
                agent = self.agents.get(agent_id)
                if agent and agent.can_handle_task(task):
                    # Calculate load score
                    load_score = (
                        agent.health.cpu_usage * 0.3 +
                        (agent.health.active_tasks / agent.resource_limits.max_tasks) * 100 * 0.4 +
                        (100 - agent.health.health_score) * 0.3
                    )
                    eligible_agents.append((load_score, agent))
        
        if eligible_agents:
            # Select agent with lowest load
            eligible_agents.sort(key=lambda x: x[0])
            return eligible_agents[0][1]
        
        return None
    
    def _health_monitor_loop(self):
        """Monitor agent health continuously"""
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    for agent in list(self.agents.values()):
                        agent.update_health()
                        
                        # Check for unhealthy agents
                        if agent.status == AgentStatus.UNHEALTHY:
                            if agent.health.consecutive_failures > 3:
                                logger.warning(f"Agent {agent.id} is unhealthy, restarting...")
                                self._restart_agent(agent)
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    def _task_scheduler_loop(self):
        """Schedule tasks to agents"""
        while not self._stop_event.is_set():
            try:
                if self.task_queue:
                    with self._lock:
                        if self.task_queue:
                            task = heapq.heappop(self.task_queue)
                    
                    agent = self._select_agent_for_task(task)
                    if agent:
                        task.assigned_agent = agent.id
                        task.started_at = datetime.now()
                        
                        with self._lock:
                            agent.current_tasks[task.id] = task
                        
                        # Simulate task execution
                        self.executor.submit(self._execute_task, agent, task)
                    else:
                        # No agent available, requeue
                        with self._lock:
                            heapq.heappush(self.task_queue, task)
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Task scheduler error: {e}")
    
    def _execute_task(self, agent: Agent, task: Task):
        """Execute a task on an agent"""
        try:
            # Simulate task execution
            time.sleep(min(task.timeout, 5))
            
            # Mark as completed
            task.completed_at = datetime.now()
            task.result = {"status": "success", "data": f"Processed by {agent.id}"}
            
            with self._lock:
                del agent.current_tasks[task.id]
                agent.health.completed_tasks += 1
                agent.health.consecutive_failures = 0
                self.completed_tasks.append(task)
                self.metrics['tasks_completed'] += 1
                
                # Update average latency
                latency = (task.completed_at - task.created_at).total_seconds()
                self.metrics['average_latency'] = (
                    self.metrics['average_latency'] * 0.9 + latency * 0.1
                )
            
            logger.info(f"Task {task.id} completed by agent {agent.id}")
            
        except Exception as e:
            self._handle_task_failure(agent, task, str(e))
    
    def _handle_task_failure(self, agent: Agent, task: Task, error: str):
        """Handle task failure with retry logic"""
        task.error = error
        task.retry_count += 1
        
        with self._lock:
            del agent.current_tasks[task.id]
            agent.health.failed_tasks += 1
            agent.health.consecutive_failures += 1
        
        if task.retry_count < task.max_retries:
            # Requeue with increased priority
            if task.priority.value > 0:
                task.priority = TaskPriority(task.priority.value - 1)
            
            with self._lock:
                heapq.heappush(self.task_queue, task)
                self.metrics['tasks_retried'] += 1
            
            logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
        else:
            with self._lock:
                self.failed_tasks.append(task)
                self.metrics['tasks_failed'] += 1
            
            logger.error(f"Task {task.id} failed permanently: {error}")
    
    def _auto_scaler_loop(self):
        """Auto-scale agents based on workload"""
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    pending_tasks = len(self.task_queue)
                    total_capacity = sum(
                        agent.resource_limits.max_tasks - agent.health.active_tasks
                        for agent in self.agents.values()
                        if agent.status in [AgentStatus.READY, AgentStatus.BUSY]
                    )
                
                # Scale up if needed
                if pending_tasks > total_capacity * 2 and len(self.agents) < self.max_agents:
                    asyncio.run(self.spawn_agent("worker", ["general"], ResourceLimits()))
                
                # Scale down if over-provisioned
                elif pending_tasks < total_capacity * 0.2 and len(self.agents) > self.min_agents:
                    self._terminate_idle_agent()
                
                time.sleep(5)
            except Exception as e:
                logger.error(f"Auto-scaler error: {e}")
    
    def _fault_detector_loop(self):
        """Detect and recover from agent failures"""
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    for agent in list(self.agents.values()):
                        # Check process health
                        if agent.process and not agent.process.is_alive():
                            logger.error(f"Agent {agent.id} process died, restarting...")
                            self._restart_agent(agent)
                        
                        # Check heartbeat timeout
                        elif (datetime.now() - agent.health.last_heartbeat).total_seconds() > 30:
                            logger.error(f"Agent {agent.id} heartbeat timeout, restarting...")
                            self._restart_agent(agent)
                
                time.sleep(2)
            except Exception as e:
                logger.error(f"Fault detector error: {e}")
    
    def _restart_agent(self, agent: Agent):
        """Restart a failed agent"""
        try:
            # Terminate old process
            if agent.process and agent.process.is_alive():
                agent.process.terminate()
                agent.process.join(timeout=5)
            
            # Reassign tasks
            for task in agent.current_tasks.values():
                task.assigned_agent = None
                heapq.heappush(self.task_queue, task)
            
            # Start new process
            agent.process = multiprocessing.Process(
                target=self._run_agent_process,
                args=(agent.id, list(agent.capabilities), agent.resource_limits)
            )
            agent.process.start()
            
            # Reset health
            agent.health = AgentHealth()
            agent.status = AgentStatus.INITIALIZING
            agent.current_tasks.clear()
            
            self.metrics['agent_failures'] += 1
            logger.info(f"Agent {agent.id} restarted successfully")
            
        except Exception as e:
            logger.error(f"Failed to restart agent {agent.id}: {e}")
            self._remove_agent(agent)
    
    def _terminate_idle_agent(self):
        """Terminate an idle agent for scale-down"""
        with self._lock:
            idle_agents = [
                agent for agent in self.agents.values()
                if agent.status == AgentStatus.READY and 
                agent.health.active_tasks == 0 and
                len(self.agents) > self.min_agents
            ]
            
            if idle_agents:
                # Terminate least recently used
                agent = min(idle_agents, key=lambda a: a.health.last_heartbeat)
                self._remove_agent(agent)
    
    def _remove_agent(self, agent: Agent):
        """Remove an agent from the orchestrator"""
        try:
            agent.status = AgentStatus.TERMINATING
            
            # Terminate process
            if agent.process and agent.process.is_alive():
                agent.process.terminate()
                agent.process.join(timeout=5)
            
            # Remove from routing
            for capability in agent.capabilities:
                if agent.id in self.task_routing[capability]:
                    self.task_routing[capability].remove(agent.id)
            
            # Remove from agents
            del self.agents[agent.id]
            
            agent.status = AgentStatus.TERMINATED
            logger.info(f"Agent {agent.id} terminated")
            
        except Exception as e:
            logger.error(f"Error removing agent {agent.id}: {e}")
    
    def _message_router_loop(self):
        """Route messages between agents"""
        while not self._stop_event.is_set():
            try:
                if not self.message_bus.empty():
                    message = self.message_bus.get(timeout=0.1)
                    # Route message to appropriate agents
                    # Implementation depends on message protocol
                    pass
                time.sleep(0.01)
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Message router error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        with self._lock:
            return {
                **self.metrics,
                'active_agents': len(self.agents),
                'healthy_agents': sum(1 for a in self.agents.values() if a.health.health_score > 50),
                'pending_tasks': len(self.task_queue),
                'agent_utilization': {
                    agent_id: {
                        'status': agent.status.value,
                        'health_score': agent.health.health_score,
                        'active_tasks': agent.health.active_tasks,
                        'cpu_usage': agent.health.cpu_usage,
                        'memory_usage': agent.health.memory_usage
                    }
                    for agent_id, agent in self.agents.items()
                }
            }
    
    def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        logger.info("Shutting down orchestrator...")
        self._stop_event.set()
        
        # Terminate all agents
        with self._lock:
            for agent in list(self.agents.values()):
                self._remove_agent(agent)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Orchestrator shutdown complete")


# Example usage
if __name__ == "__main__":
    async def main():
        # Create orchestrator
        orchestrator = AdvancedOrchestrator(max_agents=5, min_agents=2)
        
        # Spawn initial agents
        await orchestrator.spawn_agent("analyzer", ["analysis", "research"], ResourceLimits(cpu_percent=50))
        await orchestrator.spawn_agent("builder", ["build", "compile"], ResourceLimits(memory_mb=2048))
        
        # Submit some tasks
        tasks = []
        for i in range(10):
            task = Task(
                type="analysis" if i % 2 == 0 else "build",
                payload={"data": f"task_{i}"},
                priority=TaskPriority.HIGH if i < 3 else TaskPriority.NORMAL
            )
            task_id = await orchestrator.submit_task(task)
            tasks.append(task_id)
        
        # Monitor for a while
        for _ in range(10):
            await asyncio.sleep(2)
            metrics = orchestrator.get_metrics()
            print(f"\nOrchestrator Metrics:")
            print(f"  Active agents: {metrics['active_agents']}")
            print(f"  Healthy agents: {metrics['healthy_agents']}")
            print(f"  Pending tasks: {metrics['pending_tasks']}")
            print(f"  Completed tasks: {metrics['tasks_completed']}")
            print(f"  Failed tasks: {metrics['tasks_failed']}")
            print(f"  Average latency: {metrics['average_latency']:.2f}s")
        
        # Shutdown
        orchestrator.shutdown()
    
    # Run the example
    asyncio.run(main())