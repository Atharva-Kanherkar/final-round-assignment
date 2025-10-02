# FastAPI Backend - Quick Start

## What Was Built

A production-ready FastAPI backend with:
- RESTful API endpoints
- WebSocket support for real-time interviews
- PostgreSQL database integration
- Docker deployment configuration
- Digital Ocean deployment ready

---

## Quick Start (Local Development)

### Option 1: Automated Script

```bash
./start_local.sh
```

This will:
1. Create virtual environment
2. Install dependencies
3. Start PostgreSQL in Docker
4. Run database migrations
5. Start FastAPI server

### Option 2: Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start database
docker-compose up -d db

# 3. Run migrations
alembic upgrade head

# 4. Start API
uvicorn api.main:app --reload --port 8000
```

**API will be at**: `http://localhost:8000`
**Docs**: `http://localhost:8000/api/docs`

---

## API Endpoints

### Session Management

```bash
# Create new interview session
POST /api/sessions
Body: {
  "resume_text": "...",
  "job_description_text": "..."
}

# List all sessions
GET /api/sessions?limit=50&offset=0

# Get session details
GET /api/sessions/{session_id}

# Delete session
DELETE /api/sessions/{session_id}
```

### Interview Interaction

```bash
# Submit response and get evaluation
POST /api/sessions/{session_id}/respond
Body: {
  "response": "My answer to the question..."
}

# Complete interview and get final report
POST /api/sessions/{session_id}/complete

# Get conversation history
GET /api/sessions/{session_id}/messages

# Get all evaluations
GET /api/sessions/{session_id}/evaluations
```

### WebSocket (Real-time)

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/ws/interview/{session_id}');

// Receive messages
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // msg.type: "question" | "evaluation" | "status" | "complete" | "error"
};

// Send response
ws.send(JSON.stringify({
  type: "response",
  data: { response: "My answer..." }
}));
```

### Health Check

```bash
GET /api/ping
GET /api/health
```

---

## Deploy to Digital Ocean

### Quick Deploy

```bash
# 1. Ensure you have doctl installed and authenticated
doctl auth init

# 2. Create app from spec
doctl apps create --spec .do/app.yaml

# 3. Set OPENAI_API_KEY secret via dashboard
# Go to: Apps > Settings > Environment Variables
# Add: OPENAI_API_KEY = sk-your-key

# 4. Trigger deployment
doctl apps create-deployment <app-id>
```

### Manual Deploy (Droplet)

```bash
# 1. Create droplet
doctl compute droplet create interview-api \
  --region nyc1 \
  --size s-2vcpu-2gb \
  --image ubuntu-22-04-x64

# 2. SSH and setup
ssh root@<droplet-ip>
git clone <your-repo>
cd final-round-assignment

# 3. Configure and start
cp .env.example .env
# Edit .env with DATABASE_URL and OPENAI_API_KEY
docker-compose up -d

# 4. Run migrations
docker-compose exec api alembic upgrade head
```

**Your API will be at**: `http://<droplet-ip>:8000`

---

## Testing the API

### Run API Tests

```bash
pytest api/tests/ -v
```

### Manual Testing

```bash
# 1. Start API locally
./start_local.sh

# 2. In another terminal, test endpoints:

# Health check
curl http://localhost:8000/api/ping

# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "resume_text": "John Doe\nSoftware Engineer\n5 years experience\nSkills: Python, AWS, Docker\nEducation: BS Computer Science\nExperience:\n- TechCorp (2020-2023): Backend development\n- StartupXYZ (2018-2020): Full-stack development",
  "job_description_text": "Senior Backend Engineer\nCompany: TechCo\nRequirements:\n- 5+ years Python\n- AWS experience\n- System design\nResponsibilities:\n- Design scalable systems\n- Lead technical initiatives"
}
EOF

# Get sessions
curl http://localhost:8000/api/sessions

# Submit response
curl -X POST http://localhost:8000/api/sessions/<session-id>/respond \
  -H "Content-Type: application/json" \
  -d '{"response": "Python is a high-level programming language..."}'
```

---

## Database

### Access Database

```bash
# Via docker-compose
docker-compose exec db psql -U interview_user -d interview_db

# Check tables
\dt

# Query sessions
SELECT id, candidate_name, job_title, status FROM sessions;
```

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current
```

---

## File Structure

```
api/
├── main.py                     # FastAPI application
├── database.py                 # Database configuration
├── schemas.py                  # Pydantic models
├── models/
│   └── db_models.py           # SQLAlchemy models
├── routers/
│   ├── health.py              # Health check endpoints
│   └── sessions.py            # Interview endpoints
├── services/
│   └── interview_service.py   # Business logic layer
└── tests/
    └── test_api.py            # API tests

Deployment:
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Local development
├── alembic.ini                 # Migration config
├── alembic/                    # Migration scripts
├── .do/
│   └── app.yaml               # Digital Ocean spec
└── start_local.sh              # Local startup script
```

---

## What's Different from CLI Version

**CLI Version** (existing):
- Interactive terminal interface
- File-based session storage
- Direct Python execution

**API Version** (new):
- HTTP REST endpoints
- WebSocket for real-time
- PostgreSQL database
- Docker deployment
- Horizontal scaling ready

**Both use the same agent system** - No duplication!

---

## Production Checklist

- [x] FastAPI application created
- [x] Database models with SQLAlchemy
- [x] API endpoints for all operations
- [x] WebSocket for real-time interviews
- [x] Error handling and validation
- [x] Docker configuration
- [x] Database migrations (Alembic)
- [x] Digital Ocean deployment spec
- [x] Health check endpoints
- [x] API tests
- [x] Documentation

---

**System is ready to deploy on Digital Ocean!**

**Estimated Deployment Time**: 15-20 minutes
**Monthly Cost**: ~$27 (App Platform) or ~$18 (single Droplet)
