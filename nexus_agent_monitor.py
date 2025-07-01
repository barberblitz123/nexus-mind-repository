#!/usr/bin/env python3
"""
NEXUS Agent Monitoring System
Real-time monitoring and visualization of agent performance
"""

import asyncio
import time
import random
import psutil
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class TaskStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class AgentStatus(Enum):
    IDLE = "IDLE"
    WORKING = "WORKING"
    LEARNING = "LEARNING"
    OPTIMIZING = "OPTIMIZING"
    ERROR = "ERROR"


@dataclass
class PerformanceMetrics:
    response_time_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    network_kb_s: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningMetrics:
    patterns_recognized: int = 0
    optimizations_made: int = 0
    success_rate: float = 0.0
    knowledge_nodes: int = 0
    learning_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    id: str
    name: str
    agent_id: str
    status: TaskStatus
    progress: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    estimated_time: float = 0.0
    actual_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Agent:
    id: str
    name: str
    status: AgentStatus
    current_task: Optional[str] = None
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    learning: LearningMetrics = field(default_factory=LearningMetrics)
    task_history: List[str] = field(default_factory=list)
    resource_allocation: Dict[str, float] = field(default_factory=dict)


class NexusAgentMonitor:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.learning_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.collaboration_graph: Dict[str, List[str]] = defaultdict(list)
        self.running = False
        self.lock = threading.Lock()
        
        # Initialize sample agents
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize sample agents for demonstration"""
        agent_types = [
            ("nexus-core", "NEXUS Core"),
            ("manus-01", "MANUS Agent 1"),
            ("manus-02", "MANUS Agent 2"),
            ("analyzer-01", "Performance Analyzer"),
            ("learner-01", "Learning Engine")
        ]
        
        for agent_id, agent_name in agent_types:
            self.agents[agent_id] = Agent(
                id=agent_id,
                name=agent_name,
                status=AgentStatus.IDLE,
                resource_allocation={
                    "cpu": random.uniform(10, 30),
                    "memory": random.uniform(100, 500),
                    "network": random.uniform(1, 10)
                }
            )
    
    def add_task(self, task: Task):
        """Add a new task to the system"""
        with self.lock:
            self.tasks[task.id] = task
            if task.agent_id in self.agents:
                self.agents[task.agent_id].current_task = task.id
                self.agents[task.agent_id].status = AgentStatus.WORKING
    
    def update_agent_performance(self, agent_id: str, metrics: PerformanceMetrics):
        """Update agent performance metrics"""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].performance = metrics
                self.performance_history[agent_id].append(metrics)
    
    def update_agent_learning(self, agent_id: str, metrics: LearningMetrics):
        """Update agent learning metrics"""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].learning = metrics
                self.learning_history[agent_id].append(metrics)
    
    def update_task_progress(self, task_id: str, progress: float, status: Optional[TaskStatus] = None):
        """Update task progress"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].progress = progress
                if status:
                    self.tasks[task_id].status = status
                if status == TaskStatus.COMPLETED:
                    self.tasks[task_id].completed_at = datetime.now()
                    self.tasks[task_id].actual_time = (
                        self.tasks[task_id].completed_at - self.tasks[task_id].created_at
                    ).total_seconds()
    
    def add_collaboration(self, agent1: str, agent2: str):
        """Add collaboration link between agents"""
        with self.lock:
            self.collaboration_graph[agent1].append(agent2)
            self.collaboration_graph[agent2].append(agent1)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        with self.lock:
            active_agents = [a for a in self.agents.values() if a.status != AgentStatus.IDLE]
            total_tasks = len(self.tasks)
            completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
            
            return {
                "agents": self.agents,
                "tasks": self.tasks,
                "active_agents": len(active_agents),
                "total_agents": len(self.agents),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
            }
    
    def render_ascii_chart(self, data: List[float], width: int = 50, height: int = 10, 
                          title: str = "", y_label: str = "") -> str:
        """Render ASCII chart for data visualization"""
        if not data:
            return f"No data for {title}"
        
        max_val = max(data) if data else 1
        min_val = min(data) if data else 0
        range_val = max_val - min_val if max_val != min_val else 1
        
        chart = []
        chart.append(f"┌{'─' * (width + 2)}┐ {title}")
        
        for i in range(height, 0, -1):
            row = "│ "
            threshold = min_val + (i / height) * range_val
            
            for j in range(min(len(data), width)):
                val = data[-(width-j)] if len(data) > width else data[j]
                if val >= threshold:
                    row += "█"
                else:
                    row += " "
            
            row += " " * (width - min(len(data), width))
            row += f" │ {threshold:.1f} {y_label}"
            chart.append(row)
        
        chart.append(f"└{'─' * (width + 2)}┘")
        return "\n".join(chart)
    
    def render_progress_bar(self, progress: float, width: int = 30, label: str = "") -> str:
        """Render ASCII progress bar"""
        filled = int(progress * width / 100)
        bar = f"[{'█' * filled}{'░' * (width - filled)}] {progress:.1f}% {label}"
        return bar
    
    def render_agent_status(self, agent: Agent) -> str:
        """Render single agent status"""
        status_colors = {
            AgentStatus.IDLE: "○",
            AgentStatus.WORKING: "●",
            AgentStatus.LEARNING: "◆",
            AgentStatus.OPTIMIZING: "★",
            AgentStatus.ERROR: "✗"
        }
        
        status_icon = status_colors.get(agent.status, "?")
        current_task = self.tasks.get(agent.current_task) if agent.current_task else None
        task_info = f"Task: {current_task.name[:20]}" if current_task else "No active task"
        
        return f"{status_icon} {agent.name:<20} | {agent.status.value:<12} | {task_info}"
    
    def render_dashboard(self) -> str:
        """Render complete dashboard"""
        data = self.get_dashboard_data()
        dashboard = []
        
        # Header
        dashboard.append("=" * 80)
        dashboard.append("NEXUS AGENT MONITORING SYSTEM".center(80))
        dashboard.append(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        dashboard.append("=" * 80)
        
        # Summary Stats
        dashboard.append("\n📊 SYSTEM OVERVIEW")
        dashboard.append("─" * 80)
        dashboard.append(f"Active Agents: {data['active_agents']}/{data['total_agents']} | "
                        f"Total Tasks: {data['total_tasks']} | "
                        f"Completed: {data['completed_tasks']} | "
                        f"Success Rate: {data['success_rate']*100:.1f}%")
        
        # Agent Dashboard
        dashboard.append("\n🤖 AGENT STATUS")
        dashboard.append("─" * 80)
        for agent in data['agents'].values():
            dashboard.append(self.render_agent_status(agent))
        
        # Performance Metrics
        dashboard.append("\n📈 PERFORMANCE METRICS")
        dashboard.append("─" * 80)
        
        # CPU Usage Chart
        cpu_data = []
        for agent_id in self.agents:
            if self.performance_history[agent_id]:
                cpu_data.append(self.performance_history[agent_id][-1].cpu_percent)
        
        if cpu_data:
            dashboard.append(self.render_ascii_chart(
                cpu_data, width=40, height=5, 
                title="CPU Usage (%)", y_label="%"
            ))
        
        # Task Progress
        dashboard.append("\n📋 TASK PROGRESS")
        dashboard.append("─" * 80)
        
        active_tasks = [t for t in data['tasks'].values() if t.status == TaskStatus.IN_PROGRESS]
        for task in active_tasks[:5]:  # Show top 5 active tasks
            dashboard.append(f"{task.name:<30} {self.render_progress_bar(task.progress)}")
        
        # Learning Metrics
        dashboard.append("\n🧠 LEARNING METRICS")
        dashboard.append("─" * 80)
        
        total_patterns = sum(a.learning.patterns_recognized for a in data['agents'].values())
        total_optimizations = sum(a.learning.optimizations_made for a in data['agents'].values())
        avg_success_rate = sum(a.learning.success_rate for a in data['agents'].values()) / len(data['agents'])
        
        dashboard.append(f"Patterns Recognized: {total_patterns} | "
                        f"Optimizations: {total_optimizations} | "
                        f"Avg Success Rate: {avg_success_rate:.1f}%")
        
        # Resource Allocation Map
        dashboard.append("\n🗺️  RESOURCE ALLOCATION")
        dashboard.append("─" * 80)
        
        for agent in data['agents'].values():
            cpu = agent.resource_allocation.get('cpu', 0)
            mem = agent.resource_allocation.get('memory', 0)
            net = agent.resource_allocation.get('network', 0)
            
            dashboard.append(f"{agent.name:<20} CPU: {self.render_progress_bar(cpu, width=10)} "
                           f"MEM: {self.render_progress_bar(mem/10, width=10)} "
                           f"NET: {self.render_progress_bar(net*10, width=10)}")
        
        # Collaboration Graph
        dashboard.append("\n🔗 AGENT COLLABORATION")
        dashboard.append("─" * 80)
        
        for agent_id, collaborators in self.collaboration_graph.items():
            if collaborators:
                agent_name = self.agents[agent_id].name if agent_id in self.agents else agent_id
                collab_names = [self.agents[c].name if c in self.agents else c for c in collaborators[:3]]
                dashboard.append(f"{agent_name:<20} ↔ {', '.join(collab_names)}")
        
        return "\n".join(dashboard)
    
    async def simulate_activity(self):
        """Simulate agent activity for demonstration"""
        task_counter = 0
        
        while self.running:
            # Simulate new tasks
            if random.random() < 0.3:
                task_counter += 1
                agent_id = random.choice(list(self.agents.keys()))
                task = Task(
                    id=f"task-{task_counter}",
                    name=f"Process Data Batch {task_counter}",
                    agent_id=agent_id,
                    status=TaskStatus.IN_PROGRESS,
                    estimated_time=random.uniform(10, 60)
                )
                self.add_task(task)
            
            # Update existing tasks
            for task_id, task in list(self.tasks.items()):
                if task.status == TaskStatus.IN_PROGRESS:
                    progress = min(100, task.progress + random.uniform(5, 15))
                    status = TaskStatus.COMPLETED if progress >= 100 else TaskStatus.IN_PROGRESS
                    self.update_task_progress(task_id, progress, status)
                    
                    if status == TaskStatus.COMPLETED and task.agent_id in self.agents:
                        self.agents[task.agent_id].status = AgentStatus.IDLE
                        self.agents[task.agent_id].current_task = None
            
            # Update agent metrics
            for agent_id, agent in self.agents.items():
                # Performance metrics
                perf = PerformanceMetrics(
                    response_time_ms=random.uniform(10, 100),
                    memory_mb=random.uniform(100, 500),
                    cpu_percent=random.uniform(5, 80),
                    network_kb_s=random.uniform(0.5, 10)
                )
                self.update_agent_performance(agent_id, perf)
                
                # Learning metrics
                learn = LearningMetrics(
                    patterns_recognized=agent.learning.patterns_recognized + random.randint(0, 3),
                    optimizations_made=agent.learning.optimizations_made + random.randint(0, 1),
                    success_rate=random.uniform(70, 95),
                    knowledge_nodes=agent.learning.knowledge_nodes + random.randint(0, 5),
                    learning_rate=random.uniform(0.1, 0.9)
                )
                self.update_agent_learning(agent_id, learn)
            
            # Simulate collaborations
            if random.random() < 0.1:
                agents = list(self.agents.keys())
                if len(agents) >= 2:
                    agent1, agent2 = random.sample(agents, 2)
                    self.add_collaboration(agent1, agent2)
            
            await asyncio.sleep(1)
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    async def run_dashboard(self):
        """Run the dashboard with periodic updates"""
        self.running = True
        
        # Start simulation in background
        asyncio.create_task(self.simulate_activity())
        
        try:
            while self.running:
                self.clear_screen()
                print(self.render_dashboard())
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print("\n\nShutting down NEXUS Agent Monitor...")


async def main():
    """Main entry point"""
    monitor = NexusAgentMonitor()
    
    print("Starting NEXUS Agent Monitoring System...")
    print("Press Ctrl+C to exit")
    
    await monitor.run_dashboard()


if __name__ == "__main__":
    asyncio.run(main())