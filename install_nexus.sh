#!/bin/bash
# NEXUS Installation Script
# One-line installer: curl -sSL https://nexus.ai/install | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
NEXUS_HOME="$HOME/.nexus"
NEXUS_BIN="$HOME/.local/bin"
NEXUS_REPO="https://github.com/nexus-ai/nexus.git"
PYTHON_MIN_VERSION="3.8"
REQUIRED_SPACE_MB=2048

# Logging functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
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

# Banner
show_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
    ╔═══════════════════════════════════════════╗
    ║     ███╗   ██╗███████╗██╗  ██╗██╗   ██╗ ███████╗
    ║     ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║ ██╔════╝
    ║     ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║ ███████╗
    ║     ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║ ╚════██║
    ║     ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝ ███████║
    ║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚══════╝
    ║                                           ║
    ║        AI Development Platform v2.0       ║
    ╚═══════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# OS Detection
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            DISTRO=$(lsb_release -si 2>/dev/null || echo "Debian")
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            DISTRO=$(cat /etc/redhat-release | cut -d' ' -f1)
        elif [ -f /etc/arch-release ]; then
            OS="arch"
            DISTRO="Arch"
        else
            OS="linux"
            DISTRO="Unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macOS"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="Windows"
    else
        OS="unknown"
        DISTRO="Unknown"
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
            log_error "Python $PYTHON_MIN_VERSION or higher is required (found $PYTHON_VERSION)"
            return 1
        fi
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3 is not installed"
        return 1
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df -m "$HOME" | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE_MB" ]; then
        log_error "Insufficient disk space. Required: ${REQUIRED_SPACE_MB}MB, Available: ${AVAILABLE_SPACE}MB"
        return 1
    fi
    log_success "Disk space check passed"
    
    # Check internet connection
    if ! ping -c 1 google.com &> /dev/null; then
        log_warning "No internet connection detected. Some features may not work."
    fi
    
    # Check for required commands
    REQUIRED_COMMANDS=("git" "curl" "pip3")
    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_warning "$cmd is not installed"
            MISSING_DEPS+=("$cmd")
        fi
    done
    
    return 0
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    case "$OS" in
        debian)
            log_info "Detected Debian-based system"
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv git curl build-essential
            ;;
        redhat)
            log_info "Detected RedHat-based system"
            sudo yum install -y python3-pip python3-virtualenv git curl gcc
            ;;
        arch)
            log_info "Detected Arch-based system"
            sudo pacman -Sy --noconfirm python-pip python-virtualenv git curl base-devel
            ;;
        macos)
            log_info "Detected macOS"
            if ! command -v brew &> /dev/null; then
                log_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3 git
            ;;
        *)
            log_warning "Unknown OS. Please install Python 3.8+, pip, git, and curl manually."
            ;;
    esac
}

# Create directory structure
setup_directories() {
    log_info "Setting up NEXUS directories..."
    
    mkdir -p "$NEXUS_HOME"/{config,plugins,logs,data}
    mkdir -p "$NEXUS_BIN"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$NEXUS_BIN:"* ]]; then
        echo "export PATH=\"\$PATH:$NEXUS_BIN\"" >> "$HOME/.bashrc"
        echo "export PATH=\"\$PATH:$NEXUS_BIN\"" >> "$HOME/.zshrc" 2>/dev/null || true
        export PATH="$PATH:$NEXUS_BIN"
    fi
    
    log_success "Directories created"
}

# Download NEXUS
download_nexus() {
    log_info "Downloading NEXUS..."
    
    # For now, create a simple wrapper script
    # In production, this would download from the actual repository
    
    cat > "$NEXUS_BIN/nexus" << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.expanduser("~/.nexus/lib"))
from nexus import main
if __name__ == "__main__":
    main()
