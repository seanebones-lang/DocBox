# DocBox Healthcare System - Complete Deployment Guide

**Version**: 1.0.0  
**Date**: October 20, 2025  
**Status**: Production Ready

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start Deployment](#quick-start-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Security Configuration](#security-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup & Recovery](#backup-recovery)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 16 GB
- **Storage**: 100 GB SSD
- **OS**: Linux (Ubuntu 22.04 LTS recommended), macOS, or Windows with WSL2

### Recommended Production Requirements
- **CPU**: 8+ cores
- **RAM**: 32+ GB
- **Storage**: 500+ GB SSD
- **OS**: Ubuntu 22.04 LTS or RHEL 8+
- **Network**: 1 Gbps connection

### Software Requirements
- Docker 24.0+
- Docker Compose 2.20+
- Git 2.40+
- OpenSSL 3.0+

---

## Quick Start Deployment

### 1. Clone Repository
```bash
git clone https://github.com/seanebones-lang/DocBox.git
cd DocBox
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

**Required Environment Variables**:
```bash
# Application
APP_NAME=DocBox
APP_ENV=production
SECRET_KEY=<generate-secure-random-key>

# Database
DATABASE_URL=postgresql://docbox:securepassword@postgres:5432/docbox
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=securepassword
REDIS_URL=redis://redis:6379

# API Keys (for AI features)
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Security
JWT_SECRET_KEY=<generate-secure-jwt-key>
ENCRYPTION_KEY=<generate-32-byte-key>

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Generate Secure Keys
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (32 bytes, base64 encoded)
python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

### 4. Start Services
```bash
# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps
```

### 5. Initialize Databases
```bash
# Make script executable
chmod +x scripts/init-databases.sh

# Run initialization
./scripts/init-databases.sh
```

### 6. Verify Deployment
```bash
# Check API health
curl http://localhost:8000/health

# Check Web App
curl http://localhost:3000

# Check Kiosk
curl http://localhost:3001
```

### 7. Access Applications
- **API Documentation**: http://localhost:8000/docs
- **Web Application**: http://localhost:3000
- **Kiosk Application**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3030

---

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] Domain names configured (api.yourdomain.com, app.yourdomain.com)
- [ ] SSL/TLS certificates obtained
- [ ] Database backups configured
- [ ] Monitoring tools set up
- [ ] Security hardening complete
- [ ] Load balancer configured
- [ ] DNS records updated
- [ ] Firewall rules configured

### 2. SSL/TLS Configuration

#### Option A: Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d api.yourdomain.com -d app.yourdomain.com
```

#### Option B: Using Custom Certificates
```bash
# Place your certificates in:
# - /etc/ssl/certs/yourdomain.crt
# - /etc/ssl/private/yourdomain.key
```

### 3. Production Environment Variables
```bash
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security
ALLOWED_HOSTS=api.yourdomain.com,app.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com,https://kiosk.yourdomain.com

# Database (Use strong passwords!)
DATABASE_URL=postgresql://docbox:STRONG_PASSWORD@db.internal:5432/docbox

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@yourdomain.com
SMTP_PASSWORD=your-email-password
```

### 4. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/docbox`:
```nginx
# API Backend
upstream backend {
    server localhost:8000;
}

# Web Application
upstream webapp {
    server localhost:3000;
}

# Kiosk Application
upstream kiosk {
    server localhost:3001;
}

# API Server
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Web Application
server {
    listen 80;
    server_name app.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/app.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://webapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/docbox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# Block direct access to application ports from outside
sudo ufw deny 8000/tcp
sudo ufw deny 3000/tcp
sudo ufw deny 3001/tcp
```

### 6. Production Docker Compose
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    environment:
      - APP_ENV=production
      - DEBUG=false

  web-app:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  kiosk-app:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  postgres:
    restart: always
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 8G

  neo4j:
    restart: always
    volumes:
      - /var/lib/neo4j/data:/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

Deploy:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Database Setup

### PostgreSQL Initialization
```bash
# Access PostgreSQL container
docker-compose exec postgres psql -U docbox

# Verify tables
\dt

# Check migrations
SELECT * FROM alembic_version;
```

### Run Migrations
```bash
# Access backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Verify
alembic current
```

