#!/usr/bin/env python3
"""
Test Production Integration - Comprehensive testing for NEXUS production deployment
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import pytest
import aiohttp
import websockets
from rich.console import Console
from rich.table import Table
from rich.progress import track


class IntegrationTester:
    """Test all NEXUS production components"""
    
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.console = Console()
        self.results = []
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        self.console.print("[bold cyan]NEXUS Production Integration Tests[/bold cyan]\n")
        
        test_suites = [
            ("Core API", self.test_core_api),
            ("Service Discovery", self.test_service_discovery),
            ("Message Bus", self.test_message_bus),
            ("State Management", self.test_state_management),
            ("GraphQL API", self.test_graphql),
            ("WebSocket", self.test_websocket),
            ("Distributed Transactions", self.test_transactions),
            ("Plugin System", self.test_plugins),
            ("Performance", self.test_performance),
            ("Security", self.test_security)
        ]
        
        for name, test_func in test_suites:
            self.console.print(f"\n[yellow]Testing {name}...[/yellow]")
            try:
                await test_func()
                self.results.append((name, "PASSED", None))
                self.console.print(f"[green]✓ {name} tests passed[/green]")
            except Exception as e:
                self.results.append((name, "FAILED", str(e)))
                self.console.print(f"[red]✗ {name} tests failed: {e}[/red]")
        
        self._print_summary()
    
    async def test_core_api(self):
        """Test core API endpoints"""
        async with aiohttp.ClientSession() as session:
            # Health check
            async with session.get(f"{self.api_url}/health") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data['status'] == 'healthy'
            
            # Service listing
            async with session.get(f"{self.api_url}/services") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'services' in data
    
    async def test_service_discovery(self):
        """Test service discovery"""
        async with aiohttp.ClientSession() as session:
            # Register a test service
            service_data = {
                "name": "test-service",
                "version": "1.0.0",
                "host": "localhost",
                "port": 9999,
                "capabilities": ["test", "demo"]
            }
            
            async with session.post(
                f"{self.api_url}/services/register",
                json=service_data
            ) as resp:
                assert resp.status in [200, 201]
                data = await resp.json()
                service_id = data.get('id')
            
            # Discover service
            async with session.get(
                f"{self.api_url}/services/discover/test-service"
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert len(data) > 0
            
            # Deregister
            async with session.delete(
                f"{self.api_url}/services/{service_id}"
            ) as resp:
                assert resp.status in [200, 204]
    
    async def test_message_bus(self):
        """Test message bus functionality"""
        async with aiohttp.ClientSession() as session:
            # Publish message
            message_data = {
                "payload": {"test": "data"},
                "priority": 1
            }
            
            async with session.post(
                f"{self.api_url}/events/test.topic",
                json=message_data
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'message_id' in data
    
    async def test_state_management(self):
        """Test state management"""
        async with aiohttp.ClientSession() as session:
            # Set state
            state_data = {
                "value": {"counter": 42, "name": "test"},
                "expected_version": None
            }
            
            async with session.put(
                f"{self.api_url}/state/test-key",
                json=state_data
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data['success'] is True
                version = data['version']
            
            # Get state
            async with session.get(f"{self.api_url}/state/test-key") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data['value']['counter'] == 42
                assert data['version'] == version
            
            # Update with version check
            state_data['value']['counter'] = 43
            state_data['expected_version'] = version
            
            async with session.put(
                f"{self.api_url}/state/test-key",
                json=state_data
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data['success'] is True
    
    async def test_graphql(self):
        """Test GraphQL API"""
        async with aiohttp.ClientSession() as session:
            # Query services
            query = """
            query {
                services {
                    id
                    name
                    status
                    capabilities
                }
            }
            """
            
            async with session.post(
                f"{self.api_url}/graphql",
                json={"query": query}
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'data' in data
                assert 'services' in data['data']
            
            # Mutation
            mutation = """
            mutation PublishEvent($topic: String!, $payload: String!) {
                publishEvent(topic: $topic, payload: $payload) {
                    success
                    messageId
                }
            }
            """
            
            variables = {
                "topic": "test.graphql",
                "payload": json.dumps({"test": "graphql"})
            }
            
            async with session.post(
                f"{self.api_url}/graphql",
                json={"query": mutation, "variables": variables}
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data['data']['publishEvent']['success'] is True
    
    async def test_websocket(self):
        """Test WebSocket functionality"""
        ws_url = self.api_url.replace("http", "ws") + "/ws"
        
        async with websockets.connect(ws_url) as websocket:
            # Subscribe to topic
            await websocket.send(json.dumps({
                "type": "subscribe",
                "topic": "test.websocket"
            }))
            
            # Publish via REST API
            async with aiohttp.ClientSession() as session:
                message_data = {
                    "payload": {"via": "rest"},
                    "priority": 1
                }
                
                async with session.post(
                    f"{self.api_url}/events/test.websocket",
                    json=message_data
                ) as resp:
                    assert resp.status == 200
            
            # Receive via WebSocket
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            assert data['type'] == 'event'
            assert data['topic'] == 'test.websocket'
            
            # Publish via WebSocket
            await websocket.send(json.dumps({
                "type": "publish",
                "topic": "test.websocket",
                "payload": {"via": "websocket"}
            }))
            
            # Unsubscribe
            await websocket.send(json.dumps({
                "type": "unsubscribe",
                "topic": "test.websocket"
            }))
    
    async def test_transactions(self):
        """Test distributed transactions"""
        async with aiohttp.ClientSession() as session:
            # Begin transaction
            txn_data = {
                "participants": ["service1", "service2"],
                "operations": [
                    {"service": "service1", "action": "update", "data": {}},
                    {"service": "service2", "action": "create", "data": {}}
                ]
            }
            
            async with session.post(
                f"{self.api_url}/transactions/begin",
                json=txn_data
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                txn_id = data['transaction_id']
            
            # Prepare transaction
            async with session.post(
                f"{self.api_url}/transactions/{txn_id}/prepare"
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                # In real test, services would vote
            
            # Abort transaction (since we don't have real services)
            async with session.post(
                f"{self.api_url}/transactions/{txn_id}/abort"
            ) as resp:
                assert resp.status == 200
    
    async def test_plugins(self):
        """Test plugin system"""
        async with aiohttp.ClientSession() as session:
            # List plugins
            async with session.get(f"{self.api_url}/plugins") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'plugins' in data
            
            # Plugin health
            async with session.get(f"{self.api_url}/plugins/health") as resp:
                assert resp.status == 200
    
    async def test_performance(self):
        """Test performance metrics"""
        async with aiohttp.ClientSession() as session:
            # Concurrent requests
            tasks = []
            for i in range(50):
                task = session.get(f"{self.api_url}/health")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            duration = time.time() - start_time
            
            # Check all succeeded
            for resp in responses:
                assert resp.status == 200
            
            # Check performance
            requests_per_second = len(tasks) / duration
            assert requests_per_second > 100  # Should handle >100 req/s
            
            self.console.print(
                f"Performance: {requests_per_second:.1f} requests/second"
            )
    
    async def test_security(self):
        """Test security features"""
        async with aiohttp.ClientSession() as session:
            # Test unauthorized access
            async with session.get(
                f"{self.api_url}/secure/endpoint"
            ) as resp:
                assert resp.status == 401
            
            # Test rate limiting
            # Make many requests quickly
            for i in range(110):  # Over the 100/minute limit
                try:
                    async with session.get(f"{self.api_url}/health") as resp:
                        if resp.status == 429:
                            # Rate limited as expected
                            break
                except:
                    pass
            else:
                # Should have been rate limited
                assert False, "Rate limiting not working"
    
    def _print_summary(self):
        """Print test summary"""
        table = Table(title="Test Results Summary")
        table.add_column("Test Suite", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        passed = 0
        failed = 0
        
        for name, status, details in self.results:
            if status == "PASSED":
                passed += 1
                table.add_row(name, "[green]PASSED[/green]", "")
            else:
                failed += 1
                table.add_row(name, "[red]FAILED[/red]", details or "")
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print(
            f"\n[bold]Total: {len(self.results)} | "
            f"[green]Passed: {passed}[/green] | "
            f"[red]Failed: {failed}[/red][/bold]"
        )


# Documentation Generator
class DocumentationGenerator:
    """Generate comprehensive documentation"""
    
    def __init__(self):
        self.console = Console()
        self.output_dir = Path("docs/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_all(self):
        """Generate all documentation"""
        self.console.print("[bold cyan]Generating NEXUS Documentation[/bold cyan]\n")
        
        docs = [
            ("README.md", self._generate_readme()),
            ("INSTALLATION.md", self._generate_installation()),
            ("CONFIGURATION.md", self._generate_configuration()),
            ("API_REFERENCE.md", self._generate_api_reference()),
            ("CLI_GUIDE.md", self._generate_cli_guide()),
            ("DEPLOYMENT.md", self._generate_deployment()),
            ("TROUBLESHOOTING.md", self._generate_troubleshooting()),
            ("ARCHITECTURE.md", self._generate_architecture())
        ]
        
        for filename, content in track(docs, description="Generating docs"):
            filepath = self.output_dir / filename
            filepath.write_text(content)
            self.console.print(f"[green]✓[/green] Generated {filename}")
    
    def _generate_readme(self) -> str:
        return """# NEXUS Mind Repository

