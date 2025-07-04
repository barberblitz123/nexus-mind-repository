#!/usr/bin/env python3
"""
NEXUS 2.0 Webinar Interface Launcher
Simplified launcher for the webinar functionality
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add NEXUS paths to Python path
nexus_path = Path(__file__).parent / "ACTIVE_NEXUS_2.0" / "core"
sys.path.insert(0, str(nexus_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def launch_webinar_interface():
    """Launch the NEXUS webinar interface"""
    print("\n🚀 NEXUS 2.0 Webinar Interface Launcher")
    print("=" * 50)
    
    try:
        # Set minimal required environment variables
        os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')
        os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://localhost/nexus')
        os.environ.setdefault('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
        os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
        
        # Import the webinar interface
        print("📦 Loading NEXUS webinar interface...")
        from nexus_webinar_interface import app
        from nexus_config_production import ProductionConfig
        
        # Create configuration
        config = ProductionConfig()
        
        # Start the webinar interface
        print(f"🌐 Starting webinar interface on port {config.WEBINAR_PORT}...")
        
        import uvicorn
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=config.WEBINAR_PORT,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure you have installed the required dependencies:")
        print("  pip install fastapi uvicorn aiohttp redis pydantic")
        print("\nIf you're missing nexus modules, ensure you're in the correct directory.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'aiohttp',
        'redis',
        'pydantic',
        'prometheus_client'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("\nInstall them with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Main entry point"""
    print("""
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
                   Webinar Platform
    """)
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Check for optional services
    print("\n🔍 Checking optional services...")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✅ Redis is available")
    except:
        print("⚠️  Redis not available - webinar will run with limited features")
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'  # Will fail gracefully
    
    # Check PostgreSQL
    try:
        import psycopg2
        print("✅ PostgreSQL driver available")
    except:
        print("⚠️  PostgreSQL driver not installed - using in-memory storage")
    
    print("\n📋 Configuration:")
    print(f"  - Webinar Port: {os.environ.get('WEBINAR_PORT', '8003')}")
    print(f"  - Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"  - Debug Mode: {os.environ.get('DEBUG', 'False')}")
    
    print("\n🚀 Launching NEXUS Webinar Interface...")
    print("   Once started, open: http://localhost:8003")
    print("   Demo session ID: demo")
    print("\n   Press Ctrl+C to stop\n")
    
    # Run the async launcher
    try:
        asyncio.run(launch_webinar_interface())
    except KeyboardInterrupt:
        print("\n\n👋 Webinar interface stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()