#!/usr/bin/env python3
"""
NEXUS Deployment Tab - Deploy and manage applications
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
from textual.widgets import Static, Button, Input, Label, Select, ProgressBar, DataTable, Tree
from textual.reactive import reactive
from textual.message import Message
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import RenderableType
import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str
    environment: Environment
    url: str
    branch: str
    variables: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    build_command: str = "npm run build"
    deploy_command: str = "npm run deploy"
    health_check_url: Optional[str] = None


@dataclass
class DeploymentHistory:
    """Deployment history entry"""
    id: str
    environment: Environment
    version: str
    status: str
    deployed_by: str
    deployed_at: datetime
    duration: timedelta
    commit_hash: str
    commit_message: str
    rollback_available: bool = True


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None


class EnvironmentSelector(Container):
    """Environment selection widget"""
    
    DEFAULT_CSS = """
    EnvironmentSelector {
        layout: horizontal;
        height: 5;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }
    
    .env-button {
        width: 20;
        margin: 0 1;
    }
    
    .env-button.selected {
        background: $primary;
    }
    
    .env-info {
        padding: 0 2;
    }
    """
    
    selected_env = reactive(Environment.DEVELOPMENT)
    
    def compose(self) -> ComposeResult:
        """Compose the environment selector"""
        yield Static("🌍 Environment:", classes="label")
        
        for env in Environment:
            button = Button(
                env.value.capitalize(),
                id=f"env-{env.value}",
                classes="env-button"
            )
            if env == self.selected_env:
                button.add_class("selected")
            yield button
        
        yield Static("", id="env-info", classes="env-info")
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle environment selection"""
        if event.button.id and event.button.id.startswith("env-"):
            env_name = event.button.id.replace("env-", "")
            self.selected_env = Environment(env_name)
            
            # Update button states
            for button in self.query(".env-button"):
                button.remove_class("selected")
            event.button.add_class("selected")
            
            # Update info
            self.update_environment_info()
            
            # Notify parent
            self.post_message(self.EnvironmentChanged(self.selected_env))
    
    def update_environment_info(self):
        """Update environment information display"""
        info = self.query_one("#env-info", Static)
        env_configs = {
            Environment.DEVELOPMENT: "🔧 Local development server",
            Environment.STAGING: "🧪 Testing environment",
            Environment.PRODUCTION: "🚀 Live production server"
        }
        info.update(env_configs[self.selected_env])
    
    class EnvironmentChanged(Message):
        def __init__(self, environment: Environment):
            self.environment = environment
            super().__init__()


