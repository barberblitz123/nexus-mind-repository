# NEXUS 2.0 Webinar Interface

## Overview

The NEXUS Webinar Interface is a production-grade web conferencing platform fully integrated with the NEXUS 2.0 production build. It provides real-time collaboration, AI assistance, and seamless integration with all NEXUS services.

## Features

### Core Capabilities
- **Real-time video/audio conferencing** with WebRTC
- **Screen sharing** and collaborative features
- **AI-powered meeting assistant** integrated with NEXUS AI
- **Automatic transcription** and meeting summaries
- **Multi-participant support** (up to 100 participants by default)
- **Role-based access control** (host, co-host, participant, viewer)

### NEXUS 2.0 Integration
- **Production infrastructure** - Uses NEXUS core services
- **Message bus integration** - Real-time event distribution
- **Service discovery** - Automatic registration and health checks
- **Distributed state management** - Session persistence across nodes
- **Metrics and monitoring** - Prometheus metrics integration
- **Security** - JWT authentication with NEXUS auth system

## Architecture

The webinar interface is built as a microservice that integrates with:

```
┌─────────────────────────────────────────────────────┐
│                 NEXUS Webinar Interface              │
├─────────────────────────────────────────────────────┤
│  FastAPI Server (Port 8003)                         │
│  ├── REST API Endpoints                             │
│  ├── WebSocket Server                               │
│  └── Static HTML/JS Interface                      │
├─────────────────────────────────────────────────────┤
│           NEXUS Core Production Services             │
│  ├── Redis (Session Storage)                        │
│  ├── Message Bus (Event Distribution)               │
│  ├── Service Discovery (Health Monitoring)          │
│  ├── State Manager (Distributed State)              │
│  └── Database Manager (Persistent Storage)          │
└─────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Webinar-specific settings
WEBINAR_PORT=8003                    # WebSocket and API port
WEBINAR_MAX_PARTICIPANTS=100         # Maximum participants per session
WEBINAR_ENABLE_RECORDING=false       # Enable session recording

# Required NEXUS settings
REDIS_URL=redis://localhost:6379/0   # Redis connection
DATABASE_URL=postgresql://...        # PostgreSQL connection
SECRET_KEY=your-secret-key          # Application secret
JWT_SECRET_KEY=your-jwt-secret      # JWT signing key
```

### Service Configuration

The webinar interface is automatically registered in `nexus_startup_manager.py`:

```python
self.services["webinar_interface"] = ServiceInfo(
    config=ServiceConfig(
        name="webinar_interface",
        enabled=self.config.get("nexus", {}).get("features", {}).get("webinar", True),
        dependencies=["api_server", "websocket_server", "redis"],
        critical=False
    )
)
```

## API Endpoints

### Session Management
- `POST /api/webinar/create` - Create new webinar session
- `POST /api/webinar/join` - Join existing session
- `GET /api/webinar/sessions` - List active sessions

### Real-time Features
- `WS /ws/webinar` - WebSocket endpoint for real-time communication

### AI Integration
- `POST /api/webinar/ai-assist` - Query AI assistant during webinar

### Health & Monitoring
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

## Usage

### Starting the Service

1. **Via NEXUS Launcher**:
   ```bash
   ./nexus start
   ```
   The webinar interface will start automatically if enabled.

2. **Standalone Mode**:
   ```bash
   python nexus_webinar_interface.py
   ```

3. **Docker Container**:
   ```bash
   docker run -p 8003:8003 nexus-webinar
   ```

### Accessing the Interface

Navigate to: `http://localhost:8003`

Default roles:
- **Host**: Full control over session
- **Co-Host**: Moderation capabilities
- **Participant**: Standard features
- **Viewer**: View-only access

### Integration Example

```python
# Using NEXUS Integration Core
from nexus_integration_core import MessageBus

# Subscribe to webinar events
async def handle_webinar_event(event):
    if event["type"] == "participant_joined":
        print(f"User {event['user_id']} joined session {event['session_id']}")

message_bus = MessageBus()
await message_bus.subscribe("webinar.*", handle_webinar_event)
```

## Security

- **Authentication**: JWT tokens from NEXUS auth system
- **Authorization**: Role-based access control
- **Encryption**: TLS for all communications
- **Rate Limiting**: Configurable per-endpoint limits
- **CORS**: Configurable origin restrictions

## Monitoring

The webinar interface exposes Prometheus metrics:

- `nexus_webinar_connections` - Active connections per room
- `nexus_webinar_messages_total` - Message counts by type
- `nexus_webinar_latency_seconds` - Message latency histogram

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change port in environment
   export WEBINAR_PORT=8004
   ```

2. **Redis Connection Failed**
   ```bash
   # Verify Redis is running
   redis-cli ping
   ```

3. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify CORS configuration
   - Enable debug logging: `LOG_LEVEL=DEBUG`

### Debug Mode

```bash
# Enable debug logging
export DEBUG=True
export LOG_LEVEL=DEBUG
python nexus_webinar_interface.py
```

## Development

### Adding Features

1. **New API Endpoint**:
   ```python
   @app.post("/api/webinar/custom")
   async def custom_endpoint(data: CustomModel):
       # Implementation
   ```

2. **WebSocket Message Type**:
   ```python
   elif data["type"] == "custom_message":
       await handle_custom_message(data)
   ```

3. **UI Components**:
   - Edit the HTML/CSS/JS in the root endpoint
   - Or integrate with external React/Vue app

### Testing

```bash
# Run tests
pytest tests/test_webinar_interface.py

# Load testing
locust -f tests/load_test_webinar.py
```

## Roadmap

- [ ] WebRTC peer-to-peer video implementation
- [ ] Recording to cloud storage (S3/GCS)
- [ ] Live streaming integration
- [ ] Breakout rooms
- [ ] Virtual backgrounds
- [ ] Enhanced AI features (real-time translation, etc.)

## Support

For issues and questions:
- GitHub Issues: [nexus-mind-repository/issues](https://github.com/nexus-mind-repository/issues)
- Documentation: [docs.nexus-mind.ai](https://docs.nexus-mind.ai)
- Community: [Discord](https://discord.gg/nexus-mind)