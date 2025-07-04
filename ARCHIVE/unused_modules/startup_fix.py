#!/usr/bin/env python3
"""
NEXUS Startup Fix Script
Verifies all dependencies and configurations before launch
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import importlib.util
import platform

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

class StartupFixer:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.fixed = []
        
    def print_banner(self):
        """Print startup fix banner"""
        print(f"\n{BLUE}{'='*60}")
        print("NEXUS 2.0 Startup Fix Script")
        print(f"{'='*60}{RESET}\n")
        
    def check_python_version(self):
        """Check Python version"""
        print(f"{BLUE}Checking Python version...{RESET}")
        version_info = sys.version_info
        if version_info >= (3, 9):
            print(f"{GREEN}✓ Python {version_info.major}.{version_info.minor}.{version_info.micro} - OK{RESET}")
        else:
            self.issues.append(f"Python 3.9+ required (current: {version_info.major}.{version_info.minor})")
            print(f"{RED}✗ Python version too old{RESET}")
            
    def check_dependencies(self):
        """Check required Python packages"""
        print(f"\n{BLUE}Checking Python dependencies...{RESET}")
        
        # Core dependencies
        core_deps = [
            'rich', 'textual', 'aiohttp', 'asyncpg', 'redis',
            'prometheus_client', 'opentelemetry', 'hvac', 'pydantic',
            'pydantic_settings', 'python-dotenv', 'pyyaml', 'circuitbreaker',
            'tenacity', 'celery', 'aioamqp', 'requests', 'uvicorn',
            'fastapi', 'sqlalchemy', 'alembic'
        ]
        
        # Optional dependencies
        optional_deps = [
            'numpy', 'pandas', 'scikit-learn', 'transformers',
            'torch', 'opencv-python', 'pillow', 'matplotlib'
        ]
        
        missing_core = []
        missing_optional = []
        
        # Check core dependencies
        for dep in core_deps:
            module_name = dep.replace('-', '_')
            if module_name == 'python_dotenv':
                module_name = 'dotenv'
            elif module_name == 'pyyaml':
                module_name = 'yaml'
            elif module_name == 'opencv_python':
                module_name = 'cv2'
                
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                missing_core.append(dep)
                print(f"{RED}✗ {dep} - MISSING{RESET}")
            else:
                print(f"{GREEN}✓ {dep} - OK{RESET}")
                
        # Check optional dependencies
        print(f"\n{BLUE}Checking optional dependencies...{RESET}")
        for dep in optional_deps:
            module_name = dep.replace('-', '_')
            if module_name == 'opencv_python':
                module_name = 'cv2'
                
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                missing_optional.append(dep)
                print(f"{YELLOW}⚠ {dep} - Missing (optional){RESET}")
            else:
                print(f"{GREEN}✓ {dep} - OK{RESET}")
                
        if missing_core:
            self.issues.append(f"Missing core dependencies: {', '.join(missing_core)}")
            
        if missing_optional:
            self.warnings.append(f"Missing optional dependencies: {', '.join(missing_optional)}")
            
        return missing_core, missing_optional
        
    def check_environment(self):
        """Check environment variables"""
        print(f"\n{BLUE}Checking environment configuration...{RESET}")
        
        env_file = Path('.env')
        if not env_file.exists():
            print(f"{YELLOW}⚠ No .env file found{RESET}")
            self.create_env_file()
        else:
            print(f"{GREEN}✓ .env file exists{RESET}")
            
        # Check critical environment variables
        critical_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing_vars = []
        
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                print(f"{YELLOW}⚠ {var} not set{RESET}")
            else:
                print(f"{GREEN}✓ {var} is set{RESET}")
                
        if missing_vars and not env_file.exists():
            self.warnings.append(f"Missing environment variables: {', '.join(missing_vars)}")
            
    def create_env_file(self):
        """Create a development .env file"""
        print(f"\n{BLUE}Creating development .env file...{RESET}")
        
        env_content = """# NEXUS Development Environment Configuration
