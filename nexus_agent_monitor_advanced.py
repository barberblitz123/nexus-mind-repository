#!/usr/bin/env python3
"""
NEXUS Agent Monitoring System - Advanced Version
Enhanced monitoring with real integration capabilities
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
import psutil
import threading
import queue
import os
import sys


class MetricsCollector:
    """Collects real system metrics"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.network_stats = self._get_initial_network_stats()
        
    def _get_initial_network_stats(self) -> Dict[str, int]:
        """Get initial network statistics"""
        stats = psutil.net_io_counters()
        return {
            'bytes_sent': stats.bytes_sent,
            'bytes_recv': stats.bytes_recv,
            'timestamp': time.time()
        }
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / (1024 * 1024)
        
        # Network metrics
        current_net = psutil.net_io_counters()
        current_time = time.time()
        time_delta = current_time - self.network_stats['timestamp']
        
        bytes_sent_delta = current_net.bytes_sent - self.network_stats['bytes_sent']
        bytes_recv_delta = current_net.bytes_recv - self.network_stats['bytes_recv']
        
        network_kb_s = (bytes_sent_delta + bytes_recv_delta) / 1024 / time_delta if time_delta > 0 else 0
        
        # Update network stats
        self.network_stats = {
            'bytes_sent': current_net.bytes_sent,
            'bytes_recv': current_net.bytes_recv,
            'timestamp': current_time
        }
        
        # Process-specific metrics
        try:
            process_cpu = self.process.cpu_percent(interval=0.1)
            process_memory = self.process.memory_info().rss / (1024 * 1024)
        except:
            process_cpu = 0
            process_memory = 0
        
        return {
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'memory_percent': memory_percent,
            'memory_mb': memory_mb,
            'network_kb_s': network_kb_s,
            'process_cpu': process_cpu,
            'process_memory': process_memory
        }


class VisualizationEngine:
    """Advanced ASCII visualization engine"""
    
    @staticmethod
    def create_sparkline(data: List[float], width: int = 20) -> str:
        """Create a sparkline visualization"""
        if not data:
            return " " * width
        
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Sparkline characters
        sparks = " ▁▂▃▄▅▆▇█"
        
        sparkline = ""
        for val in data[-width:]:
            normalized = (val - min_val) / range_val
            index = int(normalized * (len(sparks) - 1))
            sparkline += sparks[index]
        
        return sparkline.ljust(width)
    
    @staticmethod
    def create_histogram(data: Dict[str, float], width: int = 40, show_values: bool = True) -> List[str]:
        """Create horizontal histogram"""
        if not data:
            return ["No data available"]
        
        max_val = max(data.values()) if data.values() else 1
        lines = []
        
        for label, value in data.items():
            bar_width = int((value / max_val) * width)
            bar = "█" * bar_width + "░" * (width - bar_width)
            
            if show_values:
                lines.append(f"{label:<15} │{bar}│ {value:.1f}")
            else:
                lines.append(f"{label:<15} │{bar}│")
        
        return lines
    
    @staticmethod
    def create_gauge(value: float, min_val: float = 0, max_val: float = 100, 
                    width: int = 20, label: str = "") -> str:
        """Create a gauge visualization"""
        normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0
        normalized = max(0, min(1, normalized))
        
        filled = int(normalized * width)
        
        # Color coding based on value
        if normalized < 0.3:
            indicator = "▪"
        elif normalized < 0.7:
            indicator = "▫"
        else:
            indicator = "▬"
        
        gauge = f"[{indicator * filled}{'·' * (width - filled)}] {value:.1f} {label}"
        return gauge
    
    @staticmethod
    def create_matrix_view(matrix: List[List[float]], width: int = 10, height: int = 10) -> List[str]:
        """Create a matrix/heatmap view"""
        if not matrix:
            return ["No data available"]
        
        # Normalize values
        flat_values = [val for row in matrix for val in row]
        min_val = min(flat_values) if flat_values else 0
        max_val = max(flat_values) if flat_values else 1
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Intensity characters
        intensity = " ·░▒▓█"
        
        lines = []
        for row in matrix[:height]:
            line = ""
            for val in row[:width]:
                normalized = (val - min_val) / range_val
                index = int(normalized * (len(intensity) - 1))
                line += intensity[index] * 2
            lines.append(line)
        
        return lines


