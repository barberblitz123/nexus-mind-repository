# NEXUS Integration Core

The NEXUS Integration Core is a central hub that connects all NEXUS components together, providing service discovery, message bus, state management, API gateway, and plugin system capabilities.

## Features

### 1. **Service Registry**
- Service discovery and registration
- Health monitoring with automatic status updates
- Load balancing with least-loaded strategy
- Capability-based service filtering
- Automatic heartbeat monitoring

### 2. **Message Bus**
- Publish/subscribe messaging with topic filtering
- Message priorities (LOW, NORMAL, HIGH, CRITICAL)
- Distributed messaging via ZeroMQ
- Redis persistence for message durability
- Dead letter queue for failed messages
- Wildcard topic subscriptions

### 3. **State Management**
- Global state store with versioning
- Optimistic locking for concurrent updates
- Conflict resolution with custom resolvers
- Change notifications and watchers
- State history tracking
- Persistent state with periodic snapshots

### 4. **API Gateway**
- REST API endpoints
- GraphQL server with introspection
- WebSocket support for real-time communication
- JWT authentication
- Rate limiting
- Unified access point for all services

### 5. **Plugin System**
- Dynamic plugin loading
- Sandboxed execution environment
- Hook system for extensibility
- Resource management
- Namespaced state access

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   NEXUS Integration Core                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Service   │  │   Message    │  │    State     │  │
│  │  Registry   │  │     Bus      │  │    Store     │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                 ↓                 ↓          │
│  ┌──────────────────────────────────────────────────┐  │
│  │                  API Gateway                      │  │
│  │  ┌────────┐  ┌─────────┐  ┌──────────────────┐  │  │
│  │  │  REST  │  │ GraphQL │  │    WebSocket     │  │  │
│  │  └────────┘  └─────────┘  └──────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                 Plugin System                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Installation

1. Install dependencies:
```bash
pip install -r nexus_integration_requirements.txt
```

2. Optional: Install Redis for distributed messaging:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

## Usage

### Starting the Integration Core

```python
from nexus_integration_core import NexusIntegrationCore

# Configuration
config = {
    'api_host': '0.0.0.0',
    'api_port': 8080,
    'redis_url': 'redis://localhost:6379',  # Optional
    'state_file': 'nexus_state.json',
    'plugin_dir': 'nexus_plugins'
}

# Create and start
core = NexusIntegrationCore(config)
await core.start()
```

### Registering a Service

```python
from nexus_integration_core import ServiceInfo

await core.service_registry.register(ServiceInfo(
    id="my-service",
    name="my-service",
    version="1.0.0",
    host="localhost",
    port=8081,
    capabilities=["feature1", "feature2"],
    health_check_url="/health"
))
```

### Publishing Events

```python
# Simple event
await core.message_bus.publish(
    "user.created",
    {"user_id": 123, "name": "John Doe"}
)

# High priority event
await core.message_bus.publish(
    "system.alert",
    {"severity": "critical", "message": "Database down"},
    priority=MessagePriority.CRITICAL
)
```

### Subscribing to Events

```python
async def handle_user_event(message):
    print(f"User event: {message.payload}")

# Subscribe to specific topic
core.message_bus.subscribe("user.created", handle_user_event)

# Subscribe with wildcard
core.message_bus.subscribe("user.*", handle_user_event)
```

### State Management

```python
# Set state
await core.state_store.set("app_config", {"theme": "dark"})

# Get state
config = await core.state_store.get("app_config")

# Watch for changes
def config_changed(key, old_value, new_value):
    print(f"Config changed: {old_value} -> {new_value}")

core.state_store.watch("app_config", config_changed)
```

## API Endpoints

### REST API

- `GET /health` - Health check
- `GET /services` - List all services
- `POST /services/{name}/invoke` - Invoke service method
- `GET /state/{key}` - Get state value
- `PUT /state/{key}` - Set state value
- `POST /events/{topic}` - Publish event

### GraphQL

Access GraphQL playground at `http://localhost:8080/graphql`

Example queries:

```graphql
# List services
query {
  services {
    id
    name
    status
    capabilities
  }
}

# Get state
query {
  state(key: "app_config") {
    key
    value
    version
  }
}

# Publish event
mutation {
  publishEvent(topic: "test.event", payload: "{\"data\": \"test\"}") {
    success
    messageId
  }
}
```

### WebSocket

Connect to `ws://localhost:8080/ws`

```javascript
// Subscribe to events
ws.send(JSON.stringify({
  type: "subscribe",
  topic: "system.*"
}));

// Publish event
ws.send(JSON.stringify({
  type: "publish",
  topic: "test.event",
  payload: {data: "test"}
}));
```

## Creating Plugins

```python
from nexus_integration_core import Plugin, PluginContext

class MyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "my-plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self, context: PluginContext):
        # Access core services
        self.context = context
        
        # Subscribe to events
        context.message_bus.subscribe("test.*", self.handle_event)
        
        # Register hooks
        context.plugin_system.register_hook(
            "before_service_invoke",
            self.before_invoke,
            self.name
        )
    
    async def shutdown(self):
        # Cleanup
        pass
    
    async def handle_event(self, message):
        print(f"Plugin received: {message.topic}")
    
    async def before_invoke(self, service_name, data):
        print(f"Service {service_name} being invoked")
```

## Integration with NEXUS Components

The integration core is designed to connect all NEXUS components:

- **Memory Core** - Centralized memory storage and retrieval
- **Omnipotent Core** - Code generation and analysis
- **MANUS Agent** - Autonomous task execution
- **Web Scraper** - Data collection
- **Tool Services** - Various utility services

See `launch_nexus_integration.py` for a complete example of integrating all components.

## Client Usage

Use the provided client for easy interaction:

```python
from nexus_integration_client import NexusIntegrationClient

async with NexusIntegrationClient() as client:
    # Check health
    health = await client.health_check()
    
    # List services
    services = await client.list_services()
    
    # Publish event
    await client.publish_event("test.event", {"data": "test"})
    
    # WebSocket events
    await client.connect_websocket()
    await client.subscribe_to_events("system.*")
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `api_host` | API server host | `0.0.0.0` |
| `api_port` | API server port | `8080` |
| `redis_url` | Redis connection URL | `None` |
| `state_file` | State persistence file | `nexus_state.json` |
| `plugin_dir` | Plugin directory | `nexus_plugins` |

## Performance Considerations

- Use Redis for distributed deployments
- Enable message persistence for critical events
- Monitor service health check intervals
- Adjust rate limiting based on load
- Use appropriate message priorities

## Security

- JWT authentication for API access
- Rate limiting to prevent abuse
- Plugin sandboxing for isolation
- State versioning for conflict resolution
- Audit logging via message bus

## Troubleshooting

1. **Services not discovered**: Check health check URLs and timeouts
2. **Messages not delivered**: Verify topic subscriptions and handler errors
3. **State conflicts**: Implement custom conflict resolvers
4. **Plugin errors**: Check plugin logs and sandbox restrictions
5. **WebSocket disconnects**: Monitor connection stability and heartbeats

## Future Enhancements

- [ ] Distributed state synchronization
- [ ] Advanced load balancing strategies
- [ ] Plugin marketplace
- [ ] Metrics and monitoring dashboard
- [ ] Message replay capabilities
- [ ] Enhanced security features