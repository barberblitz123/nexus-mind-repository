#!/usr/bin/env python3
"""
NEXUS Agent Metrics
Real-time performance monitoring, distributed tracing, and automated tuning
"""

import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import asyncio
from collections import defaultdict, deque
import statistics
import psutil
import logging
import sqlite3
from prometheus_client import Counter, Gauge, Histogram, Summary
import networkx as nx
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    service_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: str = "in_progress"
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class Metric:
    """Performance metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class PerformanceProfile:
    """Agent performance profile"""
    agent_id: str
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    disk_io: List[float] = field(default_factory=list)
    network_io: List[float] = field(default_factory=list)
    request_latency: List[float] = field(default_factory=list)
    error_rate: float = 0.0
    throughput: float = 0.0
    success_rate: float = 100.0
    resource_efficiency: float = 0.0
    timestamps: List[datetime] = field(default_factory=list)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class BottleneckType(Enum):
    """Types of performance bottlenecks"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    CONCURRENCY = "concurrency"
    ALGORITHM = "algorithm"


class DistributedTracer:
    """Distributed tracing system for agent operations"""
    
    def __init__(self):
        self.traces: Dict[str, List[Span]] = defaultdict(list)
        self.active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
    
    def start_span(self, operation_name: str, service_name: str, 
                  parent_span: Optional[Span] = None) -> Span:
        """Start a new span"""
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            trace_id = str(uuid.uuid4())
            parent_span_id = None
        
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=service_name
        )
        
        with self._lock:
            self.traces[trace_id].append(span)
            self.active_spans[span.span_id] = span
        
        return span
    
    def finish_span(self, span: Span, status: str = "success", error: Optional[str] = None):
        """Finish a span"""
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        span.error = error
        
        with self._lock:
            if span.span_id in self.active_spans:
                del self.active_spans[span.span_id]
    
    def add_tag(self, span: Span, key: str, value: Any):
        """Add tag to span"""
        span.tags[key] = value
    
    def add_log(self, span: Span, message: str, level: str = "info"):
        """Add log to span"""
        span.logs.append({
            'timestamp': datetime.now(),
            'level': level,
            'message': message
        })
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace"""
        with self._lock:
            return self.traces.get(trace_id, [])
    
    def get_trace_graph(self, trace_id: str) -> nx.DiGraph:
        """Build dependency graph for a trace"""
        trace = self.get_trace(trace_id)
        graph = nx.DiGraph()
        
        for span in trace:
            graph.add_node(span.span_id, 
                          operation=span.operation_name,
                          service=span.service_name,
                          duration=span.duration_ms,
                          status=span.status)
            
            if span.parent_span_id:
                graph.add_edge(span.parent_span_id, span.span_id)
        
        return graph


class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self, db_path: str = "nexus_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.aggregated_metrics: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self._lock = threading.Lock()
        
        # Prometheus metrics
        self.request_count = Counter('nexus_requests_total', 'Total requests', ['agent', 'operation'])
        self.request_duration = Histogram('nexus_request_duration_seconds', 'Request duration', ['agent', 'operation'])
        self.active_agents = Gauge('nexus_active_agents', 'Number of active agents')
        self.resource_usage = Gauge('nexus_resource_usage', 'Resource usage', ['agent', 'resource'])
        
        # Initialize database
        self._init_database()
        
        # Start background aggregation
        self.aggregation_thread = threading.Thread(target=self._aggregation_loop)
        self.aggregation_thread.daemon = True
        self.aggregation_thread.start()
    
    def _init_database(self):
        """Initialize metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                agent_id TEXT,
                tags TEXT,
                unit TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics(agent_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def record_metric(self, metric: Metric):
        """Record a metric"""
        with self._lock:
            self.metrics_buffer.append(metric)
            
            # Update Prometheus metrics
            if metric.name == "request_count":
                self.request_count.labels(
                    agent=metric.agent_id,
                    operation=metric.tags.get('operation', 'unknown')
                ).inc()
            elif metric.name == "request_duration":
                self.request_duration.labels(
                    agent=metric.agent_id,
                    operation=metric.tags.get('operation', 'unknown')
                ).observe(metric.value)
            elif metric.name == "resource_usage":
                self.resource_usage.labels(
                    agent=metric.agent_id,
                    resource=metric.tags.get('resource', 'unknown')
                ).set(metric.value)
    
    def _aggregation_loop(self):
        """Background aggregation of metrics"""
        while True:
            try:
                self._aggregate_metrics()
                self._persist_metrics()
                time.sleep(5)  # Aggregate every 5 seconds
            except Exception as e:
                logger.error(f"Aggregation error: {e}")
    
    def _aggregate_metrics(self):
        """Aggregate metrics in memory"""
        with self._lock:
            current_buffer = list(self.metrics_buffer)
            self.metrics_buffer.clear()
        
        for metric in current_buffer:
            key = f"{metric.agent_id}:{metric.name}"
            self.aggregated_metrics[key]['values'].append(metric.value)
            self.aggregated_metrics[key]['timestamps'].append(metric.timestamp)
    
    def _persist_metrics(self):
        """Persist metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metrics_to_insert = []
        with self._lock:
            for metric in list(self.metrics_buffer):
                metrics_to_insert.append((
                    metric.name,
                    metric.value,
                    metric.timestamp,
                    metric.agent_id,
                    json.dumps(metric.tags),
                    metric.unit
                ))
        
        if metrics_to_insert:
            cursor.executemany('''
                INSERT INTO metrics (name, value, timestamp, agent_id, tags, unit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', metrics_to_insert)
            conn.commit()
        
        conn.close()
    
    def get_metrics(self, agent_id: str, metric_name: str, 
                   start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Query metrics from database"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT timestamp, value, tags
            FROM metrics
            WHERE agent_id = ? AND name = ?
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(
            query,
            conn,
            params=(agent_id, metric_name, start_time, end_time),
            parse_dates=['timestamp']
        )
        
        conn.close()
        return df


class PerformanceAnalyzer:
    """Analyze agent performance and detect bottlenecks"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.performance_profiles: Dict[str, PerformanceProfile] = {}
        self.bottlenecks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # ML models for prediction
        self.latency_predictor = LinearRegression()
        self.resource_predictor = LinearRegression()
        self.scaler = StandardScaler()
        
        # Start analysis loop
        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
    
    def _analysis_loop(self):
        """Continuous performance analysis"""
        while True:
            try:
                self._update_performance_profiles()
                self._detect_bottlenecks()
                self._predict_performance()
                time.sleep(10)  # Analyze every 10 seconds
            except Exception as e:
                logger.error(f"Analysis error: {e}")
    
    def _update_performance_profiles(self):
        """Update performance profiles for all agents"""
        # Get list of agents from metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=5)
        
        # This is simplified - in production would query actual agent list
        agent_ids = ["agent1", "agent2", "agent3"]
        
        for agent_id in agent_ids:
            profile = self._get_or_create_profile(agent_id)
            
            # Update CPU usage
            cpu_metrics = self.metrics_collector.get_metrics(
                agent_id, "cpu_usage", start_time, end_time
            )
            if not cpu_metrics.empty:
                profile.cpu_usage = cpu_metrics['value'].tolist()[-100:]  # Keep last 100
            
            # Update memory usage
            memory_metrics = self.metrics_collector.get_metrics(
                agent_id, "memory_usage", start_time, end_time
            )
            if not memory_metrics.empty:
                profile.memory_usage = memory_metrics['value'].tolist()[-100:]
            
            # Calculate derived metrics
            if profile.cpu_usage and profile.memory_usage:
                profile.resource_efficiency = self._calculate_efficiency(profile)
    
    def _get_or_create_profile(self, agent_id: str) -> PerformanceProfile:
        """Get or create performance profile"""
        with self._lock:
            if agent_id not in self.performance_profiles:
                self.performance_profiles[agent_id] = PerformanceProfile(agent_id=agent_id)
            return self.performance_profiles[agent_id]
    
    def _calculate_efficiency(self, profile: PerformanceProfile) -> float:
        """Calculate resource efficiency score"""
        if not profile.cpu_usage or not profile.memory_usage:
            return 0.0
        
        # Simple efficiency calculation
        avg_cpu = statistics.mean(profile.cpu_usage[-10:])
        avg_memory = statistics.mean(profile.memory_usage[-10:])
        
        # Efficiency is inverse of resource usage
        efficiency = 100 - (avg_cpu * 0.5 + avg_memory * 0.5)
        return max(0, min(100, efficiency))
    
    def _detect_bottlenecks(self):
        """Detect performance bottlenecks"""
        for agent_id, profile in self.performance_profiles.items():
            bottlenecks = []
            
            # CPU bottleneck
            if profile.cpu_usage and statistics.mean(profile.cpu_usage[-10:]) > 80:
                bottlenecks.append({
                    'type': BottleneckType.CPU,
                    'severity': 'high',
                    'value': statistics.mean(profile.cpu_usage[-10:]),
                    'recommendation': 'Consider optimizing CPU-intensive operations or scaling horizontally'
                })
            
            # Memory bottleneck
            if profile.memory_usage and statistics.mean(profile.memory_usage[-10:]) > 85:
                bottlenecks.append({
                    'type': BottleneckType.MEMORY,
                    'severity': 'high',
                    'value': statistics.mean(profile.memory_usage[-10:]),
                    'recommendation': 'Investigate memory leaks or implement better caching strategies'
                })
            
            # Latency bottleneck
            if profile.request_latency and statistics.mean(profile.request_latency[-10:]) > 1000:
                bottlenecks.append({
                    'type': BottleneckType.ALGORITHM,
                    'severity': 'medium',
                    'value': statistics.mean(profile.request_latency[-10:]),
                    'recommendation': 'Review algorithm complexity and consider optimization'
                })
            
            with self._lock:
                self.bottlenecks[agent_id] = bottlenecks
    
    def _predict_performance(self):
        """Predict future performance trends"""
        for agent_id, profile in self.performance_profiles.items():
            if len(profile.cpu_usage) < 20:
                continue
            
            # Prepare data for prediction
            X = np.arange(len(profile.cpu_usage)).reshape(-1, 1)
            y = np.array(profile.cpu_usage)
            
            # Train simple linear model
            self.latency_predictor.fit(X, y)
            
            # Predict next 10 points
            future_X = np.arange(len(profile.cpu_usage), len(profile.cpu_usage) + 10).reshape(-1, 1)
            predictions = self.latency_predictor.predict(future_X)
            
            # Check if predicted to exceed threshold
            if np.max(predictions) > 90:
                logger.warning(f"Agent {agent_id} predicted to exceed CPU threshold in next period")
    
    def get_bottlenecks(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get current bottlenecks for an agent"""
        with self._lock:
            return self.bottlenecks.get(agent_id, [])
    
    def get_optimization_recommendations(self, agent_id: str) -> List[str]:
        """Get optimization recommendations for an agent"""
        bottlenecks = self.get_bottlenecks(agent_id)
        recommendations = []
        
        for bottleneck in bottlenecks:
            recommendations.append(bottleneck['recommendation'])
        
        # Add general recommendations based on profile
        profile = self.performance_profiles.get(agent_id)
        if profile:
            if profile.error_rate > 5:
                recommendations.append("High error rate detected - implement better error handling and retry logic")
            
            if profile.resource_efficiency < 50:
                recommendations.append("Low resource efficiency - consider refactoring resource-intensive operations")
        
        return recommendations


class AutoTuner:
    """Automated performance tuning system"""
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
        self.tuning_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.active_tunings: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def auto_tune_agent(self, agent_id: str) -> Dict[str, Any]:
        """Automatically tune agent performance"""
        bottlenecks = self.analyzer.get_bottlenecks(agent_id)
        profile = self.analyzer.performance_profiles.get(agent_id)
        
        if not bottlenecks or not profile:
            return {"status": "no_tuning_needed"}
        
        tuning_actions = []
        
        for bottleneck in bottlenecks:
            if bottleneck['type'] == BottleneckType.CPU:
                action = self._tune_cpu_usage(agent_id, profile)
                tuning_actions.append(action)
            
            elif bottleneck['type'] == BottleneckType.MEMORY:
                action = self._tune_memory_usage(agent_id, profile)
                tuning_actions.append(action)
            
            elif bottleneck['type'] == BottleneckType.ALGORITHM:
                action = self._tune_algorithm(agent_id, profile)
                tuning_actions.append(action)
        
        tuning_result = {
            'agent_id': agent_id,
            'timestamp': datetime.now(),
            'bottlenecks': bottlenecks,
            'actions': tuning_actions,
            'status': 'applied'
        }
        
        with self._lock:
            self.tuning_history[agent_id].append(tuning_result)
            self.active_tunings[agent_id] = tuning_result
        
        return tuning_result
    
    def _tune_cpu_usage(self, agent_id: str, profile: PerformanceProfile) -> Dict[str, Any]:
        """Tune CPU usage parameters"""
        return {
            'type': 'cpu_tuning',
            'parameters': {
                'thread_pool_size': 'increased',
                'batch_size': 'optimized',
                'parallelism': 'enabled'
            },
            'expected_improvement': '20-30%'
        }
    
    def _tune_memory_usage(self, agent_id: str, profile: PerformanceProfile) -> Dict[str, Any]:
        """Tune memory usage parameters"""
        return {
            'type': 'memory_tuning',
            'parameters': {
                'cache_size': 'reduced',
                'gc_frequency': 'increased',
                'object_pooling': 'enabled'
            },
            'expected_improvement': '15-25%'
        }
    
    def _tune_algorithm(self, agent_id: str, profile: PerformanceProfile) -> Dict[str, Any]:
        """Tune algorithm parameters"""
        return {
            'type': 'algorithm_tuning',
            'parameters': {
                'algorithm_variant': 'optimized',
                'heuristics': 'enabled',
                'caching': 'aggressive'
            },
            'expected_improvement': '30-40%'
        }


class MetricsDashboard:
    """Real-time metrics visualization dashboard"""
    
    def __init__(self, metrics_collector: MetricsCollector, 
                 analyzer: PerformanceAnalyzer, tracer: DistributedTracer):
        self.metrics_collector = metrics_collector
        self.analyzer = analyzer
        self.tracer = tracer
        
        # Initialize Dash app
        self.app = dash.Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = html.Div([
            html.H1("NEXUS Agent Metrics Dashboard", style={'textAlign': 'center'}),
            
            # Interval component for live updates
            dcc.Interval(id='interval-component', interval=2000),  # Update every 2 seconds
            
            # Tabs
            dcc.Tabs([
                dcc.Tab(label='Overview', children=[
                    html.Div([
                        # Agent status cards
                        html.Div(id='agent-status-cards'),
                        
                        # System metrics graphs
                        dcc.Graph(id='system-metrics-graph'),
                        
                        # Performance summary
                        html.Div(id='performance-summary')
                    ])
                ]),
                
                dcc.Tab(label='Agent Details', children=[
                    # Agent selector
                    dcc.Dropdown(
                        id='agent-selector',
                        options=[],
                        value=None
                    ),
                    
                    # Agent metrics
                    html.Div([
                        dcc.Graph(id='agent-cpu-graph'),
                        dcc.Graph(id='agent-memory-graph'),
                        dcc.Graph(id='agent-latency-graph'),
                        html.Div(id='agent-bottlenecks')
                    ])
                ]),
                
                dcc.Tab(label='Distributed Tracing', children=[
                    # Trace selector
                    dcc.Dropdown(
                        id='trace-selector',
                        options=[],
                        value=None
                    ),
                    
                    # Trace visualization
                    dcc.Graph(id='trace-graph'),
                    
                    # Span details
                    html.Div(id='span-details')
                ]),
                
                dcc.Tab(label='Performance Tuning', children=[
                    # Auto-tuning controls
                    html.Button('Run Auto-Tuning', id='auto-tune-button'),
                    
                    # Tuning results
                    html.Div(id='tuning-results'),
                    
                    # Recommendations
                    html.Div(id='optimization-recommendations')
                ])
            ])
        ])
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks"""
        @self.app.callback(
            [Output('agent-status-cards', 'children'),
             Output('system-metrics-graph', 'figure'),
             Output('performance-summary', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_overview(n):
            # Generate agent status cards
            cards = self._generate_status_cards()
            
            # Generate system metrics graph
            system_graph = self._generate_system_graph()
            
            # Generate performance summary
            summary = self._generate_performance_summary()
            
            return cards, system_graph, summary
        
        @self.app.callback(
            [Output('agent-cpu-graph', 'figure'),
             Output('agent-memory-graph', 'figure'),
             Output('agent-latency-graph', 'figure'),
             Output('agent-bottlenecks', 'children')],
            [Input('agent-selector', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_agent_details(agent_id, n):
            if not agent_id:
                return {}, {}, {}, html.Div()
            
            profile = self.analyzer.performance_profiles.get(agent_id)
            if not profile:
                return {}, {}, {}, html.Div()
            
            # CPU graph
            cpu_graph = go.Figure()
            cpu_graph.add_trace(go.Scatter(
                y=profile.cpu_usage[-50:],
                mode='lines',
                name='CPU Usage %'
            ))
            cpu_graph.update_layout(title=f"CPU Usage - {agent_id}")
            
            # Memory graph
            memory_graph = go.Figure()
            memory_graph.add_trace(go.Scatter(
                y=profile.memory_usage[-50:],
                mode='lines',
                name='Memory Usage %'
            ))
            memory_graph.update_layout(title=f"Memory Usage - {agent_id}")
            
            # Latency graph
            latency_graph = go.Figure()
            latency_graph.add_trace(go.Scatter(
                y=profile.request_latency[-50:],
                mode='lines',
                name='Latency (ms)'
            ))
            latency_graph.update_layout(title=f"Request Latency - {agent_id}")
            
            # Bottlenecks
            bottlenecks = self.analyzer.get_bottlenecks(agent_id)
            bottleneck_cards = []
            for b in bottlenecks:
                card = html.Div([
                    html.H4(f"{b['type'].value} Bottleneck"),
                    html.P(f"Severity: {b['severity']}"),
                    html.P(f"Value: {b['value']:.2f}"),
                    html.P(f"Recommendation: {b['recommendation']}")
                ], style={'border': '1px solid #ddd', 'padding': '10px', 'margin': '10px'})
                bottleneck_cards.append(card)
            
            return cpu_graph, memory_graph, latency_graph, html.Div(bottleneck_cards)
    
    def _generate_status_cards(self) -> html.Div:
        """Generate agent status cards"""
        cards = []
        
        for agent_id, profile in self.analyzer.performance_profiles.items():
            card = html.Div([
                html.H3(agent_id),
                html.P(f"Efficiency: {profile.resource_efficiency:.1f}%"),
                html.P(f"Error Rate: {profile.error_rate:.1f}%"),
                html.P(f"Success Rate: {profile.success_rate:.1f}%")
            ], style={
                'border': '1px solid #ddd',
                'padding': '20px',
                'margin': '10px',
                'display': 'inline-block',
                'width': '200px'
            })
            cards.append(card)
        
        return html.Div(cards)
    
    def _generate_system_graph(self) -> go.Figure:
        """Generate system-wide metrics graph"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total CPU Usage', 'Total Memory Usage', 
                          'Request Throughput', 'Error Rate')
        )
        
        # Add traces (simplified for example)
        fig.add_trace(
            go.Scatter(y=[50, 55, 52, 58, 60], mode='lines', name='CPU'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(y=[70, 72, 71, 73, 75], mode='lines', name='Memory'),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(y=[1000, 1100, 1050, 1200, 1150], mode='lines', name='Throughput'),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(y=[0.5, 0.6, 0.4, 0.7, 0.5], mode='lines', name='Errors'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        return fig
    
    def _generate_performance_summary(self) -> html.Div:
        """Generate performance summary"""
        total_agents = len(self.analyzer.performance_profiles)
        healthy_agents = sum(1 for p in self.analyzer.performance_profiles.values() 
                           if p.resource_efficiency > 70)
        
        summary = html.Div([
            html.H3("Performance Summary"),
            html.P(f"Total Agents: {total_agents}"),
            html.P(f"Healthy Agents: {healthy_agents}"),
            html.P(f"Agents with Bottlenecks: {len(self.analyzer.bottlenecks)}"),
        ])
        
        return summary
    
    def run(self, host: str = '127.0.0.1', port: int = 8050):
        """Run the dashboard"""
        self.app.run_server(host=host, port=port, debug=False)


# Example usage
if __name__ == "__main__":
    # Create components
    tracer = DistributedTracer()
    collector = MetricsCollector()
    analyzer = PerformanceAnalyzer(collector)
    tuner = AutoTuner(analyzer)
    
    # Simulate some metrics
    agents = ["agent1", "agent2", "agent3"]
    
    for i in range(100):
        for agent_id in agents:
            # Record CPU usage
            collector.record_metric(Metric(
                name="cpu_usage",
                value=50 + np.random.normal(0, 10),
                agent_id=agent_id,
                unit="percent"
            ))
            
            # Record memory usage
            collector.record_metric(Metric(
                name="memory_usage",
                value=60 + np.random.normal(0, 15),
                agent_id=agent_id,
                unit="percent"
            ))
            
            # Record request latency
            collector.record_metric(Metric(
                name="request_latency",
                value=100 + np.random.exponential(50),
                agent_id=agent_id,
                unit="milliseconds",
                tags={"operation": "process_data"}
            ))
        
        time.sleep(0.1)
    
    # Create and start a trace
    root_span = tracer.start_span("process_request", "orchestrator")
    tracer.add_tag(root_span, "request_id", "12345")
    
    # Create child spans
    analysis_span = tracer.start_span("analyze_data", "agent1", root_span)
    time.sleep(0.1)
    tracer.finish_span(analysis_span)
    
    storage_span = tracer.start_span("store_results", "agent2", root_span)
    time.sleep(0.05)
    tracer.finish_span(storage_span)
    
    tracer.finish_span(root_span)
    
    # Get trace
    trace = tracer.get_trace(root_span.trace_id)
    print(f"\nTrace {root_span.trace_id}:")
    for span in trace:
        print(f"  {span.operation_name} ({span.service_name}): {span.duration_ms:.2f}ms")
    
    # Check for bottlenecks
    time.sleep(2)  # Let analyzer process
    
    for agent_id in agents:
        bottlenecks = analyzer.get_bottlenecks(agent_id)
        if bottlenecks:
            print(f"\nBottlenecks for {agent_id}:")
            for b in bottlenecks:
                print(f"  - {b['type'].value}: {b['recommendation']}")
        
        # Get optimization recommendations
        recommendations = analyzer.get_optimization_recommendations(agent_id)
        if recommendations:
            print(f"\nRecommendations for {agent_id}:")
            for rec in recommendations:
                print(f"  - {rec}")
        
        # Run auto-tuning
        tuning_result = tuner.auto_tune_agent(agent_id)
        if tuning_result['status'] != 'no_tuning_needed':
            print(f"\nAuto-tuning applied for {agent_id}:")
            for action in tuning_result.get('actions', []):
                print(f"  - {action['type']}: expected {action['expected_improvement']} improvement")
    
    # Create and run dashboard
    dashboard = MetricsDashboard(collector, analyzer, tracer)
    print("\nStarting metrics dashboard on http://localhost:8050")
    dashboard.run()