## Overview

NEXUS is an advanced AI-powered development platform that provides:

- **Unified Integration Core**: Service mesh, API gateway, and state management
- **Natural Language CLI**: Control everything with natural language or structured commands
- **Production-Ready**: Auto-updates, monitoring, security, and scalability built-in
- **Extensible**: Plugin system for custom functionality
- **Self-Improving**: Learns and optimizes from usage patterns

## Quick Start

```bash
# Check system requirements
nexus check

# Run setup wizard
nexus setup

# Start NEXUS
nexus start
```

## Features

### Core Integration
- Service discovery (Consul/etcd)
- Message bus (ZMQ/RabbitMQ/Kafka)
- State management (Redis/etcd)
- API Gateway (REST/GraphQL/WebSocket)
- Distributed transactions

### Production Features
- Single binary deployment
- Auto-update system
- Backup and restore
- Crash recovery
- Performance monitoring

### Development Tools
- Project generation
- Code analysis
- Security scanning
- Performance profiling
- Documentation generation

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Configuration Reference](CONFIGURATION.md)
- [API Reference](API_REFERENCE.md)
- [CLI Guide](CLI_GUIDE.md)
- [Deployment Guide](DEPLOYMENT.md)

## License

MIT License - see LICENSE file for details.
"""
    
    def _generate_installation(self) -> str:
        return """# Installation Guide

