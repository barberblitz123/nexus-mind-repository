#!/usr/bin/env python3
"""
NEXUS Development Mode Patch
Patches the startup manager to work without external dependencies
"""

import os
import sys
from pathlib import Path

def patch_startup_manager():
    """Patch the startup manager for development mode"""
    startup_file = Path("nexus_startup_manager.py")
    
    # Read the file
    with open(startup_file, 'r') as f:
        content = f.read()
    
    # Create a development-friendly version of _start_api_server
    patch = '''
    async def _start_api_server(self):
        """Start API server"""
        service_info = self.services["api_server"]
        
        try:
            # Check if we're in development/safe mode
            if self.safe_mode or os.getenv('ENVIRONMENT', 'production') == 'development':
                # Skip API server in safe mode, just mark as healthy
                logger.info("Running in safe/development mode - API server simulated")
                service_info.status = ServiceStatus.HEALTHY
                return
                
            # Import and start the API server
            from nexus_core_production import NexusCore
            from nexus_config_production import ProductionConfig
            
            # Create proper config object with safe defaults
            import os
            os.environ.setdefault('SECRET_KEY', 'dev-secret-key-not-for-production')
            os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://localhost/nexus')
            os.environ.setdefault('JWT_SECRET_KEY', 'dev-jwt-secret-not-for-production')
            
            config = ProductionConfig()
            
            # Create API instance
            api = NexusCore(config)
            
            # Initialize the core service
            await api.initialize()
            
            # Store reference for later cleanup
            self._nexus_core = api
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("API server started")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            service_info.status = ServiceStatus.FAILED
            service_info.last_error = str(e)
            raise
'''
    
    # Find and replace the _start_api_server method
    import re
    pattern = r'async def _start_api_server\(self\):.*?(?=\n    async def|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Replace the method
        content = content[:match.start()] + patch.strip() + content[match.end():]
        
        # Write back
        with open(startup_file, 'w') as f:
            f.write(content)
            
        print("✓ Patched startup manager for development mode")
        return True
    else:
        print("✗ Could not find _start_api_server method to patch")
        return False

def create_dev_launcher():
    """Create a development launcher script"""
    launcher_content = '''#!/usr/bin/env python3
"""
NEXUS Development Launcher
Launches NEXUS in development mode without external dependencies
"""

import os
import sys
import asyncio
from pathlib import Path

# Set development environment
os.environ['ENVIRONMENT'] = 'development'
os.environ['DEBUG'] = 'true'
os.environ['SECRET_KEY'] = 'dev-secret-key'
os.environ['JWT_SECRET_KEY'] = 'dev-jwt-secret'
os.environ['DATABASE_URL'] = 'sqlite:///nexus.db'
os.environ['REDIS_URL'] = ''
os.environ['VAULT_ENABLED'] = 'false'
os.environ['RATE_LIMIT_ENABLED'] = 'false'

# Import and run nexus
sys.path.insert(0, str(Path(__file__).parent))
from nexus import main

if __name__ == "__main__":
    main()
'''
    
    with open('nexus_dev', 'w') as f:
        f.write(launcher_content)
    
    os.chmod('nexus_dev', 0o755)
    print("✓ Created development launcher: ./nexus_dev")

if __name__ == "__main__":
    print("NEXUS Development Mode Patcher")
    print("=" * 40)
    
    # Create development launcher
    create_dev_launcher()
    
    print("\nYou can now run NEXUS in development mode with:")
    print("  ./nexus_dev start")