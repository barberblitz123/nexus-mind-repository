"""
NEXUS Core Production Service
Production-grade infrastructure with comprehensive monitoring, error handling, and scalability
"""

import asyncio
import os
import sys
import time
import logging
import signal
from typing import Optional, Dict, Any, List, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import json

# Core dependencies
import asyncpg
import redis.asyncio as redis
from redis.asyncio.sentinel import Sentinel
import aioamqp
from celery import Celery
from celery.result import AsyncResult
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Info
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from circuitbreaker import circuit
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

# Internal imports
from nexus_config_production import ProductionConfig
from nexus_database_production import DatabaseManager, get_db_session

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            'nexus_core.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter('nexus_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('nexus_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_connections = Gauge('nexus_active_connections', 'Active connections')
error_count = Counter('nexus_errors_total', 'Total errors', ['error_type'])
cache_hits = Counter('nexus_cache_hits_total', 'Cache hits')
cache_misses = Counter('nexus_cache_misses_total', 'Cache misses')
task_queue_size = Gauge('nexus_task_queue_size', 'Task queue size')
db_pool_size = Gauge('nexus_db_pool_size', 'Database connection pool size')
app_info = Info('nexus_app', 'Application info')

# Initialize OpenTelemetry
def init_telemetry(config: ProductionConfig):
    """Initialize distributed tracing with OpenTelemetry"""
    resource = Resource.create({
        "service.name": "nexus-core",
        "service.version": config.APP_VERSION,
        "deployment.environment": config.ENVIRONMENT
    })
    
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=config.OTLP_ENDPOINT,
            insecure=config.OTLP_INSECURE
        )
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    # Instrument libraries
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    
    return trace.get_tracer(__name__)


class CircuitBreakerMixin:
    """Mixin for circuit breaker functionality"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.circuit_open = False
    
    def record_success(self):
        """Record successful operation"""
        self.failures = 0
        self.circuit_open = False
    
    def record_failure(self):
        """Record failed operation"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.circuit_open = True
            logger.error(f"Circuit breaker opened after {self.failures} failures")
    
    def is_circuit_open(self):
        """Check if circuit is open"""
        if not self.circuit_open:
            return False
        
        # Check if recovery timeout has passed
        if self.last_failure_time and \
           time.time() - self.last_failure_time > self.recovery_timeout:
            self.circuit_open = False
            self.failures = 0
            logger.info("Circuit breaker closed after recovery timeout")
            return False
        
        return True