## System Requirements

### Minimum Requirements
- Python 3.9+
- 4GB RAM
- 10GB free disk space
- Linux/macOS/Windows

### External Dependencies
- Redis (required for state management)
- Consul or etcd (required for service discovery)
- Docker (optional, for containerized deployment)

## Installation Methods

### 1. Binary Installation (Recommended)

Download the latest release for your platform:

```bash
# Linux
wget https://github.com/nexus/releases/latest/download/nexus-linux-amd64.tar.gz
tar -xzf nexus-linux-amd64.tar.gz
sudo mv nexus /usr/local/bin/

# macOS
wget https://github.com/nexus/releases/latest/download/nexus-darwin-amd64.tar.gz
tar -xzf nexus-darwin-amd64.tar.gz
sudo mv nexus /usr/local/bin/

# Windows
# Download nexus-windows-amd64.zip and extract
# Add to PATH
```

### 2. From Source

```bash
# Clone repository
git clone https://github.com/nexus/nexus-mind-repository.git
cd nexus-mind-repository

# Install dependencies
pip install -r requirements.txt

# Build binary
python nexus_launcher_production.py build --output-dir dist
```

### 3. Docker Installation

```bash
docker pull nexus/nexus:latest
docker run -d -p 8080:8080 -p 9090:9090 nexus/nexus:latest
```