class DatabaseManager:
    """Manages persistent storage of monitoring data"""
    
    def __init__(self, db_path: str = "nexus_monitoring.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Agent metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_mb REAL,
                    response_time_ms REAL,
                    success_rate REAL,
                    patterns_recognized INTEGER,
                    optimizations_made INTEGER
                )
            """)
            
            # Task history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    task_name TEXT,
                    status TEXT,
                    progress REAL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    execution_time_s REAL
                )
            """)
            
            # Collaboration events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collaboration_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    agent1_id TEXT NOT NULL,
                    agent2_id TEXT NOT NULL,
                    event_type TEXT,
                    data TEXT
                )
            """)
            
            conn.commit()
    
    def save_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]):
        """Save agent metrics to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_metrics 
                (agent_id, cpu_percent, memory_mb, response_time_ms, success_rate, 
                 patterns_recognized, optimizations_made)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                metrics.get('cpu_percent', 0),
                metrics.get('memory_mb', 0),
                metrics.get('response_time_ms', 0),
                metrics.get('success_rate', 0),
                metrics.get('patterns_recognized', 0),
                metrics.get('optimizations_made', 0)
            ))
            conn.commit()
    
    def get_agent_history(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get agent metrics history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM agent_metrics
                WHERE agent_id = ? 
                AND timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours), (agent_id,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


class EventBus:
    """Event bus for inter-component communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        self.subscribers[event_type].append(callback)
    
    def publish(self, event_type: str, data: Any):
        """Publish an event"""
        self.event_queue.put((event_type, data))
    
    def _process_events(self):
        """Process events in background thread"""
        while self.running:
            try:
                event_type, data = self.event_queue.get(timeout=0.1)
                for callback in self.subscribers[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        print(f"Error in event callback: {e}")
            except queue.Empty:
                continue
    
    def start(self):
        """Start event processing"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_events)
        self.worker_thread.start()
    
    def stop(self):
        """Stop event processing"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()


class AdvancedNexusMonitor:
    """Advanced monitoring system with real integration"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.visualization = VisualizationEngine()
        self.db_manager = DatabaseManager()
        self.event_bus = EventBus()
        
        # Monitoring data structures
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alert_thresholds = {
            'cpu_high': 80.0,
            'memory_high': 90.0,
            'response_slow': 1000.0,
            'success_low': 70.0
        }
        self.alerts: deque = deque(maxlen=10)
        
        # Initialize event handlers
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe('agent_update', self._handle_agent_update)
        self.event_bus.subscribe('task_complete', self._handle_task_complete)
        self.event_bus.subscribe('alert_triggered', self._handle_alert)
    
    def _handle_agent_update(self, data: Dict[str, Any]):
        """Handle agent update events"""
        agent_id = data.get('agent_id')
        if agent_id:
            self.db_manager.save_agent_metrics(agent_id, data)
    
    def _handle_task_complete(self, data: Dict[str, Any]):
        """Handle task completion events"""
        # Update task history in database
        pass
    
    def _handle_alert(self, data: Dict[str, Any]):
        """Handle alert events"""
        self.alerts.append({
            'timestamp': datetime.now(),
            'type': data.get('type'),
            'message': data.get('message'),
            'severity': data.get('severity', 'INFO')
        })
    
    def check_thresholds(self, agent_id: str, metrics: Dict[str, float]):
        """Check metrics against thresholds and trigger alerts"""
        if metrics.get('cpu_percent', 0) > self.alert_thresholds['cpu_high']:
            self.event_bus.publish('alert_triggered', {
                'type': 'CPU_HIGH',
                'message': f"Agent {agent_id} CPU usage high: {metrics['cpu_percent']:.1f}%",
                'severity': 'WARNING'
            })
        
        if metrics.get('memory_percent', 0) > self.alert_thresholds['memory_high']:
            self.event_bus.publish('alert_triggered', {
                'type': 'MEMORY_HIGH',
                'message': f"Agent {agent_id} memory usage high: {metrics['memory_percent']:.1f}%",
                'severity': 'WARNING'
            })
    
    def render_advanced_dashboard(self) -> str:
        """Render advanced dashboard with all visualizations"""
        dashboard = []
        
        # Header with system metrics
        system_metrics = self.metrics_collector.get_system_metrics()
        
        dashboard.append("╔" + "═" * 78 + "╗")
        dashboard.append("║" + "NEXUS ADVANCED MONITORING SYSTEM".center(78) + "║")
        dashboard.append("║" + f"System CPU: {system_metrics['cpu_percent']:.1f}% | "
                        f"Memory: {system_metrics['memory_percent']:.1f}% | "
                        f"Network: {system_metrics['network_kb_s']:.1f} KB/s".center(78) + "║")
        dashboard.append("╚" + "═" * 78 + "╝")
        
        # Alerts section
        if self.alerts:
            dashboard.append("\n🚨 ALERTS")
            dashboard.append("─" * 80)
            for alert in list(self.alerts)[-3:]:  # Show last 3 alerts
                severity_icon = "⚠️" if alert['severity'] == 'WARNING' else "❌"
                dashboard.append(f"{severity_icon} [{alert['timestamp'].strftime('%H:%M:%S')}] "
                               f"{alert['message']}")
        
        # Agent Performance Matrix
        dashboard.append("\n📊 AGENT PERFORMANCE MATRIX")
        dashboard.append("─" * 80)
        
        if self.agents:
            # Create performance matrix
            agent_names = list(self.agents.keys())[:5]
            metrics = ['CPU %', 'Memory MB', 'Response ms', 'Success %']
            
            # Header
            header = "Agent".ljust(15) + " │ " + " │ ".join(m.center(12) for m in metrics)
            dashboard.append(header)
            dashboard.append("─" * len(header))
            
            # Agent rows
            for agent_name in agent_names:
                agent = self.agents.get(agent_name, {})
                perf = agent.get('performance', {})
                
                values = [
                    self.visualization.create_gauge(perf.get('cpu_percent', 0), 0, 100, 10),
                    self.visualization.create_gauge(perf.get('memory_mb', 0), 0, 1000, 10),
                    self.visualization.create_gauge(perf.get('response_time_ms', 0), 0, 200, 10),
                    self.visualization.create_gauge(perf.get('success_rate', 0), 0, 100, 10)
                ]
                
                row = agent_name[:15].ljust(15) + " │ " + " │ ".join(values)
                dashboard.append(row)
        
        # Learning Progress Sparklines
        dashboard.append("\n🧠 LEARNING PROGRESS")
        dashboard.append("─" * 80)
        
        for agent_id, history in list(self.performance_history.items())[:5]:
            if history:
                patterns_data = [h.get('patterns_recognized', 0) for h in history]
                sparkline = self.visualization.create_sparkline(patterns_data, 40)
                dashboard.append(f"{agent_id:<15} Patterns: {sparkline} "
                               f"[{patterns_data[-1] if patterns_data else 0}]")
        
        # Resource Distribution
        dashboard.append("\n💾 RESOURCE DISTRIBUTION")
        dashboard.append("─" * 80)
        
        if self.agents:
            resource_data = {}
            for agent_id, agent in self.agents.items():
                allocation = agent.get('resource_allocation', {})
                resource_data[agent_id] = allocation.get('memory', 0)
            
            histogram = self.visualization.create_histogram(resource_data, width=35)
            for line in histogram[:5]:
                dashboard.append(line)
        
        return "\n".join(dashboard)
    
    async def run(self):
        """Run the advanced monitoring system"""
        self.event_bus.start()
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(self.render_advanced_dashboard())
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down advanced monitoring...")
        finally:
            self.event_bus.stop()


async def main():
    """Main entry point for advanced monitor"""
    monitor = AdvancedNexusMonitor()
    
    # Simulate some agents for demo
    for i in range(3):
        monitor.agents[f"agent-{i}"] = {
            'performance': {
                'cpu_percent': 30 + i * 10,
                'memory_mb': 200 + i * 50,
                'response_time_ms': 50 + i * 20,
                'success_rate': 85 + i * 3
            },
            'resource_allocation': {
                'memory': 300 + i * 100,
                'cpu': 2 + i
            }
        }
    
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())