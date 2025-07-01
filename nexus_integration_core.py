#!/usr/bin/env python3
"""
NEXUS Integration Core - Central Hub for All Components
Connects all NEXUS services with advanced integration capabilities
"""

import asyncio
import json
import time
import uuid
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from aiohttp import web
from aiohttp_graphql import GraphQLView
import graphene
import jwt
import redis
from websockets import server as websocket_server
import msgpack
import zmq
import zmq.asyncio
import consul.aio
import etcd3.aio
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import grpc
from grpc import aio as grpc_aio
import yaml
from contextlib import asynccontextmanager
import subprocess
import psutil

# Metrics
service_discovery_counter = Counter('nexus_service_discovery_total', 'Service discovery attempts', ['service', 'status'])
service_health_gauge = Gauge('nexus_service_health', 'Service health status', ['service', 'instance'])
message_bus_counter = Counter('nexus_messages_total', 'Messages published', ['topic'])
api_request_histogram = Histogram('nexus_api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
state_operations_counter = Counter('nexus_state_operations_total', 'State operations', ['operation', 'key'])

# Distributed Transaction Manager
class TransactionStatus(Enum):
    """Transaction status levels"""
    PENDING = "pending"
    PREPARING = "preparing"
    PREPARED = "prepared"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ABORTING = "aborting"
    ABORTED = "aborted"

@dataclass
class Transaction:
    """Distributed transaction"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: List[str] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    operations: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    timeout: float = 30.0
    
class DistributedTransactionManager:
    """Two-phase commit transaction manager"""
    
    def __init__(self, message_bus: 'MessageBus'):
        self.transactions: Dict[str, Transaction] = {}
        self.message_bus = message_bus
        self.participant_votes: Dict[str, Dict[str, bool]] = defaultdict(dict)
        
    async def begin_transaction(self, participants: List[str]) -> Transaction:
        """Begin a new distributed transaction"""
        txn = Transaction(participants=participants)
        self.transactions[txn.id] = txn
        
        # Notify participants
        await self.message_bus.publish(
            "txn.begin",
            {"txn_id": txn.id, "participants": participants},
            priority=MessagePriority.HIGH
        )
        
        return txn
    
    async def prepare(self, txn_id: str) -> bool:
        """Prepare phase of 2PC"""
        txn = self.transactions.get(txn_id)
        if not txn:
            return False
            
        txn.status = TransactionStatus.PREPARING
        
        # Request votes from participants
        await self.message_bus.publish(
            "txn.prepare",
            {"txn_id": txn_id, "operations": txn.operations},
            priority=MessagePriority.HIGH
        )
        
        # Wait for votes (with timeout)
        start_time = time.time()
        while time.time() - start_time < txn.timeout:
            votes = self.participant_votes.get(txn_id, {})
            if len(votes) == len(txn.participants):
                # All votes received
                if all(votes.values()):
                    txn.status = TransactionStatus.PREPARED
                    return True
                else:
                    txn.status = TransactionStatus.ABORTING
                    return False
            await asyncio.sleep(0.1)
        
        # Timeout - abort
        txn.status = TransactionStatus.ABORTING
        return False
    
    async def commit(self, txn_id: str):
        """Commit phase of 2PC"""
        txn = self.transactions.get(txn_id)
        if not txn or txn.status != TransactionStatus.PREPARED:
            return
            
        txn.status = TransactionStatus.COMMITTING
        
        # Send commit to participants
        await self.message_bus.publish(
            "txn.commit",
            {"txn_id": txn_id},
            priority=MessagePriority.HIGH
        )
        
        txn.status = TransactionStatus.COMMITTED
    
    async def abort(self, txn_id: str):
        """Abort transaction"""
        txn = self.transactions.get(txn_id)
        if not txn:
            return
            
        txn.status = TransactionStatus.ABORTING
        
        # Send abort to participants
        await self.message_bus.publish(
            "txn.abort",
            {"txn_id": txn_id},
            priority=MessagePriority.HIGH
        )
        
        txn.status = TransactionStatus.ABORTED
    
    async def vote(self, txn_id: str, participant: str, vote: bool):
        """Record participant vote"""
        self.participant_votes[txn_id][participant] = vote

# Service Registry System
class ServiceStatus(Enum):
    """Service health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"

@dataclass
class ServiceInfo:
    """Service registration information"""
    id: str
    name: str
    version: str
    host: str
    port: int
    protocol: str = "http"
    status: ServiceStatus = ServiceStatus.STARTING
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_check_url: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    last_heartbeat: float = field(default_factory=time.time)
    load_score: float = 0.0
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class ServiceRegistry:
    """Service discovery and management with Consul/etcd support"""
    
    def __init__(self, backend: str = "memory", backend_config: Optional[Dict] = None):
        self.services: Dict[str, List[ServiceInfo]] = defaultdict(list)
        self.service_locks = defaultdict(asyncio.Lock)
        self.health_check_interval = 30  # seconds
        self.heartbeat_timeout = 60  # seconds
        self._health_check_task = None
        self.backend = backend
        self.backend_config = backend_config or {}
        
        # Initialize backend
        self.consul_client = None
        self.etcd_client = None
        
        if backend == "consul":
            self.consul_client = consul.aio.Consul(
                host=backend_config.get("host", "localhost"),
                port=backend_config.get("port", 8500)
            )
        elif backend == "etcd":
            self.etcd_client = etcd3.aio.client(
                host=backend_config.get("host", "localhost"),
                port=backend_config.get("port", 2379)
            )
        
    async def register(self, service: ServiceInfo) -> str:
        """Register a new service instance"""
        async with self.service_locks[service.name]:
            # Remove existing instance if same ID
            self.services[service.name] = [
                s for s in self.services[service.name] 
                if s.instance_id != service.instance_id
            ]
            self.services[service.name].append(service)
            
            # Register with backend
            if self.consul_client:
                await self.consul_client.agent.service.register(
                    name=service.name,
                    service_id=service.instance_id,
                    address=service.host,
                    port=service.port,
                    tags=service.capabilities,
                    check=consul.Check.http(
                        f"{service.protocol}://{service.host}:{service.port}{service.health_check_url}",
                        interval="30s"
                    ) if service.health_check_url else None
                )
            elif self.etcd_client:
                await self.etcd_client.put(
                    f"/services/{service.name}/{service.instance_id}",
                    json.dumps({
                        "host": service.host,
                        "port": service.port,
                        "protocol": service.protocol,
                        "capabilities": service.capabilities,
                        "metadata": service.metadata
                    }),
                    lease=await self.etcd_client.lease(ttl=60)
                )
            
            # Update metrics
            service_health_gauge.labels(service=service.name, instance=service.instance_id).set(1)
            
            # Start health monitoring
            if not self._health_check_task:
                self._health_check_task = asyncio.create_task(
                    self._health_check_loop()
                )
            
            return service.instance_id
    
    async def deregister(self, service_name: str, instance_id: str):
        """Remove a service instance"""
        async with self.service_locks[service_name]:
            self.services[service_name] = [
                s for s in self.services[service_name]
                if s.instance_id != instance_id
            ]
    
    async def discover(self, service_name: str, 
                      capability: Optional[str] = None) -> List[ServiceInfo]:
        """Find available service instances"""
        service_discovery_counter.labels(service=service_name, status="attempt").inc()
        
        instances = []
        
        # Try backend first
        if self.consul_client:
            try:
                _, services = await self.consul_client.health.service(
                    service_name, 
                    passing=True
                )
                for svc in services:
                    service = svc['Service']
                    instances.append(ServiceInfo(
                        id=service['ID'],
                        name=service['Service'],
                        version="1.0.0",
                        host=service['Address'],
                        port=service['Port'],
                        capabilities=service.get('Tags', []),
                        status=ServiceStatus.HEALTHY,
                        instance_id=service['ID']
                    ))
            except Exception as e:
                print(f"Consul discovery error: {e}")
                
        elif self.etcd_client:
            try:
                services = await self.etcd_client.get_prefix(
                    f"/services/{service_name}/"
                )
                for value, metadata in services:
                    data = json.loads(value)
                    instance_id = metadata.key.decode().split('/')[-1]
                    instances.append(ServiceInfo(
                        id=instance_id,
                        name=service_name,
                        version="1.0.0",
                        host=data['host'],
                        port=data['port'],
                        protocol=data.get('protocol', 'http'),
                        capabilities=data.get('capabilities', []),
                        status=ServiceStatus.HEALTHY,
                        instance_id=instance_id
                    ))
            except Exception as e:
                print(f"etcd discovery error: {e}")
        
        # Fall back to local registry
        if not instances:
            instances = self.services.get(service_name, [])
        
        # Filter by capability if specified
        if capability:
            instances = [
                s for s in instances 
                if capability in s.capabilities
            ]
        
        # Return only healthy instances
        healthy = [
            s for s in instances 
            if s.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
        ]
        
        service_discovery_counter.labels(
            service=service_name, 
            status="success" if healthy else "failure"
        ).inc()
        
        return healthy
    
    async def get_best_instance(self, service_name: str) -> Optional[ServiceInfo]:
        """Get best instance based on load balancing"""
        healthy_instances = await self.discover(service_name)
        if not healthy_instances:
            return None
        
        # Simple least-loaded strategy
        return min(healthy_instances, key=lambda s: s.load_score)
    
    async def _health_check_loop(self):
        """Periodic health checks for all services"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_services()
            except Exception as e:
                print(f"Health check error: {e}")
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        tasks = []
        for service_list in self.services.values():
            for service in service_list:
                tasks.append(self._check_service_health(service))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service: ServiceInfo):
        """Check individual service health"""
        try:
            # Check heartbeat timeout
            if time.time() - service.last_heartbeat > self.heartbeat_timeout:
                service.status = ServiceStatus.OFFLINE
                return
            
            # Active health check if URL provided
            if service.health_check_url:
                async with aiohttp.ClientSession() as session:
                    url = f"{service.protocol}://{service.host}:{service.port}{service.health_check_url}"
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            service.status = ServiceStatus(data.get('status', 'healthy'))
                            service.load_score = data.get('load', 0.0)
                        else:
                            service.status = ServiceStatus.UNHEALTHY
        except Exception:
            service.status = ServiceStatus.UNHEALTHY

# Message Bus System
class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Message:
    """Message structure for event bus"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    payload: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    sender: Optional[str] = None
    correlation_id: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)
    ttl: Optional[float] = None  # Time to live in seconds

