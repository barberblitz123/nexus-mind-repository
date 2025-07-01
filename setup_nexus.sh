#!/bin/bash
# NEXUS Setup Script - Install and configure NEXUS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
show_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
EOF
    echo -e "${NC}"
    echo -e "${CYAN}NEXUS Setup - Your AI Pair Programmer${NC}"
    echo ""
}

# Check if running on supported platform
check_platform() {
    echo -e "${BLUE}Checking platform...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${GREEN}✓ Platform supported: $OSTYPE${NC}"
    else
        echo -e "${RED}✗ Unsupported platform: $OSTYPE${NC}"
        echo "NEXUS requires Linux or macOS"
        exit 1
    fi
}

# Check Python version
check_python() {
    echo -e "${BLUE}Checking Python...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc) -eq 1 ]]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
        else
            echo -e "${RED}✗ Python 3.8+ required (found $PYTHON_VERSION)${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Python 3 not found${NC}"
        exit 1
    fi
}

# Check Node.js
check_node() {
    echo -e "${BLUE}Checking Node.js...${NC}"
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
    else
        echo -e "${YELLOW}⚠ Node.js not found (optional for web interfaces)${NC}"
    fi
}

# Install Python dependencies
install_python_deps() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    
    # Core dependencies
    DEPS=(
        "fastapi"
        "uvicorn[standard]"
        "aiohttp"
        "rich"
        "click"
        "numpy"
        "pandas"
        "websockets"
        "psutil"
        "pyttsx3"
        "SpeechRecognition"
        "Pillow"
        "pytesseract"
        "beautifulsoup4"
        "selenium"
        "httpx"
        "tenacity"
        "cryptography"
        "networkx"
        "chromadb"
    )
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    for dep in "${DEPS[@]}"; do
        echo "Installing $dep..."
        pip install "$dep" || echo -e "${YELLOW}⚠ Failed to install $dep${NC}"
    done
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Setup NEXUS command
setup_nexus_command() {
    echo -e "${BLUE}Setting up NEXUS command...${NC}"
    
    # Get NEXUS directory
    NEXUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Create bin directory if not exists
    mkdir -p "$HOME/.local/bin"
    
    # Create wrapper script
    cat > "$HOME/.local/bin/nexus" << EOF
#!/bin/bash
# NEXUS Command Wrapper

# Activate virtual environment if exists
if [ -d "$NEXUS_DIR/venv" ]; then
    source "$NEXUS_DIR/venv/bin/activate"
fi

# Set NEXUS_HOME
export NEXUS_HOME="$NEXUS_DIR"

# Run NEXUS CLI
python3 "$NEXUS_DIR/nexus" "\$@"
EOF
    
    # Make executable
    chmod +x "$HOME/.local/bin/nexus"
    chmod +x "$NEXUS_DIR/nexus"
    chmod +x "$NEXUS_DIR/nexus_complete_launcher.py"
    
    echo -e "${GREEN}✓ NEXUS command installed${NC}"
}

# Setup shell integration
setup_shell_integration() {
    echo -e "${BLUE}Setting up shell integration...${NC}"
    
    # Detect shell
    SHELL_NAME=$(basename "$SHELL")
    
    case $SHELL_NAME in
        bash)
            RC_FILE="$HOME/.bashrc"
            ;;
        zsh)
            RC_FILE="$HOME/.zshrc"
            ;;
        *)
            echo -e "${YELLOW}⚠ Unknown shell: $SHELL_NAME${NC}"
            RC_FILE=""
            ;;
    esac
    
    if [ -n "$RC_FILE" ]; then
        # Add to PATH if not already there
        if ! grep -q ".local/bin" "$RC_FILE"; then
            echo "" >> "$RC_FILE"
            echo "# NEXUS PATH" >> "$RC_FILE"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
            echo -e "${GREEN}✓ Added to PATH in $RC_FILE${NC}"
        else
            echo -e "${GREEN}✓ PATH already configured${NC}"
        fi
        
        # Add NEXUS_HOME
        if ! grep -q "NEXUS_HOME" "$RC_FILE"; then
            echo "export NEXUS_HOME=\"$NEXUS_DIR\"" >> "$RC_FILE"
        fi
        
        # Add completion
        if [ "$SHELL_NAME" = "bash" ]; then
            echo "" >> "$RC_FILE"
            echo "# NEXUS Bash Completion" >> "$RC_FILE"
            echo "eval \"\$(_NEXUS_COMPLETE=bash_source nexus)\"" >> "$RC_FILE"
        elif [ "$SHELL_NAME" = "zsh" ]; then
            echo "" >> "$RC_FILE"
            echo "# NEXUS Zsh Completion" >> "$RC_FILE"
            echo "eval \"\$(_NEXUS_COMPLETE=zsh_source nexus)\"" >> "$RC_FILE"
        fi
    fi
}

# Create default configuration
create_default_config() {
    echo -e "${BLUE}Creating default configuration...${NC}"
    
    # Create .nexus directory
    mkdir -p "$HOME/.nexus"
    
    # Create config.json
    cat > "$HOME/.nexus/config.json" << EOF
{
  "api_url": "http://localhost:8081",
  "manus_url": "http://localhost:8002",
  "voice_url": "http://localhost:8004",
  "theme": "cyberpunk",
  "voice_enabled": true,
  "auto_update": true
}
EOF
    
    # Copy .env.example to .env if not exists
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
    fi
    
    echo -e "${GREEN}✓ Configuration created${NC}"
}

# Install system dependencies
install_system_deps() {
    echo -e "${BLUE}Checking system dependencies...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            echo "Installing system packages (may require sudo)..."
            sudo apt-get update
            sudo apt-get install -y \
                tesseract-ocr \
                espeak \
                portaudio19-dev \
                python3-pyaudio \
                chromium-driver \
                2>/dev/null || echo -e "${YELLOW}⚠ Some system packages failed to install${NC}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Installing system packages..."
            brew install tesseract portaudio 2>/dev/null || echo -e "${YELLOW}⚠ Some system packages failed to install${NC}"
        fi
    fi
}

# Main setup function
main() {
    show_banner
    
    # Run checks
    check_platform
    check_python
    check_node
    
    # Install dependencies
    install_system_deps
    install_python_deps
    
    # Setup NEXUS
    setup_nexus_command
    setup_shell_integration
    create_default_config
    
    echo ""
    echo -e "${GREEN}✨ NEXUS setup complete!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Reload your shell: source ~/.bashrc (or ~/.zshrc)"
    echo "2. Start NEXUS: nexus launch"
    echo "3. Or use quick commands:"
    echo "   - nexus status      # Check system status"
    echo "   - nexus chat        # Start chat interface"
    echo "   - nexus create app  # Create new project"
    echo ""
    echo -e "${CYAN}Thank you for installing NEXUS!${NC}"
}

# Run main function
main