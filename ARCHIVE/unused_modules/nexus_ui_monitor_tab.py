#!/usr/bin/env python3
"""
NEXUS Monitor Tab - System monitoring and agent management
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
from textual.widgets import Static, Button, ProgressBar, DataTable, Tree, Sparkline, Label
from textual.reactive import reactive
from textual.message import Message
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import RenderableType
from rich.progress import Progress, BarColumn, TextColumn
import random
from dataclasses import dataclass, field
from enum import Enum
import psutil
import json


class AgentStatus(Enum):
    """Agent status states"""
    IDLE = "idle"
    WORKING = "working"
    LEARNING = "learning"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Agent:
    """Represents an AI agent"""
    id: str
    name: str
    type: str
    status: AgentStatus
    current_task: Optional[str] = None
    progress: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    tasks_completed: int = 0
    errors: int = 0
    uptime: timedelta = timedelta()


@dataclass
class Goal:
    """Represents an active goal"""
    id: str
    title: str
    description: str
    agents: List[str]
    progress: float
    status: str
    created_at: datetime
    deadline: Optional[datetime] = None
    subtasks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SystemMetric:
    """System performance metric"""
    name: str
    value: float
    unit: str
    history: List[float] = field(default_factory=list)
    threshold: Optional[float] = None


class AgentDashboard(Container):
    """Agent activity dashboard"""
    
    DEFAULT_CSS = """
    AgentDashboard {
        background: $surface;
        border: solid $primary;
        padding: 1;
        height: 100%;
    }
    
    .dashboard-header {
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .agent-grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        height: auto;
    }
    
    .agent-card {
        background: $panel;
        border: solid $surface;
        padding: 1;
        height: 10;
    }
    
    .agent-card.working {
        border-color: $primary;
    }
    
    .agent-card.learning {
        border-color: $secondary;
    }
    
    .agent-card.error {
        border-color: $error;
    }
    
    .agent-card.offline {
        opacity: 0.5;
    }
    
    .agent-name {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .agent-task {
        height: 3;
        overflow: hidden;
    }
    
    .agent-stats {
        layout: horizontal;
        height: 3;
        margin-top: 1;
    }
    
    .stat-item {
        width: 33%;
        text-align: center;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agents: List[Agent] = self._create_demo_agents()
    
    def _create_demo_agents(self) -> List[Agent]:
        """Create demo agents"""
        return [
            Agent(
                id="agent-1",
                name="Code Assistant",
                type="Development",
                status=AgentStatus.WORKING,
                current_task="Optimizing database queries",
                progress=65.0,
                cpu_usage=45.2,
                memory_usage=128.5,
                tasks_completed=42
            ),
            Agent(
                id="agent-2",
                name="Design Agent",
                type="Creative",
                status=AgentStatus.IDLE,
                cpu_usage=12.1,
                memory_usage=64.0,
                tasks_completed=15
            ),
            Agent(
                id="agent-3",
                name="Test Runner",
                type="Quality",
                status=AgentStatus.LEARNING,
                current_task="Learning new test patterns",
                progress=30.0,
                cpu_usage=78.9,
                memory_usage=256.0,
                tasks_completed=128
            ),
            Agent(
                id="agent-4",
                name="Doc Writer",
                type="Documentation",
                status=AgentStatus.WORKING,
                current_task="Generating API documentation",
                progress=90.0,
                cpu_usage=23.4,
                memory_usage=96.0,
                tasks_completed=67
            )
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the agent dashboard"""
        yield Static("🤖 Active Agents", classes="dashboard-header")
        
        with Container(classes="agent-grid"):
            for agent in self.agents:
                yield self.render_agent_card(agent)
    
    def render_agent_card(self, agent: Agent) -> Container:
        """Render an agent card"""
        with Container(classes=f"agent-card {agent.status.value}"):
            # Agent name and type
            yield Static(f"{agent.name} ({agent.type})", classes="agent-name")
            
            # Status and task
            status_icon = {
                AgentStatus.IDLE: "💤",
                AgentStatus.WORKING: "⚙️",
                AgentStatus.LEARNING: "🧠",
                AgentStatus.ERROR: "❌",
                AgentStatus.OFFLINE: "🔌"
            }[agent.status]
            
            with Container(classes="agent-task"):
                yield Static(f"{status_icon} {agent.status.value.upper()}")
                if agent.current_task:
                    yield Static(agent.current_task, classes="task-description")
                    yield ProgressBar(total=100, progress=agent.progress)
            
            # Stats
            with Container(classes="agent-stats"):
                with Container(classes="stat-item"):
                    yield Static(f"CPU: {agent.cpu_usage:.1f}%")
                with Container(classes="stat-item"):
                    yield Static(f"MEM: {agent.memory_usage:.0f}MB")
                with Container(classes="stat-item"):
                    yield Static(f"Tasks: {agent.tasks_completed}")
        
        return Container()
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]):
        """Update an agent's status"""
        for agent in self.agents:
            if agent.id == agent_id:
                for key, value in updates.items():
                    setattr(agent, key, value)
                self.refresh()
                break


class LearningProgress(Container):
    """Learning progress visualization"""
    
    DEFAULT_CSS = """
    LearningProgress {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .progress-header {
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .learning-item {
        margin: 1 0;
        padding: 1;
        background: $panel;
    }
    
    .learning-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .progress-bar {
        margin: 1 0;
    }
    
    .learning-stats {
        layout: horizontal;
        height: 3;
    }
    
    .sparkline-container {
        height: 5;
        margin: 1 0;
        border: solid $surface;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.learning_items = [
            {
                "name": "Code Patterns",
                "progress": 78,
                "accuracy": 92.5,
                "samples": 1250,
                "history": [random.randint(60, 95) for _ in range(20)]
            },
            {
                "name": "UI/UX Best Practices",
                "progress": 65,
                "accuracy": 88.3,
                "samples": 890,
                "history": [random.randint(50, 90) for _ in range(20)]
            },
            {
                "name": "Performance Optimization",
                "progress": 45,
                "accuracy": 76.2,
                "samples": 456,
                "history": [random.randint(40, 80) for _ in range(20)]
            }
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the learning progress display"""
        yield Static("🧠 Learning Progress", classes="progress-header")
        
        with ScrollableContainer():
            for item in self.learning_items:
                yield self.render_learning_item(item)
    
    def render_learning_item(self, item: Dict[str, Any]) -> Container:
        """Render a learning progress item"""
        with Container(classes="learning-item"):
            yield Static(item["name"], classes="learning-title")
            
            # Progress bar
            progress_bar = ProgressBar(total=100, progress=item["progress"])
            yield progress_bar
            
            # Stats
            with Container(classes="learning-stats"):
                yield Static(f"Progress: {item['progress']}%")
                yield Static(f"Accuracy: {item['accuracy']}%")
                yield Static(f"Samples: {item['samples']}")
            
            # Sparkline for history
            with Container(classes="sparkline-container"):
                sparkline = Sparkline(
                    data=item["history"],
                    width=40,
                    height=3
                )
                yield sparkline
        
        return Container()


class GoalsTracker(Container):
    """Active goals tracking"""
    
    DEFAULT_CSS = """
    GoalsTracker {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .goals-header {
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .goal-item {
        margin: 1 0;
        padding: 1;
        background: $panel;
        border-left: thick $primary;
    }
    
    .goal-item.completed {
        border-left-color: $success;
    }
    
    .goal-item.in-progress {
        border-left-color: $warning;
    }
    
    .goal-item.overdue {
        border-left-color: $error;
    }
    
    .goal-title {
        text-style: bold;
    }
    
    .goal-meta {
        layout: horizontal;
        height: 3;
        margin: 1 0;
    }
    
    .subtasks-list {
        margin-left: 2;
        margin-top: 1;
    }
    
    .subtask-item {
        height: 2;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.goals: List[Goal] = self._create_demo_goals()
    
    def _create_demo_goals(self) -> List[Goal]:
        """Create demo goals"""
        return [
            Goal(
                id="goal-1",
                title="Build E-commerce Platform",
                description="Complete full-stack e-commerce application",
                agents=["agent-1", "agent-2", "agent-3"],
                progress=75.0,
                status="in-progress",
                created_at=datetime.now() - timedelta(days=5),
                deadline=datetime.now() + timedelta(days=10),
                subtasks=[
                    {"name": "Database schema", "completed": True},
                    {"name": "API endpoints", "completed": True},
                    {"name": "Frontend UI", "completed": False},
                    {"name": "Payment integration", "completed": False}
                ]
            ),
            Goal(
                id="goal-2",
                title="Optimize Performance",
                description="Improve application response time by 50%",
                agents=["agent-1", "agent-3"],
                progress=40.0,
                status="in-progress",
                created_at=datetime.now() - timedelta(days=2),
                subtasks=[
                    {"name": "Profile bottlenecks", "completed": True},
                    {"name": "Optimize queries", "completed": False},
                    {"name": "Implement caching", "completed": False}
                ]
            )
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the goals tracker"""
        yield Static("🎯 Active Goals", classes="goals-header")
        
        with ScrollableContainer():
            for goal in self.goals:
                yield self.render_goal_item(goal)
    
    def render_goal_item(self, goal: Goal) -> Container:
        """Render a goal item"""
        # Determine status class
        status_class = goal.status
        if goal.deadline and goal.deadline < datetime.now():
            status_class = "overdue"
        
        with Container(classes=f"goal-item {status_class}"):
            yield Static(goal.title, classes="goal-title")
            yield Static(goal.description, classes="goal-description")
            
            # Progress bar
            yield ProgressBar(total=100, progress=goal.progress)
            
            # Meta information
            with Container(classes="goal-meta"):
                yield Static(f"Agents: {len(goal.agents)}")
                yield Static(f"Progress: {goal.progress:.0f}%")
                if goal.deadline:
                    days_left = (goal.deadline - datetime.now()).days
                    yield Static(f"Due: {days_left} days")
            
            # Subtasks
            if goal.subtasks:
                with Container(classes="subtasks-list"):
                    for subtask in goal.subtasks:
                        icon = "✅" if subtask["completed"] else "⬜"
                        yield Static(
                            f"{icon} {subtask['name']}",
                            classes="subtask-item"
                        )
        
        return Container()


class ResourceUsage(Container):
    """System resource usage display"""
    
    DEFAULT_CSS = """
    ResourceUsage {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .resource-header {
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .resource-grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
    }
    
    .resource-card {
        background: $panel;
        border: solid $surface;
        padding: 1;
        height: 12;
    }
    
    .resource-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    
    .resource-value {
        text-align: center;
        font-size: 24;
        text-style: bold;
        margin: 1 0;
    }
    
    .resource-bar {
        margin: 1 0;
    }
    
    .resource-details {
        height: 3;
        text-align: center;
    }
    
    .resource-sparkline {
        height: 5;
        margin-top: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics: Dict[str, SystemMetric] = {
            "cpu": SystemMetric(
                name="CPU Usage",
                value=0.0,
                unit="%",
                history=[],
                threshold=80.0
            ),
            "memory": SystemMetric(
                name="Memory Usage",
                value=0.0,
                unit="%",
                history=[],
                threshold=90.0
            ),
            "disk": SystemMetric(
                name="Disk Usage",
                value=0.0,
                unit="%",
                history=[],
                threshold=85.0
            ),
            "network": SystemMetric(
                name="Network I/O",
                value=0.0,
                unit="MB/s",
                history=[]
            )
        }
        self.update_metrics()
    
    def update_metrics(self):
        """Update system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.metrics["cpu"].value = cpu_percent
            self.metrics["cpu"].history.append(cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            self.metrics["memory"].value = memory.percent
            self.metrics["memory"].history.append(memory.percent)
            
            # Disk
            disk = psutil.disk_usage('/')
            self.metrics["disk"].value = disk.percent
            self.metrics["disk"].history.append(disk.percent)
            
            # Network (simplified)
            self.metrics["network"].value = random.uniform(0, 10)
            self.metrics["network"].history.append(self.metrics["network"].value)
            
            # Keep history limited
            for metric in self.metrics.values():
                if len(metric.history) > 20:
                    metric.history = metric.history[-20:]
        except:
            # Use mock data if psutil fails
            for key in self.metrics:
                value = random.uniform(20, 80)
                self.metrics[key].value = value
                self.metrics[key].history.append(value)
    
    def compose(self) -> ComposeResult:
        """Compose the resource usage display"""
        yield Static("📊 System Resources", classes="resource-header")
        
        with Container(classes="resource-grid"):
            for key, metric in self.metrics.items():
                yield self.render_resource_card(key, metric)
    
    def render_resource_card(self, key: str, metric: SystemMetric) -> Container:
        """Render a resource card"""
        # Determine color based on threshold
        value_style = ""
        if metric.threshold and metric.value > metric.threshold:
            value_style = "red"
        elif metric.threshold and metric.value > metric.threshold * 0.8:
            value_style = "yellow"
        
        with Container(classes="resource-card"):
            yield Static(metric.name, classes="resource-title")
            
            # Value display
            value_text = f"{metric.value:.1f}{metric.unit}"
            yield Static(
                Text(value_text, style=value_style),
                classes="resource-value"
            )
            
            # Progress bar
            if metric.unit == "%":
                yield ProgressBar(
                    total=100,
                    progress=metric.value,
                    classes="resource-bar"
                )
            
            # Sparkline
            if metric.history:
                sparkline = Sparkline(
                    data=metric.history,
                    width=20,
                    height=3,
                    classes="resource-sparkline"
                )
                yield sparkline
            
            # Additional details
            if key == "memory":
                memory = psutil.virtual_memory()
                used_gb = memory.used / (1024**3)
                total_gb = memory.total / (1024**3)
                yield Static(
                    f"{used_gb:.1f}GB / {total_gb:.1f}GB",
                    classes="resource-details"
                )
        
        return Container()


class ErrorLogs(Container):
    """Error logs viewer"""
    
    DEFAULT_CSS = """
    ErrorLogs {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .logs-header {
        layout: horizontal;
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .log-filters {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }
    
    .filter-button {
        width: 15;
        margin: 0 1;
    }
    
    .logs-container {
        height: 20;
        overflow-y: scroll;
    }
    
    .log-entry {
        margin: 1 0;
        padding: 1;
        background: $panel;
        border-left: thick $error;
    }
    
    .log-entry.warning {
        border-left-color: $warning;
    }
    
    .log-entry.info {
        border-left-color: $primary;
    }
    
    .log-timestamp {
        text-style: dim;
    }
    
    .log-level {
        text-style: bold;
        margin: 0 1;
    }
    
    .log-message {
        margin-top: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logs = self._generate_demo_logs()
        self.filter_level = "all"
    
    def _generate_demo_logs(self) -> List[Dict[str, Any]]:
        """Generate demo log entries"""
        levels = ["error", "warning", "info"]
        messages = [
            "Failed to connect to database",
            "Memory usage exceeded threshold",
            "API rate limit approaching",
            "Successfully deployed to production",
            "Cache invalidated",
            "Backup completed",
            "SSL certificate expiring soon",
            "Disk space running low"
        ]
        
        logs = []
        for i in range(20):
            timestamp = datetime.now() - timedelta(minutes=random.randint(0, 60))
            logs.append({
                "timestamp": timestamp,
                "level": random.choice(levels),
                "message": random.choice(messages),
                "source": f"agent-{random.randint(1, 4)}"
            })
        
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)
    
    def compose(self) -> ComposeResult:
        """Compose the error logs viewer"""
        with Container(classes="logs-header"):
            yield Static("📋 System Logs", classes="title")
            yield Static(f"Total: {len(self.logs)}", classes="log-count")
        
        # Filters
        with Container(classes="log-filters"):
            yield Button("All", id="filter-all", classes="filter-button")
            yield Button("Errors", id="filter-error", classes="filter-button")
            yield Button("Warnings", id="filter-warning", classes="filter-button")
            yield Button("Info", id="filter-info", classes="filter-button")
        
        # Logs
        with ScrollableContainer(classes="logs-container", id="logs-container"):
            self.render_logs()
    
    def render_logs(self):
        """Render filtered logs"""
        container = self.query_one("#logs-container")
        container.remove_children()
        
        filtered_logs = self.logs
        if self.filter_level != "all":
            filtered_logs = [l for l in self.logs if l["level"] == self.filter_level]
        
        for log in filtered_logs:
            with Container(classes=f"log-entry {log['level']}"):
                # Header line
                with Horizontal():
                    yield Static(
                        log["timestamp"].strftime("%H:%M:%S"),
                        classes="log-timestamp"
                    )
                    yield Static(
                        log["level"].upper(),
                        classes=f"log-level {log['level']}"
                    )
                    yield Static(f"[{log['source']}]", classes="log-source")
                
                # Message
                yield Static(log["message"], classes="log-message")
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle filter button presses"""
        if event.button.id and event.button.id.startswith("filter-"):
            self.filter_level = event.button.id.replace("filter-", "")
            self.render_logs()


class AlertConfig(Container):
    """Alert configuration panel"""
    
    DEFAULT_CSS = """
    AlertConfig {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .config-header {
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .alert-table {
        height: 15;
        margin: 1 0;
    }
    
    .add-alert-form {
        layout: vertical;
        margin-top: 1;
        padding: 1;
        background: $panel;
    }
    
    .form-row {
        layout: horizontal;
        height: 3;
        margin: 1 0;
    }
    
    .form-input {
        width: 30;
        margin: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alerts = [
            {
                "name": "High CPU Usage",
                "condition": "cpu > 80%",
                "action": "Email",
                "enabled": True
            },
            {
                "name": "Low Disk Space",
                "condition": "disk < 10GB",
                "action": "Notification",
                "enabled": True
            },
            {
                "name": "Agent Error",
                "condition": "errors > 5",
                "action": "SMS",
                "enabled": False
            }
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the alert configuration panel"""
        yield Static("🔔 Alert Configuration", classes="config-header")
        
        # Alerts table
        table = DataTable(classes="alert-table")
        table.add_columns("Alert", "Condition", "Action", "Status")
        
        for alert in self.alerts:
            status = "✅ Enabled" if alert["enabled"] else "❌ Disabled"
            table.add_row(
                alert["name"],
                alert["condition"],
                alert["action"],
                status
            )
        
        yield table
        
        # Add new alert form
        with Container(classes="add-alert-form"):
            yield Static("Add New Alert", classes="form-title")
            
            with Container(classes="form-row"):
                yield Label("Name:")
                yield Input(placeholder="Alert name", classes="form-input")
            
            with Container(classes="form-row"):
                yield Label("Condition:")
                yield Input(placeholder="e.g., cpu > 80%", classes="form-input")
            
            with Container(classes="form-row"):
                yield Label("Action:")
                yield Select(
                    options=[
                        ("email", "Email"),
                        ("notification", "Notification"),
                        ("sms", "SMS"),
                        ("webhook", "Webhook")
                    ],
                    classes="form-input"
                )
            
            yield Button("➕ Add Alert", id="add-alert", variant="primary")


class MonitorTab(Container):
    """System monitoring and management interface"""
    
    DEFAULT_CSS = """
    MonitorTab {
        layout: grid;
        grid-size: 3 2;
        grid-columns: 1fr 1fr 1fr;
        grid-rows: 1fr 1fr;
    }
    
    .panel {
        margin: 1;
    }
    
    .agent-dashboard {
        column-span: 2;
    }
    
    .resource-panel {
        row-span: 2;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_timer = None
    
    def compose(self) -> ComposeResult:
        """Compose the monitoring interface"""
        # Agent dashboard (spans 2 columns)
        yield AgentDashboard(classes="panel agent-dashboard")
        
        # Learning progress
        yield LearningProgress(classes="panel")
        
        # Goals tracker
        yield GoalsTracker(classes="panel")
        
        # Resource usage (spans 2 rows)
        yield ResourceUsage(classes="panel resource-panel")
        
        # Error logs
        yield ErrorLogs(classes="panel")
        
        # Alert configuration
        yield AlertConfig(classes="panel")
    
    async def on_mount(self):
        """Start update timer when mounted"""
        self.update_timer = self.set_interval(5.0, self.update_metrics)
    
    async def update_metrics(self):
        """Update all metrics periodically"""
        # Update resource usage
        resource_panel = self.query_one(ResourceUsage)
        resource_panel.update_metrics()
        resource_panel.refresh()
        
        # Update agent statuses (simulate changes)
        agent_dashboard = self.query_one(AgentDashboard)
        for agent in agent_dashboard.agents:
            if agent.status == AgentStatus.WORKING and agent.progress < 100:
                agent.progress += random.uniform(0, 10)
                if agent.progress >= 100:
                    agent.progress = 0
                    agent.status = AgentStatus.IDLE
                    agent.current_task = None
                    agent.tasks_completed += 1
            
            # Random status changes
            if random.random() < 0.1 and agent.status == AgentStatus.IDLE:
                agent.status = AgentStatus.WORKING
                agent.current_task = f"Processing task #{agent.tasks_completed + 1}"
                agent.progress = 0
        
        agent_dashboard.refresh()


if __name__ == "__main__":
    # Demo
    from textual.app import App
    
    class MonitorDemo(App):
        def compose(self) -> ComposeResult:
            yield MonitorTab()
    
    app = MonitorDemo()
    app.run()