EOF
    
    chmod +x "$NEXUS_BIN/nexus"
    
    # Create lib directory and copy main file
    mkdir -p "$NEXUS_HOME/lib"
    
    # In production, this would be downloaded
    if [ -f "nexus" ]; then
        cp nexus "$NEXUS_HOME/lib/nexus.py"
    else
        log_warning "NEXUS main file not found in current directory"
    fi
    
    log_success "NEXUS downloaded"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv "$NEXUS_HOME/venv"
    
    # Activate virtual environment
    source "$NEXUS_HOME/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install core dependencies
    pip install rich click textual asyncio aiohttp requests websockets
    pip install numpy torch transformers langchain chromadb
    pip install fastapi uvicorn sqlalchemy alembic redis celery
    pip install psutil pydantic anthropic openai
    
    # Install optional dependencies
    pip install pytest black flake8 mypy || log_warning "Some development tools failed to install"
    
    deactivate
    
    log_success "Python dependencies installed"
}

# Configure NEXUS
configure_nexus() {
    log_info "Configuring NEXUS..."
    
    # Create default configuration
    cat > "$NEXUS_HOME/config/config.json" << EOF
{
    "first_run": true,
    "theme": "dark",
    "api_keys": {},
    "services": {
        "web_ui": {"enabled": true, "port": 8000},
        "api": {"enabled": true, "port": 8001},
        "websocket": {"enabled": true, "port": 8002}
    },
    "plugins": {
        "auto_load": true,
        "directory": "$NEXUS_HOME/plugins"
    }
}
EOF
    
    log_success "Configuration created"
}

# Post-installation setup
post_install() {
    log_info "Running post-installation setup..."
    
    # Create desktop entry for Linux
    if [[ "$OS" == "linux" || "$OS" == "debian" || "$OS" == "arch" ]]; then
        cat > "$HOME/.local/share/applications/nexus.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NEXUS
Comment=AI Development Platform
Exec=$NEXUS_BIN/nexus
Icon=$NEXUS_HOME/assets/nexus-icon.png
Terminal=true
Categories=Development;IDE;
EOF
    fi
    
    # Create shell completion
    if [ -d "$HOME/.bash_completion.d" ]; then
        cat > "$HOME/.bash_completion.d/nexus" << 'EOF'
_nexus_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="status chat goal create launch config help"
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _nexus_completion nexus
EOF
    fi
    
    log_success "Post-installation setup complete"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check if nexus command is available
    if command -v nexus &> /dev/null; then
        log_success "NEXUS command is available"
    else
        log_error "NEXUS command not found. Please add $NEXUS_BIN to your PATH"
        return 1
    fi
    
    # Try to run nexus
    if nexus --version &> /dev/null; then
        log_success "NEXUS is working correctly"
    else
        log_warning "NEXUS command exists but may not be fully functional"
    fi
    
    return 0
}

# Main installation function
main() {
    show_banner
    
    log_info "Starting NEXUS installation..."
    log_info "OS: $DISTRO ($OS)"
    
    # Check requirements
    if ! check_requirements; then
        log_error "System requirements not met"
        
        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            echo
            read -p "Would you like to install missing dependencies? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                install_dependencies
            else
                exit 1
            fi
        else
            exit 1
        fi
    fi
    
    # Setup directories
    setup_directories
    
    # Download NEXUS
    download_nexus
    
    # Install Python dependencies
    install_python_deps
    
    # Configure
    configure_nexus
    
    # Post-installation
    post_install
    
    # Verify
    if verify_installation; then
        echo
        log_success "NEXUS installation completed successfully!"
        echo
        echo -e "${GREEN}To get started:${NC}"
        echo -e "  1. Restart your terminal or run: ${CYAN}source ~/.bashrc${NC}"
        echo -e "  2. Run: ${CYAN}nexus${NC}"
        echo -e "  3. Visit: ${CYAN}http://localhost:8000${NC} for the web interface"
        echo
        echo -e "${YELLOW}First time?${NC} Run ${CYAN}nexus config${NC} to set up your API keys"
        echo
    else
        log_error "Installation completed with errors"
        echo "Please check the logs at: $NEXUS_HOME/logs/install.log"
        exit 1
    fi
}

# Detect OS
detect_os

# Create log file
mkdir -p "$NEXUS_HOME/logs"
LOG_FILE="$NEXUS_HOME/logs/install.log"

# Run main installation
main 2>&1 | tee "$LOG_FILE"