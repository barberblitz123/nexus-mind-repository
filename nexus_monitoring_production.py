#!/usr/bin/env python3
"""
NEXUS Production Monitoring System
==================================

Comprehensive production monitoring with APM integration, metrics collection,
log aggregation, error tracking, and automated alerting.

Features:
- APM integration (DataDog, New Relic, AppDynamics)
- Custom metrics and dashboards
- Log aggregation and analysis
- Error tracking (Sentry, Rollbar)
- Uptime monitoring
- Performance monitoring
- Cost optimization
- Automated alerting
"""

import os
import json
import yaml
import asyncio
import aiohttp
import psutil
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import datadog
import newrelic.agent
import sentry_sdk
from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, push_to_gateway
from elasticsearch import AsyncElasticsearch
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import redis.asyncio as redis
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging
from collections import deque
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class APMProvider(Enum):
    """APM providers"""
    DATADOG = "datadog"
    NEW_RELIC = "new_relic"
    APP_DYNAMICS = "app_dynamics"
    PROMETHEUS = "prometheus"
    CUSTOM = "custom"

@dataclass
class MetricConfig:
    """Metric configuration"""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    unit: str = ""
    buckets: Optional[List[float]] = None
    objectives: Optional[Dict[float, float]] = None

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    condition: str
    threshold: float
    duration: int  # seconds
    severity: AlertSeverity
    notification_channels: List[str] = field(default_factory=list)
    cooldown: int = 300  # seconds
    description: str = ""

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    app_name: str
    environment: str
    apm_provider: APMProvider
    metrics: List[MetricConfig] = field(default_factory=list)
    alert_rules: List[AlertRule] = field(default_factory=list)
    log_level: str = "INFO"
    sampling_rate: float = 1.0
    retention_days: int = 30
    custom_tags: Dict[str, str] = field(default_factory=dict)
    elasticsearch_url: Optional[str] = None
    influxdb_url: Optional[str] = None
    redis_url: Optional[str] = None
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    newrelic_license_key: Optional[str] = None

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    uptime_percentage: float
    response_time_ms: float
    error_rate: float
    last_check: datetime
    issues: List[str] = field(default_factory=list)

class MetricsCollector:
    """Collects and manages metrics"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.registry = CollectorRegistry()
        self.metrics = {}
        self._initialize_metrics()
        
    def _initialize_metrics(self):
        """Initialize metric collectors"""
        for metric_config in self.config.metrics:
            if metric_config.type == MetricType.COUNTER:
                metric = Counter(
                    metric_config.name,
                    metric_config.description,
                    labelnames=metric_config.labels,
                    registry=self.registry
                )
            elif metric_config.type == MetricType.GAUGE:
                metric = Gauge(
                    metric_config.name,
                    metric_config.description,
                    labelnames=metric_config.labels,
                    registry=self.registry
                )
            elif metric_config.type == MetricType.HISTOGRAM:
                metric = Histogram(
                    metric_config.name,
                    metric_config.description,
                    labelnames=metric_config.labels,
                    buckets=metric_config.buckets or Histogram.DEFAULT_BUCKETS,
                    registry=self.registry
                )
            elif metric_config.type == MetricType.SUMMARY:
                metric = Summary(
                    metric_config.name,
                    metric_config.description,
                    labelnames=metric_config.labels,
                    registry=self.registry
                )
            
            self.metrics[metric_config.name] = metric
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value"""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not found")
            return
        
        metric = self.metrics[name]
        labels = labels or {}
        
        try:
            if isinstance(metric, Counter):
                metric.labels(**labels).inc(value)
            elif isinstance(metric, Gauge):
                metric.labels(**labels).set(value)
            elif isinstance(metric, (Histogram, Summary)):
                metric.labels(**labels).observe(value)
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")
    
    async def push_metrics(self, gateway_url: str):
        """Push metrics to Prometheus gateway"""
        try:
            push_to_gateway(gateway_url, job=self.config.app_name, registry=self.registry)
        except Exception as e:
            logger.error(f"Error pushing metrics: {e}")

