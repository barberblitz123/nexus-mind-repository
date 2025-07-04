#!/bin/bash
# NEXUS 2.0 Local-Only Launcher
# No external services required!

echo "=========================================="
echo "NEXUS 2.0 - Local Edition Launcher"
echo "No APIs, No Subscriptions, No Cloud!"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "nexus_local_venv" ]; then
    echo "Creating local virtual environment..."
    python3 -m venv nexus_local_venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source nexus_local_venv/bin/activate 2>/dev/null || . nexus_local_venv/Scripts/activate 2>/dev/null

# Install requirements if needed
if [ ! -f "nexus_local_venv/.installed" ]; then
    echo "Installing local-only dependencies..."
    pip install -r requirements_local_only.txt
    touch nexus_local_venv/.installed
fi

# Launch NEXUS Local Edition
echo ""
echo "Launching NEXUS 2.0 Local Edition..."
echo "Everything runs on YOUR machine!"
echo ""
python3 nexus_2.0_local_only.py

# Deactivate virtual environment when done
deactivate 2>/dev/null || true