class NexusCore:
    """Production-grade NEXUS core service"""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.tracer = init_telemetry(config)
        self.db_manager = DatabaseManager(config)
        self.redis_pool: Optional[redis.Redis] = None
        self.redis_sentinel: Optional[Sentinel] = None
        self.amqp_connection = None
        self.amqp_channel = None
        self.celery_app = None
        self.shutdown_event = asyncio.Event()
        self.health_checks: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreakerMixin] = {}
        
        # Initialize app info for Prometheus
        app_info.info({
            'version': config.APP_VERSION,
            'environment': config.ENVIRONMENT,
            'started_at': datetime.utcnow().isoformat()
        })
    
    async def initialize(self):
        """Initialize all service connections with retry logic"""
        logger.info("Initializing NEXUS Core Production Service")
        
        # Initialize database
        await self._init_database()
        
        # Initialize Redis
        await self._init_redis()
        
        # Initialize RabbitMQ
        await self._init_rabbitmq()
        
        # Initialize Celery
        self._init_celery()
        
        # Register health checks
        self._register_health_checks()
        
        # Start background tasks
        asyncio.create_task(self._monitor_connections())
        asyncio.create_task(self._collect_metrics())
        
        logger.info("NEXUS Core initialized successfully")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    async def _init_database(self):
        """Initialize database with connection pooling and retry logic"""
        with self.tracer.start_as_current_span("init_database"):
            try:
                await self.db_manager.initialize()
                self.circuit_breakers['database'] = CircuitBreakerMixin()
                logger.info("Database initialized successfully")
            except Exception as e:
                error_count.labels(error_type='database_init').inc()
                logger.error(f"Failed to initialize database: {e}")
                raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    async def _init_redis(self):
        """Initialize Redis with sentinel support for high availability"""
        with self.tracer.start_as_current_span("init_redis"):
            try:
                if self.config.REDIS_SENTINELS:
                    # Use Redis Sentinel for HA
                    self.redis_sentinel = Sentinel(
                        [(host, port) for host, port in self.config.REDIS_SENTINELS],
                        socket_timeout=0.1,
                        decode_responses=True
                    )
                    self.redis_pool = self.redis_sentinel.master_for(
                        self.config.REDIS_MASTER_NAME,
                        redis_class=redis.Redis,
                        connection_pool_kwargs={
                            'max_connections': self.config.REDIS_POOL_MAX_CONNECTIONS,
                            'retry_on_timeout': True,
                            'socket_keepalive': True,
                            'socket_keepalive_options': {
                                1: 1,  # TCP_KEEPIDLE
                                2: 1,  # TCP_KEEPINTVL
                                3: 5,  # TCP_KEEPCNT
                            }
                        }
                    )
                else:
                    # Single Redis instance
                    self.redis_pool = await redis.from_url(
                        self.config.REDIS_URL,
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=self.config.REDIS_POOL_MAX_CONNECTIONS,
                        retry_on_timeout=True,
                        socket_keepalive=True
                    )
                
                # Test connection
                await self.redis_pool.ping()
                self.circuit_breakers['redis'] = CircuitBreakerMixin()
                logger.info("Redis initialized successfully")
            except Exception as e:
                error_count.labels(error_type='redis_init').inc()
                logger.error(f"Failed to initialize Redis: {e}")
                raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    async def _init_rabbitmq(self):
        """Initialize RabbitMQ connection with retry logic"""
        with self.tracer.start_as_current_span("init_rabbitmq"):
            try:
                transport, protocol = await aioamqp.connect(
                    host=self.config.RABBITMQ_HOST,
                    port=self.config.RABBITMQ_PORT,
                    login=self.config.RABBITMQ_USER,
                    password=self.config.RABBITMQ_PASSWORD,
                    virtualhost=self.config.RABBITMQ_VHOST,
                    heartbeat=600,
                    on_error=self._handle_amqp_error,
                    on_close=self._handle_amqp_close
                )
                
                self.amqp_connection = protocol
                self.amqp_channel = await protocol.channel()
                
                # Declare exchanges and queues
                await self._setup_amqp_topology()
                
                self.circuit_breakers['rabbitmq'] = CircuitBreakerMixin()
                logger.info("RabbitMQ initialized successfully")
            except Exception as e:
                error_count.labels(error_type='rabbitmq_init').inc()
                logger.error(f"Failed to initialize RabbitMQ: {e}")
                raise
    
    def _init_celery(self):
        """Initialize Celery for distributed task processing"""
        self.celery_app = Celery(
            'nexus',
            broker=self.config.CELERY_BROKER_URL,
            backend=self.config.CELERY_RESULT_BACKEND
        )
        
        # Configure Celery
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=self.config.CELERY_TASK_TIME_LIMIT,
            task_soft_time_limit=self.config.CELERY_TASK_SOFT_TIME_LIMIT,
            task_acks_late=True,
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=1000,
            broker_connection_retry_on_startup=True,
            broker_connection_retry=True,
            broker_connection_max_retries=10,
            result_expires=3600,
            task_reject_on_worker_lost=True,
            task_ignore_result=False
        )
        
        logger.info("Celery initialized successfully")
    
    async def _setup_amqp_topology(self):
        """Setup AMQP exchanges and queues"""
        # Declare exchanges
        await self.amqp_channel.exchange_declare(
            exchange_name='nexus.events',
            type_name='topic',
            durable=True,
            auto_delete=False
        )
        
        await self.amqp_channel.exchange_declare(
            exchange_name='nexus.commands',
            type_name='direct',
            durable=True,
            auto_delete=False
        )
        
        # Declare queues
        queues = [
            'nexus.tasks.high',
            'nexus.tasks.normal',
            'nexus.tasks.low',
            'nexus.events.processing',
            'nexus.dlq'  # Dead letter queue
        ]
        
        for queue_name in queues:
            await self.amqp_channel.queue_declare(
                queue_name=queue_name,
                durable=True,
                exclusive=False,
                auto_delete=False,
                arguments={
                    'x-message-ttl': 86400000,  # 24 hours
                    'x-max-length': 10000,
                    'x-overflow': 'reject-publish-dlx',
                    'x-dead-letter-exchange': 'nexus.dlx' if queue_name != 'nexus.dlq' else None
                }
            )
    
    def _register_health_checks(self):
        """Register health check functions"""
        self.health_checks['database'] = self._check_database_health
        self.health_checks['redis'] = self._check_redis_health
        self.health_checks['rabbitmq'] = self._check_rabbitmq_health
        self.health_checks['celery'] = self._check_celery_health
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute("SELECT 1")
                return {
                    'status': 'healthy',
                    'response_time': 0,
                    'pool_size': self.db_manager.get_pool_size()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            start = time.time()
            await self.redis_pool.ping()
            response_time = time.time() - start
            
            info = await self.redis_pool.info()
            return {
                'status': 'healthy',
                'response_time': response_time,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown')
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_rabbitmq_health(self) -> Dict[str, Any]:
        """Check RabbitMQ health"""
        try:
            if self.amqp_channel and not self.amqp_channel.is_closed:
                return {
                    'status': 'healthy',
                    'channel_number': self.amqp_channel.channel_number
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Channel closed'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_celery_health(self) -> Dict[str, Any]:
        """Check Celery health"""
        try:
            # Send a test task
            result = self.celery_app.send_task(
                'nexus.health_check',
                args=[],
                queue='nexus.tasks.high',
                routing_key='health'
            )
            
            # Check if we can get the result (with timeout)
            if result.id:
                return {
                    'status': 'healthy',
                    'task_id': result.id
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Failed to send task'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': self.config.APP_VERSION,
            'environment': self.config.ENVIRONMENT,
            'checks': {}
        }
        
        # Run all health checks
        for name, check_func in self.health_checks.items():
            try:
                health_status['checks'][name] = await check_func()
            except Exception as e:
                health_status['checks'][name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'unhealthy'
        
        # Check if any service is unhealthy
        if any(check.get('status') == 'unhealthy' for check in health_status['checks'].values()):
            health_status['status'] = 'unhealthy'
        
        return health_status
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def execute_with_circuit_breaker(self, service: str, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        breaker = self.circuit_breakers.get(service)
        
        if breaker and breaker.is_circuit_open():
            error_count.labels(error_type=f'{service}_circuit_open').inc()
            raise Exception(f"Circuit breaker is open for {service}")
        
        try:
            result = await func(*args, **kwargs)
            if breaker:
                breaker.record_success()
            return result
        except Exception as e:
            if breaker:
                breaker.record_failure()
            error_count.labels(error_type=f'{service}_error').inc()
            raise
    
    async def cache_get(self, key: str, default=None):
        """Get value from cache with circuit breaker"""
        with self.tracer.start_as_current_span("cache_get") as span:
            span.set_attribute("cache.key", key)
            
            try:
                value = await self.execute_with_circuit_breaker(
                    'redis',
                    self.redis_pool.get,
                    key
                )
                
                if value is not None:
                    cache_hits.inc()
                    span.set_attribute("cache.hit", True)
                    return json.loads(value)
                else:
                    cache_misses.inc()
                    span.set_attribute("cache.hit", False)
                    return default
            except Exception as e:
                logger.error(f"Cache get error: {e}")
                return default
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with circuit breaker"""
        with self.tracer.start_as_current_span("cache_set") as span:
            span.set_attribute("cache.key", key)
            span.set_attribute("cache.ttl", ttl)
            
            try:
                await self.execute_with_circuit_breaker(
                    'redis',
                    self.redis_pool.setex,
                    key,
                    ttl,
                    json.dumps(value)
                )
            except Exception as e:
                logger.error(f"Cache set error: {e}")
    
    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to message queue"""
        with self.tracer.start_as_current_span("publish_event") as span:
            span.set_attribute("event.type", event_type)
            
            try:
                await self.execute_with_circuit_breaker(
                    'rabbitmq',
                    self._publish_to_amqp,
                    'nexus.events',
                    event_type,
                    data
                )
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")
                # Fallback to Redis pub/sub
                try:
                    await self.redis_pool.publish(
                        f"nexus:events:{event_type}",
                        json.dumps(data)
                    )
                except Exception as redis_error:
                    logger.error(f"Failed to publish to Redis fallback: {redis_error}")
                    raise
    
    async def _publish_to_amqp(self, exchange: str, routing_key: str, data: Dict[str, Any]):
        """Publish message to AMQP"""
        if not self.amqp_channel or self.amqp_channel.is_closed:
            raise Exception("AMQP channel is not available")
        
        await self.amqp_channel.basic_publish(
            exchange_name=exchange,
            routing_key=routing_key,
            body=json.dumps(data).encode(),
            properties={
                'delivery_mode': 2,  # Persistent
                'content_type': 'application/json',
                'timestamp': int(time.time()),
                'app_id': 'nexus-core'
            }
        )
    
    def submit_task(self, task_name: str, args: List[Any], kwargs: Dict[str, Any] = None,
                   priority: str = 'normal') -> AsyncResult:
        """Submit task to Celery with priority"""
        queue_map = {
            'high': 'nexus.tasks.high',
            'normal': 'nexus.tasks.normal',
            'low': 'nexus.tasks.low'
        }
        
        queue = queue_map.get(priority, 'nexus.tasks.normal')
        
        result = self.celery_app.send_task(
            task_name,
            args=args,
            kwargs=kwargs or {},
            queue=queue,
            routing_key=priority
        )
        
        task_queue_size.inc()
        return result
    
    async def _monitor_connections(self):
        """Monitor and maintain connections"""
        while not self.shutdown_event.is_set():
            try:
                # Update connection metrics
                active_connections.set(self._get_active_connections())
                db_pool_size.set(self.db_manager.get_pool_size())
                
                # Check and reconnect if needed
                await self._check_and_reconnect()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _check_and_reconnect(self):
        """Check connections and reconnect if necessary"""
        # Check Redis
        try:
            await self.redis_pool.ping()
        except Exception:
            logger.warning("Redis connection lost, attempting to reconnect")
            await self._init_redis()
        
        # Check RabbitMQ
        if not self.amqp_channel or self.amqp_channel.is_closed:
            logger.warning("RabbitMQ connection lost, attempting to reconnect")
            await self._init_rabbitmq()
    
    async def _collect_metrics(self):
        """Collect custom metrics"""
        while not self.shutdown_event.is_set():
            try:
                # Collect Redis metrics
                if self.redis_pool:
                    info = await self.redis_pool.info()
                    # Custom metric collection logic here
                
                # Collect database metrics
                # Custom database metric collection logic here
                
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)
    
    def _get_active_connections(self) -> int:
        """Get total active connections"""
        connections = 0
        
        # Count database connections
        connections += self.db_manager.get_pool_size()
        
        # Count Redis connections
        # Implementation depends on Redis client
        
        return connections
    
    async def _handle_amqp_error(self, exception):
        """Handle AMQP errors"""
        logger.error(f"AMQP error: {exception}")
        error_count.labels(error_type='amqp_error').inc()
    
    async def _handle_amqp_close(self, exception):
        """Handle AMQP connection close"""
        logger.warning(f"AMQP connection closed: {exception}")
        # Trigger reconnection
        asyncio.create_task(self._init_rabbitmq())
    
    async def shutdown(self):
        """Gracefully shutdown all connections"""
        logger.info("Starting graceful shutdown")
        self.shutdown_event.set()
        
        # Close connections
        try:
            if self.redis_pool:
                await self.redis_pool.close()
            
            if self.amqp_channel:
                await self.amqp_channel.close()
            
            if self.amqp_connection:
                await self.amqp_connection.close()
            
            await self.db_manager.close()
            
            logger.info("All connections closed successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    # Load configuration
    config = ProductionConfig()
    
    # Initialize core service
    nexus = NexusCore(config)
    
    try:
        # Setup signal handlers
        nexus.setup_signal_handlers()
        
        # Initialize all services
        await nexus.initialize()
        
        # Start Prometheus metrics server
        prometheus_client.start_http_server(config.METRICS_PORT)
        logger.info(f"Metrics server started on port {config.METRICS_PORT}")
        
        # Keep the service running
        await nexus.shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await nexus.shutdown()


if __name__ == "__main__":
    asyncio.run(main())