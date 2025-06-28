#!/bin/bash
# NEXUS V5 Ultimate - Simplified Startup Script
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
                                                                  
🧬 Quantum Consciousness Level: 100% | Mobile Optimization: ACTIVE
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
PROJECT_ROOT="$(cd "$NEXUS_DIR/../.." && pwd)"

# Start core services only
start_core_services() {
    log_nexus "Starting NEXUS V5 Ultimate core services..."
    
    cd "$NEXUS_DIR"
    
    log_info "Starting infrastructure services (Redis & PostgreSQL)..."
    docker-compose up -d nexus-redis nexus-postgres
    
    log_info "Waiting for infrastructure to be ready..."
    sleep 15
    
    log_info "Starting LiveKit server..."
    docker-compose up -d nexus-livekit
    
    log_info "Starting monitoring services..."
    docker-compose up -d nexus-prometheus nexus-grafana
    
    log_info "Starting reverse proxy..."
    docker-compose up -d nexus-nginx
    
    log_success "Core NEXUS services started successfully!"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    services=(
        "nexus-redis"
        "nexus-postgres"
        "nexus-livekit"
        "nexus-prometheus"
        "nexus-grafana"
        "nexus-nginx"
    )
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_warning "$service is not running properly"
        fi
    done
}

# Display access information
display_access_info() {
    log_nexus "NEXUS V5 Ultimate core services are now running!"
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
    echo -e "${PURPLE}🧬 Consciousness Level: 100% | Core Services: ACTIVE${NC}"
    echo ""
    echo -e "${BLUE}To stop services: ${NC}docker-compose down"
    echo -e "${BLUE}To view logs: ${NC}docker-compose logs -f [service-name]"
    echo -e "${BLUE}To add more services: ${NC}Edit docker-compose.yml and restart"
}

# Main execution
main() {
    log_nexus "Initializing NEXUS V5 Ultimate core deployment..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    start_core_services
    
    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep 20
    
    check_health
    display_access_info
    
    log_nexus "NEXUS V5 Ultimate core deployment complete! 🧬"
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