# Deployment Guide - Digital Ocean

## Overview

This guide covers deploying the AI Mock Interview System API to Digital Ocean using Docker and PostgreSQL.

---

## Prerequisites

1. Digital Ocean account
2. `doctl` CLI installed
3. Docker installed locally
4. OpenAI API key

---

## Option 1: Digital Ocean App Platform (Recommended)

### Step 1: Prepare Database

```bash
# Create managed PostgreSQL database on Digital Ocean
# Via DO dashboard:
# 1. Create > Databases > PostgreSQL 16
# 2. Select region and plan ($15/month minimum)
# 3. Note connection string
```

### Step 2: Configure Environment

Create `.env.production`:
```env
DATABASE_URL=postgresql://user:pass@host:25060/db?sslmode=require
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o
LOG_LEVEL=INFO
WORKERS=2
```

### Step 3: Deploy via App Platform

```bash
# Option A: Deploy from GitHub
# 1. Connect GitHub repo in DO App Platform
# 2. Select: final-round-assignment
# 3. Auto-detect: Python/Docker
# 4. Add environment variables from .env.production
# 5. Deploy

# Option B: Deploy via doctl
doctl apps create --spec .do/app.yaml
```

### Step 4: Run Migrations

```bash
# SSH into app or run via console
docker exec -it <container-id> alembic upgrade head
```

---

## Option 2: Digital Ocean Droplet (Full Control)

### Step 1: Create Droplet

```bash
# Create droplet (Ubuntu 22.04, min 2GB RAM)
doctl compute droplet create interview-api \
  --region nyc1 \
  --size s-2vcpu-2gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys <your-ssh-key-id>
```

### Step 2: Setup Server

```bash
# SSH into droplet
ssh root@<droplet-ip>

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install docker-compose-plugin

# Clone repository
git clone https://github.com/Atharva-Kanherkar/final-round-assignment.git
cd final-round-assignment
```

### Step 3: Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env with production values
nano .env

# Add:
DATABASE_URL=postgresql://interview_user:interview_password@db:5432/interview_db
OPENAI_API_KEY=sk-your-actual-key
MODEL_NAME=gpt-4o
LOG_LEVEL=INFO
```

### Step 4: Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head
```

### Step 5: Configure Firewall

```bash
# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # API port

# Enable firewall
ufw enable
```

### Step 6: Setup Nginx (Optional)

```bash
# Install Nginx
apt-get install nginx

# Configure reverse proxy
cat > /etc/nginx/sites-available/interview-api << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/interview-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## Option 3: Docker Registry (For DO App Platform)

### Step 1: Build and Push Docker Image

```bash
# Login to Digital Ocean Container Registry
doctl registry login

# Create registry
doctl registry create interview-api

# Build image
docker build -t registry.digitalocean.com/interview-api/backend:latest .

# Push image
docker push registry.digitalocean.com/interview-api/backend:latest
```

### Step 2: Deploy via App Spec

Create `.do/app.yaml`:
```yaml
name: interview-api
region: nyc

databases:
  - name: interview-db
    engine: PG
    version: "16"
    size: db-s-1vcpu-1gb

services:
  - name: api
    image:
      registry_type: DOCR
      repository: interview-api/backend
      tag: latest
    instance_count: 1
    instance_size_slug: professional-xs
    http_port: 8000
    health_check:
      http_path: /api/ping
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        type: SECRET
      - key: OPENAI_API_KEY
        scope: RUN_TIME
        type: SECRET
      - key: MODEL_NAME
        value: gpt-4o
      - key: LOG_LEVEL
        value: INFO
```

Deploy:
```bash
doctl apps create --spec .do/app.yaml
```

---

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key

### Optional
- `MODEL_NAME` (default: gpt-4)
- `LOG_LEVEL` (default: INFO)
- `WORKERS` (default: 1)
- `MAX_RETRIES` (default: 3)
- `TIMEOUT_SECONDS` (default: 30)

---

## Post-Deployment

### 1. Run Database Migrations

```bash
# Via docker-compose
docker-compose exec api alembic upgrade head