class BuildStatus(Container):
    """Build status display with logs"""
    
    DEFAULT_CSS = """
    BuildStatus {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .build-header {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }
    
    .build-progress {
        width: 100%;
        height: 1;
        margin: 1 0;
    }
    
    .build-logs {
        height: 20;
        background: $background;
        border: solid $surface;
        padding: 1;
        overflow-y: scroll;
    }
    
    .log-entry {
        font-family: monospace;
    }
    
    .log-entry.error {
        color: $error;
    }
    
    .log-entry.warning {
        color: $warning;
    }
    
    .log-entry.success {
        color: $success;
    }
    """
    
    build_status = reactive("idle")
    build_progress = reactive(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_entries: List[Tuple[str, str]] = []
        self.build_process = None
    
    def compose(self) -> ComposeResult:
        """Compose the build status display"""
        with Container(classes="build-header"):
            yield Static("🔨 Build Status", classes="title")
            yield Static("Idle", id="build-status-text")
        
        yield ProgressBar(id="build-progress", classes="build-progress", total=100)
        
        yield Static("📋 Build Logs", classes="section-title")
        with ScrollableContainer(id="build-logs", classes="build-logs"):
            yield Static("No build logs yet...", classes="placeholder")
    
    async def start_build(self, config: DeploymentConfig):
        """Start a build process"""
        self.build_status = "building"
        self.build_progress = 0
        self.log_entries.clear()
        
        # Update UI
        self.update_status_text("Building...")
        await self.add_log("Build started", "info")
        await self.add_log(f"Command: {config.build_command}", "info")
        
        # Simulate build process
        try:
            # In real implementation, this would run actual build command
            for i in range(101):
                await asyncio.sleep(0.05)  # Simulate work
                self.build_progress = i
                self.query_one("#build-progress", ProgressBar).progress = i
                
                # Add some logs
                if i == 25:
                    await self.add_log("Installing dependencies...", "info")
                elif i == 50:
                    await self.add_log("Compiling source code...", "info")
                elif i == 75:
                    await self.add_log("Optimizing assets...", "info")
                elif i == 90:
                    await self.add_log("Running tests...", "info")
            
            self.build_status = "success"
            self.update_status_text("Build successful!")
            await self.add_log("Build completed successfully", "success")
            
        except Exception as e:
            self.build_status = "failed"
            self.update_status_text("Build failed!")
            await self.add_log(f"Build error: {str(e)}", "error")
    
    async def add_log(self, message: str, level: str = "info"):
        """Add a log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_entries.append((f"[{timestamp}] {message}", level))
        
        # Update logs display
        logs_container = self.query_one("#build-logs")
        
        # Clear placeholder if present
        if len(self.log_entries) == 1:
            logs_container.remove_children()
        
        # Add new log entry
        log_static = Static(f"[{timestamp}] {message}", classes=f"log-entry {level}")
        await logs_container.mount(log_static)
        
        # Scroll to bottom
        logs_container.scroll_end()
    
    def update_status_text(self, text: str):
        """Update the status text"""
        self.query_one("#build-status-text", Static).update(text)


class DeploymentTimeline(Container):
    """Deployment history timeline"""
    
    DEFAULT_CSS = """
    DeploymentTimeline {
        background: $surface;
        border: solid $primary;
        padding: 1;
        height: 100%;
    }
    
    .timeline-header {
        height: 3;
        border-bottom: solid $surface;
        margin-bottom: 1;
    }
    
    .timeline-container {
        height: 100%;
        overflow-y: scroll;
    }
    
    .timeline-entry {
        layout: horizontal;
        height: 5;
        margin: 1 0;
        padding: 1;
        background: $panel;
        border-left: thick $primary;
    }
    
    .timeline-entry.success {
        border-left-color: $success;
    }
    
    .timeline-entry.failed {
        border-left-color: $error;
    }
    
    .timeline-entry.rollback {
        border-left-color: $warning;
    }
    
    .rollback-button {
        width: 12;
        height: 3;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history: List[DeploymentHistory] = []
    
    def compose(self) -> ComposeResult:
        """Compose the deployment timeline"""
        yield Static("📅 Deployment History", classes="timeline-header")
        
        with ScrollableContainer(classes="timeline-container"):
            if not self.history:
                yield Static("No deployments yet", classes="placeholder")
            else:
                for entry in self.history:
                    yield self.render_timeline_entry(entry)
    
    def render_timeline_entry(self, entry: DeploymentHistory) -> Container:
        """Render a timeline entry"""
        with Container(classes=f"timeline-entry {entry.status}"):
            # Main info
            with Vertical():
                yield Static(
                    f"{entry.environment.value.upper()} - v{entry.version}",
                    classes="entry-title"
                )
                yield Static(
                    f"🕐 {entry.deployed_at.strftime('%Y-%m-%d %H:%M')} by {entry.deployed_by}",
                    classes="entry-time"
                )
                yield Static(
                    f"📝 {entry.commit_message[:50]}...",
                    classes="entry-commit"
                )
            
            # Actions
            if entry.rollback_available and entry.status == "success":
                yield Button(
                    "↩️ Rollback",
                    id=f"rollback-{entry.id}",
                    classes="rollback-button"
                )
        
        return Container()
    
    def add_deployment(self, deployment: DeploymentHistory):
        """Add a deployment to history"""
        self.history.insert(0, deployment)  # Add to beginning
        self.refresh()
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle rollback button press"""
        if event.button.id and event.button.id.startswith("rollback-"):
            deployment_id = event.button.id.replace("rollback-", "")
            self.post_message(self.RollbackRequested(deployment_id))
    
    class RollbackRequested(Message):
        def __init__(self, deployment_id: str):
            self.deployment_id = deployment_id
            super().__init__()


class EnvironmentVariables(Container):
    """Environment variables editor"""
    
    DEFAULT_CSS = """
    EnvironmentVariables {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .var-table {
        height: 20;
        margin: 1 0;
    }
    
    .var-actions {
        layout: horizontal;
        height: 3;
        margin-top: 1;
    }
    
    .var-input {
        width: 30;
        margin: 0 1;
    }
    
    .add-button {
        width: 10;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.variables: Dict[str, str] = {}
    
    def compose(self) -> ComposeResult:
        """Compose the variables editor"""
        yield Static("🔧 Environment Variables", classes="panel-title")
        
        # Variables table
        table = DataTable(id="var-table", classes="var-table")
        table.add_columns("Variable", "Value", "Actions")
        yield table
        
        # Add new variable
        with Horizontal(classes="var-actions"):
            yield Input(placeholder="Variable name", id="var-name", classes="var-input")
            yield Input(placeholder="Value", id="var-value", classes="var-input")
            yield Button("➕ Add", id="add-var", classes="add-button")
    
    def load_variables(self, variables: Dict[str, str]):
        """Load variables into the editor"""
        self.variables = variables.copy()
        self.update_table()
    
    def update_table(self):
        """Update the variables table"""
        table = self.query_one("#var-table", DataTable)
        table.clear()
        
        for name, value in self.variables.items():
            # Mask sensitive values
            display_value = "••••••••" if self._is_sensitive(name) else value
            table.add_row(name, display_value, "🗑️ Delete")
    
    def _is_sensitive(self, name: str) -> bool:
        """Check if variable name suggests sensitive data"""
        sensitive_patterns = ["KEY", "SECRET", "PASSWORD", "TOKEN", "PRIVATE"]
        return any(pattern in name.upper() for pattern in sensitive_patterns)
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses"""
        if event.button.id == "add-var":
            await self.add_variable()
    
    async def add_variable(self):
        """Add a new variable"""
        name_input = self.query_one("#var-name", Input)
        value_input = self.query_one("#var-value", Input)
        
        name = name_input.value.strip()
        value = value_input.value.strip()
        
        if name and value:
            self.variables[name] = value
            self.update_table()
            
            # Clear inputs
            name_input.value = ""
            value_input.value = ""
            
            # Notify parent
            self.post_message(self.VariablesUpdated(self.variables))
    
    class VariablesUpdated(Message):
        def __init__(self, variables: Dict[str, str]):
            self.variables = variables
            super().__init__()


class PerformanceMetrics(Container):
    """Performance metrics display"""
    
    DEFAULT_CSS = """
    PerformanceMetrics {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .metrics-grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        margin: 1 0;
    }
    
    .metric-card {
        background: $panel;
        border: solid $surface;
        padding: 1;
        height: 8;
    }
    
    .metric-value {
        text-align: center;
        text-style: bold;
        font-size: 24;
    }
    
    .metric-label {
        text-align: center;
        margin-top: 1;
    }
    
    .metric-card.warning {
        border-color: $warning;
    }
    
    .metric-card.error {
        border-color: $error;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics: List[PerformanceMetric] = []
    
    def compose(self) -> ComposeResult:
        """Compose the metrics display"""
        yield Static("📊 Performance Metrics", classes="panel-title")
        
        with Container(classes="metrics-grid"):
            # Default metrics
            metrics = [
                ("Response Time", "0ms", "normal"),
                ("Uptime", "100%", "normal"),
                ("Memory Usage", "0MB", "normal"),
                ("Error Rate", "0%", "normal")
            ]
            
            for label, value, status in metrics:
                with Container(classes=f"metric-card {status}"):
                    yield Static(value, classes="metric-value")
                    yield Static(label, classes="metric-label")
    
    def update_metrics(self, metrics: List[PerformanceMetric]):
        """Update the metrics display"""
        self.metrics = metrics
        # In real implementation, update the metric cards


class CostTracking(Container):
    """Cost tracking display"""
    
    DEFAULT_CSS = """
    CostTracking {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .cost-summary {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 1fr 1fr;
        margin: 1 0;
    }
    
    .cost-item {
        text-align: center;
        padding: 1;
    }
    
    .cost-value {
        text-style: bold;
        font-size: 18;
    }
    
    .cost-breakdown {
        margin-top: 1;
        height: 10;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the cost tracking display"""
        yield Static("💰 Cost Tracking", classes="panel-title")
        
        with Container(classes="cost-summary"):
            with Container(classes="cost-item"):
                yield Static("$0.00", classes="cost-value")
                yield Static("Today", classes="cost-label")
            
            with Container(classes="cost-item"):
                yield Static("$0.00", classes="cost-value")
                yield Static("This Month", classes="cost-label")
            
            with Container(classes="cost-item"):
                yield Static("$0.00", classes="cost-value")
                yield Static("Projected", classes="cost-label")
        
        # Cost breakdown table
        table = DataTable(classes="cost-breakdown")
        table.add_columns("Service", "Usage", "Cost")
        table.add_row("Compute", "0 hours", "$0.00")
        table.add_row("Storage", "0 GB", "$0.00")
        table.add_row("Network", "0 GB", "$0.00")
        yield table


class DeployTab(Container):
    """Deployment management interface"""
    
    DEFAULT_CSS = """
    DeployTab {
        layout: grid;
        grid-size: 2 3;
        grid-columns: 2fr 1fr;
        grid-rows: auto 1fr 1fr;
    }
    
    .env-selector {
        column-span: 2;
    }
    
    .main-panel {
        layout: vertical;
        row-span: 2;
    }
    
    .side-panel {
        layout: vertical;
        row-span: 2;
    }
    
    .deploy-actions {
        layout: horizontal;
        height: 5;
        padding: 1;
        background: $surface;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .deploy-button {
        width: 20;
        height: 3;
        margin: 0 1;
    }
    
    .deploy-button.primary {
        background: $success;
    }
    
    .panel-section {
        margin-bottom: 1;
        flex: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_env = Environment.DEVELOPMENT
        self.deployment_configs: Dict[Environment, DeploymentConfig] = {}
        self.is_deploying = False
    
    def compose(self) -> ComposeResult:
        """Compose the deployment interface"""
        # Environment selector
        yield EnvironmentSelector(classes="env-selector")
        
        # Main panel
        with Container(classes="main-panel"):
            # Deploy actions
            with Container(classes="deploy-actions"):
                yield Button(
                    "🚀 Deploy",
                    id="deploy-btn",
                    classes="deploy-button primary"
                )
                yield Button(
                    "🔨 Build Only",
                    id="build-btn",
                    classes="deploy-button"
                )
                yield Button(
                    "🧪 Test Deploy",
                    id="test-btn",
                    classes="deploy-button"
                )
            
            # Build status
            yield BuildStatus(classes="panel-section")
            
            # Deployment timeline
            yield DeploymentTimeline(classes="panel-section")
        
        # Side panel
        with Container(classes="side-panel"):
            # Environment variables
            yield EnvironmentVariables(classes="panel-section")
            
            # Performance metrics
            yield PerformanceMetrics(classes="panel-section")
            
            # Cost tracking
            yield CostTracking(classes="panel-section")
    
    async def on_environment_selector_environment_changed(self, message: EnvironmentSelector.EnvironmentChanged):
        """Handle environment change"""
        self.current_env = message.environment
        await self.load_environment_config()
    
    async def load_environment_config(self):
        """Load configuration for current environment"""
        # Load config from file or API
        config = self.deployment_configs.get(self.current_env)
        
        if config:
            # Update variables editor
            vars_editor = self.query_one(EnvironmentVariables)
            vars_editor.load_variables(config.variables)
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "deploy-btn":
            await self.deploy()
        elif button_id == "build-btn":
            await self.build_only()
        elif button_id == "test-btn":
            await self.test_deploy()
    
    async def deploy(self):
        """Start deployment process"""
        if self.is_deploying:
            return
        
        self.is_deploying = True
        
        # Get or create config
        config = self.deployment_configs.get(
            self.current_env,
            DeploymentConfig(
                name=f"{self.current_env.value}-deployment",
                environment=self.current_env,
                url=f"https://{self.current_env.value}.example.com",
                branch=self.current_env.value
            )
        )
        
        # Start build
        build_status = self.query_one(BuildStatus)
        await build_status.start_build(config)
        
        # If build successful, deploy
        if build_status.build_status == "success":
            await build_status.add_log("Starting deployment...", "info")
            
            # Simulate deployment
            await asyncio.sleep(2)
            
            # Add to history
            deployment = DeploymentHistory(
                id=f"deploy-{datetime.now().timestamp()}",
                environment=self.current_env,
                version="1.0.0",
                status="success",
                deployed_by="NEXUS User",
                deployed_at=datetime.now(),
                duration=timedelta(minutes=2, seconds=30),
                commit_hash="abc123",
                commit_message="Update feature X"
            )
            
            timeline = self.query_one(DeploymentTimeline)
            timeline.add_deployment(deployment)
            
            await build_status.add_log("Deployment completed!", "success")
        
        self.is_deploying = False
    
    async def build_only(self):
        """Run build without deploying"""
        if self.is_deploying:
            return
        
        self.is_deploying = True
        
        config = self.deployment_configs.get(
            self.current_env,
            DeploymentConfig(
                name=f"{self.current_env.value}-build",
                environment=self.current_env,
                url="",
                branch=self.current_env.value
            )
        )
        
        build_status = self.query_one(BuildStatus)
        await build_status.start_build(config)
        
        self.is_deploying = False
    
    async def test_deploy(self):
        """Run test deployment"""
        # Similar to deploy but with test flag
        await self.deploy()
    
    async def on_deployment_timeline_rollback_requested(self, message: DeploymentTimeline.RollbackRequested):
        """Handle rollback request"""
        # Implement rollback logic
        self.notify(f"Rollback requested for deployment {message.deployment_id}")


if __name__ == "__main__":
    # Demo
    from textual.app import App
    
    class DeployDemo(App):
        def compose(self) -> ComposeResult:
            yield DeployTab()
    
    app = DeployDemo()
    app.run()