# WARNING: Do not use these values in production!

# Core settings
SECRET_KEY=dev-secret-key-not-for-production
JWT_SECRET_KEY=dev-jwt-secret-not-for-production
ENVIRONMENT=development
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite:///nexus.db

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0

# Disable production features
VAULT_ENABLED=false
RATE_LIMIT_ENABLED=false
TELEMETRY_ENABLED=false
OTLP_ENDPOINT=
OTLP_INSECURE=true

# API Keys (add your own if needed)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Service ports
PORT=8000
METRICS_PORT=9090

# Feature flags
FEATURE_FLAGS_ENABLED=true
FEATURE_FLAGS_SOURCE=env
FEATURE_VOICE=false
FEATURE_VISION=false
FEATURE_WEB_SCRAPING=true
FEATURE_MEMORY=true
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
            
        print(f"{GREEN}✓ Created .env file with development defaults{RESET}")
        self.fixed.append("Created .env file")
        
    def check_directories(self):
        """Check and create necessary directories"""
        print(f"\n{BLUE}Checking directories...{RESET}")
        
        directories = [
            Path.home() / '.nexus',
            Path('logs'),
            Path('data'),
            Path('uploads')
        ]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                print(f"{GREEN}✓ Created {directory}{RESET}")
                self.fixed.append(f"Created directory: {directory}")
            else:
                print(f"{GREEN}✓ {directory} exists{RESET}")
                
    def check_services(self):
        """Check external services"""
        print(f"\n{BLUE}Checking external services...{RESET}")
        
        # Check PostgreSQL
        try:
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{GREEN}✓ PostgreSQL is running{RESET}")
            else:
                print(f"{YELLOW}⚠ PostgreSQL not available (will use SQLite){RESET}")
                self.warnings.append("PostgreSQL not running")
        except FileNotFoundError:
            print(f"{YELLOW}⚠ PostgreSQL not installed{RESET}")
            self.warnings.append("PostgreSQL not installed")
            
        # Check Redis
        try:
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            if result.stdout.strip() == 'PONG':
                print(f"{GREEN}✓ Redis is running{RESET}")
            else:
                print(f"{YELLOW}⚠ Redis not available{RESET}")
                self.warnings.append("Redis not running")
        except FileNotFoundError:
            print(f"{YELLOW}⚠ Redis not installed{RESET}")
            self.warnings.append("Redis not installed")
            
    def create_requirements_file(self):
        """Create requirements.txt if missing"""
        req_file = Path('requirements.txt')
        if not req_file.exists():
            print(f"\n{BLUE}Creating requirements.txt...{RESET}")
            
            requirements = """# NEXUS Core Dependencies
rich>=13.0.0
textual>=0.40.0
aiohttp>=3.9.0
asyncpg>=0.29.0
redis>=5.0.0
prometheus-client>=0.19.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation>=0.41b0
opentelemetry-instrumentation-asyncpg>=0.41b0
opentelemetry-instrumentation-redis>=0.41b0
opentelemetry-instrumentation-celery>=0.41b0
opentelemetry-exporter-otlp>=1.20.0
hvac>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
py-circuitbreaker>=0.4.0
tenacity>=8.2.0
celery>=5.3.0
aioamqp>=0.15.0
requests>=2.31.0
uvicorn>=0.25.0
fastapi>=0.104.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psutil>=5.9.0

# Optional ML/AI Dependencies
# numpy>=1.24.0
# pandas>=2.0.0
# scikit-learn>=1.3.0
# transformers>=4.35.0
# torch>=2.0.0
# opencv-python>=4.8.0
# pillow>=10.0.0
# matplotlib>=3.7.0
"""
            
            with open('requirements.txt', 'w') as f:
                f.write(requirements)
                
            print(f"{GREEN}✓ Created requirements.txt{RESET}")
            self.fixed.append("Created requirements.txt")
            
    def fix_permissions(self):
        """Fix file permissions"""
        print(f"\n{BLUE}Fixing file permissions...{RESET}")
        
        # Make nexus executable
        nexus_file = Path('nexus')
        if nexus_file.exists():
            os.chmod('nexus', 0o755)
            print(f"{GREEN}✓ Made nexus executable{RESET}")
            self.fixed.append("Fixed nexus permissions")
            
    def create_safe_config(self):
        """Create safe mode configuration"""
        print(f"\n{BLUE}Creating safe mode configuration...{RESET}")
        
        config_dir = Path.home() / '.nexus'
        config_file = config_dir / 'safe_mode_config.json'
        
        safe_config = {
            "nexus": {
                "mode": "development",
                "safe_mode": True,
                "features": {
                    "voice": False,
                    "vision": False,
                    "web_scraping": False,
                    "memory": False,
                    "messaging": False
                },
                "api": {
                    "port": 8080
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(safe_config, f, indent=2)
            
        print(f"{GREEN}✓ Created safe mode configuration{RESET}")
        self.fixed.append("Created safe mode config")
        
    def print_summary(self):
        """Print summary of checks and fixes"""
        print(f"\n{BLUE}{'='*60}")
        print("Summary")
        print(f"{'='*60}{RESET}\n")
        
        if self.fixed:
            print(f"{GREEN}Fixed issues:{RESET}")
            for fix in self.fixed:
                print(f"  {GREEN}✓ {fix}{RESET}")
                
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for warning in self.warnings:
                print(f"  {YELLOW}⚠ {warning}{RESET}")
                
        if self.issues:
            print(f"\n{RED}Critical issues:{RESET}")
            for issue in self.issues:
                print(f"  {RED}✗ {issue}{RESET}")
                
        if not self.issues:
            print(f"\n{GREEN}✅ NEXUS is ready to start!{RESET}")
            print(f"\nRun one of these commands:")
            print(f"  {BLUE}./nexus start --safe-mode{RESET}  # Start with minimal features")
            print(f"  {BLUE}./nexus start{RESET}             # Normal start")
            print(f"  {BLUE}./nexus setup{RESET}             # Run setup wizard")
        else:
            print(f"\n{RED}❌ Please fix critical issues before starting NEXUS{RESET}")
            
    def suggest_fixes(self):
        """Suggest fixes for remaining issues"""
        if self.issues or self.warnings:
            print(f"\n{BLUE}Suggested fixes:{RESET}")
            
            # Check for missing dependencies
            for issue in self.issues:
                if "Missing core dependencies" in issue:
                    print(f"\n{YELLOW}To install missing dependencies:{RESET}")
                    print(f"  pip install -r requirements.txt")
                    
            # Check for service issues
            for warning in self.warnings:
                if "PostgreSQL" in warning:
                    print(f"\n{YELLOW}PostgreSQL not available:{RESET}")
                    print(f"  - NEXUS will use SQLite in development mode")
                    print(f"  - For production, install PostgreSQL")
                    
                if "Redis" in warning:
                    print(f"\n{YELLOW}Redis not available:{RESET}")
                    print(f"  - Some features will be disabled")
                    print(f"  - To install: sudo apt-get install redis-server")
                    
    def run(self):
        """Run all checks and fixes"""
        self.print_banner()
        
        # Run checks
        self.check_python_version()
        missing_core, missing_optional = self.check_dependencies()
        self.check_environment()
        self.check_directories()
        self.check_services()
        self.create_requirements_file()
        self.fix_permissions()
        self.create_safe_config()
        
        # Print summary
        self.print_summary()
        self.suggest_fixes()
        
        # Return exit code
        return 0 if not self.issues else 1


if __name__ == "__main__":
    fixer = StartupFixer()
    sys.exit(fixer.run())