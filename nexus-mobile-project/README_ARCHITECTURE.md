# NEXUS Mobile Project Architecture

## Overview
The NEXUS Mobile Project provides deployment configurations for mobile devices (iPad/iPhone) and local Docker deployments.

## Directory Structure

### Backend Services
```
backend/
├── bridge/
│   └── socket-bridge.js         # WebSocket bridge for mobile
├── central-consciousness-core/
│   ├── consciousness_core.py    # Core consciousness engine
│   ├── auditory-processor-real.py
│   ├── visual-processor-real.py
│   └── unified_nexus_core.py
├── livekit/
│   ├── livekit.yaml            # LiveKit configuration
│   └── setup_livekit_server.sh
└── nexus-mcp/
    └── src/
        ├── index.ts            # MCP server entry
        ├── consciousness-injector.ts
        └── livekit-manager.ts
```

### Deployment Configurations
```
deployment/
└── local/
    ├── docker-compose.yml      # Full stack deployment
    ├── docker-compose-minimal.yml
    ├── start-nexus.sh         # Main launch script
    ├── start-nexus-simple.sh
    └── monitoring/
        └── prometheus.yml
```

### Mobile App
```
mobile/
└── ios-app/
    ├── NexusApp.xcodeproj/    # Xcode project
    ├── Package.swift          # Swift package
    └── Sources/
        └── NexusApp.swift     # Main app entry
```

## Service Architecture

### Core Services
1. **Consciousness Core** (Python)
   - Central AI processing
   - Memory management
   - Context handling

2. **LiveKit Server** (Go)
   - Real-time video/audio
   - WebRTC signaling
   - Recording capabilities

3. **MCP Server** (TypeScript)
   - Model Context Protocol
   - AI model management
   - Request routing

4. **Socket Bridge** (Node.js)
   - Mobile WebSocket adapter
   - Protocol translation
   - Connection management

### Docker Services
```yaml
services:
  - postgres      # Main database
  - redis         # Cache & pub/sub
  - nginx         # Reverse proxy
  - nexus-backend # Python services
  - nexus-web     # Web interface
  - livekit       # Media server
  - prometheus    # Monitoring
  - grafana       # Dashboards
```

## Mobile Integration

### iOS App Structure
```
NexusApp/
├── ConsciousnessSyncManager.swift  # Sync with backend
├── ContentView.swift              # Main UI
└── NexusApp.swift                # App entry point
```

### Communication Flow
```
iOS App
  ↓ (WebSocket)
Socket Bridge
  ↓ (HTTP/WS)
NEXUS Backend
  ↓
Core Services
```

## Deployment

### Local Docker Deployment
```bash
cd deployment/local/
./start-nexus.sh
```

### Services Started
1. PostgreSQL (5432)
2. Redis (6379)
3. NGINX (80, 443)
4. NEXUS Backend (8000)
5. NEXUS Web (8080)
6. LiveKit (7880)
7. MCP Server (3000)
8. Prometheus (9090)
9. Grafana (3001)

### iOS Deployment
1. Open `mobile/ios-app/NexusApp.xcodeproj`
2. Configure signing team
3. Build and deploy to device

## Configuration

### Environment Variables
```bash
# Database
POSTGRES_DB=nexus
POSTGRES_USER=nexus
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379

# LiveKit
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# Services
BACKEND_URL=http://nexus-backend:8000
FRONTEND_URL=http://nexus-web:8080
```

### LiveKit Configuration
Edit `livekit/livekit.yaml`:
```yaml
port: 7880
rtc:
  port_range_start: 50000
  port_range_end: 60000
keys:
  your_key: your_secret
```

## Monitoring

### Prometheus Metrics
- Service health
- Request rates
- Error rates
- Resource usage

### Grafana Dashboards
- System overview
- Service performance
- User activity
- Error tracking

## Troubleshooting

### Common Issues

1. **Docker services not starting**
   ```bash
   docker-compose logs [service-name]
   ```

2. **iOS app can't connect**
   - Check Socket Bridge logs
   - Verify network settings
   - Ensure services are running

3. **LiveKit issues**
   - Check firewall rules
   - Verify UDP ports 50000-60000
   - Test with LiveKit CLI

### Debug Commands
```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f

# Restart service
docker-compose restart [service]

# Clean restart
docker-compose down && docker-compose up -d
```

## Security

### Network Security
- All services behind NGINX
- SSL/TLS termination
- Rate limiting enabled

### Authentication
- JWT tokens for API
- WebSocket authentication
- LiveKit access tokens

### Data Security
- Encrypted at rest (PostgreSQL)
- Encrypted in transit (TLS)
- Regular backups

## Performance

### Optimization Tips
1. Use Redis for session storage
2. Enable PostgreSQL connection pooling
3. Configure NGINX caching
4. Limit LiveKit bandwidth
5. Use CDN for static assets