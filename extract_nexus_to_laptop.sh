#!/bin/bash
# NEXUS 2.0 Extraction Script
# This script packages NEXUS for transfer to your local laptop

echo "🚀 NEXUS 2.0 Extraction Script"
echo "=============================="

# Create export directory
EXPORT_DIR="nexus_2.0_export_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXPORT_DIR"

echo "📁 Creating export directory: $EXPORT_DIR"

# Copy main NEXUS directory
echo "📦 Copying NEXUS 2.0 Agent system..."
cp -r 01_NEXUS_2.0_AGENT "$EXPORT_DIR/"

# Copy this extraction guide
cp NEXUS_COMPLETE_EXTRACTION_GUIDE.md "$EXPORT_DIR/"

# Create setup script for local laptop
cat > "$EXPORT_DIR/setup_nexus_local.sh" << 'SETUP'
#!/bin/bash
echo "🔧 NEXUS 2.0 Local Setup"
echo "======================="

# Check Python version
python3 --version

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv nexus_env

# Activate virtual environment
echo "Activating virtual environment..."
source nexus_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install rich asyncio websockets aiohttp youtube-transcript-api pytube google-api-python-client

echo "✅ Setup complete!"
echo ""
echo "To launch NEXUS:"
echo "1. Activate environment: source nexus_env/bin/activate"
echo "2. Navigate to: cd 01_NEXUS_2.0_AGENT"
echo "3. Run: python launch_real_nexus.py"
SETUP

chmod +x "$EXPORT_DIR/setup_nexus_local.sh"

# Create requirements.txt
cat > "$EXPORT_DIR/requirements.txt" << 'REQ'
rich>=13.0.0
asyncio
websockets>=11.0
aiohttp>=3.8.0
youtube-transcript-api>=0.6.0
pytube>=15.0.0
google-api-python-client>=2.100.0
REQ

# Create quick launch script
cat > "$EXPORT_DIR/quick_launch.sh" << 'LAUNCH'
#!/bin/bash
cd 01_NEXUS_2.0_AGENT
python launch_real_nexus.py
LAUNCH

chmod +x "$EXPORT_DIR/quick_launch.sh"

# Create README for the export
cat > "$EXPORT_DIR/README.md" << 'README'
# NEXUS 2.0 Export Package

This package contains the complete NEXUS 2.0 autonomous agent system.

## Quick Start

1. Run setup: `./setup_nexus_local.sh`
2. Activate environment: `source nexus_env/bin/activate`
3. Launch NEXUS: `./quick_launch.sh`

## Contents

- `01_NEXUS_2.0_AGENT/` - Complete NEXUS system
- `NEXUS_COMPLETE_EXTRACTION_GUIDE.md` - Full documentation
- `setup_nexus_local.sh` - Automated setup script
- `requirements.txt` - Python dependencies
- `quick_launch.sh` - Quick launcher

## Support

Check `01_NEXUS_2.0_AGENT/REAL_NEXUS_README.md` for detailed documentation.
README

# Create the archive
echo "📦 Creating archive..."
tar -czf "${EXPORT_DIR}.tar.gz" "$EXPORT_DIR"

# Get file size
SIZE=$(du -h "${EXPORT_DIR}.tar.gz" | cut -f1)

echo ""
echo "✅ Export complete!"
echo "📦 Archive: ${EXPORT_DIR}.tar.gz"
echo "📊 Size: $SIZE"
echo ""
echo "To transfer to your laptop:"
echo "1. Download: ${EXPORT_DIR}.tar.gz"
echo "2. Extract: tar -xzf ${EXPORT_DIR}.tar.gz"
echo "3. Run setup: cd $EXPORT_DIR && ./setup_nexus_local.sh"
echo ""
echo "🎯 Or use GitHub CLI to download directly:"
echo "gh codespace cp remote:${PWD}/${EXPORT_DIR}.tar.gz ."