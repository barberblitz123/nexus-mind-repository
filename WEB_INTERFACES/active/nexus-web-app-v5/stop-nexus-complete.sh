#!/bin/bash

# Nexus Complete System Shutdown Script
# This script gracefully stops all Nexus components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NEXUS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${NEXUS_HOME}/pids"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

# Stop a service
stop_service() {
    local service_name=$1
    local pid_file="${PID_DIR}/${service_name}.pid"
    
    if [ ! -f "$pid_file" ]; then
        log "$service_name is not running"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        log "$service_name is not running (stale PID file)"
        rm -f "$pid_file"
        return 0
    fi
    
    log "Stopping $service_name (PID: $pid)..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for process to stop (max 30 seconds)
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        log "Force stopping $service_name..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$pid_file"
    log "$service_name stopped"
}

# Main execution
main() {
    log "Stopping Nexus Complete System..."
    
    # Stop services in reverse order
    stop_service "api-gateway"
    stop_service "nexus-server-v2"
    stop_service "knowledge-server"
    stop_service "processor-server"
    stop_service "context-server"
    stop_service "ide-server"
    stop_service "consciousness-server"
    
    log "All Nexus services stopped"
}

main "$@"