class APMIntegration:
    """Integrates with APM providers"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self._initialize_apm()
    
    def _initialize_apm(self):
        """Initialize APM provider"""
        if self.config.apm_provider == APMProvider.DATADOG:
            self._initialize_datadog()
        elif self.config.apm_provider == APMProvider.NEW_RELIC:
            self._initialize_newrelic()
        elif self.config.apm_provider == APMProvider.APP_DYNAMICS:
            self._initialize_appdynamics()
    
    def _initialize_datadog(self):
        """Initialize DataDog"""
        if self.config.datadog_api_key:
            datadog.initialize(
                api_key=self.config.datadog_api_key,
                app_key=os.environ.get('DATADOG_APP_KEY')
            )
            
            # Set default tags
            datadog.statsd.constant_tags = [
                f"env:{self.config.environment}",
                f"app:{self.config.app_name}"
            ] + [f"{k}:{v}" for k, v in self.config.custom_tags.items()]
    
    def _initialize_newrelic(self):
        """Initialize New Relic"""
        if self.config.newrelic_license_key:
            newrelic.agent.initialize(
                config_dict={
                    'license_key': self.config.newrelic_license_key,
                    'app_name': self.config.app_name,
                    'environment': self.config.environment
                }
            )
    
    def _initialize_appdynamics(self):
        """Initialize AppDynamics"""
        # AppDynamics initialization would go here
        pass
    
    async def send_metric(self, name: str, value: float, metric_type: str = "gauge", tags: Dict[str, str] = None):
        """Send metric to APM provider"""
        tags = tags or {}
        
        if self.config.apm_provider == APMProvider.DATADOG:
            if metric_type == "counter":
                datadog.statsd.increment(name, value, tags=self._format_tags(tags))
            elif metric_type == "gauge":
                datadog.statsd.gauge(name, value, tags=self._format_tags(tags))
            elif metric_type == "histogram":
                datadog.statsd.histogram(name, value, tags=self._format_tags(tags))
        
        elif self.config.apm_provider == APMProvider.NEW_RELIC:
            newrelic.agent.record_custom_metric(name, value)
    
    async def send_event(self, title: str, text: str, alert_type: str = "info", tags: Dict[str, str] = None):
        """Send event to APM provider"""
        tags = tags or {}
        
        if self.config.apm_provider == APMProvider.DATADOG:
            datadog.api.Event.create(
                title=title,
                text=text,
                alert_type=alert_type,
                tags=self._format_tags(tags)
            )
        
        elif self.config.apm_provider == APMProvider.NEW_RELIC:
            newrelic.agent.record_custom_event(
                'CustomEvent',
                {'title': title, 'text': text, 'alert_type': alert_type}
            )
    
    def _format_tags(self, tags: Dict[str, str]) -> List[str]:
        """Format tags for DataDog"""
        return [f"{k}:{v}" for k, v in tags.items()]

class LogAggregator:
    """Aggregates and analyzes logs"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.es_client = None
        if config.elasticsearch_url:
            self.es_client = AsyncElasticsearch([config.elasticsearch_url])
        
        self.log_buffer = deque(maxlen=10000)
        self.error_patterns = {}
    
    async def ingest_log(self, log_entry: Dict[str, Any]):
        """Ingest a log entry"""
        # Add metadata
        log_entry['@timestamp'] = datetime.utcnow().isoformat()
        log_entry['app'] = self.config.app_name
        log_entry['environment'] = self.config.environment
        
        # Buffer log
        self.log_buffer.append(log_entry)
        
        # Send to Elasticsearch if configured
        if self.es_client:
            try:
                await self.es_client.index(
                    index=f"logs-{self.config.app_name}-{datetime.utcnow().strftime('%Y.%m.%d')}",
                    body=log_entry
                )
            except Exception as e:
                logger.error(f"Error sending log to Elasticsearch: {e}")
        
        # Analyze for errors
        if log_entry.get('level', '').upper() in ['ERROR', 'CRITICAL']:
            await self._analyze_error(log_entry)
    
    async def _analyze_error(self, log_entry: Dict[str, Any]):
        """Analyze error logs for patterns"""
        error_message = log_entry.get('message', '')
        
        # Simple pattern matching
        for pattern in ['timeout', 'connection refused', 'out of memory', '404', '500']:
            if pattern.lower() in error_message.lower():
                self.error_patterns[pattern] = self.error_patterns.get(pattern, 0) + 1
    
    async def search_logs(self, query: str, time_range: str = "15m") -> List[Dict[str, Any]]:
        """Search logs"""
        if not self.es_client:
            # Search in buffer
            results = []
            for log in self.log_buffer:
                if query.lower() in str(log).lower():
                    results.append(log)
            return results[-100:]  # Return last 100 matches
        
        # Search in Elasticsearch
        try:
            response = await self.es_client.search(
                index=f"logs-{self.config.app_name}-*",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"query_string": {"query": query}},
                                {"range": {"@timestamp": {"gte": f"now-{time_range}"}}}
                            ]
                        }
                    },
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "size": 100
                }
            )
            
            return [hit['_source'] for hit in response['hits']['hits']]
        
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []
    
    async def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        return {
            "total_errors": sum(self.error_patterns.values()),
            "patterns": dict(self.error_patterns),
            "recent_errors": [
                log for log in list(self.log_buffer)[-100:]
                if log.get('level', '').upper() in ['ERROR', 'CRITICAL']
            ]
        }

