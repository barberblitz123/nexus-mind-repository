#!/bin/bash
# NEXUS Stage + Desktop Manager - Install and Run Script

echo "╔══════════════════════════════════════════════════════╗"
echo "║     NEXUS Stage + Desktop Manager Installation       ║"
echo "╚══════════════════════════════════════════════════════╝"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version found"

# Create virtual environment
echo -e "\nCreating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo -e "\nActivating virtual environment..."
source venv/bin/activate

# Install dependencies
echo -e "\nInstalling dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create configs directory if not exists
if [ ! -d "configs" ]; then
    mkdir -p configs
    echo "✅ Created configs directory"
fi

# Create default config
if [ ! -f "configs/app_config.json" ]; then
    cat > configs/app_config.json << EOF
{
  "stage_manager": {
    "max_active_agents": 4,
    "default_window_size": {"width": 800, "height": 600},
    "auto_arrange": true
  },
  "desktop_manager": {
    "chat_history_limit": 1000,
    "preview_pane_limit": 6,
    "auto_save_interval": 300
  },
  "general": {
    "theme": "dark",
    "auto_save_workspace": true,
    "debug_mode": false
  }
}
EOF
    echo "✅ Created default configuration"
fi

echo -e "\n╔══════════════════════════════════════════════════════╗"
echo "║            Installation Complete!                     ║"
echo "╚══════════════════════════════════════════════════════╝"

echo -e "\nLaunching NEXUS Stage + Desktop Manager...\n"

# Run the application
python launch_interconnected_demo.py