### Create Initial Admin User
```bash
# Access backend container
docker-compose exec backend python

# In Python shell:
from models.user import User, UserRole
from database.postgres import async_session_maker
from security.auth import get_password_hash
import asyncio
from uuid import uuid4

async def create_admin():
    async with async_session_maker() as session:
        admin = User(
            id=uuid4(),
            email="admin@yourdomain.com",
            hashed_password=get_password_hash("CHANGE_THIS_PASSWORD"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        session.add(admin)
        await session.commit()
        print("Admin user created!")

asyncio.run(create_admin())
```

### Backup Configuration
```bash
# Create backup script
cat > /usr/local/bin/docbox-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/docbox"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U docbox docbox | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Neo4j backup
docker-compose exec -T neo4j neo4j-admin backup --backup-dir=/backups --name=neo4j_$DATE

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/docbox-backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/docbox-backup.sh" | crontab -
```

---

## Security Configuration

### 1. Secure PostgreSQL
```sql
-- Restrict permissions
REVOKE ALL ON DATABASE docbox FROM PUBLIC;
GRANT CONNECT ON DATABASE docbox TO docbox;

-- Enable row-level security for patient data
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

### 2. Secure Redis
```bash
# Edit redis.conf
requirepass your-strong-redis-password
bind 127.0.0.1
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 3. Enable HTTPS Only
```python
# In backend/config.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 4. Rate Limiting
```python
# Already configured in backend/main.py
# Adjust limits in production:
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000
```

---

## Monitoring Setup

### Prometheus Configuration
Metrics available at: `http://localhost:9090`

Key metrics to monitor:
- `http_requests_total` - Total API requests
- `http_request_duration_seconds` - Request latency
- `database_connections_active` - DB connections
- `appointment_checkins_total` - Check-in operations

### Grafana Dashboards
Access at: `http://localhost:3030`

Default credentials:
- Username: `admin`
- Password: `admin` (change immediately)

Import dashboard:
```bash
# Use provided dashboard JSON in monitoring/grafana-dashboard.json
```

### Log Management
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f web-app

# Export logs to file
docker-compose logs > /var/log/docbox/app.log
```

---

## Backup & Recovery

### Automated Backups
```bash
# Daily backups (already configured above)
/usr/local/bin/docbox-backup.sh
```

### Manual Backup
```bash
# PostgreSQL
docker-compose exec postgres pg_dump -U docbox docbox > backup.sql

# Neo4j
docker-compose exec neo4j neo4j-admin backup --backup-dir=/backups

# Application files
tar -czf docbox-app-backup.tar.gz backend/ web-app/ kiosk-app/
```

### Restore from Backup
```bash
# Stop services
docker-compose down

# Restore PostgreSQL
cat backup.sql | docker-compose exec -T postgres psql -U docbox docbox

# Restore Neo4j
docker-compose exec neo4j neo4j-admin restore --from=/backups/neo4j_backup

# Start services
docker-compose up -d
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs backend

# Verify configuration
docker-compose config

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
docker-compose exec postgres pg_isready -U docbox

# Check credentials
echo $DATABASE_URL

# Verify network
docker-compose exec backend ping postgres
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Optimize database
docker-compose exec postgres psql -U docbox -c "VACUUM ANALYZE;"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### HIPAA Audit Log Issues
```bash
# Verify audit logging
docker-compose exec backend python -c "from security.audit import audit_logger; print('Audit logging active')"

# Check audit log table
docker-compose exec postgres psql -U docbox -c "SELECT COUNT(*) FROM audit_logs;"
```

---

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 4
  
  web-app:
    deploy:
      replicas: 2
```

Deploy:
```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### Load Balancing
Use Nginx upstream:
```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
    server backend4:8000;
}
```

---

## Health Checks

### Automated Health Monitoring
```bash
# Create health check script
cat > /usr/local/bin/docbox-health.sh << 'EOF'
#!/bin/bash

# Check API
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "API health check failed"
    # Send alert
    exit 1
fi

# Check Web App
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Web app health check failed"
    exit 1
fi

echo "All services healthy"
EOF

chmod +x /usr/local/bin/docbox-health.sh

# Run every 5 minutes
echo "*/5 * * * * /usr/local/bin/docbox-health.sh" | crontab -
```

---

## Support

**Documentation**: See all `.md` files in repository root  
**Issues**: https://github.com/seanebones-lang/DocBox/issues  
**License**: MIT  

---

**END OF DEPLOYMENT GUIDE**

*System Version: 1.0.0*  
*Last Updated: October 20, 2025*  
*Status: Production Ready ✅*

