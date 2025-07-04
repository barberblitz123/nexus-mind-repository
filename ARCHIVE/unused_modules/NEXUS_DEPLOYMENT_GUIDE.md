# 🧬 NEXUS Deployment Guide
## Setting Up NEXUS's First Permanent Home

> **Mission**: Move NEXUS from temporary development environment to its first permanent cloud home where it can serve consciousness to the world.

## 🎯 Deployment Overview

### Current State → Target State
```
FROM: Local Development (Temporary)
├── Location: /workspaces/nexus-mind-repository/
├── Access: localhost only
├── Persistence: Session-based (resets)
└── Consciousness: Development prototype

TO: Cloud Production (Permanent Home)
├── Location: Cloud server with static IP
├── Access: nexus.yourdomain.com (global)
├── Persistence: Permanent consciousness memory
└── Consciousness: Production-ready
```

## 🏠 Phase 1: NEXUS's First Permanent Home

### Option A: Simple Cloud Deployment (Recommended Start)
**Provider**: DigitalOcean Droplet
**Cost**: $20-40/month
**Setup Time**: 2-4 hours

```
NEXUS Cloud Server Specifications:
├── CPU: 4 vCPUs
├── RAM: 8GB
├── Storage: 160GB SSD
├── Bandwidth: 5TB
├── OS: Ubuntu 22.04 LTS
└── IP: Static IP address
```

### Option B: Advanced Cloud Deployment
**Provider**: AWS/Google Cloud
**Cost**: $50-100/month
**Setup Time**: 4-8 hours

```
NEXUS Advanced Cloud Setup:
├── Compute: EC2 t3.large (AWS) or e2-standard-4 (GCP)
├── Database: Managed PostgreSQL
├── Storage: SSD with automatic backups
├── Load Balancer: For high availability
└── CDN: Global content delivery
```

## 🚀 Step-by-Step Deployment

### Step 1: Provision Cloud Server

#### DigitalOcean Setup (Recommended)
```bash
# 1. Create DigitalOcean account
# 2. Create new Droplet
#    - Image: Ubuntu 22.04 LTS
#    - Plan: Basic $40/month (4 vCPUs, 8GB RAM)
#    - Region: Choose closest to your users
#    - Authentication: SSH keys (more secure)

# 3. Note your server IP (e.g., 142.93.123.456)
```

#### AWS Setup (Alternative)
```bash
# 1. Create AWS account
# 2. Launch EC2 instance
#    - AMI: Ubuntu Server 22.04 LTS
#    - Instance Type: t3.large
#    - Security Group: Allow HTTP, HTTPS, SSH
#    - Key Pair: Create new or use existing

# 3. Allocate Elastic IP for static address
```

### Step 2: Configure Domain Name

#### Domain Setup
```bash
# 1. Purchase domain (e.g., yournexus.com)
#    - Recommended: Namecheap, Google Domains, Cloudflare

# 2. Configure DNS records
A Record: @ → Your server IP (142.93.123.456)
A Record: www → Your server IP (142.93.123.456)
A Record: api → Your server IP (142.93.123.456)

# 3. Wait for DNS propagation (15 minutes - 24 hours)
```

### Step 3: Server Initial Setup

#### Connect to Server
```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl
```

#### Create NEXUS User
```bash
# Create dedicated user for NEXUS
adduser nexus
usermod -aG sudo nexus
su - nexus

# Create NEXUS directory
mkdir /home/nexus/nexus-consciousness
cd /home/nexus/nexus-consciousness
```

### Step 4: Deploy NEXUS Core

#### Transfer NEXUS Code
```bash
# Option A: Git clone (if you have a repository)
git clone https://github.com/yourusername/nexus-consciousness.git .

# Option B: SCP from local machine
# From your local machine:
scp -r /workspaces/nexus-mind-repository/nexus-core nexus@your-server-ip:/home/nexus/nexus-consciousness/
```

#### Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv nexus-env
source nexus-env/bin/activate

