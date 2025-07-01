#!/usr/bin/env python3
"""
NEXUS Integration Hub
Central event bus, API gateway, state synchronization,
transaction management, and rollback capabilities
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import pickle
import aiohttp
from aiohttp import web
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NEXUS-Integration')


class EventType(Enum):
    SYSTEM = "system"
    COMPONENT = "component"
    TASK = "task"
    STATE = "state"
    ERROR = "error"
    NOTIFICATION = "notification"
    TRANSACTION = "transaction"


class TransactionState(Enum):
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class Event:
    """Represents a system event"""
    id: str
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class Transaction:
    """Represents a distributed transaction"""
    id: str
    operations: List[Dict[str, Any]]
    state: TransactionState = TransactionState.PENDING
    participants: Set[str] = field(default_factory=set)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateSnapshot:
    """Represents a component state snapshot"""
    component: str
    state: Dict[str, Any]
    version: int
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: str = ""


class NEXUSIntegrationHub:
    """Central integration hub for all NEXUS components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        
        # Event bus
        self.event_subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.event_history: deque = deque(maxlen=self.config['event_history_size'])
        self.event_lock = threading.Lock()
        
        # State management
        self.component_states: Dict[str, StateSnapshot] = {}
        self.state_versions: Dict[str, int] = defaultdict(int)
        self.state_lock = threading.Lock()
        
        # Transaction management
        self.active_transactions: Dict[str, Transaction] = {}
        self.completed_transactions: deque = deque(maxlen=self.config['transaction_history_size'])
        self.transaction_lock = threading.Lock()
        
        # API Gateway
        self.api_routes: Dict[str, Callable] = {}
        self.api_app = None
        self.api_runner = None
        
        # WebSocket connections for real-time updates
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Component registry
        self.registered_components: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self.metrics = {
            'events_processed': 0,
            'transactions_completed': 0,
            'api_requests': 0,
            'state_syncs': 0
        }
        
        # Start services
        asyncio.create_task(self._start_services())
        
        logger.info("NEXUS Integration Hub initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'api_host': '0.0.0.0',
            'api_port': 8080,
            'websocket_port': 8081,
            'event_history_size': 10000,
            'transaction_history_size': 1000,
            'transaction_timeout': 300,  # 5 minutes
            'state_sync_interval': 30,    # seconds
            'max_retry_attempts': 3,
            'rollback_timeout': 60        # seconds
        }
    
    # Event Bus Methods
    async def publish_event(self, event_type: EventType, source: str, 
                           data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Publish an event to the event bus"""
        event = Event(
            id=f"evt_{uuid.uuid4().hex}",
            type=event_type,
            source=source,
            data=data,
            metadata=metadata or {}
        )
        
        with self.event_lock:
            self.event_history.append(event)
            self.metrics['events_processed'] += 1
        
        # Notify subscribers asynchronously
        asyncio.create_task(self._notify_subscribers(event))
        
        # Send to WebSocket clients
        asyncio.create_task(self._broadcast_event(event))
        
        logger.debug(f"Published event {event.id} from {source}")
        
        return event.id
    
    def subscribe_event(self, event_type: EventType, handler: Callable) -> bool:
        """Subscribe to events of a specific type"""
        with self.event_lock:
            self.event_subscribers[event_type].append(handler)
        
        logger.info(f"Subscribed handler to {event_type.value} events")
        return True
    
    def unsubscribe_event(self, event_type: EventType, handler: Callable) -> bool:
        """Unsubscribe from events"""
        with self.event_lock:
            if handler in self.event_subscribers[event_type]:
                self.event_subscribers[event_type].remove(handler)
                return True
        return False
    
    async def _notify_subscribers(self, event: Event):
        """Notify all subscribers of an event"""
        handlers = []
        with self.event_lock:
            handlers = self.event_subscribers[event.type].copy()
        
        # Execute handlers in parallel
        tasks = []
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(event))
            else:
                # Run sync handlers in thread executor
                tasks.append(
                    asyncio.get_event_loop().run_in_executor(None, handler, event)
                )
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any handler errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Event handler error: {result}")
    
    # State Synchronization Methods
    async def sync_state(self, component: str, state: Dict[str, Any]) -> bool:
        """Synchronize component state"""
        with self.state_lock:
            # Increment version
            self.state_versions[component] += 1
            version = self.state_versions[component]
            
            # Create snapshot
            snapshot = StateSnapshot(
                component=component,
                state=state.copy(),
                version=version,
                checksum=self._calculate_checksum(state)
            )
            
            # Store snapshot
            self.component_states[component] = snapshot
            self.metrics['state_syncs'] += 1
        
        # Publish state change event
        await self.publish_event(
            EventType.STATE,
            component,
            {
                'version': version,
                'checksum': snapshot.checksum
            },
            {'sync_type': 'full'}
        )
        
        logger.info(f"Synchronized state for {component} (v{version})")
        return True
    
    async def get_state(self, component: str) -> Optional[Dict[str, Any]]:
        """Get current state of a component"""
        with self.state_lock:
            snapshot = self.component_states.get(component)
            if snapshot:
                return {
                    'state': snapshot.state.copy(),
                    'version': snapshot.version,
                    'timestamp': snapshot.timestamp.isoformat(),
                    'checksum': snapshot.checksum
                }
        return None
    
    async def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all components"""
        with self.state_lock:
            return {
                component: {
                    'state': snapshot.state.copy(),
                    'version': snapshot.version,
                    'timestamp': snapshot.timestamp.isoformat()
                }
                for component, snapshot in self.component_states.items()
            }
    
    # Transaction Management Methods
    async def begin_transaction(self, operations: List[Dict[str, Any]], 
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """Begin a new distributed transaction"""
        transaction = Transaction(
            id=f"txn_{uuid.uuid4().hex}",
            operations=operations,
            metadata=metadata or {}
        )
        
        # Extract participants from operations
        for op in operations:
            transaction.participants.add(op.get('component', 'unknown'))
        
        with self.transaction_lock:
            self.active_transactions[transaction.id] = transaction
        
        # Start transaction timeout
        asyncio.create_task(self._transaction_timeout_handler(transaction.id))
        
        # Publish transaction start event
        await self.publish_event(
            EventType.TRANSACTION,
            'integration_hub',
            {
                'transaction_id': transaction.id,
                'action': 'begin',
                'participants': list(transaction.participants)
            }
        )
        
        logger.info(f"Started transaction {transaction.id} with {len(operations)} operations")
        
        return transaction.id
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction"""
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            if transaction.state != TransactionState.PENDING:
                logger.error(f"Transaction {transaction_id} not in pending state")
                return False
        
        try:
            # Execute all operations
            for operation in transaction.operations:
                success = await self._execute_operation(operation, transaction_id)
                if not success:
                    # Rollback on failure
                    await self.rollback_transaction(transaction_id)
                    return False
            
            # Mark as committed
            with self.transaction_lock:
                transaction.state = TransactionState.COMMITTED
                transaction.end_time = datetime.now()
                
                # Move to completed
                del self.active_transactions[transaction_id]
                self.completed_transactions.append(transaction)
                self.metrics['transactions_completed'] += 1
            
            # Publish commit event
            await self.publish_event(
                EventType.TRANSACTION,
                'integration_hub',
                {
                    'transaction_id': transaction_id,
                    'action': 'commit',
                    'duration': (transaction.end_time - transaction.start_time).seconds
                }
            )
            
            logger.info(f"Committed transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error committing transaction {transaction_id}: {e}")
            await self.rollback_transaction(transaction_id)
            return False
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction"""
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                # Check completed transactions
                for txn in self.completed_transactions:
                    if txn.id == transaction_id:
                        transaction = txn
                        break
                
                if not transaction:
                    logger.error(f"Transaction {transaction_id} not found")
                    return False
        
        try:
            # Execute rollback operations
            for component, rollback_data in transaction.rollback_data.items():
                await self._execute_rollback(component, rollback_data, transaction_id)
            
            # Update transaction state
            with self.transaction_lock:
                transaction.state = TransactionState.ROLLED_BACK
                transaction.end_time = datetime.now()
                
                # Ensure it's in completed list
                if transaction_id in self.active_transactions:
                    del self.active_transactions[transaction_id]
                    self.completed_transactions.append(transaction)
            
            # Publish rollback event
            await self.publish_event(
                EventType.TRANSACTION,
                'integration_hub',
                {
                    'transaction_id': transaction_id,
                    'action': 'rollback',
                    'reason': 'Requested or failed operation'
                }
            )
            
            logger.info(f"Rolled back transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back transaction {transaction_id}: {e}")
            
            with self.transaction_lock:
                transaction.state = TransactionState.FAILED
            
            return False
    
    async def _execute_operation(self, operation: Dict[str, Any], transaction_id: str) -> bool:
        """Execute a single operation within a transaction"""
        component = operation.get('component')
        method = operation.get('method')
        args = operation.get('args', {})
        
        # Get component
        comp_info = self.registered_components.get(component)
        if not comp_info:
            logger.error(f"Component {component} not registered")
            return False
        
        instance = comp_info.get('instance')
        if not instance:
            logger.error(f"Component {component} has no instance")
            return False
        
        # Store current state for rollback
        if hasattr(instance, 'get_state'):
            current_state = await instance.get_state()
            transaction = self.active_transactions[transaction_id]
            transaction.rollback_data[component] = current_state
        
        # Execute operation
        try:
            method_func = getattr(instance, method, None)
            if not method_func:
                logger.error(f"Method {method} not found on {component}")
                return False
            
            # Add transaction context
            args['_transaction_id'] = transaction_id
            
            if asyncio.iscoroutinefunction(method_func):
                result = await method_func(**args)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, method_func, **args
                )
            
            # Check result
            if isinstance(result, dict) and not result.get('success', True):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing operation {method} on {component}: {e}")
            return False
    
    async def _execute_rollback(self, component: str, rollback_data: Any, transaction_id: str):
        """Execute rollback for a component"""
        comp_info = self.registered_components.get(component)
        if not comp_info:
            logger.error(f"Component {component} not registered for rollback")
            return
        
        instance = comp_info.get('instance')
        if not instance:
            return
        
        # Restore state if possible
        if hasattr(instance, 'restore_state'):
            try:
                await instance.restore_state(rollback_data)
                logger.info(f"Restored state for {component}")
            except Exception as e:
                logger.error(f"Error restoring state for {component}: {e}")
    
    async def _transaction_timeout_handler(self, transaction_id: str):
        """Handle transaction timeout"""
        timeout = self.config['transaction_timeout']
        await asyncio.sleep(timeout)
        
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if transaction and transaction.state == TransactionState.PENDING:
                logger.warning(f"Transaction {transaction_id} timed out")
                
        # Rollback timed out transaction
        await self.rollback_transaction(transaction_id)
    
    # API Gateway Methods
    def register_api_route(self, path: str, handler: Callable, methods: List[str] = ['GET']):
        """Register an API route"""
        self.api_routes[path] = {
            'handler': handler,
            'methods': methods
        }
        logger.info(f"Registered API route: {path}")
    
    async def _start_api_server(self):
        """Start the API server"""
        app = web.Application()
        
        # Add routes
        app.router.add_route('*', '/api/event', self._handle_event_api)
        app.router.add_route('GET', '/api/state/{component}', self._handle_state_api)
        app.router.add_route('POST', '/api/transaction', self._handle_transaction_api)
        app.router.add_route('GET', '/api/health', self._handle_health_api)
        app.router.add_route('GET', '/api/metrics', self._handle_metrics_api)
        
        # Add custom routes
        for path, route_info in self.api_routes.items():
            for method in route_info['methods']:
                app.router.add_route(method, f'/api{path}', route_info['handler'])
        
        self.api_app = app
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config['api_host'], self.config['api_port'])
        await site.start()
        
        self.api_runner = runner
        
        logger.info(f"API server started on {self.config['api_host']}:{self.config['api_port']}")
    
    async def _handle_event_api(self, request: web.Request) -> web.Response:
        """Handle event API requests"""
        self.metrics['api_requests'] += 1
        
        if request.method == 'POST':
            # Publish event
            try:
                data = await request.json()
                event_id = await self.publish_event(
                    EventType(data.get('type', 'notification')),
                    data.get('source', 'api'),
                    data.get('data', {}),
                    data.get('metadata')
                )
                
                return web.json_response({
                    'success': True,
                    'event_id': event_id
                })
                
            except Exception as e:
                return web.json_response({
                    'success': False,
                    'error': str(e)
                }, status=400)
        
        elif request.method == 'GET':
            # Get event history
            limit = int(request.query.get('limit', 100))
            
            with self.event_lock:
                events = list(self.event_history)[-limit:]
            
            return web.json_response({
                'success': True,
                'events': [e.to_dict() for e in events],
                'total': len(events)
            })
        
        return web.json_response({'error': 'Method not allowed'}, status=405)
    
    async def _handle_state_api(self, request: web.Request) -> web.Response:
        """Handle state API requests"""
        self.metrics['api_requests'] += 1
        
        component = request.match_info.get('component')
        
        if component == '_all':
            # Get all states
            states = await self.get_all_states()
            return web.json_response({
                'success': True,
                'states': states
            })
        else:
            # Get specific component state
            state = await self.get_state(component)
            if state:
                return web.json_response({
                    'success': True,
                    'component': component,
                    'state': state
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': f'Component {component} not found'
                }, status=404)
    
    async def _handle_transaction_api(self, request: web.Request) -> web.Response:
        """Handle transaction API requests"""
        self.metrics['api_requests'] += 1
        
        try:
            data = await request.json()
            
            if data.get('action') == 'begin':
                # Start new transaction
                transaction_id = await self.begin_transaction(
                    data.get('operations', []),
                    data.get('metadata')
                )
                
                return web.json_response({
                    'success': True,
                    'transaction_id': transaction_id
                })
            
            elif data.get('action') == 'commit':
                # Commit transaction
                success = await self.commit_transaction(data.get('transaction_id'))
                
                return web.json_response({
                    'success': success
                })
            
            elif data.get('action') == 'rollback':
                # Rollback transaction
                success = await self.rollback_transaction(data.get('transaction_id'))
                
                return web.json_response({
                    'success': success
                })
            
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Invalid action'
                }, status=400)
                
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    async def _handle_health_api(self, request: web.Request) -> web.Response:
        """Handle health check API"""
        return web.json_response({
            'status': 'healthy',
            'components': len(self.registered_components),
            'active_transactions': len(self.active_transactions),
            'event_subscribers': sum(len(subs) for subs in self.event_subscribers.values()),
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_metrics_api(self, request: web.Request) -> web.Response:
        """Handle metrics API"""
        return web.json_response({
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    # WebSocket Methods
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        async def websocket_handler(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info(f"WebSocket client connected: {websocket.remote_address}")
            
            try:
                # Send initial state
                await websocket.send(json.dumps({
                    'type': 'connection',
                    'data': {
                        'message': 'Connected to NEXUS Integration Hub',
                        'timestamp': datetime.now().isoformat()
                    }
                }))
                
                # Keep connection alive
                await websocket.wait_closed()
                
            finally:
                self.websocket_clients.remove(websocket)
                logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
        
        # Start server
        server = await websockets.serve(
            websocket_handler,
            self.config['api_host'],
            self.config['websocket_port']
        )
        
        logger.info(f"WebSocket server started on {self.config['api_host']}:{self.config['websocket_port']}")
    
    async def _broadcast_event(self, event: Event):
        """Broadcast event to all WebSocket clients"""
        if not self.websocket_clients:
            return
        
        message = json.dumps({
            'type': 'event',
            'data': event.to_dict()
        })
        
        # Send to all connected clients
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.websocket_clients -= disconnected
    
    # Component Registration
    def register_component(self, name: str, instance: Any, 
                          capabilities: Optional[List[str]] = None) -> bool:
        """Register a component with the hub"""
        self.registered_components[name] = {
            'instance': instance,
            'capabilities': capabilities or [],
            'registered_at': datetime.now()
        }
        
        logger.info(f"Registered component: {name}")
        
        # Publish registration event
        asyncio.create_task(self.publish_event(
            EventType.SYSTEM,
            'integration_hub',
            {
                'action': 'component_registered',
                'component': name,
                'capabilities': capabilities or []
            }
        ))
        
        return True
    
    def unregister_component(self, name: str) -> bool:
        """Unregister a component"""
        if name in self.registered_components:
            del self.registered_components[name]
            
            logger.info(f"Unregistered component: {name}")
            
            # Publish unregistration event
            asyncio.create_task(self.publish_event(
                EventType.SYSTEM,
                'integration_hub',
                {
                    'action': 'component_unregistered',
                    'component': name
                }
            ))
            
            return True
        
        return False
    
    # Utility Methods
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data"""
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    async def _start_services(self):
        """Start all hub services"""
        # Start API server
        await self._start_api_server()
        
        # Start WebSocket server
        await self._start_websocket_server()
        
        # Start state sync loop
        asyncio.create_task(self._state_sync_loop())
        
        logger.info("All integration hub services started")
    
    async def _state_sync_loop(self):
        """Periodic state synchronization check"""
        while True:
            try:
                await asyncio.sleep(self.config['state_sync_interval'])
                
                # Check component states
                for name, comp_info in self.registered_components.items():
                    instance = comp_info['instance']
                    
                    if hasattr(instance, 'get_state'):
                        try:
                            current_state = await instance.get_state()
                            
                            # Check if state has changed
                            existing = self.component_states.get(name)
                            if not existing or self._calculate_checksum(current_state) != existing.checksum:
                                await self.sync_state(name, current_state)
                                
                        except Exception as e:
                            logger.error(f"Error syncing state for {name}: {e}")
                
            except Exception as e:
                logger.error(f"Error in state sync loop: {e}")
    
    async def shutdown(self):
        """Shutdown the integration hub"""
        logger.info("Shutting down NEXUS Integration Hub...")
        
        # Close WebSocket connections
        for client in list(self.websocket_clients):
            await client.close()
        
        # Stop API server
        if self.api_runner:
            await self.api_runner.cleanup()
        
        # Rollback any pending transactions
        for txn_id in list(self.active_transactions.keys()):
            await self.rollback_transaction(txn_id)
        
        logger.info("NEXUS Integration Hub shutdown complete")


# Demo function
async def demo_integration_hub():
    """Demonstrate integration hub capabilities"""
    
    # Create hub
    hub = NEXUSIntegrationHub()
    
    # Wait for services to start
    await asyncio.sleep(1)
    
    # Create mock component
    class MockComponent:
        def __init__(self, name):
            self.name = name
            self.state = {'value': 0, 'status': 'ready'}
        
        async def get_state(self):
            return self.state.copy()
        
        async def update_value(self, new_value, _transaction_id=None):
            self.state['value'] = new_value
            return {'success': True}
        
        async def restore_state(self, old_state):
            self.state = old_state.copy()
    
    # Register components
    comp1 = MockComponent("component1")
    comp2 = MockComponent("component2")
    
    hub.register_component("component1", comp1, ["update", "query"])
    hub.register_component("component2", comp2, ["update", "query"])
    
    # Subscribe to events
    events_received = []
    
    async def event_handler(event: Event):
        events_received.append(event)
        print(f"Received event: {event.type.value} from {event.source}")
    
    hub.subscribe_event(EventType.STATE, event_handler)
    hub.subscribe_event(EventType.TRANSACTION, event_handler)
    
    # Publish some events
    await hub.publish_event(
        EventType.NOTIFICATION,
        "demo",
        {"message": "Demo started"}
    )
    
    # Sync component states
    await hub.sync_state("component1", comp1.state)
    await hub.sync_state("component2", comp2.state)
    
    # Get states
    state1 = await hub.get_state("component1")
    print("Component1 state:", state1)
    
    # Start a transaction
    transaction_id = await hub.begin_transaction([
        {
            'component': 'component1',
            'method': 'update_value',
            'args': {'new_value': 42}
        },
        {
            'component': 'component2',
            'method': 'update_value',
            'args': {'new_value': 100}
        }
    ])
    
    print(f"Started transaction: {transaction_id}")
    
    # Commit transaction
    success = await hub.commit_transaction(transaction_id)
    print(f"Transaction commit: {'Success' if success else 'Failed'}")
    
    # Check updated states
    await hub.sync_state("component1", comp1.state)
    await hub.sync_state("component2", comp2.state)
    
    # Start another transaction and rollback
    transaction_id2 = await hub.begin_transaction([
        {
            'component': 'component1',
            'method': 'update_value',
            'args': {'new_value': 999}
        }
    ])
    
    # Execute but then rollback
    await hub.commit_transaction(transaction_id2)
    await hub.rollback_transaction(transaction_id2)
    
    print("\nEvents received:", len(events_received))
    print("Metrics:", hub.metrics)
    
    # Test API
    print("\nTesting API endpoints:")
    print(f"API available at http://localhost:{hub.config['api_port']}/api/")
    print(f"WebSocket available at ws://localhost:{hub.config['websocket_port']}/")
    
    # Shutdown
    await hub.shutdown()


if __name__ == "__main__":
    asyncio.run(demo_integration_hub())