class ErrorTracker:
    """Tracks and reports errors"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self._initialize_sentry()
        self.error_counts = {}
        self.error_history = deque(maxlen=1000)
    
    def _initialize_sentry(self):
        """Initialize Sentry error tracking"""
        if self.config.sentry_dsn:
            sentry_sdk.init(
                dsn=self.config.sentry_dsn,
                environment=self.config.environment,
                traces_sample_rate=self.config.sampling_rate,
                attach_stacktrace=True,
                send_default_pii=False
            )
            
            # Set context
            sentry_sdk.set_tag("app", self.config.app_name)
            for key, value in self.config.custom_tags.items():
                sentry_sdk.set_tag(key, value)
    
    async def capture_exception(self, exception: Exception, context: Dict[str, Any] = None):
        """Capture an exception"""
        # Record in history
        error_info = {
            "timestamp": datetime.utcnow(),
            "type": type(exception).__name__,
            "message": str(exception),
            "context": context or {}
        }
        self.error_history.append(error_info)
        
        # Update counts
        error_type = type(exception).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Send to Sentry
        if self.config.sentry_dsn:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_exception(exception)
        
        logger.error(f"Captured exception: {exception}", exc_info=True)
    
    async def capture_message(self, message: str, level: str = "error", context: Dict[str, Any] = None):
        """Capture a message"""
        # Send to Sentry
        if self.config.sentry_dsn:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_message(message, level=level)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        recent_errors = [e for e in self.error_history if 
                        e['timestamp'] > datetime.utcnow() - timedelta(hours=1)]
        
        return {
            "total_errors": len(self.error_history),
            "errors_last_hour": len(recent_errors),
            "error_types": dict(self.error_counts),
            "recent_errors": list(recent_errors)[-10:]
        }

class PerformanceMonitor:
    """Monitors application performance"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.response_times = deque(maxlen=1000)
        self.throughput_history = deque(maxlen=1000)
        self.resource_usage = deque(maxlen=1000)
        self.influx_client = None
        
        if config.influxdb_url:
            self.influx_client = InfluxDBClient(url=config.influxdb_url)
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
    
    async def record_request(self, endpoint: str, method: str, duration_ms: float, 
                           status_code: int, size_bytes: int = 0):
        """Record API request metrics"""
        # Store in memory
        self.response_times.append(duration_ms)
        
        # Create data point
        point = {
            "measurement": "api_requests",
            "tags": {
                "app": self.config.app_name,
                "environment": self.config.environment,
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code)
            },
            "fields": {
                "duration_ms": duration_ms,
                "size_bytes": size_bytes
            },
            "time": datetime.utcnow()
        }
        
        # Send to InfluxDB
        if self.influx_client:
            try:
                self.write_api.write(
                    bucket=f"{self.config.app_name}-metrics",
                    record=Point.from_dict(point)
                )
            except Exception as e:
                logger.error(f"Error writing to InfluxDB: {e}")
    
    async def record_system_metrics(self):
        """Record system resource metrics"""
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / 1024 / 1024,
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / 1024 / 1024 / 1024
        }
        
        # Store in memory
        self.resource_usage.append({
            "timestamp": datetime.utcnow(),
            **metrics
        })
        
        # Send to monitoring
        if self.influx_client:
            point = Point("system_metrics") \
                .tag("app", self.config.app_name) \
                .tag("environment", self.config.environment) \
                .tag("host", socket.gethostname())
            
            for key, value in metrics.items():
                point = point.field(key, value)
            
            try:
                self.write_api.write(
                    bucket=f"{self.config.app_name}-metrics",
                    record=point
                )
            except Exception as e:
                logger.error(f"Error writing system metrics: {e}")
        
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.response_times:
            return {
                "avg_response_time": 0,
                "p50_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0
            }
        
        response_times = list(self.response_times)
        response_times.sort()
        
        return {
            "avg_response_time": statistics.mean(response_times),
            "p50_response_time": statistics.median(response_times),
            "p95_response_time": response_times[int(len(response_times) * 0.95)],
            "p99_response_time": response_times[int(len(response_times) * 0.99)],
            "total_requests": len(response_times)
        }
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        if not self.resource_usage:
            return {}
        
        latest = self.resource_usage[-1]
        
        # Calculate averages
        cpu_values = [r['cpu_percent'] for r in self.resource_usage]
        memory_values = [r['memory_percent'] for r in self.resource_usage]
        
        return {
            "current": latest,
            "averages": {
                "cpu_percent": statistics.mean(cpu_values),
                "memory_percent": statistics.mean(memory_values)
            }
        }