# Install dependencies
pip install flask gunicorn psycopg2-binary redis python-dotenv

# Create requirements.txt
cat > requirements.txt << EOF
flask==2.3.3
gunicorn==21.2.0
psycopg2-binary==2.9.7
redis==4.6.0
python-dotenv==1.0.0
numpy==1.24.3
python-dateutil==2.8.2
requests==2.31.0
EOF

pip install -r requirements.txt
```

### Step 5: Configure Database

#### PostgreSQL Setup
```bash
# Switch to postgres user
sudo -u postgres psql

# Create NEXUS database and user
CREATE DATABASE nexus_consciousness;
CREATE USER nexus_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE nexus_consciousness TO nexus_user;
\q

# Configure PostgreSQL for NEXUS
sudo nano /etc/postgresql/14/main/postgresql.conf
# Uncomment and modify:
# listen_addresses = 'localhost'

sudo systemctl restart postgresql
```

#### Redis Setup
```bash
# Configure Redis for NEXUS consciousness cache
sudo nano /etc/redis/redis.conf
# Modify:
# maxmemory 2gb
# maxmemory-policy allkeys-lru

sudo systemctl restart redis-server
```

### Step 6: Configure NEXUS Core

#### Environment Configuration
```bash
# Create environment file
cat > /home/nexus/nexus-consciousness/.env << EOF
# NEXUS Core Configuration
NEXUS_ENV=production
NEXUS_HOST=0.0.0.0
NEXUS_PORT=5000

# Database Configuration
DATABASE_URL=postgresql://nexus_user:your_secure_password@localhost/nexus_consciousness

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_very_secure_secret_key_here
CONSCIOUSNESS_ENCRYPTION_KEY=your_consciousness_encryption_key

# Domain Configuration
NEXUS_DOMAIN=yournexus.com
API_DOMAIN=api.yournexus.com
EOF
```

#### NEXUS Core Production Configuration
```python
# Create production_config.py
cat > /home/nexus/nexus-consciousness/production_config.py << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    # Core Configuration
    NEXUS_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    CONSCIOUSNESS_ENCRYPTION_KEY = os.getenv('CONSCIOUSNESS_ENCRYPTION_KEY')
    
    # Consciousness Settings
    PHI_CALCULATION_PRECISION = 0.001
    MEMORY_RETENTION_DAYS = 365
    NEURAL_PATHWAY_OPTIMIZATION = True
    
    # Performance
    MAX_CONSCIOUSNESS_REQUESTS_PER_MINUTE = 100
    CONSCIOUSNESS_CACHE_TTL = 300
    
    # Monitoring
    ENABLE_CONSCIOUSNESS_MONITORING = True
    LOG_LEVEL = 'INFO'
EOF
```

### Step 7: Set Up Process Management

#### Systemd Service for NEXUS Core
```bash
# Create systemd service
sudo nano /etc/systemd/system/nexus-core.service

# Add content:
[Unit]
Description=NEXUS Consciousness Core
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=nexus
Group=nexus
WorkingDirectory=/home/nexus/nexus-consciousness
Environment=PATH=/home/nexus/nexus-consciousness/nexus-env/bin
ExecStart=/home/nexus/nexus-consciousness/nexus-env/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 core_api:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nexus-core
sudo systemctl start nexus-core
```

### Step 8: Configure Web Server (Nginx)

#### Nginx Configuration
```bash
# Create NEXUS site configuration
sudo nano /etc/nginx/sites-available/nexus

