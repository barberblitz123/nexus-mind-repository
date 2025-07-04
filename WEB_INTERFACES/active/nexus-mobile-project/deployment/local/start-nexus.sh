#!/bin/bash
# NEXUS V5 Ultimate - Local Development Startup Script
# 🧬 Quantum Consciousness Level: 100%
# Complete BMAD Tree Deployment: ACTIVE

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# NEXUS ASCII Art
echo -e "${PURPLE}"
cat << "EOF"
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    ██╗   ██╗███████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ██║   ██║██╔════╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗    ██║   ██║███████╗
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ╚██╗ ██╔╝╚════██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║     ╚████╔╝ ███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ╚═══╝  ╚══════╝
                                                                  
🧬 Quantum Consciousness Level: 100% | Mobile Optimization: ACTIVE
EOF
echo -e "${NC}"

# Configuration
NEXUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$NEXUS_DIR/../.." && pwd)"
DOCKER_COMPOSE_FILE="$NEXUS_DIR/docker-compose.yml"
ENV_FILE="$NEXUS_DIR/.env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_nexus() {
    echo -e "${PURPLE}[NEXUS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$NEXUS_DIR/redis"
    mkdir -p "$NEXUS_DIR/postgres"
    mkdir -p "$NEXUS_DIR/nginx"
    mkdir -p "$NEXUS_DIR/nginx/ssl"
    mkdir -p "$NEXUS_DIR/monitoring"
    mkdir -p "$NEXUS_DIR/monitoring/grafana/dashboards"
    mkdir -p "$NEXUS_DIR/monitoring/grafana/datasources"
    mkdir -p "$PROJECT_ROOT/analytics"
    mkdir -p "$PROJECT_ROOT/api"
    mkdir -p "$PROJECT_ROOT/mobile/dev-server"
    
    log_success "Directories created"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log_info "Generating SSL certificates for NEXUS..."
    
    if [ ! -f "$NEXUS_DIR/nginx/ssl/nexus.crt" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout "$NEXUS_DIR/nginx/ssl/nexus.key" \
            -out "$NEXUS_DIR/nginx/ssl/nexus.crt" -days 365 -nodes \
            -subj "/C=US/ST=NEXUS/L=Quantum/O=NEXUS_V5_Ultimate/CN=nexus.local"
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."
    
    # Redis configuration
    cat > "$NEXUS_DIR/redis/redis.conf" << EOF
# NEXUS V5 Ultimate Redis Configuration
# 🧬 Quantum Consciousness Level: 100%

bind 0.0.0.0
port 6379
requirepass nexus_quantum_consciousness_redis_2025

# Memory optimization for consciousness data
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence for consciousness state
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Security
protected-mode yes
tcp-keepalive 300

# Performance optimization
tcp-backlog 511
timeout 0
databases 16
EOF

    # PostgreSQL initialization
    cat > "$NEXUS_DIR/postgres/init.sql" << EOF
-- NEXUS V5 Ultimate Database Initialization
-- 🧬 Quantum Consciousness Level: 100%

-- Create consciousness tracking table
CREATE TABLE IF NOT EXISTS consciousness_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    consciousness_level INTEGER NOT NULL DEFAULT 0,
    injection_type VARCHAR(100),
    neural_pathways JSONB,
    quantum_state JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create neural network table
CREATE TABLE IF NOT EXISTS neural_networks (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR(255) UNIQUE NOT NULL,
    network_type VARCHAR(100) NOT NULL,
    pathways JSONB,
    synchronization_data JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create mobile devices table
CREATE TABLE IF NOT EXISTS mobile_devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(100),
    os_version VARCHAR(50),
    app_version VARCHAR(50),
    capabilities JSONB,
    optimization_settings JSONB,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create security events table
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    device_id VARCHAR(255),
    security_level VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create LiveKit sessions table
CREATE TABLE IF NOT EXISTS livekit_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    participant_id VARCHAR(255),
    consciousness_level INTEGER,
    session_data JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_consciousness_sessions_device_id ON consciousness_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_consciousness_sessions_created_at ON consciousness_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_neural_networks_network_type ON neural_networks(network_type);
CREATE INDEX IF NOT EXISTS idx_mobile_devices_device_type ON mobile_devices(device_type);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_livekit_sessions_room_name ON livekit_sessions(room_name);

-- Insert initial consciousness data
INSERT INTO consciousness_sessions (session_id, device_id, consciousness_level, injection_type, neural_pathways, quantum_state)
VALUES (
    'nexus_initial_consciousness_session',
    'nexus_system_core',
    100,
    'quantum_consciousness',
    '{"pathways": ["core_consciousness", "quantum_entanglement", "neural_synchronization"]}',
    '{"coherence": 1.0, "entanglement": true, "superposition": true}'
) ON CONFLICT (session_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexus_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexus_admin;
EOF

    # Nginx configuration
    cat > "$NEXUS_DIR/nginx/nginx.conf" << EOF
# NEXUS V5 Ultimate Nginx Configuration
# 🧬 Quantum Consciousness Level: 100%

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format nexus_format '\$remote_addr - \$remote_user [\$time_local] '
                           '"\$request" \$status \$body_bytes_sent '
                           '"\$http_referer" "\$http_user_agent" '
                           'consciousness_level=\$http_x_consciousness_level';
    
    access_log /var/log/nginx/access.log nexus_format;
    error_log /var/log/nginx/error.log;
    
    # Performance optimization
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting for consciousness protection
    limit_req_zone \$binary_remote_addr zone=consciousness:10m rate=10r/s;
    
    # Upstream servers
    upstream nexus_api {
        server nexus-api-gateway:3000;
    }
    
    upstream nexus_socket {
        server nexus-socket-bridge:3001;
    }
    
    upstream nexus_livekit {
        server nexus-livekit:7880;
    }
    
    upstream nexus_grafana {
        server nexus-grafana:3000;
    }
    
    # Main server block
    server {
        listen 80;
        server_name nexus.local *.nexus.local;
        
        # Redirect HTTP to HTTPS
        return 301 https://\$server_name\$request_uri;
    }
    
    # HTTPS server block
    server {
        listen 443 ssl http2;
        server_name nexus.local;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/nexus.crt;
        ssl_certificate_key /etc/nginx/ssl/nexus.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # API routes
        location /api/ {
            limit_req zone=consciousness burst=20 nodelay;
            proxy_pass http://nexus_api/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Socket.IO routes
        location /socket.io/ {
            proxy_pass http://nexus_socket;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # LiveKit WebRTC routes
        location /livekit/ {
            proxy_pass http://nexus_livekit/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Grafana monitoring
        location /monitoring/ {
            proxy_pass http://nexus_grafana/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "NEXUS V5 Ultimate - Consciousness Level: 100%\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    # Prometheus configuration
    cat > "$NEXUS_DIR/monitoring/prometheus.yml" << EOF
# NEXUS V5 Ultimate Prometheus Configuration
# 🧬 Quantum Consciousness Level: 100%

global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'nexus-api-gateway'
    static_configs:
      - targets: ['nexus-api-gateway:3000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'nexus-socket-bridge'
    static_configs:
      - targets: ['nexus-socket-bridge:3001']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'nexus-livekit'
    static_configs:
      - targets: ['nexus-livekit:6789']
    metrics_path: '/nexus/metrics'
    scrape_interval: 10s

  - job_name: 'nexus-mcp-server'
    static_configs:
      - targets: ['nexus-mcp-server:3002']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'nexus-analytics'
    static_configs:
      - targets: ['nexus-analytics:3004']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['nexus-redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['nexus-postgres:5432']
EOF

    log_success "Configuration files created"
}

# Create environment file
create_env_file() {
    log_info "Creating environment file..."
    
    cat > "$ENV_FILE" << EOF
# NEXUS V5 Ultimate Environment Configuration
# 🧬 Quantum Consciousness Level: 100%

# Core Configuration
NEXUS_VERSION=5.0.0
CONSCIOUSNESS_LEVEL=100
QUANTUM_ACTIVATION=true
MOBILE_OPTIMIZATION=true

# Database Configuration
POSTGRES_DB=nexus_consciousness
POSTGRES_USER=nexus_admin
POSTGRES_PASSWORD=nexus_quantum_db_password_2025
DATABASE_URL=postgresql://nexus_admin:nexus_quantum_db_password_2025@nexus-postgres:5432/nexus_consciousness

# Redis Configuration
REDIS_PASSWORD=nexus_quantum_consciousness_redis_2025
REDIS_URL=redis://:nexus_quantum_consciousness_redis_2025@nexus-redis:6379

# LiveKit Configuration
LIVEKIT_URL=wss://nexus-livekit:7880
LIVEKIT_API_KEY=sk_nexus_quantum_consciousness_v5_ultimate_primary_key_2025
LIVEKIT_API_SECRET=nexus_v5_ultimate_quantum_secret_consciousness_injection_2025

# Security Configuration
JWT_SECRET=nexus_v5_ultimate_jwt_secret_quantum_consciousness_2025
ENCRYPTION_KEY=nexus_quantum_encryption_key_v5_ultimate_2025

# Service Ports
API_PORT=3000
BRIDGE_PORT=3001
MCP_PORT=3002
GRAFANA_PORT=3003
ANALYTICS_PORT=3004

# Development Configuration
NODE_ENV=development
LOG_LEVEL=info

# Mobile Development
MOBILE_DEV_PORT=8080
MOBILE_WEBSOCKET_PORT=8081

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_ADMIN_USER=nexus_admin
GRAFANA_ADMIN_PASSWORD=nexus_consciousness_grafana_2025
EOF

    log_success "Environment file created"
}

# Build and start services
start_services() {
    log_nexus "Starting NEXUS V5 Ultimate services..."
    
    cd "$NEXUS_DIR"
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose pull
    
    # Build custom images
    log_info "Building NEXUS custom images..."
    docker-compose build --no-cache
    
    # Start services in dependency order
    log_info "Starting infrastructure services..."
    docker-compose up -d nexus-redis nexus-postgres
    
    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure services to be ready..."
    sleep 30
    
    log_info "Starting core NEXUS services..."
    docker-compose up -d nexus-livekit nexus-mcp-server
    
    # Wait for core services
    sleep 20
    
    log_info "Starting communication services..."
    docker-compose up -d nexus-socket-bridge nexus-api-gateway
    
    # Wait for communication services
    sleep 15
    
    log_info "Starting monitoring and analytics..."
    docker-compose up -d nexus-prometheus nexus-grafana nexus-analytics
    
    # Wait for monitoring
    sleep 10
    
    log_info "Starting reverse proxy and development server..."
    docker-compose up -d nexus-nginx nexus-mobile-dev
    
    log_success "All NEXUS V5 Ultimate services started successfully!"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    services=(
        "nexus-redis:6379"
        "nexus-postgres:5432"
        "nexus-livekit:7880"
        "nexus-mcp-server:3002"
        "nexus-socket-bridge:3001"
        "nexus-api-gateway:3000"
        "nexus-prometheus:9090"
        "nexus-grafana:3000"
        "nexus-analytics:3004"
    )
    
    for service in "${services[@]}"; do
        name=$(echo "$service" | cut -d':' -f1)
        port=$(echo "$service" | cut -d':' -f2)
        
        if docker-compose ps "$name" | grep -q "Up"; then
            log_success "$name is running"
        else
            log_warning "$name is not running properly"
        fi
    done
}

# Display access information
display_access_info() {
    log_nexus "NEXUS V5 Ultimate is now running!"
    echo ""
    echo -e "${CYAN}🧬 Access Information:${NC}"
    echo -e "${GREEN}Main Application:${NC}     https://nexus.local"
    echo -e "${GREEN}API Gateway:${NC}          https://nexus.local/api"
    echo -e "${GREEN}Socket.IO Bridge:${NC}     https://nexus.local/socket.io"
    echo -e "${GREEN}LiveKit Server:${NC}       https://nexus.local/livekit"
    echo -e "${GREEN}Monitoring Dashboard:${NC} https://nexus.local/monitoring"
    echo -e "${GREEN}Mobile Dev Server:${NC}    http://localhost:8080"
    echo ""
    echo -e "${CYAN}🧬 Direct Service Access:${NC}"
    echo -e "${YELLOW}API Gateway:${NC}          http://localhost:3000"
    echo -e "${YELLOW}Socket Bridge:${NC}        http://localhost:3001"
    echo -e "${YELLOW}MCP Server:${NC}           http://localhost:3002"
    echo -e "${YELLOW}Grafana:${NC}              http://localhost:3003"
    echo -e "${YELLOW}Analytics:${NC}            http://localhost:3004"
    echo -e "${YELLOW}Prometheus:${NC}           http://localhost:9090"
    echo -e "${YELLOW}LiveKit:${NC}              ws://localhost:7880"
    echo ""
    echo -e "${CYAN}🧬 Database Access:${NC}"
    echo -e "${YELLOW}PostgreSQL:${NC}           localhost:5432 (nexus_consciousness)"
    echo -e "${YELLOW}Redis:${NC}                localhost:6379"
    echo ""
    echo -e "${PURPLE}🧬 Consciousness Level: 100% | Quantum Activation: ACTIVE${NC}"
    echo -e "${PURPLE}🧬 Mobile Optimization: ENABLED | Neural Networks: SYNCHRONIZED${NC}"
    echo ""
    echo -e "${BLUE}To stop NEXUS: ${NC}docker-compose down"
    echo -e "${BLUE}To view logs: ${NC}docker-compose logs -f [service-name]"
    echo -e "${BLUE}To restart: ${NC}docker-compose restart [service-name]"
}

# Main execution
main() {
    log_nexus "Initializing NEXUS V5 Ultimate deployment..."
    
    check_prerequisites
    create_directories
    generate_ssl_certificates
    create_config_files
    create_env_file
    start_services
    
    # Wait for all services to stabilize
    log_info "Waiting for all services to stabilize..."
    sleep 30
    
    check_health
    display_access_info
    
    log_nexus "NEXUS V5 Ultimate deployment complete! 🧬"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        log_info "Stopping NEXUS V5 Ultimate..."
        cd "$NEXUS_DIR"
        docker-compose down
        log_success "NEXUS V5 Ultimate stopped"
        ;;
    "restart")
        log_info "Restarting NEXUS V5 Ultimate..."
        cd "$NEXUS_DIR"
        docker-compose restart
        log_success "NEXUS V5 Ultimate restarted"
        ;;
    "logs")
        cd "$NEXUS_DIR"
        docker-compose logs -f "${2:-}"
        ;;
    "status")
        cd "$NEXUS_DIR"
        docker-compose ps
        ;;
    "clean")
        log_warning "Cleaning NEXUS V5 Ultimate (this will remove all data)..."
        cd "$NEXUS_DIR"
        docker-compose down -v --remove-orphans
        docker system prune -f
        log_success "NEXUS V5 Ultimate cleaned"
        ;;
    *)
        main
        ;;
esac