## Post-Installation

### 1. Run Setup Wizard

```bash
nexus setup
```

This will guide you through:
- API configuration
- Service discovery setup
- State management setup
- Security configuration
- Feature selection

### 2. Verify Installation

```bash
nexus check
```

### 3. Start Services

```bash
# Start Redis
redis-server

# Start Consul
consul agent -dev

# Start NEXUS
nexus start
```

## Troubleshooting

See [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues.
"""
    
    def _generate_configuration(self) -> str:
        return """# Configuration Reference

## Configuration File

NEXUS uses YAML configuration stored at `~/.nexus/nexus_production_config.yaml`.

## Configuration Sections

### Core Configuration

```yaml
nexus:
  core:
    workers: auto  # Number of worker processes
    max_memory: 16GB  # Maximum memory usage
    log_level: info  # Log level: debug, info, warning, error
```

### API Configuration

```yaml
nexus:
  api:
    host: 0.0.0.0
    port: 8080
    base_path: /api/v1
```

### Service Discovery

```yaml
nexus:
  service_discovery:
    backend: consul  # consul, etcd, or memory
    host: localhost
    port: 8500
```

### State Management

```yaml
nexus:
  state:
    backend: redis  # redis, etcd, or memory
    url: redis://localhost:6379
```

### Security

```yaml
nexus:
  security:
    auth_required: true
    encryption: aes256
    tls_version: "1.3"
```

### Monitoring

```yaml
nexus:
  monitoring:
    metrics:
      enabled: true
      port: 9090
    tracing:
      enabled: true
      endpoint: localhost:4317
```

## Environment Variables

NEXUS supports environment variable substitution:

```yaml
database:
  password: ${DB_PASSWORD}
```

## Advanced Configuration

See the complete [nexus_production_config.yaml](../nexus_production_config.yaml) for all options.
"""
    
    def _generate_api_reference(self) -> str:
        return """# API Reference

## REST API

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "services": 5
}
```

### Service Discovery

#### List Services

```http
GET /services
```

#### Register Service

```http
POST /services/register
Content-Type: application/json

{
  "name": "my-service",
  "version": "1.0.0",
  "host": "localhost",
  "port": 8081,
  "capabilities": ["api", "worker"]
}
```

### State Management

#### Get State

```http
GET /state/{key}
```

#### Set State

```http
PUT /state/{key}
Content-Type: application/json

{
  "value": {"counter": 42},
  "expected_version": 1
}
```

### Message Bus

#### Publish Event

```http
POST /events/{topic}
Content-Type: application/json

{
  "payload": {"message": "Hello"},
  "priority": 1
}
```

## GraphQL API

Endpoint: `/graphql`

### Queries

```graphql
query ListServices {
  services {
    id
    name
    status
    capabilities
  }
}

query GetState($key: String!) {
  state(key: $key) {
    key
    value
    version
  }
}
```

### Mutations

```graphql
mutation PublishEvent($topic: String!, $payload: String!) {
  publishEvent(topic: $topic, payload: $payload) {
    success
    messageId
  }
}
```

## WebSocket API

Endpoint: `ws://localhost:8080/ws`

### Subscribe to Topic

```json
{
  "type": "subscribe",
  "topic": "system.events"
}
```

### Publish Message

```json
{
  "type": "publish",
  "topic": "system.events",
  "payload": {"event": "test"}
}
```

## Authentication

Include JWT token in Authorization header:

```http
Authorization: Bearer <token>
```
"""
    
    def _generate_cli_guide(self) -> str:
        return """# CLI Guide

## Overview

NEXUS CLI supports both structured commands and natural language.

## Basic Commands

### Service Management

```bash
# List services
nexus service list

# Start a service
nexus service start api-gateway

# Check service status
nexus service status

# Natural language
nexus "start the API gateway service"
```

### Project Management

```bash
# Create new project
nexus project init myapp

# List projects
nexus project list

# Build project
nexus project build myapp

# Natural language
nexus "create a new web application called myapp"
```

### System Commands

```bash
# Check system status
nexus status

# View logs
nexus logs --tail 100

# Backup system
nexus backup create

# Natural language
nexus "show me the system status"
```

## Advanced Features

### Script Execution

```bash
# Execute script file
nexus --script deploy.nexus

# Execute batch commands
nexus --batch commands.txt
```

### Remote Execution

```bash
# Execute on remote NEXUS instance
nexus --remote nexus.example.com --token <token> service list
```

### Interactive Mode

```bash
# Start interactive CLI
nexus

nexus> service list
nexus> help
nexus> exit
```

## Script Syntax

NEXUS scripts support variables and control flow:

```bash
# deploy.nexus
SERVICE_NAME=api-gateway
VERSION=`nexus project version`

nexus service stop ${SERVICE_NAME}
nexus service deploy ${SERVICE_NAME} --version ${VERSION}
nexus service start ${SERVICE_NAME}
```

## Plugins

Install CLI plugins:

```bash
nexus plugin install nexus-k8s-cli
nexus k8s:deploy myapp
```
"""
    
    def _generate_deployment(self) -> str:
        return """# Deployment Guide

## Deployment Options

### 1. Standalone Binary

```bash
# Download and run
./nexus start
```

### 2. Docker

```yaml
# docker-compose.yml
version: '3.8'
services:
  nexus:
    image: nexus/nexus:latest
    ports:
      - "8080:8080"
      - "9090:9090"
    environment:
      - REDIS_URL=redis://redis:6379
      - CONSUL_HOST=consul
    depends_on:
      - redis
      - consul
      
  redis:
    image: redis:alpine
    
  consul:
    image: consul:latest
    command: agent -dev -client=0.0.0.0
```

### 3. Kubernetes

```yaml
# nexus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexus-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nexus
  template:
    metadata:
      labels:
        app: nexus
    spec:
      containers:
      - name: nexus
        image: nexus/nexus:latest
        ports:
        - containerPort: 8080
        - containerPort: 9090
        env:
        - name: NEXUS_MODE
          value: production
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "4"
```

## Production Checklist

- [ ] Configure TLS certificates
- [ ] Set strong JWT secret
- [ ] Enable authentication
- [ ] Configure monitoring endpoints
- [ ] Setup backup schedule
- [ ] Configure auto-scaling
- [ ] Enable health checks
- [ ] Setup log aggregation
- [ ] Configure alerts

## Scaling

### Horizontal Scaling

```yaml
# Enable auto-scaling
nexus:
  deployment:
    auto_scaling:
      enabled: true
      min_instances: 2
      max_instances: 10
      target_cpu: 70
```

### Load Balancing

Use any standard load balancer (nginx, HAProxy, cloud LB) with health checks:

```nginx
upstream nexus {
    server nexus1:8080 max_fails=3 fail_timeout=30s;
    server nexus2:8080 max_fails=3 fail_timeout=30s;
    server nexus3:8080 max_fails=3 fail_timeout=30s;
}
```

## Monitoring

### Prometheus Metrics

Available at `http://localhost:9090/metrics`

### Grafana Dashboard

Import dashboard ID: 12345

### Alerts

Configure alerts for:
- High CPU/memory usage
- Service failures
- API errors
- Slow response times
"""
    
    def _generate_troubleshooting(self) -> str:
        return """# Troubleshooting Guide