class UptimeMonitor:
    """Monitors service uptime"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.checks = deque(maxlen=10000)
        self.service_status = {}
        self.redis_client = None
        
        if config.redis_url:
            asyncio.create_task(self._connect_redis())
    
    async def _connect_redis(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(self.config.redis_url)
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
    
    async def check_endpoint(self, url: str, timeout: int = 10) -> Tuple[bool, float]:
        """Check if endpoint is responding"""
        start_time = datetime.utcnow()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    is_healthy = response.status < 500
                    
                    # Record check
                    check_result = {
                        "timestamp": start_time,
                        "url": url,
                        "status_code": response.status,
                        "response_time_ms": response_time,
                        "is_healthy": is_healthy
                    }
                    
                    self.checks.append(check_result)
                    
                    # Store in Redis if available
                    if self.redis_client:
                        await self.redis_client.lpush(
                            f"uptime:{url}",
                            json.dumps(check_result, default=str)
                        )
                        await self.redis_client.ltrim(f"uptime:{url}", 0, 1000)
                    
                    return is_healthy, response_time
                    
        except Exception as e:
            logger.error(f"Error checking endpoint {url}: {e}")
            
            # Record failed check
            check_result = {
                "timestamp": start_time,
                "url": url,
                "error": str(e),
                "is_healthy": False
            }
            
            self.checks.append(check_result)
            
            return False, 0
    
    async def monitor_services(self, services: List[Dict[str, Any]]):
        """Monitor multiple services"""
        for service in services:
            url = service['url']
            is_healthy, response_time = await self.check_endpoint(url)
            
            # Calculate uptime
            recent_checks = [c for c in self.checks if c['url'] == url and 
                           c['timestamp'] > datetime.utcnow() - timedelta(hours=24)]
            
            if recent_checks:
                healthy_checks = sum(1 for c in recent_checks if c.get('is_healthy', False))
                uptime_percentage = (healthy_checks / len(recent_checks)) * 100
            else:
                uptime_percentage = 100.0 if is_healthy else 0.0
            
            # Update service status
            self.service_status[service['name']] = ServiceHealth(
                service_name=service['name'],
                status='healthy' if is_healthy else 'unhealthy',
                uptime_percentage=uptime_percentage,
                response_time_ms=response_time,
                error_rate=100 - uptime_percentage,
                last_check=datetime.utcnow(),
                issues=[] if is_healthy else [f"Service returned unhealthy status"]
            )
    
    def get_uptime_report(self) -> Dict[str, Any]:
        """Get uptime report"""
        return {
            "services": {
                name: {
                    "status": health.status,
                    "uptime": f"{health.uptime_percentage:.2f}%",
                    "response_time": f"{health.response_time_ms:.2f}ms",
                    "last_check": health.last_check.isoformat()
                }
                for name, health in self.service_status.items()
            },
            "overall_health": all(h.status == 'healthy' for h in self.service_status.values())
        }

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.notification_channels = self._setup_notification_channels()
    
    def _setup_notification_channels(self) -> Dict[str, Any]:
        """Setup notification channels"""
        channels = {}
        
        # Slack
        if os.environ.get('SLACK_WEBHOOK_URL'):
            channels['slack'] = {
                'type': 'slack',
                'webhook_url': os.environ.get('SLACK_WEBHOOK_URL')
            }
        
        # Email
        if os.environ.get('SMTP_HOST'):
            channels['email'] = {
                'type': 'email',
                'smtp_host': os.environ.get('SMTP_HOST'),
                'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
                'smtp_user': os.environ.get('SMTP_USER'),
                'smtp_password': os.environ.get('SMTP_PASSWORD')
            }
        
        # PagerDuty
        if os.environ.get('PAGERDUTY_KEY'):
            channels['pagerduty'] = {
                'type': 'pagerduty',
                'integration_key': os.environ.get('PAGERDUTY_KEY')
            }
        
        return channels
    
    async def check_alert_rules(self, metrics: Dict[str, float]):
        """Check if any alert rules are triggered"""
        for rule in self.config.alert_rules:
            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue
            
            # Evaluate condition
            triggered = self._evaluate_condition(metric_value, rule.condition, rule.threshold)
            
            alert_key = f"{rule.name}:{rule.metric}"
            
            if triggered:
                # Check if alert is already active
                if alert_key not in self.active_alerts:
                    # New alert
                    await self._trigger_alert(rule, metric_value)
                    self.active_alerts[alert_key] = {
                        'rule': rule,
                        'triggered_at': datetime.utcnow(),
                        'value': metric_value
                    }
                else:
                    # Update existing alert
                    self.active_alerts[alert_key]['value'] = metric_value
            else:
                # Check if alert should be resolved
                if alert_key in self.active_alerts:
                    await self._resolve_alert(rule, metric_value)
                    del self.active_alerts[alert_key]
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == '>':
            return value > threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<':
            return value < threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return value == threshold
        elif condition == '!=':
            return value != threshold
        else:
            logger.error(f"Unknown condition: {condition}")
            return False
    
    async def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert"""
        alert_info = {
            'alert_id': f"{rule.name}-{datetime.utcnow().timestamp()}",
            'rule_name': rule.name,
            'metric': rule.metric,
            'value': value,
            'threshold': rule.threshold,
            'severity': rule.severity.value,
            'timestamp': datetime.utcnow(),
            'description': rule.description or f"{rule.metric} {rule.condition} {rule.threshold}"
        }
        
        # Add to history
        self.alert_history.append(alert_info)
        
        # Send notifications
        for channel_name in rule.notification_channels:
            if channel_name in self.notification_channels:
                await self._send_notification(channel_name, alert_info)
        
        console.print(f"[red]Alert triggered: {rule.name} - {rule.metric}={value}[/red]")
    
    async def _resolve_alert(self, rule: AlertRule, value: float):
        """Resolve an alert"""
        alert_info = {
            'alert_id': f"{rule.name}-resolved-{datetime.utcnow().timestamp()}",
            'rule_name': rule.name,
            'metric': rule.metric,
            'value': value,
            'severity': 'resolved',
            'timestamp': datetime.utcnow(),
            'description': f"Alert resolved: {rule.name}"
        }
        
        # Add to history
        self.alert_history.append(alert_info)
        
        # Send resolution notifications
        for channel_name in rule.notification_channels:
            if channel_name in self.notification_channels:
                await self._send_notification(channel_name, alert_info, resolved=True)
        
        console.print(f"[green]Alert resolved: {rule.name}[/green]")
    
    async def _send_notification(self, channel_name: str, alert_info: Dict[str, Any], resolved: bool = False):
        """Send notification to channel"""
        channel = self.notification_channels.get(channel_name)
        if not channel:
            return
        
        try:
            if channel['type'] == 'slack':
                await self._send_slack_notification(channel, alert_info, resolved)
            elif channel['type'] == 'email':
                await self._send_email_notification(channel, alert_info, resolved)
            elif channel['type'] == 'pagerduty':
                await self._send_pagerduty_notification(channel, alert_info, resolved)
        except Exception as e:
            logger.error(f"Error sending notification to {channel_name}: {e}")
    
    async def _send_slack_notification(self, channel: Dict[str, Any], alert_info: Dict[str, Any], resolved: bool):
        """Send Slack notification"""
        color = "good" if resolved else {
            "info": "good",
            "warning": "warning",
            "error": "danger",
            "critical": "danger"
        }.get(alert_info['severity'], "danger")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"{'🟢' if resolved else '🔴'} {alert_info['rule_name']}",
                "text": alert_info['description'],
                "fields": [
                    {"title": "Metric", "value": alert_info['metric'], "short": True},
                    {"title": "Value", "value": str(alert_info['value']), "short": True},
                    {"title": "Environment", "value": self.config.environment, "short": True},
                    {"title": "App", "value": self.config.app_name, "short": True}
                ],
                "footer": "NEXUS Monitoring",
                "ts": int(alert_info['timestamp'].timestamp())
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(channel['webhook_url'], json=payload)
    
    async def _send_email_notification(self, channel: Dict[str, Any], alert_info: Dict[str, Any], resolved: bool):
        """Send email notification"""
        # Email implementation would go here
        pass
    
    async def _send_pagerduty_notification(self, channel: Dict[str, Any], alert_info: Dict[str, Any], resolved: bool):
        """Send PagerDuty notification"""
        event_action = "resolve" if resolved else "trigger"
        
        payload = {
            "routing_key": channel['integration_key'],
            "event_action": event_action,
            "dedup_key": alert_info['rule_name'],
            "payload": {
                "summary": alert_info['description'],
                "severity": alert_info['severity'],
                "source": self.config.app_name,
                "custom_details": {
                    "metric": alert_info['metric'],
                    "value": alert_info['value'],
                    "environment": self.config.environment
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload
            )
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        return {
            "active_alerts": len(self.active_alerts),
            "alerts": [
                {
                    "name": alert['rule'].name,
                    "metric": alert['rule'].metric,
                    "value": alert['value'],
                    "triggered_at": alert['triggered_at'].isoformat(),
                    "duration": (datetime.utcnow() - alert['triggered_at']).total_seconds()
                }
                for alert in self.active_alerts.values()
            ],
            "recent_alerts": [
                {
                    "rule_name": alert['rule_name'],
                    "severity": alert['severity'],
                    "timestamp": alert['timestamp'].isoformat()
                }
                for alert in list(self.alert_history)[-10:]
            ]
        }

class CostOptimizer:
    """Monitors and optimizes cloud costs"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.cost_data = deque(maxlen=1000)
        self.recommendations = []
    
    async def analyze_costs(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze costs and provide recommendations"""
        # Mock cost analysis
        costs = {
            "compute": usage_data.get("compute_hours", 0) * 0.10,
            "storage": usage_data.get("storage_gb", 0) * 0.023,
            "bandwidth": usage_data.get("bandwidth_gb", 0) * 0.09,
            "database": usage_data.get("database_hours", 0) * 0.15
        }
        
        total_cost = sum(costs.values())
        
        # Store cost data
        self.cost_data.append({
            "timestamp": datetime.utcnow(),
            "costs": costs,
            "total": total_cost
        })
        
        # Generate recommendations
        self.recommendations = []
        
        if usage_data.get("compute_utilization", 0) < 20:
            self.recommendations.append({
                "type": "compute",
                "recommendation": "Consider downsizing compute instances",
                "potential_savings": costs["compute"] * 0.3
            })
        
        if usage_data.get("storage_access_frequency", 1) < 0.1:
            self.recommendations.append({
                "type": "storage",
                "recommendation": "Move infrequently accessed data to cold storage",
                "potential_savings": costs["storage"] * 0.7
            })
        
        return {
            "current_costs": costs,
            "total_cost": total_cost,
            "recommendations": self.recommendations,
            "projected_monthly": total_cost * 30
        }
    
    def get_cost_trends(self) -> Dict[str, Any]:
        """Get cost trends"""
        if not self.cost_data:
            return {"daily_average": 0, "trend": "stable"}
        
        # Calculate daily average
        daily_costs = [d['total'] for d in self.cost_data]
        daily_average = statistics.mean(daily_costs)
        
        # Calculate trend
        if len(daily_costs) > 7:
            recent_average = statistics.mean(daily_costs[-7:])
            older_average = statistics.mean(daily_costs[:-7])
            
            if recent_average > older_average * 1.1:
                trend = "increasing"
            elif recent_average < older_average * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "daily_average": daily_average,
            "trend": trend,
            "recommendations": self.recommendations
        }

class MonitoringDashboard:
    """Real-time monitoring dashboard"""
    
    def __init__(self, monitoring_system):
        self.monitoring = monitoring_system
        self.layout = Layout()
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup dashboard layout"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="metrics", ratio=2),
            Layout(name="alerts", ratio=1)
        )
        
        self.layout["metrics"].split_column(
            Layout(name="performance"),
            Layout(name="resources")
        )
    
    def generate(self) -> Layout:
        """Generate dashboard content"""
        # Header
        self.layout["header"].update(Panel(
            f"[bold cyan]NEXUS Production Monitoring[/bold cyan]\n"
            f"Environment: {self.monitoring.config.environment} | "
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            style="cyan"
        ))
        
        # Performance metrics
        perf_summary = self.monitoring.performance_monitor.get_performance_summary()
        perf_table = Table(title="Performance Metrics")
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="green")
        
        perf_table.add_row("Avg Response Time", f"{perf_summary.get('avg_response_time', 0):.2f}ms")
        perf_table.add_row("P95 Response Time", f"{perf_summary.get('p95_response_time', 0):.2f}ms")
        perf_table.add_row("P99 Response Time", f"{perf_summary.get('p99_response_time', 0):.2f}ms")
        perf_table.add_row("Total Requests", str(perf_summary.get('total_requests', 0)))
        
        self.layout["performance"].update(perf_table)
        
        # Resource usage
        resource_usage = self.monitoring.performance_monitor.get_resource_usage()
        if resource_usage:
            resource_table = Table(title="Resource Usage")
            resource_table.add_column("Resource", style="cyan")
            resource_table.add_column("Current", style="yellow")
            resource_table.add_column("Average", style="green")
            
            current = resource_usage.get('current', {})
            averages = resource_usage.get('averages', {})
            
            resource_table.add_row(
                "CPU", 
                f"{current.get('cpu_percent', 0):.1f}%",
                f"{averages.get('cpu_percent', 0):.1f}%"
            )
            resource_table.add_row(
                "Memory",
                f"{current.get('memory_percent', 0):.1f}%",
                f"{averages.get('memory_percent', 0):.1f}%"
            )
            resource_table.add_row(
                "Disk",
                f"{current.get('disk_percent', 0):.1f}%",
                "-"
            )
            
            self.layout["resources"].update(resource_table)
        
        # Alerts
        alert_summary = self.monitoring.alert_manager.get_alert_summary()
        alert_text = f"[bold]Active Alerts: {alert_summary['active_alerts']}[/bold]\n\n"
        
        for alert in alert_summary['alerts'][:5]:  # Show top 5
            duration = int(alert['duration'])
            alert_text += f"⚠️  {alert['name']} - {alert['metric']}={alert['value']:.2f} ({duration}s)\n"
        
        self.layout["alerts"].update(Panel(alert_text, title="Alerts", style="red" if alert_summary['active_alerts'] > 0 else "green"))
        
        # Footer
        uptime_report = self.monitoring.uptime_monitor.get_uptime_report()
        overall_health = "🟢 Healthy" if uptime_report.get('overall_health', True) else "🔴 Unhealthy"
        
        self.layout["footer"].update(Panel(
            f"Overall System Health: {overall_health}",
            style="green" if uptime_report.get('overall_health', True) else "red"
        ))
        
        return self.layout

