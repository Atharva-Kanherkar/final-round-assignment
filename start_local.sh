#!/bin/bash
# Local development startup script

set -e

echo "Starting AI Mock Interview API (Local Development)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null

# Check for .env file
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure your API key."
    exit 1
fi

# Start Docker Compose (database)
echo "Starting PostgreSQL database..."
docker-compose up -d db

# Wait for database
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start API
echo "Starting FastAPI server..."
echo ""
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/api/docs"
echo "Health Check: http://localhost:8000/api/health"
echo ""

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