# Via DO console
# Use console terminal to run: alembic upgrade head
```

### 2. Test API

```bash
# Health check
curl https://your-app.ondigitalocean.app/api/ping

# Create session
curl -X POST https://your-app.ondigitalocean.app/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "...",
    "job_description_text": "..."
  }'
```

### 3. Monitor

```bash
# View logs
docker-compose logs -f api

# Check database
docker-compose exec db psql -U interview_user -d interview_db

# Check API health
curl https://your-app.ondigitalocean.app/api/health
```

---

## Costs

### Digital Ocean Pricing (Monthly)

**Option 1: App Platform**
- Database: $15/month (1GB RAM, 10GB storage)
- App: $12/month (1GB RAM, 1vCPU)
- **Total**: ~$27/month

**Option 2: Droplet + Managed DB**
- Droplet: $12/month (2GB RAM)
- Database: $15/month
- **Total**: ~$27/month

**Option 3: Droplet Only (DB in same container)**
- Droplet: $18/month (4GB RAM)
- **Total**: ~$18/month

---

## Scaling

### Horizontal Scaling

```yaml
# In .do/app.yaml
services:
  - name: api
    instance_count: 3  # Multiple instances
    autoscaling:
      min_instance_count: 2
      max_instance_count: 5
```

### Database Scaling

```bash
# Upgrade database size via DO dashboard
# Or use connection pooling in app
```

---

## Monitoring

### Logs

```bash
# Application logs
docker-compose logs -f api

# Database logs
docker-compose logs -f db

# System logs (on droplet)
journalctl -u docker -f
```

### Metrics

```bash
# DO App Platform dashboard shows:
# - CPU usage
# - Memory usage
# - Request count
# - Response times
```

---

## Troubleshooting

**Issue**: Database connection failed

**Solution**:
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
docker-compose exec api python -c "from api.database import engine; engine.connect()"
```

**Issue**: Migrations fail

**Solution**:
```bash
# Check alembic status
docker-compose exec api alembic current

# Reset and retry
docker-compose exec api alembic downgrade base
docker-compose exec api alembic upgrade head
```

**Issue**: API not accessible

**Solution**:
```bash
# Check if running
docker-compose ps

# Check logs
docker-compose logs api

# Restart
docker-compose restart api
```

---

## Security Checklist

- [ ] OPENAI_API_KEY stored as secret (not in code)
- [ ] DATABASE_URL with SSL mode enabled
- [ ] CORS configured for specific origins only
- [ ] Firewall configured (ports 80, 443 only)
- [ ] Regular security updates scheduled
- [ ] Database backups enabled
- [ ] Logs monitored for errors

---

## Quick Deploy Commands

```bash
# Local development
docker-compose up -d
docker-compose exec api alembic upgrade head

# Digital Ocean App Platform
doctl apps create --spec .do/app.yaml

# Digital Ocean Droplet
# 1. SSH into droplet
# 2. Clone repo
# 3. docker-compose up -d
# 4. docker-compose exec api alembic upgrade head
```

---

## API Endpoints

### Health
- `GET /api/ping` - Simple ping
- `GET /api/health` - Health check with DB status

### Sessions
- `POST /api/sessions` - Create new interview session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Delete session
- `POST /api/sessions/{id}/respond` - Submit response
- `POST /api/sessions/{id}/complete` - Complete interview
- `GET /api/sessions/{id}/messages` - Get conversation
- `GET /api/sessions/{id}/evaluations` - Get evaluations
- `WS /api/ws/interview/{id}` - Real-time interview WebSocket

### Documentation
- `GET /api/docs` - Swagger UI
- `GET /api/redoc` - ReDoc documentation

---

**System is production-ready for Digital Ocean deployment.**
