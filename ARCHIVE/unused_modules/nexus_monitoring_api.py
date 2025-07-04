#!/usr/bin/env python3
"""
NEXUS Monitoring API
RESTful API, GraphQL, and WebSocket interfaces for monitoring
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

import aiohttp
import prometheus_client
import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from graphene import (
    Boolean, Field, Float, Int, List as GrapheneList,
    ObjectType, Schema, String
)
from pydantic import BaseModel, Field as PydanticField
from redis import asyncio as aioredis
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

app = FastAPI(title="NEXUS Monitoring API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricValue(BaseModel):
    """Metric value model"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = PydanticField(default_factory=dict)


class Metric(BaseModel):
    """Metric model"""
    name: str
    type: MetricType
    description: str
    unit: Optional[str] = None
    values: List[MetricValue] = PydanticField(default_factory=list)
    current_value: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Alert(BaseModel):
    """Alert model"""
    id: str
    name: str
    severity: AlertSeverity
    condition: str
    message: str
    metric_name: str
    threshold: float
    current_value: Optional[float] = None
    triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_active: bool = True
    labels: Dict[str, str] = PydanticField(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Dashboard(BaseModel):
    """Dashboard model"""
    id: str
    name: str
    description: str
    panels: List[Dict[str, Any]] = PydanticField(default_factory=list)
    refresh_interval: int = 30
    time_range: str = "1h"
    created_at: datetime = PydanticField(default_factory=datetime.now)
    updated_at: datetime = PydanticField(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SLATarget(BaseModel):
    """SLA target model"""
    name: str
    description: str
    target_percentage: float
    measurement_window: str
    metric_query: str
    current_percentage: Optional[float] = None
    is_meeting_target: bool = True
    error_budget_remaining: Optional[float] = None


class Report(BaseModel):
    """Report model"""
    id: str
    name: str
    type: str
    parameters: Dict[str, Any] = PydanticField(default_factory=dict)
    schedule: Optional[str] = None
    recipients: List[str] = PydanticField(default_factory=list)
    last_generated: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricAggregation(BaseModel):
    """Metric aggregation request"""
    metric_name: str
    aggregation_type: str = "avg"  # avg, sum, min, max, count
    time_range: str = "1h"
    group_by: Optional[List[str]] = None
    filters: Optional[Dict[str, str]] = None


class MetricsStore:
    """In-memory metrics store with Redis backing"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.metric_values: Dict[str, Deque[MetricValue]] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.alerts: Dict[str, Alert] = {}
        self.dashboards: Dict[str, Dashboard] = {}
        self.sla_targets: Dict[str, SLATarget] = {}
        self.reports: Dict[str, Report] = {}
        self.redis: Optional[aioredis.Redis] = None
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        self.prom_metrics = {
            'api_requests': prometheus_client.Counter(
                'nexus_api_requests_total',
                'Total API requests',
                ['method', 'endpoint', 'status']
            ),
            'api_latency': prometheus_client.Histogram(
                'nexus_api_latency_seconds',
                'API request latency',
                ['method', 'endpoint']
            ),
            'active_alerts': prometheus_client.Gauge(
                'nexus_active_alerts',
                'Number of active alerts',
                ['severity']
            ),
            'metric_ingestion_rate': prometheus_client.Counter(
                'nexus_metric_ingestion_total',
                'Total metrics ingested'
            )
        }
    
    async def connect_redis(self, url: str = "redis://localhost"):
        """Connect to Redis for persistence"""
        try:
            self.redis = await aioredis.from_url(url)
            await self.redis.ping()
            console.print("[green]Connected to Redis[/green]")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            console.print("[yellow]Running without Redis persistence[/yellow]")
    
    async def add_metric(self, metric: Metric) -> Metric:
        """Add or update a metric"""
        self.metrics[metric.name] = metric
        self.prom_metrics['metric_ingestion_rate'].inc()
        
        # Store in Redis if available
        if self.redis:
            await self.redis.hset(
                "metrics",
                metric.name,
                json.dumps(metric.dict())
            )
        
        return metric
    
    async def add_metric_value(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> MetricValue:
        """Add a metric value"""
        metric_value = MetricValue(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        
        self.metric_values[metric_name].append(metric_value)
        
        # Update current value in metric
        if metric_name in self.metrics:
            self.metrics[metric_name].current_value = value
        
        # Store in Redis if available
        if self.redis:
            await self.redis.lpush(
                f"metric_values:{metric_name}",
                json.dumps(asdict(metric_value))
            )
            await self.redis.ltrim(f"metric_values:{metric_name}", 0, 9999)
        
        # Check alerts
        await self._check_alerts(metric_name, value)
        
        return metric_value
    
    async def get_metric_values(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[MetricValue]:
        """Get metric values within time range"""
        values = list(self.metric_values[metric_name])
        
        if start_time:
            values = [v for v in values if v.timestamp >= start_time]
        
        if end_time:
            values = [v for v in values if v.timestamp <= end_time]
        
        return values[-limit:]
    
    async def aggregate_metrics(
        self,
        aggregation: MetricAggregation
    ) -> Dict[str, Any]:
        """Aggregate metrics"""
        # Parse time range
        now = datetime.now()
        if aggregation.time_range.endswith('h'):
            hours = int(aggregation.time_range[:-1])
            start_time = now - timedelta(hours=hours)
        elif aggregation.time_range.endswith('d'):
            days = int(aggregation.time_range[:-1])
            start_time = now - timedelta(days=days)
        else:
            start_time = now - timedelta(hours=1)
        
        # Get values
        values = await self.get_metric_values(
            aggregation.metric_name,
            start_time=start_time
        )
        
        if not values:
            return {"result": None, "count": 0}
        
        # Apply filters
        if aggregation.filters:
            filtered_values = []
            for value in values:
                match = all(
                    value.labels.get(k) == v
                    for k, v in aggregation.filters.items()
                )
                if match:
                    filtered_values.append(value)
            values = filtered_values
        
        # Group by labels if requested
        if aggregation.group_by:
            groups = defaultdict(list)
            for value in values:
                group_key = tuple(
                    value.labels.get(label, 'unknown')
                    for label in aggregation.group_by
                )
                groups[group_key].append(value.value)
            
            results = {}
            for group_key, group_values in groups.items():
                results[str(group_key)] = self._calculate_aggregation(
                    group_values,
                    aggregation.aggregation_type
                )
            
            return {"results": results, "count": len(values)}
        
        # Simple aggregation
        all_values = [v.value for v in values]
        result = self._calculate_aggregation(all_values, aggregation.aggregation_type)
        
        return {"result": result, "count": len(values)}
    
    def _calculate_aggregation(
        self,
        values: List[float],
        aggregation_type: str
    ) -> float:
        """Calculate aggregation on values"""
        if not values:
            return 0.0
        
        if aggregation_type == "avg":
            return sum(values) / len(values)
        elif aggregation_type == "sum":
            return sum(values)
        elif aggregation_type == "min":
            return min(values)
        elif aggregation_type == "max":
            return max(values)
        elif aggregation_type == "count":
            return float(len(values))
        else:
            return sum(values) / len(values)
    
    async def add_alert(self, alert: Alert) -> Alert:
        """Add or update an alert"""
        self.alerts[alert.id] = alert
        
        # Update Prometheus metric
        active_count = sum(
            1 for a in self.alerts.values()
            if a.is_active and a.severity == alert.severity
        )
        self.prom_metrics['active_alerts'].labels(
            severity=alert.severity
        ).set(active_count)
        
        # Store in Redis if available
        if self.redis:
            await self.redis.hset(
                "alerts",
                alert.id,
                json.dumps(alert.dict())
            )
        
        return alert
    
    async def _check_alerts(self, metric_name: str, value: float):
        """Check if any alerts should be triggered"""
        for alert in self.alerts.values():
            if alert.metric_name == metric_name and alert.is_active:
                # Simple threshold check
                if self._evaluate_alert_condition(alert, value):
                    if not alert.triggered_at:
                        alert.triggered_at = datetime.now()
                        alert.current_value = value
                        console.print(
                            f"[red]Alert triggered: {alert.name} "
                            f"(value: {value}, threshold: {alert.threshold})[/red]"
                        )
                        
                        # Send notifications
                        await self._send_alert_notification(alert)
                else:
                    # Alert condition no longer met
                    if alert.triggered_at and not alert.resolved_at:
                        alert.resolved_at = datetime.now()
                        alert.is_active = False
                        console.print(f"[green]Alert resolved: {alert.name}[/green]")
    
    def _evaluate_alert_condition(self, alert: Alert, value: float) -> bool:
        """Evaluate alert condition"""
        # Simple threshold comparison
        if ">" in alert.condition:
            return value > alert.threshold
        elif "<" in alert.condition:
            return value < alert.threshold
        elif ">=" in alert.condition:
            return value >= alert.threshold
        elif "<=" in alert.condition:
            return value <= alert.threshold
        elif "==" in alert.condition:
            return value == alert.threshold
        
        return False
    
    async def _send_alert_notification(self, alert: Alert):
        """Send alert notifications"""
        # Implementation would send to various channels
        # (Slack, PagerDuty, email, etc.)
        pass
    
    async def calculate_sla(self, target: SLATarget) -> SLATarget:
        """Calculate SLA compliance"""
        # Parse measurement window
        now = datetime.now()
        if target.measurement_window.endswith('h'):
            hours = int(target.measurement_window[:-1])
            start_time = now - timedelta(hours=hours)
        elif target.measurement_window.endswith('d'):
            days = int(target.measurement_window[:-1])
            start_time = now - timedelta(days=days)
        else:
            start_time = now - timedelta(days=30)
        
        # Get metric values (simplified - would use metric_query in real implementation)
        metric_name = target.metric_query.split(' ')[0]  # Extract metric name
        values = await self.get_metric_values(metric_name, start_time=start_time)
        
        if not values:
            target.current_percentage = 100.0
            target.is_meeting_target = True
            target.error_budget_remaining = 100.0
            return target
        
        # Calculate success rate (example: values > 0 are successful)
        successful = sum(1 for v in values if v.value > 0)
        total = len(values)
        
        target.current_percentage = (successful / total) * 100 if total > 0 else 100.0
        target.is_meeting_target = target.current_percentage >= target.target_percentage
        
        # Calculate error budget
        allowed_failures = total * (1 - target.target_percentage / 100)
        actual_failures = total - successful
        error_budget_used = (actual_failures / allowed_failures * 100) if allowed_failures > 0 else 0
        target.error_budget_remaining = max(0, 100 - error_budget_used)
        
        return target


# Initialize store
metrics_store = MetricsStore()


# REST API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    await metrics_store.connect_redis()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/metrics")
async def create_metric(metric: Metric):
    """Create or update a metric"""
    result = await metrics_store.add_metric(metric)
    return result


@app.get("/metrics")
async def list_metrics(
    type: Optional[MetricType] = None,
    limit: int = Query(100, le=1000)
):
    """List all metrics"""
    metrics = list(metrics_store.metrics.values())
    
    if type:
        metrics = [m for m in metrics if m.type == type]
    
    return metrics[:limit]


@app.get("/metrics/{metric_name}")
async def get_metric(metric_name: str):
    """Get a specific metric"""
    if metric_name not in metrics_store.metrics:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    return metrics_store.metrics[metric_name]


@app.post("/metrics/{metric_name}/values")
async def add_metric_value(
    metric_name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """Add a value to a metric"""
    if metric_name not in metrics_store.metrics:
        # Auto-create metric if it doesn't exist
        metric = Metric(
            name=metric_name,
            type=MetricType.GAUGE,
            description=f"Auto-created metric: {metric_name}"
        )
        await metrics_store.add_metric(metric)
    
    result = await metrics_store.add_metric_value(metric_name, value, labels)
    
    metrics_store.prom_metrics['api_requests'].labels(
        method="POST",
        endpoint="/metrics/values",
        status="200"
    ).inc()
    
    return result


@app.get("/metrics/{metric_name}/values")
async def get_metric_values(
    metric_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, le=10000)
):
    """Get metric values"""
    if metric_name not in metrics_store.metrics:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    values = await metrics_store.get_metric_values(
        metric_name,
        start_time,
        end_time,
        limit
    )
    
    return values


@app.post("/metrics/aggregate")
async def aggregate_metrics(aggregation: MetricAggregation):
    """Aggregate metrics"""
    result = await metrics_store.aggregate_metrics(aggregation)
    return result


@app.post("/alerts")
async def create_alert(alert: Alert):
    """Create or update an alert"""
    result = await metrics_store.add_alert(alert)
    return result


@app.get("/alerts")
async def list_alerts(
    severity: Optional[AlertSeverity] = None,
    active_only: bool = True
):
    """List alerts"""
    alerts = list(metrics_store.alerts.values())
    
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    if active_only:
        alerts = [a for a in alerts if a.is_active]
    
    return alerts


@app.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get a specific alert"""
    if alert_id not in metrics_store.alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return metrics_store.alerts[alert_id]


@app.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    if alert_id not in metrics_store.alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    del metrics_store.alerts[alert_id]
    return {"message": "Alert deleted"}


@app.post("/dashboards")
async def create_dashboard(dashboard: Dashboard):
    """Create or update a dashboard"""
    metrics_store.dashboards[dashboard.id] = dashboard
    return dashboard


@app.get("/dashboards")
async def list_dashboards():
    """List all dashboards"""
    return list(metrics_store.dashboards.values())


@app.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get a specific dashboard"""
    if dashboard_id not in metrics_store.dashboards:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    return metrics_store.dashboards[dashboard_id]


@app.post("/sla-targets")
async def create_sla_target(target: SLATarget):
    """Create or update an SLA target"""
    metrics_store.sla_targets[target.name] = target
    return target


@app.get("/sla-targets")
async def list_sla_targets():
    """List all SLA targets with current status"""
    targets = []
    
    for target in metrics_store.sla_targets.values():
        calculated_target = await metrics_store.calculate_sla(target)
        targets.append(calculated_target)
    
    return targets


@app.get("/sla-targets/{target_name}")
async def get_sla_target(target_name: str):
    """Get a specific SLA target"""
    if target_name not in metrics_store.sla_targets:
        raise HTTPException(status_code=404, detail="SLA target not found")
    
    target = metrics_store.sla_targets[target_name]
    return await metrics_store.calculate_sla(target)


@app.post("/reports")
async def create_report(report: Report):
    """Create or update a report"""
    metrics_store.reports[report.id] = report
    return report


@app.get("/reports")
async def list_reports():
    """List all reports"""
    return list(metrics_store.reports.values())


@app.post("/reports/{report_id}/generate")
async def generate_report(report_id: str):
    """Generate a report"""
    if report_id not in metrics_store.reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = metrics_store.reports[report_id]
    
    # Implementation would generate actual report
    report_data = {
        "id": report_id,
        "name": report.name,
        "generated_at": datetime.now().isoformat(),
        "data": {
            "metrics_count": len(metrics_store.metrics),
            "active_alerts": sum(1 for a in metrics_store.alerts.values() if a.is_active),
            "sla_compliance": [
                {
                    "name": target.name,
                    "compliance": target.current_percentage,
                    "is_meeting": target.is_meeting_target
                }
                for target in metrics_store.sla_targets.values()
            ]
        }
    }
    
    report.last_generated = datetime.now()
    
    return report_data


# GraphQL Schema

class MetricGraphQL(ObjectType):
    """GraphQL metric type"""
    name = String()
    type = String()
    description = String()
    unit = String()
    current_value = Float()
    
    values = GrapheneList(lambda: MetricValueGraphQL, limit=Int())
    
    def resolve_values(self, info, limit=100):
        values = list(metrics_store.metric_values[self.name])[-limit:]
        return [
            MetricValueGraphQL(
                timestamp=v.timestamp.isoformat(),
                value=v.value,
                labels=json.dumps(v.labels)
            )
            for v in values
        ]


class MetricValueGraphQL(ObjectType):
    """GraphQL metric value type"""
    timestamp = String()
    value = Float()
    labels = String()


class AlertGraphQL(ObjectType):
    """GraphQL alert type"""
    id = String()
    name = String()
    severity = String()
    condition = String()
    message = String()
    metric_name = String()
    threshold = Float()
    current_value = Float()
    triggered_at = String()
    resolved_at = String()
    is_active = Boolean()


class Query(ObjectType):
    """GraphQL queries"""
    metrics = GrapheneList(MetricGraphQL, type=String())
    metric = Field(MetricGraphQL, name=String(required=True))
    alerts = GrapheneList(AlertGraphQL, active_only=Boolean())
    alert = Field(AlertGraphQL, id=String(required=True))
    
    def resolve_metrics(self, info, type=None):
        metrics = list(metrics_store.metrics.values())
        if type:
            metrics = [m for m in metrics if m.type == type]
        return metrics
    
    def resolve_metric(self, info, name):
        return metrics_store.metrics.get(name)
    
    def resolve_alerts(self, info, active_only=True):
        alerts = list(metrics_store.alerts.values())
        if active_only:
            alerts = [a for a in alerts if a.is_active]
        return alerts
    
    def resolve_alert(self, info, id):
        return metrics_store.alerts.get(id)


schema = Schema(query=Query)


@app.post("/graphql")
async def graphql_endpoint(query: str):
    """GraphQL endpoint"""
    result = schema.execute(query)
    
    if result.errors:
        return JSONResponse(
            status_code=400,
            content={"errors": [str(e) for e in result.errors]}
        )
    
    return result.data


# WebSocket for real-time updates

class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = defaultdict(set)
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
        # Remove from all subscriptions
        for subscribers in self.subscriptions.values():
            subscribers.discard(websocket)
    
    async def subscribe(self, websocket: WebSocket, metric_name: str):
        self.subscriptions[metric_name].add(websocket)
    
    async def unsubscribe(self, websocket: WebSocket, metric_name: str):
        self.subscriptions[metric_name].discard(websocket)
    
    async def broadcast_metric_update(self, metric_name: str, value: MetricValue):
        """Broadcast metric update to subscribers"""
        if metric_name in self.subscriptions:
            message = {
                "type": "metric_update",
                "metric_name": metric_name,
                "value": value.value,
                "timestamp": value.timestamp.isoformat(),
                "labels": value.labels
            }
            
            disconnected = []
            
            for websocket in self.subscriptions[metric_name]:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected clients
            for websocket in disconnected:
                self.disconnect(websocket)
    
    async def broadcast_alert(self, alert: Alert):
        """Broadcast alert to all connections"""
        message = {
            "type": "alert",
            "alert": alert.dict()
        }
        
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "subscribe":
                await manager.subscribe(websocket, data["metric_name"])
                await websocket.send_json({
                    "type": "subscribed",
                    "metric_name": data["metric_name"]
                })
            
            elif data["type"] == "unsubscribe":
                await manager.unsubscribe(websocket, data["metric_name"])
                await websocket.send_json({
                    "type": "unsubscribed",
                    "metric_name": data["metric_name"]
                })
            
            elif data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Prometheus metrics endpoint
@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        prometheus_client.generate_latest(),
        media_type="text/plain"
    )


# Integration endpoints for popular monitoring tools

@app.post("/integrations/datadog/metrics")
async def datadog_metrics_webhook(data: Dict[str, Any]):
    """DataDog metrics webhook"""
    # Parse DataDog format and store metrics
    for series in data.get("series", []):
        metric_name = series["metric"]
        
        # Create metric if it doesn't exist
        if metric_name not in metrics_store.metrics:
            metric = Metric(
                name=metric_name,
                type=MetricType.GAUGE,
                description=f"DataDog metric: {metric_name}"
            )
            await metrics_store.add_metric(metric)
        
        # Add values
        for point in series.get("points", []):
            timestamp, value = point
            await metrics_store.add_metric_value(
                metric_name,
                value,
                labels=series.get("tags", {})
            )
    
    return {"status": "ok"}


@app.post("/integrations/newrelic/webhook")
async def newrelic_webhook(data: Dict[str, Any]):
    """New Relic webhook for alerts"""
    # Parse New Relic alert format
    alert = Alert(
        id=f"newrelic-{data.get('incident_id', 'unknown')}",
        name=data.get('policy_name', 'New Relic Alert'),
        severity=AlertSeverity.ERROR,
        condition=data.get('condition_name', ''),
        message=data.get('details', ''),
        metric_name="newrelic.alert",
        threshold=0,
        triggered_at=datetime.now()
    )
    
    await metrics_store.add_alert(alert)
    await manager.broadcast_alert(alert)
    
    return {"status": "ok"}


@app.post("/integrations/pagerduty/webhook")
async def pagerduty_webhook(data: Dict[str, Any]):
    """PagerDuty webhook for incidents"""
    # Parse PagerDuty incident format
    for message in data.get("messages", []):
        incident = message.get("incident", {})
        
        alert = Alert(
            id=f"pagerduty-{incident.get('id', 'unknown')}",
            name=incident.get('title', 'PagerDuty Incident'),
            severity=AlertSeverity.CRITICAL,
            condition="PagerDuty incident",
            message=incident.get('summary', ''),
            metric_name="pagerduty.incident",
            threshold=0,
            triggered_at=datetime.fromisoformat(
                incident.get('created_at', datetime.now().isoformat())
            )
        )
        
        await metrics_store.add_alert(alert)
        await manager.broadcast_alert(alert)
    
    return {"status": "ok"}


# HTML dashboard for testing WebSocket
@app.get("/dashboard")
async def dashboard():
    """Simple dashboard for testing"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEXUS Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .metric { border: 1px solid #ddd; padding: 10px; margin: 10px 0; }
            .alert { background-color: #fee; border: 1px solid #fcc; padding: 10px; margin: 10px 0; }
            #metrics, #alerts { max-height: 400px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <h1>NEXUS Monitoring Dashboard</h1>
        
        <h2>Real-time Metrics</h2>
        <div id="metrics"></div>
        
        <h2>Alerts</h2>
        <div id="alerts"></div>
        
        <h2>Subscribe to Metric</h2>
        <input type="text" id="metricName" placeholder="Metric name">
        <button onclick="subscribe()">Subscribe</button>
        
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            const metrics = {};
            const alerts = [];
            
            ws.onopen = () => {
                console.log("Connected to WebSocket");
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === "metric_update") {
                    metrics[data.metric_name] = data;
                    updateMetricsDisplay();
                } else if (data.type === "alert") {
                    alerts.unshift(data.alert);
                    if (alerts.length > 10) alerts.pop();
                    updateAlertsDisplay();
                }
            };
            
            function subscribe() {
                const metricName = document.getElementById("metricName").value;
                if (metricName) {
                    ws.send(JSON.stringify({
                        type: "subscribe",
                        metric_name: metricName
                    }));
                }
            }
            
            function updateMetricsDisplay() {
                const container = document.getElementById("metrics");
                container.innerHTML = Object.entries(metrics).map(([name, data]) => `
                    <div class="metric">
                        <strong>${name}</strong>: ${data.value.toFixed(2)}
                        <small>(${new Date(data.timestamp).toLocaleTimeString()})</small>
                    </div>
                `).join("");
            }
            
            function updateAlertsDisplay() {
                const container = document.getElementById("alerts");
                container.innerHTML = alerts.map(alert => `
                    <div class="alert">
                        <strong>${alert.name}</strong> [${alert.severity}]<br>
                        ${alert.message}<br>
                        <small>${new Date(alert.triggered_at).toLocaleString()}</small>
                    </div>
                `).join("");
            }
            
            // Keep connection alive
            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: "ping" }));
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


def run_monitoring_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the monitoring API server"""
    console.print(f"[cyan]Starting NEXUS Monitoring API on {host}:{port}[/cyan]")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_monitoring_api()