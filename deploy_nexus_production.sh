#!/bin/bash
# NEXUS Production Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NEXUS_VERSION=${NEXUS_VERSION:-"1.0.0"}
NEXUS_HOME=${NEXUS_HOME:-"/opt/nexus"}
NEXUS_USER=${NEXUS_USER:-"nexus"}
NEXUS_DATA=${NEXUS_DATA:-"/var/lib/nexus"}
NEXUS_LOG=${NEXUS_LOG:-"/var/log/nexus"}

# Functions
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[*]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_system() {
    print_status "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
        print_status "Detected Linux distribution: $DISTRO"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "Detected macOS"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $PYTHON_VERSION"
    
    # Check memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 4 ]; then
        print_warning "Less than 4GB RAM detected. NEXUS may run slowly."
    fi
}

install_dependencies() {
    print_status "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Update package manager
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y \
                python3-pip \
                python3-venv \
                redis-server \
                consul \
                git \
                curl \
                build-essential \
                libssl-dev \
                libffi-dev \
                python3-dev
        elif command -v yum &> /dev/null; then
            yum update -y
            yum install -y \
                python3-pip \
                python3-devel \
                redis \
                git \
                curl \
                gcc \
                openssl-devel
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            print_error "Homebrew not found. Please install Homebrew first."
            exit 1
        fi
        
        brew update
        brew install python@3.9 redis consul
    fi
}

create_user() {
    print_status "Creating NEXUS user..."
    
    if ! id "$NEXUS_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$NEXUS_HOME" -m "$NEXUS_USER"
        print_status "User $NEXUS_USER created"
    else
        print_status "User $NEXUS_USER already exists"
    fi
}

create_directories() {
    print_status "Creating directories..."
    
    mkdir -p "$NEXUS_HOME"
    mkdir -p "$NEXUS_DATA"
    mkdir -p "$NEXUS_LOG"
    mkdir -p "$NEXUS_DATA/plugins"
    mkdir -p "$NEXUS_DATA/backups"
    
    chown -R "$NEXUS_USER:$NEXUS_USER" "$NEXUS_HOME"
    chown -R "$NEXUS_USER:$NEXUS_USER" "$NEXUS_DATA"
    chown -R "$NEXUS_USER:$NEXUS_USER" "$NEXUS_LOG"
}

download_nexus() {
    print_status "Downloading NEXUS v$NEXUS_VERSION..."
    
    # Determine platform
    PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    fi
    
    DOWNLOAD_URL="https://github.com/nexus/nexus-mind-repository/releases/download/v${NEXUS_VERSION}/nexus-${NEXUS_VERSION}-${PLATFORM}-${ARCH}.tar.gz"
    
    # For development, use local build
    if [ -f "dist/nexus" ]; then
        print_warning "Using local build"
        cp dist/nexus "$NEXUS_HOME/nexus"
        chmod +x "$NEXUS_HOME/nexus"
    else
        # Download from releases
        curl -L "$DOWNLOAD_URL" -o "/tmp/nexus.tar.gz"
        tar -xzf "/tmp/nexus.tar.gz" -C "$NEXUS_HOME"
        rm "/tmp/nexus.tar.gz"
    fi
    
    chown -R "$NEXUS_USER:$NEXUS_USER" "$NEXUS_HOME"
}

configure_nexus() {
    print_status "Configuring NEXUS..."
    
    # Copy default configuration
    if [ -f "nexus_production_config.yaml" ]; then
        cp nexus_production_config.yaml "$NEXUS_DATA/nexus_production_config.yaml"
    fi
    
    # Update paths in config
    sed -i "s|/var/lib/nexus|$NEXUS_DATA|g" "$NEXUS_DATA/nexus_production_config.yaml"
    sed -i "s|/opt/nexus/plugins|$NEXUS_DATA/plugins|g" "$NEXUS_DATA/nexus_production_config.yaml"
    
    chown "$NEXUS_USER:$NEXUS_USER" "$NEXUS_DATA/nexus_production_config.yaml"
}

setup_systemd() {
    print_status "Setting up systemd service..."
    
    cat > /etc/systemd/system/nexus.service << EOF
[Unit]
Description=NEXUS Mind Repository
After=network.target redis.service consul.service
Wants=redis.service consul.service

[Service]
Type=simple
User=$NEXUS_USER
Group=$NEXUS_USER
WorkingDirectory=$NEXUS_HOME
ExecStart=$NEXUS_HOME/nexus start --config $NEXUS_DATA/nexus_production_config.yaml
ExecStop=$NEXUS_HOME/nexus stop
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nexus

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$NEXUS_DATA $NEXUS_LOG

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryLimit=16G

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable nexus.service
}

setup_nginx() {
    print_status "Setting up nginx reverse proxy..."
    
    if ! command -v nginx &> /dev/null; then
        print_warning "nginx not installed. Skipping reverse proxy setup."
        return
    fi
    
    cat > /etc/nginx/sites-available/nexus << EOF
upstream nexus_backend {
    server 127.0.0.1:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name _;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/nexus.crt;
    ssl_certificate_key /etc/ssl/private/nexus.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API Gateway
    location / {
        proxy_pass http://nexus_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Metrics endpoint (restricted)
    location /metrics {
        proxy_pass http://127.0.0.1:9090/metrics;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/nexus /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
}

setup_firewall() {
    print_status "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp   # SSH
        ufw allow 80/tcp   # HTTP
        ufw allow 443/tcp  # HTTPS
        ufw allow 8080/tcp # NEXUS API
        ufw allow 9090/tcp # Metrics (restricted)
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=8080/tcp
        firewall-cmd --permanent --add-port=9090/tcp
        firewall-cmd --reload
    fi
}

start_services() {
    print_status "Starting services..."
    
    # Start Redis
    systemctl start redis
    systemctl enable redis
    
    # Start Consul
    systemctl start consul
    systemctl enable consul
    
    # Wait for services
    sleep 5
    
    # Start NEXUS
    systemctl start nexus
    
    # Check status
    sleep 5
    if systemctl is-active --quiet nexus; then
        print_status "NEXUS is running"
    else
        print_error "NEXUS failed to start. Check logs: journalctl -u nexus"
        exit 1
    fi
}

post_install() {
    print_status "Running post-installation tasks..."
    
    # Run setup wizard if first install
    if [ ! -f "$NEXUS_DATA/.configured" ]; then
        print_status "Running initial setup..."
        sudo -u "$NEXUS_USER" "$NEXUS_HOME/nexus" setup
        touch "$NEXUS_DATA/.configured"
    fi
    
    # Create initial backup
    sudo -u "$NEXUS_USER" "$NEXUS_HOME/nexus" backup create --name initial
    
    print_status "Installation complete!"
    echo
    echo "NEXUS is now running at:"
    echo "  - API: http://localhost:8080"
    echo "  - Metrics: http://localhost:9090/metrics"
    echo
    echo "To check status: systemctl status nexus"
    echo "To view logs: journalctl -u nexus -f"
    echo "To stop: systemctl stop nexus"
}

# Main installation flow
main() {
    echo "NEXUS Production Deployment"
    echo "=========================="
    echo
    
    check_root
    check_system
    install_dependencies
    create_user
    create_directories
    download_nexus
    configure_nexus
    setup_systemd
    setup_nginx
    setup_firewall
    start_services
    post_install
}

# Run main function
main "$@"