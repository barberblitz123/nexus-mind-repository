# NEXUS 2.0 Troubleshooting Guide

## Common Startup Issues and Fixes

### 1. Database Connection Errors

**Error**: `password authentication failed for user "codespace"`

**Solutions**:
- The application expects a PostgreSQL database but might not have one running
- For development, you can use SQLite or run without a database
- To fix:
  ```bash
  # Option 1: Run in safe mode (no database required)
  ./nexus start --safe-mode
  
  # Option 2: Set environment variables for development
  export DATABASE_URL="sqlite:///nexus.db"
  export ENVIRONMENT="development"
  ```

### 2. Redis Authentication Errors

**Error**: `Authentication required`

**Solutions**:
- Redis is expecting authentication but none is provided
- For development, you can disable Redis or use a local instance without auth
- To fix:
  ```bash
  # Option 1: Run without Redis (safe mode)
  ./nexus start --safe-mode
  
  # Option 2: Set Redis URL without authentication
  export REDIS_URL="redis://localhost:6379/0"
  ```

### 3. OpenTelemetry Connection Errors

**Error**: `Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317`

**Solutions**:
- The telemetry exporter is trying to connect to a non-existent service
- This is non-critical and can be disabled
- To fix:
  ```bash
  export OTLP_ENDPOINT=""
  export TELEMETRY_ENABLED="false"
  ```

### 4. Missing Environment Variables

**Error**: Various authentication and configuration errors

**Solutions**:
- Create a `.env` file with required variables:
  ```bash
  # Create .env file
  cat > .env << EOF
  # Core settings
  SECRET_KEY=dev-secret-key-not-for-production
  JWT_SECRET_KEY=dev-jwt-secret-not-for-production
  ENVIRONMENT=development
  DEBUG=true
  
  # Database (use SQLite for development)
  DATABASE_URL=sqlite:///nexus.db
  
  # Redis (optional for development)
  REDIS_URL=redis://localhost:6379/0
  
  # Disable production features
  VAULT_ENABLED=false
  RATE_LIMIT_ENABLED=false
  TELEMETRY_ENABLED=false
  OTLP_ENDPOINT=""
  EOF
  ```

## Dependency Verification Steps

### 1. Check Python Version
```bash
python3 --version
# Should be 3.9 or higher
```

### 2. Verify Core Dependencies
```bash
# Run the startup fix script
python3 startup_fix.py
```

### 3. Install Missing Dependencies
```bash
# If any dependencies are missing
pip install -r requirements.txt
```

## Environment Setup Requirements

### Minimum Requirements
- Python 3.9+
- 2GB RAM
- 1GB free disk space

### Development Environment Setup
1. Clone the repository
2. Create virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.env` file (see above)
5. Run startup fix script:
   ```bash
   python3 startup_fix.py
   ```

### Production Environment Setup
1. Ensure PostgreSQL is installed and running
2. Ensure Redis is installed and running
3. Configure environment variables properly
4. Use proper secrets management (Vault)
5. Enable monitoring services

## Step-by-Step Launch Instructions

### Quick Start (Development Mode)
1. Run the startup fix script:
   ```bash
   python3 startup_fix.py
   ```
2. Launch NEXUS in one of these ways:
   ```bash
   # Option 1: Minimal mode (recommended for first start)
   ./nexus_minimal.py
   
   # Option 2: Development mode
   ./nexus_dev start
   
   # Option 3: Safe mode (if above fail)
   ./nexus start --safe-mode
   ```

### Normal Start (With All Services)
1. Ensure all services are running:
   - PostgreSQL
   - Redis
   - OpenTelemetry Collector (optional)
2. Configure environment:
   ```bash
   source .env
   ```
3. Run startup check:
   ```bash
   ./nexus check --verbose
   ```
4. Start NEXUS:
   ```bash
   ./nexus start
   ```

### First-Time Setup
1. Run the setup wizard:
   ```bash
   ./nexus setup
   ```
2. Follow the prompts to configure:
   - User profile
   - API keys (optional)
   - Feature flags
   - Service preferences

## Common Error Messages

### "Some components not available"
- This means optional components are missing
- NEXUS will run in limited mode
- Not critical for basic functionality

### "Terminal UI not available"
- The terminal interface couldn't load
- Check if all UI dependencies are installed:
  ```bash
  pip install rich textual
  ```

### "Configuration file corrupted"
- Delete the corrupted config and re-run setup:
  ```bash
  rm ~/.nexus/config.json
  ./nexus setup
  ```

## Debug Mode

To get more detailed error information:
```bash
./nexus start --debug
```

This will:
- Enable verbose logging
- Show stack traces
- Log to `nexus_core.log`

## Getting Help

1. Check the logs:
   - `nexus_core.log` - Main application log
   - `nexus_verification.log` - Startup verification log

2. Run diagnostics:
   ```bash
   ./nexus doctor
   ```

3. Check system status:
   ```bash
   ./nexus check --verbose
   ```

## Safe Mode

Safe mode disables all external dependencies and runs with minimal features:
```bash
./nexus start --safe-mode
```

This is useful for:
- Testing basic functionality
- Running without databases
- Development and debugging
- First-time setup