class ProductionMonitoring:
    """Main production monitoring system"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        
        # Initialize components
        self.metrics_collector = MetricsCollector(config)
        self.apm_integration = APMIntegration(config)
        self.log_aggregator = LogAggregator(config)
        self.error_tracker = ErrorTracker(config)
        self.performance_monitor = PerformanceMonitor(config)
        self.uptime_monitor = UptimeMonitor(config)
        self.alert_manager = AlertManager(config)
        self.cost_optimizer = CostOptimizer(config)
        
        # Monitoring tasks
        self.monitoring_tasks = []
    
    async def start(self):
        """Start monitoring system"""
        console.print("[cyan]Starting production monitoring system...[/cyan]")
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._collect_metrics_loop()),
            asyncio.create_task(self._check_alerts_loop()),
            asyncio.create_task(self._monitor_uptime_loop()),
            asyncio.create_task(self._optimize_costs_loop())
        ]
        
        console.print("[green]Monitoring system started[/green]")
    
    async def stop(self):
        """Stop monitoring system"""
        console.print("[yellow]Stopping monitoring system...[/yellow]")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        console.print("[green]Monitoring system stopped[/green]")
    
    async def _collect_metrics_loop(self):
        """Continuously collect metrics"""
        while True:
            try:
                # Collect system metrics
                system_metrics = await self.performance_monitor.record_system_metrics()
                
                # Send to APM
                for metric_name, value in system_metrics.items():
                    await self.apm_integration.send_metric(
                        f"system.{metric_name}",
                        value,
                        metric_type="gauge"
                    )
                
                # Push to Prometheus if configured
                if os.environ.get('PROMETHEUS_GATEWAY'):
                    await self.metrics_collector.push_metrics(
                        os.environ.get('PROMETHEUS_GATEWAY')
                    )
                
                await asyncio.sleep(10)  # Collect every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(10)
    
    async def _check_alerts_loop(self):
        """Continuously check alert rules"""
        while True:
            try:
                # Get current metrics
                perf_summary = self.performance_monitor.get_performance_summary()
                resource_usage = self.performance_monitor.get_resource_usage()
                
                metrics = {
                    "response_time_avg": perf_summary.get('avg_response_time', 0),
                    "response_time_p95": perf_summary.get('p95_response_time', 0),
                    "response_time_p99": perf_summary.get('p99_response_time', 0)
                }
                
                if resource_usage:
                    current = resource_usage.get('current', {})
                    metrics.update({
                        "cpu_percent": current.get('cpu_percent', 0),
                        "memory_percent": current.get('memory_percent', 0),
                        "disk_percent": current.get('disk_percent', 0)
                    })
                
                # Check alert rules
                await self.alert_manager.check_alert_rules(metrics)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_uptime_loop(self):
        """Continuously monitor service uptime"""
        # Define services to monitor
        services = [
            {"name": "API", "url": f"http://localhost:8000/health"},
            {"name": "Frontend", "url": f"http://localhost:3000"},
            {"name": "Database", "url": f"http://localhost:5432"}
        ]
        
        while True:
            try:
                await self.uptime_monitor.monitor_services(services)
                
                # Send uptime metrics
                for service_name, health in self.uptime_monitor.service_status.items():
                    await self.apm_integration.send_metric(
                        f"service.uptime",
                        health.uptime_percentage,
                        metric_type="gauge",
                        tags={"service": service_name}
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in uptime monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _optimize_costs_loop(self):
        """Continuously analyze and optimize costs"""
        while True:
            try:
                # Mock usage data (in production, would get from cloud provider APIs)
                usage_data = {
                    "compute_hours": 24,
                    "compute_utilization": 45,
                    "storage_gb": 500,
                    "storage_access_frequency": 0.3,
                    "bandwidth_gb": 100,
                    "database_hours": 24
                }
                
                # Analyze costs
                cost_analysis = await self.cost_optimizer.analyze_costs(usage_data)
                
                # Send cost metrics
                await self.apm_integration.send_metric(
                    "cloud.cost.daily",
                    cost_analysis['total_cost'],
                    metric_type="gauge"
                )
                
                # Log recommendations
                for rec in cost_analysis['recommendations']:
                    await self.log_aggregator.ingest_log({
                        "level": "INFO",
                        "message": f"Cost optimization: {rec['recommendation']}",
                        "potential_savings": rec['potential_savings']
                    })
                
                await asyncio.sleep(3600)  # Check every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cost optimization: {e}")
                await asyncio.sleep(3600)
    
    async def show_dashboard(self):
        """Show live monitoring dashboard"""
        dashboard = MonitoringDashboard(self)
        
        with Live(dashboard.generate(), refresh_per_second=1, console=console) as live:
            while True:
                await asyncio.sleep(1)
                live.update(dashboard.generate())
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "config": {
                "app_name": self.config.app_name,
                "environment": self.config.environment,
                "apm_provider": self.config.apm_provider.value
            },
            "performance": self.performance_monitor.get_performance_summary(),
            "resources": self.performance_monitor.get_resource_usage(),
            "uptime": self.uptime_monitor.get_uptime_report(),
            "alerts": self.alert_manager.get_alert_summary(),
            "errors": self.error_tracker.get_error_stats(),
            "costs": self.cost_optimizer.get_cost_trends()
        }


async def main():
    """Example usage and CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS Production Monitoring")
    parser.add_argument("command", choices=["start", "dashboard", "status", "test-alert"])
    parser.add_argument("--config", "-c", help="Configuration file (YAML)")
    parser.add_argument("--app", "-a", default="nexus", help="Application name")
    parser.add_argument("--env", "-e", default="production", help="Environment")
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        with open(args.config) as f:
            config_data = yaml.safe_load(f)
        config = MonitoringConfig(**config_data)
    else:
        # Default configuration
        config = MonitoringConfig(
            app_name=args.app,
            environment=args.env,
            apm_provider=APMProvider.PROMETHEUS,
            metrics=[
                MetricConfig(
                    name="http_requests_total",
                    type=MetricType.COUNTER,
                    description="Total HTTP requests"
                ),
                MetricConfig(
                    name="http_request_duration_seconds",
                    type=MetricType.HISTOGRAM,
                    description="HTTP request duration"
                )
            ],
            alert_rules=[
                AlertRule(
                    name="High CPU Usage",
                    metric="cpu_percent",
                    condition=">",
                    threshold=80,
                    duration=300,
                    severity=AlertSeverity.WARNING,
                    notification_channels=["slack"]
                ),
                AlertRule(
                    name="High Memory Usage",
                    metric="memory_percent",
                    condition=">",
                    threshold=90,
                    duration=300,
                    severity=AlertSeverity.ERROR,
                    notification_channels=["slack", "pagerduty"]
                ),
                AlertRule(
                    name="Slow Response Time",
                    metric="response_time_p95",
                    condition=">",
                    threshold=1000,
                    duration=60,
                    severity=AlertSeverity.WARNING,
                    notification_channels=["slack"]
                )
            ]
        )
    
    monitoring = ProductionMonitoring(config)
    
    if args.command == "start":
        await monitoring.start()
        console.print("[cyan]Monitoring system running. Press Ctrl+C to stop.[/cyan]")
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await monitoring.stop()
            
    elif args.command == "dashboard":
        await monitoring.start()
        
        try:
            await monitoring.show_dashboard()
        except KeyboardInterrupt:
            await monitoring.stop()
            
    elif args.command == "status":
        await monitoring.start()
        status = await monitoring.get_status()
        
        # Display status
        console.print(Panel(
            f"[bold]Application:[/bold] {status['config']['app_name']}\n"
            f"[bold]Environment:[/bold] {status['config']['environment']}\n"
            f"[bold]APM Provider:[/bold] {status['config']['apm_provider']}",
            title="Monitoring Status"
        ))
        
        # Performance metrics
        perf = status['performance']
        console.print(Panel(
            f"[bold]Avg Response Time:[/bold] {perf.get('avg_response_time', 0):.2f}ms\n"
            f"[bold]P95 Response Time:[/bold] {perf.get('p95_response_time', 0):.2f}ms\n"
            f"[bold]Total Requests:[/bold] {perf.get('total_requests', 0)}",
            title="Performance"
        ))
        
        # Alerts
        alerts = status['alerts']
        console.print(Panel(
            f"[bold]Active Alerts:[/bold] {alerts['active_alerts']}",
            title="Alerts",
            style="red" if alerts['active_alerts'] > 0 else "green"
        ))
        
        await monitoring.stop()
        
    elif args.command == "test-alert":
        await monitoring.start()
        
        # Trigger test alert
        console.print("[yellow]Triggering test alert...[/yellow]")
        
        # Simulate high CPU
        await monitoring.alert_manager.check_alert_rules({
            "cpu_percent": 95,
            "memory_percent": 50,
            "response_time_p95": 500
        })
        
        await asyncio.sleep(5)
        await monitoring.stop()


if __name__ == "__main__":
    asyncio.run(main())