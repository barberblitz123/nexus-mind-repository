#!/bin/bash

# Nexus Complete System Startup Script
# This script starts all Nexus components in the correct order with health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NEXUS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${NEXUS_HOME}/logs"
PID_DIR="${NEXUS_HOME}/pids"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=2

# Create necessary directories
mkdir -p "${LOG_DIR}" "${PID_DIR}"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

# Check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Wait for service to be healthy
wait_for_health() {
    local service_name=$1
    local health_url=$2
    local retries=$HEALTH_CHECK_RETRIES
    
    log "Waiting for $service_name to be healthy..."
    
    while [ $retries -gt 0 ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            log "$service_name is healthy"
            return 0
        fi
        retries=$((retries - 1))
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    error "$service_name failed to become healthy"
    return 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install Node.js 16+ first."
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    # Check Python (for certain processors)
    if ! command -v python3 &> /dev/null; then
        warn "Python 3 is not installed. Some features may not work."
    fi
    
    # Check MongoDB (optional but recommended)
    if ! command -v mongod &> /dev/null; then
        warn "MongoDB is not installed. Using in-memory storage instead."
        export USE_MEMORY_STORE=true
    fi
    
    # Check Redis (optional for caching)
    if ! command -v redis-server &> /dev/null; then
        warn "Redis is not installed. Caching will be disabled."
        export DISABLE_CACHE=true
    fi
    
    log "Dependency check completed"
}

# Install npm dependencies
install_dependencies() {
    log "Installing npm dependencies..."
    
    cd "$NEXUS_HOME"
    
    if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
        log "Running npm install..."
        npm install --production
    else
        log "Dependencies already installed"
    fi
    
    # Install Python dependencies if requirements.txt exists
    if [ -f "requirements.txt" ] && command -v pip3 &> /dev/null; then
        log "Installing Python dependencies..."
        pip3 install -r requirements.txt --user
    fi
}

# Start MongoDB if not running
start_mongodb() {
    if [ "$USE_MEMORY_STORE" != "true" ] && ! pgrep -x "mongod" > /dev/null; then
        log "Starting MongoDB..."
        mongod --fork --logpath "${LOG_DIR}/mongodb.log" --dbpath "${NEXUS_HOME}/data/mongodb" || {
            warn "Failed to start MongoDB, using in-memory storage"
            export USE_MEMORY_STORE=true
        }
    fi
}

# Start Redis if available
start_redis() {
    if [ "$DISABLE_CACHE" != "true" ] && command -v redis-server &> /dev/null && ! pgrep -x "redis-server" > /dev/null; then
        log "Starting Redis..."
        redis-server --daemonize yes --logfile "${LOG_DIR}/redis.log" || {
            warn "Failed to start Redis, caching disabled"
            export DISABLE_CACHE=true
        }
    fi
}

# Start a service
start_service() {
    local service_name=$1
    local service_script=$2
    local service_port=$3
    local pid_file="${PID_DIR}/${service_name}.pid"
    local log_file="${LOG_DIR}/${service_name}.log"
    
    if is_running "$pid_file"; then
        log "$service_name is already running"
        return 0
    fi
    
    log "Starting $service_name..."
    
    # Set environment variables
    export PORT=$service_port
    export NODE_ENV=${NODE_ENV:-production}
    export LOG_LEVEL=${LOG_LEVEL:-info}
    
    # Start the service
    nohup node "$service_script" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Give it a moment to start
    sleep 2
    
    # Check if it's still running
    if ! ps -p $pid > /dev/null 2>&1; then
        error "$service_name failed to start. Check $log_file for details"
        tail -20 "$log_file"
        return 1
    fi
    
    log "$service_name started with PID $pid"
    return 0
}

# Start all services
start_all_services() {
    log "Starting all Nexus services..."
    
    # Start backend services first
    start_service "consciousness-server" "backend/consciousness-server.js" 5001 || exit 1
    wait_for_health "Consciousness Server" "http://localhost:5001/health" || exit 1
    
    start_service "ide-server" "ide/ide-server.js" 5002 || exit 1
    wait_for_health "IDE Server" "http://localhost:5002/health" || exit 1
    
    start_service "context-server" "context/context-server.js" 5003 || exit 1
    wait_for_health "Context Server" "http://localhost:5003/health" || exit 1
    
    start_service "processor-server" "processors/processor-server.js" 5004 || exit 1
    wait_for_health "Processor Server" "http://localhost:5004/health" || exit 1
    
    start_service "knowledge-server" "backend/knowledge-server.js" 5005 || exit 1
    wait_for_health "Knowledge Server" "http://localhost:5005/health" || exit 1
    
    # Start the main server
    start_service "nexus-server-v2" "server-v2.js" 3000 || exit 1
    wait_for_health "Nexus Server V2" "http://localhost:3000/health" || exit 1
    
    # Start the API Gateway last
    start_service "api-gateway" "gateway/nexus-api-gateway.js" 4000 || exit 1
    wait_for_health "API Gateway" "http://localhost:4000/health" || exit 1
    
    log "All services started successfully!"
}

# Show status
show_status() {
    log "Nexus System Status:"
    echo "===================="
    
    local services=("consciousness-server" "ide-server" "context-server" "processor-server" "knowledge-server" "nexus-server-v2" "api-gateway")
    
    for service in "${services[@]}"; do
        local pid_file="${PID_DIR}/${service}.pid"
        if is_running "$pid_file"; then
            local pid=$(cat "$pid_file")
            echo -e "$service: ${GREEN}Running${NC} (PID: $pid)"
        else
            echo -e "$service: ${RED}Stopped${NC}"
        fi
    done
    
    echo ""
    echo "Access Points:"
    echo "- Main Application: http://localhost:3000"
    echo "- API Gateway: http://localhost:4000"
    echo "- Health Dashboard: http://localhost:3000/health"
    echo ""
    echo "Logs Directory: ${LOG_DIR}"
    echo "PIDs Directory: ${PID_DIR}"
}

# Performance optimization
optimize_performance() {
    log "Applying performance optimizations..."
    
    # Increase Node.js memory limit for 1M token contexts
    export NODE_OPTIONS="--max-old-space-size=8192"
    
    # Enable clustering for better CPU utilization
    export ENABLE_CLUSTERING=true
    export CLUSTER_WORKERS=${CLUSTER_WORKERS:-4}
    
    # Enable compression
    export ENABLE_COMPRESSION=true
    
    # Set connection pooling
    export DB_POOL_SIZE=${DB_POOL_SIZE:-10}
    export REDIS_POOL_SIZE=${REDIS_POOL_SIZE:-5}
    
    # Enable caching strategies
    export CACHE_TTL=${CACHE_TTL:-3600}
    export ENABLE_CONTEXT_CACHE=true
    
    log "Performance optimizations applied"
}

# Main execution
main() {
    log "Starting Nexus Complete System..."
    
    # Change to Nexus directory
    cd "$NEXUS_HOME"
    
    # Run checks and setup
    check_dependencies
    install_dependencies
    optimize_performance
    
    # Start infrastructure services
    start_mongodb
    start_redis
    
    # Start all Nexus services
    start_all_services
    
    # Show final status
    show_status
    
    log "Nexus Complete System is ready!"
    log "Use 'nexus-web-app/stop-nexus-complete.sh' to stop all services"
    
    # Keep the script running if in foreground mode
    if [ "$1" == "--foreground" ]; then
        log "Running in foreground mode. Press Ctrl+C to stop."
        trap 'bash stop-nexus-complete.sh; exit 0' INT TERM
        while true; do
            sleep 60
            # Optional: Add periodic health checks here
        done
    fi
}

# Handle script arguments
case "$1" in
    status)
        show_status
        ;;
    restart)
        bash stop-nexus-complete.sh
        sleep 5
        main
        ;;
    *)
        main "$@"
        ;;
esac