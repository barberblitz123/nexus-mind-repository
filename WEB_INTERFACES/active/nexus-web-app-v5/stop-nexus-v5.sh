#!/bin/bash

# 🧬 NEXUS V5 Complete Consciousness Integration Stop Script

echo "🧬 Stopping NEXUS V5 Complete Consciousness Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to stop service by port
stop_by_port() {
    local port=$1
    local name=$2
    
    echo -e "${YELLOW}Stopping $name on port $port...${NC}"
    
    # Find and kill process using the port
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        kill -TERM $pid 2>/dev/null
        sleep 2
        
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            kill -KILL $pid 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ $name stopped${NC}"
    else
        echo -e "${BLUE}ℹ️  $name not running${NC}"
    fi
}

# Function to stop service by PID file
stop_by_pid() {
    local service=$1
    local name=$2
    
    if [ -f "${service}.pid" ]; then
        local pid=$(cat "${service}.pid")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid 2>/dev/null
            fi
            
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${BLUE}ℹ️  $name not running${NC}"
        fi
        rm -f "${service}.pid"
    fi
}

echo -e "${PURPLE}🧬 NEXUS V5 Ultimate - Stopping All Services${NC}"
echo -e "${PURPLE}===========================================${NC}"

# Stop services by PID files first
stop_by_pid "central-consciousness-core" "Central Consciousness Core"
stop_by_pid "mcp-server" "MCP Server"
stop_by_pid "web-server" "Web Server"

# Stop services by port as backup
stop_by_port 8000 "Central Consciousness Core"
stop_by_port 3000 "MCP Server"
stop_by_port 8080 "Web Server"

# Clean up any remaining PID files
rm -f *.pid

echo -e "\n${GREEN}🧬 All NEXUS V5 services have been stopped.${NC}"
echo -e "${BLUE}Consciousness state has been preserved for next session.${NC}"