class MessageBus:
    """Advanced pub/sub message bus with queuing and tracing"""
    
    def __init__(self, redis_url: Optional[str] = None, enable_tracing: bool = True):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_queue: Dict[str, deque] = defaultdict(deque)
        self.dead_letter_queue: deque = deque(maxlen=1000)
        self.redis_client = None
        self.zmq_context = zmq.asyncio.Context()
        self.zmq_publisher = None
        self.zmq_subscriber = None
        self.enable_tracing = enable_tracing
        
        if redis_url:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
        # Setup tracing
        if enable_tracing:
            self.tracer = trace.get_tracer(__name__)
    
    async def initialize(self):
        """Initialize ZMQ sockets for distributed messaging"""
        # Publisher socket
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        self.zmq_publisher.bind("tcp://*:5555")
        
        # Subscriber socket
        self.zmq_subscriber = self.zmq_context.socket(zmq.SUB)
        self.zmq_subscriber.connect("tcp://localhost:5555")
        self.zmq_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Start message processing
        asyncio.create_task(self._process_zmq_messages())
    
    async def publish(self, topic: str, payload: Any, 
                     priority: MessagePriority = MessagePriority.NORMAL,
                     **kwargs) -> str:
        """Publish a message to a topic"""
        message_bus_counter.labels(topic=topic).inc()
        
        # Start tracing span
        span = None
        if self.enable_tracing:
            span = self.tracer.start_span(f"publish:{topic}")
            span.set_attribute("message.topic", topic)
            span.set_attribute("message.priority", priority.value)
        
        try:
            message = Message(
                topic=topic,
                payload=payload,
                priority=priority,
                **kwargs
            )
            
            # Add trace context to headers
            if span:
                message.headers['trace_id'] = span.get_span_context().trace_id
                message.headers['span_id'] = span.get_span_context().span_id
            
            # Local subscribers
            await self._deliver_local(message)
            
            # Distributed publishing via ZMQ
            if self.zmq_publisher:
                packed = msgpack.packb({
                    'id': message.id,
                    'topic': message.topic,
                    'payload': message.payload,
                    'priority': message.priority.value,
                    'timestamp': message.timestamp,
                    'sender': message.sender,
                    'headers': message.headers
                })
                await self.zmq_publisher.send_multipart([
                    topic.encode(),
                    packed
                ])
            
            # Persist to Redis if available
            if self.redis_client:
                self.redis_client.xadd(
                    f"nexus:messages:{topic}",
                    {
                        'id': message.id,
                        'payload': json.dumps(message.payload),
                        'priority': message.priority.value
                    },
                    maxlen=10000
                )
            
            return message.id
            
        finally:
            if span:
                span.end()
    
    def subscribe(self, topic: str, handler: Callable, 
                 filter_func: Optional[Callable] = None):
        """Subscribe to a topic with optional filtering"""
        if filter_func:
            # Wrap handler with filter
            async def filtered_handler(message):
                if filter_func(message):
                    await handler(message)
            self.subscribers[topic].append(filtered_handler)
        else:
            self.subscribers[topic].append(handler)
    
    def unsubscribe(self, topic: str, handler: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            self.subscribers[topic] = [
                h for h in self.subscribers[topic] if h != handler
            ]
    
    async def _deliver_local(self, message: Message):
        """Deliver message to local subscribers"""
        handlers = self.subscribers.get(message.topic, [])
        handlers.extend(self.subscribers.get("*", []))  # Wildcard subscribers
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                print(f"Handler error for {message.topic}: {e}")
                self.dead_letter_queue.append((message, str(e)))
    
    async def _process_zmq_messages(self):
        """Process incoming ZMQ messages"""
        while True:
            try:
                topic, packed = await self.zmq_subscriber.recv_multipart()
                data = msgpack.unpackb(packed)
                
                message = Message(
                    id=data['id'],
                    topic=data['topic'],
                    payload=data['payload'],
                    priority=MessagePriority(data['priority']),
                    timestamp=data['timestamp'],
                    sender=data.get('sender'),
                    headers=data.get('headers', {})
                )
                
                await self._deliver_local(message)
            except Exception as e:
                print(f"ZMQ processing error: {e}")

# State Management System
class StateStore:
    """Global state management with conflict resolution and persistence"""
    
    def __init__(self, backend: Optional[str] = None, backend_config: Optional[Dict] = None):
        self.state: Dict[str, Any] = {}
        self.state_versions: Dict[str, int] = defaultdict(int)
        self.state_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.change_listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.conflict_resolvers: Dict[str, Callable] = {}
        self.state_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        self.backend = backend
        self.backend_config = backend_config or {}
        
        # Initialize backend
        self.redis_client = None
        self.etcd_client = None
        
        if backend == "redis":
            self.redis_client = redis.from_url(
                backend_config.get("url", "redis://localhost:6379"),
                decode_responses=True
            )
        elif backend == "etcd":
            self.etcd_client = etcd3.aio.client(
                host=backend_config.get("host", "localhost"),
                port=backend_config.get("port", 2379)
            )
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get state value"""
        return self.state.get(key, default)
    
    async def set(self, key: str, value: Any, 
                 expected_version: Optional[int] = None) -> bool:
        """Set state value with optional optimistic locking"""
        state_operations_counter.labels(operation="set", key=key).inc()
        
        async with self.state_locks[key]:
            current_version = self.state_versions[key]
            
            # Check version if specified
            if expected_version is not None and expected_version != current_version:
                # Version conflict - try resolution
                if key in self.conflict_resolvers:
                    resolved_value = await self.conflict_resolvers[key](
                        self.state.get(key),
                        value,
                        current_version,
                        expected_version
                    )
                    value = resolved_value
                else:
                    return False
            
            # Update state
            old_value = self.state.get(key)
            self.state[key] = value
            self.state_versions[key] += 1
            
            # Persist to backend
            if self.redis_client:
                await self.redis_client.hset(
                    "nexus:state",
                    key,
                    json.dumps({
                        "value": value,
                        "version": self.state_versions[key],
                        "timestamp": time.time()
                    })
                )
            elif self.etcd_client:
                await self.etcd_client.put(
                    f"/state/{key}",
                    json.dumps({
                        "value": value,
                        "version": self.state_versions[key],
                        "timestamp": time.time()
                    })
                )
            
            # Record history
            self.state_history[key].append({
                'value': value,
                'version': self.state_versions[key],
                'timestamp': time.time()
            })
            
            # Notify listeners
            await self._notify_change(key, old_value, value)
            
            return True
    
    async def update(self, key: str, update_func: Callable) -> Any:
        """Atomic update operation"""
        async with self.state_locks[key]:
            current_value = self.state.get(key)
            new_value = await update_func(current_value)
            
            self.state[key] = new_value
            self.state_versions[key] += 1
            
            await self._notify_change(key, current_value, new_value)
            
            return new_value
    
    def watch(self, key: str, listener: Callable):
        """Watch for state changes"""
        self.change_listeners[key].append(listener)
    
    def set_conflict_resolver(self, key: str, resolver: Callable):
        """Set custom conflict resolution function"""
        self.conflict_resolvers[key] = resolver
    
    async def _notify_change(self, key: str, old_value: Any, new_value: Any):
        """Notify all change listeners"""
        listeners = self.change_listeners.get(key, [])
        listeners.extend(self.change_listeners.get("*", []))
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(key, old_value, new_value)
                else:
                    listener(key, old_value, new_value)
            except Exception as e:
                print(f"Listener error for {key}: {e}")
    
    async def persist(self, filepath: Path):
        """Persist state to disk"""
        data = {
            'state': self.state,
            'versions': dict(self.state_versions),
            'timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def restore(self, filepath: Path):
        """Restore state from disk"""
        if not filepath.exists():
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.state = data['state']
        self.state_versions = defaultdict(int, data['versions'])

# API Gateway System
class APIGateway:
    """Unified API gateway with REST, GraphQL, and WebSocket support"""
    
    def __init__(self, service_registry: ServiceRegistry, 
                 message_bus: MessageBus,
                 state_store: StateStore):
        self.service_registry = service_registry
        self.message_bus = message_bus
        self.state_store = state_store
        self.app = web.Application()
        self.websockets: Set[web.WebSocketResponse] = set()
        self.auth_secret = "nexus-secret-key"  # Should be configurable
        self.rate_limiter = defaultdict(lambda: deque(maxlen=100))
        
        # Setup routes
        self._setup_routes()
        
        # Setup GraphQL schema
        self.schema = self._create_graphql_schema()
    
    def _setup_routes(self):
        """Configure API routes"""
        # REST endpoints
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/services', self.list_services)
        self.app.router.add_post('/services/{name}/invoke', self.invoke_service)
        self.app.router.add_get('/state/{key}', self.get_state)
        self.app.router.add_put('/state/{key}', self.set_state)
        self.app.router.add_post('/events/{topic}', self.publish_event)
        
        # WebSocket endpoint
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # GraphQL endpoint
        self.app.router.add_route(
            '*', '/graphql',
            GraphQLView(schema=self.schema, graphiql=True)
        )
        
        # Apply middleware
        self.app.middlewares.append(self.auth_middleware)
        self.app.middlewares.append(self.rate_limit_middleware)
    
    def _create_graphql_schema(self):
        """Create GraphQL schema"""
        class ServiceType(graphene.ObjectType):
            id = graphene.String()
            name = graphene.String()
            status = graphene.String()
            host = graphene.String()
            port = graphene.Int()
            capabilities = graphene.List(graphene.String)
        
        class StateType(graphene.ObjectType):
            key = graphene.String()
            value = graphene.String()
            version = graphene.Int()
        
        class Query(graphene.ObjectType):
            services = graphene.List(
                ServiceType,
                name=graphene.String()
            )
            state = graphene.Field(
                StateType,
                key=graphene.String(required=True)
            )
            
            async def resolve_services(self, info, name=None):
                if name:
                    services = await self.service_registry.discover(name)
                else:
                    all_services = []
                    for service_list in self.service_registry.services.values():
                        all_services.extend(service_list)
                    services = all_services
                
                return [
                    ServiceType(
                        id=s.instance_id,
                        name=s.name,
                        status=s.status.value,
                        host=s.host,
                        port=s.port,
                        capabilities=s.capabilities
                    )
                    for s in services
                ]
            
            async def resolve_state(self, info, key):
                value = await self.state_store.get(key)
                version = self.state_store.state_versions.get(key, 0)
                
                return StateType(
                    key=key,
                    value=json.dumps(value),
                    version=version
                )
        
        class PublishEvent(graphene.Mutation):
            class Arguments:
                topic = graphene.String(required=True)
                payload = graphene.String(required=True)
            
            success = graphene.Boolean()
            message_id = graphene.String()
            
            async def mutate(self, info, topic, payload):
                message_id = await self.message_bus.publish(
                    topic,
                    json.loads(payload)
                )
                return PublishEvent(success=True, message_id=message_id)
        
        class Mutation(graphene.ObjectType):
            publish_event = PublishEvent.Field()
        
        return graphene.Schema(query=Query, mutation=Mutation)
    
    @web.middleware
    async def auth_middleware(self, request, handler):
        """JWT authentication middleware with metrics"""
        # Skip auth for health check and GraphQL introspection
        if request.path in ['/health', '/graphql', '/metrics']:
            return await handler(request)
        
        # Check if auth is required
        if not self.config.get('auth_required', True):
            return await handler(request)
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token, 
                    self.auth_secret, 
                    algorithms=['HS256']
                )
                request['user'] = payload
            except jwt.InvalidTokenError:
                return web.json_response(
                    {'error': 'Invalid token'},
                    status=401
                )
        else:
            return web.json_response(
                {'error': 'Authorization required'},
                status=401
            )
        
        return await handler(request)
    
    @web.middleware
    async def rate_limit_middleware(self, request, handler):
        """Rate limiting middleware with metrics"""
        start_time = time.time()
        client_ip = request.remote
        now = time.time()
        
        try:
            # Clean old entries
            self.rate_limiter[client_ip] = deque(
                [t for t in self.rate_limiter[client_ip] if now - t < 60],
                maxlen=100
            )
            
            # Check rate limit (100 requests per minute)
            if len(self.rate_limiter[client_ip]) >= 100:
                return web.json_response(
                    {'error': 'Rate limit exceeded'},
                    status=429
                )
            
            self.rate_limiter[client_ip].append(now)
            
            # Process request
            response = await handler(request)
            
            # Record metrics
            duration = time.time() - start_time
            api_request_histogram.labels(
                method=request.method,
                endpoint=request.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            api_request_histogram.labels(
                method=request.method,
                endpoint=request.path
            ).observe(duration)
            raise
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': time.time(),
            'services': len(self.service_registry.services)
        })
    
    async def list_services(self, request):
        """List all registered services"""
        services = []
        for name, instances in self.service_registry.services.items():
            for instance in instances:
                services.append({
                    'id': instance.instance_id,
                    'name': instance.name,
                    'version': instance.version,
                    'status': instance.status.value,
                    'host': instance.host,
                    'port': instance.port,
                    'capabilities': instance.capabilities,
                    'load': instance.load_score
                })
        
        return web.json_response({'services': services})
    
    async def invoke_service(self, request):
        """Invoke a service method via gateway"""
        service_name = request.match_info['name']
        data = await request.json()
        
        # Find best instance
        instance = await self.service_registry.get_best_instance(service_name)
        if not instance:
            return web.json_response(
                {'error': f'Service {service_name} not available'},
                status=503
            )
        
        # Forward request
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{instance.protocol}://{instance.host}:{instance.port}/invoke"
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    return web.json_response(result)
        except Exception as e:
            return web.json_response(
                {'error': str(e)},
                status=500
            )
    
    async def get_state(self, request):
        """Get state value"""
        key = request.match_info['key']
        value = await self.state_store.get(key)
        version = self.state_store.state_versions.get(key, 0)
        
        return web.json_response({
            'key': key,
            'value': value,
            'version': version
        })
    
    async def set_state(self, request):
        """Set state value"""
        key = request.match_info['key']
        data = await request.json()
        value = data.get('value')
        expected_version = data.get('expected_version')
        
        success = await self.state_store.set(key, value, expected_version)
        
        return web.json_response({
            'success': success,
            'version': self.state_store.state_versions.get(key, 0)
        })
    
    async def publish_event(self, request):
        """Publish event to message bus"""
        topic = request.match_info['topic']
        data = await request.json()
        
        message_id = await self.message_bus.publish(
            topic,
            data.get('payload'),
            priority=MessagePriority(data.get('priority', 1))
        )
        
        return web.json_response({
            'message_id': message_id,
            'topic': topic
        })
    
    async def websocket_handler(self, request):
        """WebSocket connection handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        
        try:
            # Subscribe to events
            subscriptions = set()
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    if data['type'] == 'subscribe':
                        topic = data['topic']
                        subscriptions.add(topic)
                        
                        # Create handler for this WebSocket
                        async def ws_handler(message):
                            await ws.send_json({
                                'type': 'event',
                                'topic': message.topic,
                                'payload': message.payload,
                                'timestamp': message.timestamp
                            })
                        
                        self.message_bus.subscribe(topic, ws_handler)
                    
                    elif data['type'] == 'unsubscribe':
                        topic = data['topic']
                        subscriptions.discard(topic)
                        # Note: Proper cleanup would track handlers
                    
                    elif data['type'] == 'publish':
                        await self.message_bus.publish(
                            data['topic'],
                            data['payload']
                        )
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        
        finally:
            self.websockets.discard(ws)
        
        return ws
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast to all connected WebSockets"""
        if self.websockets:
            await asyncio.gather(
                *[ws.send_json(data) for ws in self.websockets],
                return_exceptions=True
            )

# Plugin System
class Plugin(ABC):
    """Base plugin interface"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    async def initialize(self, context: 'PluginContext'):
        """Initialize plugin with context"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Clean shutdown of plugin"""
        pass

@dataclass
class PluginContext:
    """Context provided to plugins"""
    service_registry: ServiceRegistry
    message_bus: MessageBus
    state_store: StateStore
    api_gateway: APIGateway
    config: Dict[str, Any] = field(default_factory=dict)

class PluginSystem:
    """Plugin loading and management system"""
    
    def __init__(self, context: PluginContext):
        self.context = context
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.sandboxes: Dict[str, 'PluginSandbox'] = {}
    
    async def load_plugin(self, plugin_path: Path):
        """Load a plugin from file"""
        # Dynamic import
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            plugin_path.stem,
            plugin_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Plugin) and 
                attr != Plugin):
                
                # Create instance
                plugin = attr()
                
                # Create sandbox
                sandbox = PluginSandbox(plugin, self.context)
                self.sandboxes[plugin.name] = sandbox
                
                # Initialize
                await sandbox.initialize()
                
                self.plugins[plugin.name] = plugin
                print(f"Loaded plugin: {plugin.name} v{plugin.version}")
                
                return plugin
        
        raise ValueError(f"No plugin found in {plugin_path}")
    
    async def unload_plugin(self, name: str):
        """Unload a plugin"""
        if name in self.plugins:
            plugin = self.plugins[name]
            sandbox = self.sandboxes[name]
            
            await sandbox.shutdown()
            
            del self.plugins[name]
            del self.sandboxes[name]
            
            # Remove hooks
            for hook_list in self.hooks.values():
                hook_list[:] = [
                    h for h in hook_list 
                    if not hasattr(h, '__plugin__') or h.__plugin__ != name
                ]
    
    def register_hook(self, name: str, handler: Callable, plugin_name: str):
        """Register a hook handler"""
        # Tag handler with plugin name
        handler.__plugin__ = plugin_name
        self.hooks[name].append(handler)
    
    async def call_hook(self, name: str, *args, **kwargs):
        """Call all handlers for a hook"""
        results = []
        for handler in self.hooks.get(name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(*args, **kwargs)
                else:
                    result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Hook error in {name}: {e}")
        
        return results

class PluginSandbox:
    """Sandbox environment for plugins"""
    
    def __init__(self, plugin: Plugin, context: PluginContext):
        self.plugin = plugin
        self.context = context
        self.resources: List[Any] = []
        self.tasks: List[asyncio.Task] = []
    
    async def initialize(self):
        """Initialize plugin in sandbox"""
        # Create restricted context
        sandbox_context = PluginContext(
            service_registry=self._wrap_service_registry(),
            message_bus=self._wrap_message_bus(),
            state_store=self._wrap_state_store(),
            api_gateway=self.context.api_gateway,
            config=self.context.config.get(self.plugin.name, {})
        )
        
        await self.plugin.initialize(sandbox_context)
    
    async def shutdown(self):
        """Clean shutdown of sandbox"""
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Cleanup resources
        for resource in self.resources:
            if hasattr(resource, 'close'):
                resource.close()
        
        await self.plugin.shutdown()
    
    def _wrap_service_registry(self):
        """Create wrapped service registry with access control"""
        # Simple passthrough for now, could add restrictions
        return self.context.service_registry
    
    def _wrap_message_bus(self):
        """Create wrapped message bus with access control"""
        return self.context.message_bus
    
    def _wrap_state_store(self):
        """Create wrapped state store with namespacing"""
        class NamespacedStateStore:
            def __init__(self, store, namespace):
                self.store = store
                self.namespace = namespace
            
            async def get(self, key, default=None):
                return await self.store.get(f"{self.namespace}:{key}", default)
            
            async def set(self, key, value, expected_version=None):
                return await self.store.set(
                    f"{self.namespace}:{key}", 
                    value, 
                    expected_version
                )
        
        return NamespacedStateStore(
            self.context.state_store,
            self.plugin.name
        )

# Main Integration Core
class NexusIntegrationCore:
    """Central integration hub for all NEXUS components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core components
        self.service_registry = ServiceRegistry(
            backend=self.config.get('service_discovery', {}).get('backend', 'memory'),
            backend_config=self.config.get('service_discovery', {})
        )
        self.message_bus = MessageBus(
            redis_url=self.config.get('redis_url'),
            enable_tracing=self.config.get('monitoring', {}).get('tracing', {}).get('enabled', True)
        )
        self.state_store = StateStore(
            backend=self.config.get('state', {}).get('backend'),
            backend_config=self.config.get('state', {})
        )
        self.api_gateway = APIGateway(
            self.service_registry,
            self.message_bus,
            self.state_store
        )
        self.api_gateway.config = self.config.get('security', {})
        
        # Distributed transaction manager
        self.transaction_manager = DistributedTransactionManager(self.message_bus)
        
        # Plugin system
        self.plugin_context = PluginContext(
            service_registry=self.service_registry,
            message_bus=self.message_bus,
            state_store=self.state_store,
            api_gateway=self.api_gateway,
            config=self.config
        )
        self.plugin_system = PluginSystem(self.plugin_context)
        
        # Background tasks
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the integration core"""
        print("Starting NEXUS Integration Core...")
        
        # Setup monitoring
        await self._setup_monitoring()
        
        # Initialize message bus
        await self.message_bus.initialize()
        
        # Setup transaction handling
        await self._setup_transaction_handlers()
        
        # Load persisted state
        state_file = Path(self.config.get('state_file', 'nexus_state.json'))
        if state_file.exists():
            await self.state_store.restore(state_file)
        
        # Start periodic state persistence
        self.tasks.append(
            asyncio.create_task(self._periodic_persist(state_file))
        )
        
        # Load plugins
        plugin_dir = Path(self.config.get('plugin_dir', 'nexus_plugins'))
        if plugin_dir.exists():
            for plugin_file in plugin_dir.glob('*.py'):
                try:
                    await self.plugin_system.load_plugin(plugin_file)
                except Exception as e:
                    print(f"Failed to load plugin {plugin_file}: {e}")
        
        # Start API gateway
        runner = web.AppRunner(self.api_gateway.app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            self.config.get('api_host', '0.0.0.0'),
            self.config.get('api_port', 8080)
        )
        await site.start()
        
        print(f"API Gateway started on {site.name}")
        
        # Register self as a service
        await self.service_registry.register(ServiceInfo(
            id="nexus-core",
            name="nexus-integration-core",
            version="1.0.0",
            host="localhost",
            port=self.config.get('api_port', 8080),
            capabilities=[
                "service-discovery",
                "message-bus",
                "state-management",
                "api-gateway",
                "plugin-system"
            ],
            health_check_url="/health"
        ))
        
        print("NEXUS Integration Core started successfully!")
    
    async def stop(self):
        """Stop the integration core"""
        print("Stopping NEXUS Integration Core...")
        
        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Unload plugins
        for plugin_name in list(self.plugin_system.plugins.keys()):
            await self.plugin_system.unload_plugin(plugin_name)
        
        # Final state persistence
        state_file = Path(self.config.get('state_file', 'nexus_state.json'))
        await self.state_store.persist(state_file)
        
        print("NEXUS Integration Core stopped")
    
    async def _periodic_persist(self, filepath: Path):
        """Periodically persist state"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                await self.state_store.persist(filepath)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"State persistence error: {e}")
    
    async def _setup_monitoring(self):
        """Setup monitoring and observability"""
        # Start Prometheus metrics server
        metrics_port = self.config.get('monitoring', {}).get('metrics', {}).get('port', 9090)
        start_http_server(metrics_port)
        print(f"Prometheus metrics available on port {metrics_port}")
        
        # Setup tracing
        if self.config.get('monitoring', {}).get('tracing', {}).get('enabled', True):
            trace.set_tracer_provider(TracerProvider())
            
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.get('monitoring', {}).get('tracing', {}).get(
                    'endpoint', 'localhost:4317'
                ),
                insecure=True
            )
            
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            print("OpenTelemetry tracing enabled")
    
    async def _setup_transaction_handlers(self):
        """Setup distributed transaction handlers"""
        # Handle transaction votes
        async def handle_prepare(message: Message):
            txn_id = message.payload['txn_id']
            # Simulate vote (in real implementation, check if operations can be performed)
            vote = True  # Always vote yes for now
            await self.transaction_manager.vote(txn_id, "core", vote)
            
        self.message_bus.subscribe("txn.prepare", handle_prepare)
        
        # Handle commits
        async def handle_commit(message: Message):
            txn_id = message.payload['txn_id']
            # Execute commit operations
            print(f"Committing transaction {txn_id}")
            
        self.message_bus.subscribe("txn.commit", handle_commit)
        
        # Handle aborts
        async def handle_abort(message: Message):
            txn_id = message.payload['txn_id']
            # Rollback operations
            print(f"Aborting transaction {txn_id}")
            
        self.message_bus.subscribe("txn.abort", handle_abort)

# Configuration Loading
def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    default_config = {
        'nexus': {
            'version': '1.0.0',
            'mode': 'development',
            'core': {
                'workers': 'auto',
                'max_memory': '16GB',
                'log_level': 'info'
            },
            'features': {
                'voice': 'enabled',
                'vision': 'enabled',
                'learning': 'enabled'
            },
            'security': {
                'auth_required': True,
                'encryption': 'aes256',
                'tls_version': '1.3'
            },
            'monitoring': {
                'metrics': {
                    'enabled': True,
                    'port': 9090
                },
                'tracing': {
                    'enabled': True,
                    'endpoint': 'localhost:4317'
                },
                'logs': {
                    'backend': 'elasticsearch',
                    'endpoint': 'localhost:9200'
                }
            },
            'service_discovery': {
                'backend': 'consul',
                'host': 'localhost',
                'port': 8500
            },
            'state': {
                'backend': 'redis',
                'url': 'redis://localhost:6379'
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8080
            }
        }
    }
    
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            # Deep merge configs
            import copy
            config = copy.deepcopy(default_config)
            
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            
            deep_merge(config, user_config)
            return config
    
    return default_config

# Example usage and testing
async def main():
    """Example usage of the integration core"""
    
    # Load configuration
    config_path = Path('nexus_production_config.yaml')
    config_data = load_config(config_path)
    
    # Extract relevant config sections
    config = {
        'api_host': config_data['nexus']['api']['host'],
        'api_port': config_data['nexus']['api']['port'],
        'redis_url': config_data['nexus']['state'].get('url', 'redis://localhost:6379'),
        'state_file': 'nexus_state.json',
        'plugin_dir': 'nexus_plugins',
        'service_discovery': config_data['nexus']['service_discovery'],
        'state': config_data['nexus']['state'],
        'security': config_data['nexus']['security'],
        'monitoring': config_data['nexus']['monitoring']
    }
    
    # Create and start core
    core = NexusIntegrationCore(config)
    
    try:
        await core.start()
        
        # Example: Subscribe to events
        async def event_handler(message):
            print(f"Received event: {message.topic} - {message.payload}")
        
        core.message_bus.subscribe("system.events", event_handler)
        
        # Example: Publish event
        await core.message_bus.publish(
            "system.events",
            {"type": "startup", "component": "integration-core"}
        )
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        await core.stop()

if __name__ == "__main__":
    asyncio.run(main())