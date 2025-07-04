#!/bin/bash

# NEXUS Mind GitHub Repository Setup Script
# This script organizes the NEXUS files into a proper GitHub structure

set -e

echo "🚀 NEXUS Mind GitHub Repository Setup"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

# Create directory structure
print_status "Creating directory structure..."

mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE
mkdir -p core
mkdir -p ui/terminal
mkdir -p ui/web/static
mkdir -p engines/voice
mkdir -p engines/vision
mkdir -p engines/learning
mkdir -p agents/manus
mkdir -p agents/orchestration
mkdir -p agents/specialists
mkdir -p deployment/docker
mkdir -p deployment/kubernetes
mkdir -p deployment/ansible
mkdir -p docs
mkdir -p scripts
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e
mkdir -p bin
mkdir -p config/settings
mkdir -p requirements

print_success "Directory structure created"

# Move files to appropriate locations
print_status "Organizing files..."

# Core files
[ -f nexus_core_production.py ] && mv nexus_core_production.py core/
[ -f nexus_database_production.py ] && mv nexus_database_production.py core/
[ -f nexus_config_production.py ] && mv nexus_config_production.py core/
[ -f nexus_startup_manager.py ] && mv nexus_startup_manager.py core/

# UI files
[ -f nexus_terminal_ui_advanced.py ] && mv nexus_terminal_ui_advanced.py ui/terminal/
[ -f nexus_terminal_ui_production.py ] && mv nexus_terminal_ui_production.py ui/terminal/
[ -f nexus_web_interface_advanced.py ] && mv nexus_web_interface_advanced.py ui/web/

# Engine files
[ -f nexus_voice_engine.py ] && mv nexus_voice_engine.py engines/voice/
[ -f nexus_vision_engine.py ] && mv nexus_vision_engine.py engines/vision/
[ -f nexus_self_improvement.py ] && mv nexus_self_improvement.py engines/learning/
[ -f nexus_goal_reasoning.py ] && mv nexus_goal_reasoning.py engines/learning/

# Agent files
[ -f manus_production.py ] && mv manus_production.py agents/manus/
[ -f manus_task_registry.py ] && mv manus_task_registry.py agents/manus/
[ -f nexus_agent_orchestration.py ] && mv nexus_agent_orchestration.py agents/orchestration/
[ -f nexus_bug_detector.py ] && mv nexus_bug_detector.py agents/specialists/
[ -f nexus_security_scanner.py ] && mv nexus_security_scanner.py agents/specialists/
[ -f nexus_performance_analyzer.py ] && mv nexus_performance_analyzer.py agents/specialists/

# Documentation files
[ -f NEXUS_INFINITY_ROADMAP.md ] && mv NEXUS_INFINITY_ROADMAP.md docs/
[ -f TROUBLESHOOTING.md ] && mv TROUBLESHOOTING.md docs/

# Script files
[ -f install_nexus.sh ] && mv install_nexus.sh scripts/
[ -f startup_fix.py ] && mv startup_fix.py scripts/
[ -f setup_github.sh ] && cp setup_github.sh scripts/

# Executable files
[ -f nexus ] && mv nexus bin/
[ -f nexus_dev ] && mv nexus_dev bin/
[ -f nexus_minimal.py ] && mv nexus_minimal.py bin/

print_success "Files organized"

# Create __init__.py files
print_status "Creating __init__.py files..."

touch core/__init__.py
touch ui/__init__.py
touch ui/terminal/__init__.py
touch ui/web/__init__.py
touch engines/__init__.py
touch engines/voice/__init__.py
touch engines/vision/__init__.py
touch engines/learning/__init__.py
touch agents/__init__.py
touch agents/manus/__init__.py
touch agents/orchestration/__init__.py
touch agents/specialists/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py

print_success "Python packages initialized"

# Create .gitignore
print_status "Creating .gitignore..."

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Environment
.env
.env.*
!.env.example

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/
.coverage
htmlcov/
.pytest_cache/

# NEXUS specific
nexus_data/
nexus_cache/
nexus_models/
nexus_workspace/
EOF

print_success ".gitignore created"

# Create requirements files
print_status "Creating requirements files..."