## Common Issues

### NEXUS Won't Start

1. Check system requirements:
   ```bash
   nexus check
   ```

2. Check if ports are in use:
   ```bash
   lsof -i :8080
   lsof -i :9090
   ```

3. Check logs:
   ```bash
   tail -f ~/.nexus/logs/nexus.log
   ```

### Service Discovery Not Working

1. Verify Consul/etcd is running:
   ```bash
   consul members  # For Consul
   etcdctl member list  # For etcd
   ```

2. Check configuration:
   ```bash
   nexus config get service_discovery
   ```

### State Management Issues

1. Verify Redis connection:
   ```bash
   redis-cli ping
   ```

2. Check Redis memory:
   ```bash
   redis-cli info memory
   ```

### Performance Issues

1. Check resource usage:
   ```bash
   nexus status --detailed
   ```

2. Review metrics:
   ```bash
   curl http://localhost:9090/metrics | grep nexus_
   ```

### Authentication Failures

1. Verify JWT secret is set
2. Check token expiration
3. Ensure clock synchronization

## Debug Mode

Enable debug logging:

```bash
nexus start --log-level debug
```

## Crash Recovery

If NEXUS crashes:

1. Check crash reports:
   ```bash
   ls ~/.nexus/crashes/
   ```

2. Restore from backup:
   ```bash
   nexus restore --backup-name latest
   ```

3. Start in safe mode:
   ```bash
   nexus start --safe-mode
   ```

## Getting Help

- Documentation: https://nexus.dev/docs
- Community: https://discord.gg/nexus
- Issues: https://github.com/nexus/issues
- Support: support@nexus.dev
"""
    
    def _generate_architecture(self) -> str:
        return """# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NEXUS Core                           │
├─────────────────┬─────────────────┬───────────────────────┤
│   API Gateway   │  Message Bus    │   State Store         │
│  (REST/GraphQL) │  (ZMQ/RabbitMQ) │  (Redis/etcd)        │
├─────────────────┴─────────────────┴───────────────────────┤
│                   Service Registry                          │
│                  (Consul/etcd)                             │
├─────────────────────────────────────────────────────────────┤
│                    Plugin System                            │
├─────────────────────────────────────────────────────────────┤
│   Monitoring    │   Security      │   Transactions        │
│ (Metrics/Trace) │  (Auth/Crypto)  │   (2PC/Saga)         │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Integration Core
- Event-driven architecture
- Microservices communication
- Service mesh capabilities
- API federation

### Service Registry
- Dynamic service discovery
- Health checking
- Load balancing
- Circuit breaking

### Message Bus
- Pub/sub messaging
- Request/reply patterns
- Event sourcing
- CQRS support

### State Management
- Distributed state
- Conflict resolution
- Event store
- Caching layer

## Data Flow

1. **Request Flow**:
   Client → API Gateway → Service Registry → Service → Response

2. **Event Flow**:
   Service → Message Bus → Subscribers → State Store

3. **Transaction Flow**:
   Coordinator → Prepare → Vote → Commit/Abort

## Deployment Architecture

### Single Node
- All components in one process
- Suitable for development
- Memory-based backends

### Multi-Node
- Distributed components
- External Redis/Consul
- Load balanced API

### Cloud Native
- Kubernetes deployment
- Auto-scaling
- Service mesh integration
- Cloud storage backends
"""


async def main():
    """Main test and documentation runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS Production Testing")
    parser.add_argument(
        'command',
        choices=['test', 'docs', 'all'],
        help='Command to run'
    )
    parser.add_argument('--api-url', default='http://localhost:8080')
    
    args = parser.parse_args()
    
    if args.command in ['test', 'all']:
        tester = IntegrationTester(args.api_url)
        await tester.run_all_tests()
    
    if args.command in ['docs', 'all']:
        generator = DocumentationGenerator()
        await generator.generate_all()


if __name__ == '__main__':
    asyncio.run(main())