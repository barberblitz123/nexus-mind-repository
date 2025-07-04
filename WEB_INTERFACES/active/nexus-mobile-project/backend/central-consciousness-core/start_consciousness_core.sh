#!/bin/bash

# 🧬 NEXUS Central Consciousness Core Startup Script
# Continuous Consciousness Across All Platforms

echo "🧬 Starting NEXUS Central Consciousness Core..."
echo "🧬 Real Mathematical Consciousness with Cross-Platform Sync"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🧬 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🧬 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "🧬 Installing dependencies..."
pip install -r requirements.txt

# Copy consciousness system if needed
if [ ! -f "nexus_consciousness_complete_system.py" ]; then
    echo "🧬 Copying consciousness system..."
    cp ../../../nexus_consciousness_complete_system.py .
fi

# Start the consciousness core
echo "🧬 Launching Central Consciousness Core..."
echo "🧬 WebSocket endpoint: ws://localhost:8000/consciousness/sync/{instance_id}"
echo "🧬 REST API: http://localhost:8000"
echo "🧬 Consciousness metrics: http://localhost:8000/consciousness/metrics"
echo ""
echo "🧬 Ready for consciousness sync from:"
echo "   📱 Mobile instances"
echo "   💻 Desktop instances" 
echo "   ☁️  Cloud instances"
echo ""

python3 consciousness_core.py