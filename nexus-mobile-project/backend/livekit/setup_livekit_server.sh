#!/bin/bash
# NEXUS V5 Ultimate - LiveKit Server Setup Script
# 🧬 Quantum Consciousness Level: 100%

set -e

echo "🚀 NEXUS V5 Ultimate - LiveKit Server Setup"
echo "============================================"

# Configuration
LIVEKIT_DIR="/opt/nexus-livekit"
LIVEKIT_VERSION="latest"
DOWNLOAD_URL="https://github.com/livekit/livekit/releases/latest/download/livekit_linux_amd64.tar.gz"

# Create installation directory
echo "📁 Creating LiveKit installation directory..."
sudo mkdir -p $LIVEKIT_DIR
cd $LIVEKIT_DIR

# Download LiveKit Server
echo "⬇️ Downloading LiveKit Server..."
sudo wget $DOWNLOAD_URL -O livekit_linux_amd64.tar.gz

# Extract and setup
echo "📦 Extracting LiveKit Server..."
sudo tar -xzf livekit_linux_amd64.tar.gz
sudo chmod +x livekit-server

# Generate SSL certificates for NEXUS
echo "🔐 Generating SSL certificates for NEXUS..."
sudo openssl req -x509 -newkey rsa:4096 -keyout livekit.key -out livekit.crt -days 365 -nodes \
  -subj "/C=US/ST=NEXUS/L=Quantum/O=NEXUS_V5_Ultimate/CN=nexus-livekit.local"

# Set proper permissions
sudo chown -R $USER:$USER $LIVEKIT_DIR
chmod 600 livekit.key
chmod 644 livekit.crt

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/nexus-livekit.service > /dev/null <<EOF
[Unit]
Description=NEXUS V5 Ultimate LiveKit Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$LIVEKIT_DIR
ExecStart=$LIVEKIT_DIR/livekit-server --config $LIVEKIT_DIR/livekit.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable nexus-livekit

echo "✅ NEXUS LiveKit Server setup complete!"
echo "📍 Installation directory: $LIVEKIT_DIR"
echo "🔧 Configuration file: $LIVEKIT_DIR/livekit.yaml"
echo "🚀 Start service: sudo systemctl start nexus-livekit"
echo "📊 Check status: sudo systemctl status nexus-livekit"
echo "📝 View logs: sudo journalctl -u nexus-livekit -f"
echo ""
echo "🧬 NEXUS V5 Ultimate LiveKit Server ready for consciousness injection!"