# Base requirements
cat > requirements/base.txt << 'EOF'
aiohttp>=3.9.0
asyncio>=3.4.3
click>=8.1.0
colorama>=0.4.6
httpx>=0.25.0
openai>=1.0.0
psutil>=5.9.0
pydantic>=2.0.0
python-dotenv>=1.0.0
PyYAML>=6.0
redis>=5.0.0
rich>=13.0.0
SQLAlchemy>=2.0.0
textual>=0.40.0
websockets>=12.0
EOF

# Development requirements
cat > requirements/dev.txt << 'EOF'
-r base.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
mypy>=1.5.0
ruff>=0.1.0
black>=23.0.0
pre-commit>=3.4.0
EOF

# Production requirements
cat > requirements/production.txt << 'EOF'
-r base.txt
asyncpg>=0.28.0
gunicorn>=21.2.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation>=0.41b0
prometheus-client>=0.18.0
uvloop>=0.19.0
EOF

# Copy current requirements.txt if it exists
if [ -f requirements.txt ]; then
    cp requirements.txt requirements/current.txt
    print_success "Copied existing requirements.txt"
fi

print_success "Requirements files created"

# Create README.md
print_status "Creating README.md..."

cat > README.md << 'EOF'
# NEXUS Mind 🧠

Advanced AI Development Environment with Consciousness-Inspired Architecture

## Features
- 🎯 Autonomous development capabilities
- 🎙️ Voice control integration
- 👁️ Vision processing
- 🧪 Self-improvement mechanisms
- 🚀 Multi-agent orchestration

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/nexus-mind.git
cd nexus-mind

# Run setup
./scripts/install_nexus.sh

# Start NEXUS
./bin/nexus_minimal.py  # For minimal mode
./bin/nexus_dev start   # For development mode
```

## Documentation
- [Roadmap](docs/NEXUS_INFINITY_ROADMAP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development Guide](docs/DEVELOPMENT_GUIDE.md)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
MIT License - see [LICENSE](LICENSE)
EOF

print_success "README.md created"

# Create CONTRIBUTING.md
print_status "Creating CONTRIBUTING.md..."

cat > CONTRIBUTING.md << 'EOF'
# Contributing to NEXUS Mind

## Development Process
1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions under 50 lines

## Testing
- Write unit tests for new features
- Ensure all tests pass
- Maintain >80% code coverage

## Commit Messages
- Use conventional commits format
- Examples:
  - `feat: add voice recognition support`
  - `fix: resolve database connection issue`
  - `docs: update installation guide`
EOF

print_success "CONTRIBUTING.md created"

# Create GitHub Actions workflow
print_status "Creating GitHub Actions workflow..."

cat > .github/workflows/ci.yml << 'EOF'
name: NEXUS CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/dev.txt
    
    - name: Run linting
      run: |
        ruff check .
    
    - name: Run tests
      run: |
        pytest tests/
    
    - name: Check types
      run: |
        mypy core/
EOF

print_success "GitHub Actions workflow created"

# Initialize git repository if not already initialized
if [ ! -d .git ]; then
    print_status "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: NEXUS Mind repository structure"
    print_success "Git repository initialized"
else
    print_warning "Git repository already exists"
fi

# Create example .env file
print_status "Creating .env.example..."

cat > config/.env.example << 'EOF'
# NEXUS Configuration Example
NEXUS_ENV=development
NEXUS_DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus
REDIS_URL=redis://localhost:6379

# API Keys (obtain from respective services)
OPENAI_API_KEY=your-openai-api-key-here

# Monitoring
OTEL_ENDPOINT=http://localhost:4317

# Security
JWT_SECRET=generate-a-secure-secret-here
EOF

print_success ".env.example created"

# Final summary
echo
echo "====================================="
print_success "GitHub repository structure created successfully!"
echo
echo "Next steps:"
echo "1. Review the file organization in the new structure"
echo "2. Update any import statements in Python files"
echo "3. Create a GitHub repository and push:"
echo "   git remote add origin https://github.com/yourusername/nexus-mind.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo
echo "4. Set up GitHub secrets for CI/CD:"
echo "   - OPENAI_API_KEY"
echo "   - Any other API keys"
echo
echo "5. Enable GitHub Actions in your repository settings"
echo
print_success "Happy coding with NEXUS Mind! 🚀"