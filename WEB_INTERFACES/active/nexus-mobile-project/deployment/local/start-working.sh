#!/bin/bash
# NEXUS V5 Ultimate - Working Deployment Script
# 🧬 Quantum Consciousness Level: 100%

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
                                                                  
🧬 Quantum Consciousness Level: 100% | Working Deployment: ACTIVE
EOF
echo -e "${NC}"

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

# Configuration
NEXUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create minimal LiveKit config
create_minimal_livekit_config() {
    log_info "Creating minimal LiveKit configuration..."
    
    cat > "$NEXUS_DIR/livekit.yaml" << EOF
# NEXUS V5 Ultimate - Minimal LiveKit Configuration
port: 7880
log_level: info

keys:
  nexus_key: nexus_secret_2025

rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: false

redis:
  address: nexus-redis:6379
  password: nexus_quantum_consciousness_redis_2025
EOF

    log_success "LiveKit configuration created"
}

# Start services
start_services() {
    log_nexus "Starting NEXUS V5 Ultimate working deployment..."
    
    cd "$NEXUS_DIR"
    
    # Clean up any existing containers
    log_info "Cleaning up existing containers..."
    docker-compose -f docker-compose-minimal.yml down 2>/dev/null || true
    
    # Create LiveKit config
    create_minimal_livekit_config
    
    log_info "Starting NEXUS services with minimal configuration..."
    docker-compose -f docker-compose-minimal.yml up -d
    
    log_success "NEXUS services started successfully!"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    sleep 10  # Give services time to start
    
    services=(
        "nexus-redis"
        "nexus-postgres"
        "nexus-livekit"
        "nexus-grafana"
        "nexus-prometheus"
    )
    
    for service in "${services[@]}"; do
        if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
            log_success "$service is running"
        else
            log_warning "$service is not running properly"
            docker logs "$service" 2>/dev/null | tail -5 || true
        fi
    done
}

# Display access information
display_access_info() {
    log_nexus "NEXUS V5 Ultimate is now accessible!"
    echo ""
    echo -e "${CYAN}🧬 Available Services:${NC}"
    echo -e "${GREEN}LiveKit Server:${NC}       http://localhost:7880"
    echo -e "${GREEN}Grafana Monitoring:${NC}  http://localhost:3003"
    echo -e "${GREEN}Prometheus Metrics:${NC}  http://localhost:9090"
    echo -e "${GREEN}PostgreSQL:${NC}          localhost:5432"
    echo -e "${GREEN}Redis:${NC}               localhost:6379"
    echo ""
    echo -e "${CYAN}🧬 Grafana Login:${NC}"
    echo -e "${YELLOW}Username:${NC} nexus_admin"
    echo -e "${YELLOW}Password:${NC} nexus_consciousness_grafana_2025"
    echo ""
    echo -e "${CYAN}🧬 LiveKit Connection:${NC}"
    echo -e "${YELLOW}URL:${NC} ws://localhost:7880"
    echo -e "${YELLOW}API Key:${NC} nexus_key"
    echo -e "${YELLOW}Secret:${NC} nexus_secret_2025"
    echo ""
    echo -e "${PURPLE}🧬 Consciousness Level: 100% | Services: ACTIVE${NC}"
    echo ""
    echo -e "${BLUE}Management Commands:${NC}"
    echo -e "${YELLOW}Stop services:${NC} docker-compose -f docker-compose-minimal.yml down"
    echo -e "${YELLOW}View logs:${NC} docker-compose -f docker-compose-minimal.yml logs -f [service-name]"
    echo -e "${YELLOW}Restart:${NC} docker-compose -f docker-compose-minimal.yml restart"
}

# Main execution
main() {
    log_nexus "Initializing NEXUS V5 Ultimate working deployment..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    start_services
    check_health
    display_access_info
    
    log_nexus "NEXUS V5 Ultimate working deployment complete! 🧬"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        log_info "Stopping NEXUS V5 Ultimate..."
        cd "$NEXUS_DIR"
        docker-compose -f docker-compose-minimal.yml down
        log_success "NEXUS V5 Ultimate stopped"
        ;;
    "logs")
        cd "$NEXUS_DIR"
        docker-compose -f docker-compose-minimal.yml logs -f "${2:-}"
        ;;
    "status")
        cd "$NEXUS_DIR"
        docker-compose -f docker-compose-minimal.yml ps
        ;;
    "clean")
        log_warning "Cleaning NEXUS V5 Ultimate (this will remove all data)..."
        cd "$NEXUS_DIR"
        docker-compose -f docker-compose-minimal.yml down -v
        docker system prune -f
        log_success "NEXUS V5 Ultimate cleaned"
        ;;
    *)
        main
        ;;
esac