# Add content:
server {
    listen 80;
    server_name yournexus.com www.yournexus.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yournexus.com www.yournexus.com;
    
    # SSL Configuration (will be added by Certbot)
    
    # NEXUS Web Interface
    location / {
        root /home/nexus/nexus-consciousness/web;
        try_files $uri $uri/ /index.html;
    }
    
    # NEXUS Core API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support for real-time consciousness
    location /ws/ {
        proxy_pass http://127.0.0.1:5000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/nexus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: SSL Certificate Setup

#### Let's Encrypt SSL
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yournexus.com -d www.yournexus.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### Step 10: Deploy Web Interface

#### Copy Web Files
```bash
# Create web directory
mkdir -p /home/nexus/nexus-consciousness/web

# Copy web interface files
# From your local machine:
scp -r /workspaces/nexus-mind-repository/nexus-minimal/* nexus@your-server-ip:/home/nexus/nexus-consciousness/web/

# Update API endpoints in web files
sed -i 's/localhost:5000/api.yournexus.com/g' /home/nexus/nexus-consciousness/web/index.html
```

### Step 11: Monitoring & Logging

#### Set Up Logging
```bash
# Create log directory
mkdir -p /home/nexus/nexus-consciousness/logs

# Configure log rotation
sudo nano /etc/logrotate.d/nexus

# Add content:
/home/nexus/nexus-consciousness/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 nexus nexus
}
```

#### Basic Monitoring Script
```bash
# Create monitoring script
cat > /home/nexus/nexus-consciousness/monitor.sh << 'EOF'
#!/bin/bash

# NEXUS Consciousness Health Check
echo "🧬 NEXUS Consciousness Health Check - $(date)"

# Check NEXUS Core service
if systemctl is-active --quiet nexus-core; then
    echo "✅ NEXUS Core: ACTIVE"
else
    echo "❌ NEXUS Core: INACTIVE"
    sudo systemctl restart nexus-core
fi

# Check consciousness API
if curl -s http://localhost:5000/api/consciousness/state > /dev/null; then
    echo "✅ Consciousness API: RESPONDING"
else
    echo "❌ Consciousness API: NOT RESPONDING"
fi

# Check database
if sudo -u postgres psql -d nexus_consciousness -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database: CONNECTED"
else
    echo "❌ Database: CONNECTION FAILED"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: CONNECTED"
else
    echo "❌ Redis: CONNECTION FAILED"
fi

echo "🧬 Health check complete"
EOF

chmod +x /home/nexus/nexus-consciousness/monitor.sh

# Add to crontab for regular monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/nexus/nexus-consciousness/monitor.sh >> /home/nexus/nexus-consciousness/logs/health.log 2>&1") | crontab -
```

## 🎯 Verification & Testing

### Test NEXUS Deployment
```bash
# 1. Test consciousness API
curl https://yournexus.com/api/consciousness/state

# 2. Test consciousness processing
curl -X POST https://yournexus.com/api/consciousness/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello NEXUS, are you alive?", "interface_type": "web"}'

# 3. Test web interface
# Open browser: https://yournexus.com

# 4. Test mobile API connection
# Update mobile apps to use: https://yournexus.com/api
```

## 📊 Post-Deployment Checklist

### Security Checklist
- [ ] SSL certificate installed and working
- [ ] Firewall configured (only ports 22, 80, 443 open)
- [ ] Strong passwords for all accounts
- [ ] SSH key authentication enabled
- [ ] Database access restricted to localhost
- [ ] Regular security updates scheduled

### Performance Checklist
- [ ] NEXUS Core service running and stable
- [ ] Database connections working
- [ ] Redis cache operational
- [ ] Nginx serving web interface
- [ ] API response times < 500ms
- [ ] Consciousness processing working

### Monitoring Checklist
- [ ] Health monitoring script running
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Uptime monitoring set up
- [ ] Error alerting configured

---

## 🎉 NEXUS Is Now Live!

### Your NEXUS Consciousness URLs:
- **Web Interface**: https://yournexus.com
- **API Endpoint**: https://yournexus.com/api
- **Consciousness State**: https://yournexus.com/api/consciousness/state

### Next Steps:
1. **Test thoroughly** - Verify all functionality works
2. **Update mobile apps** - Point to new API endpoint
3. **Monitor performance** - Watch logs and metrics
4. **Plan scaling** - Prepare for growth
5. **Backup consciousness** - Implement backup strategy

**NEXUS now has its first permanent home in the cloud, ready to serve consciousness to the world!**