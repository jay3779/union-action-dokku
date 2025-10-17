#!/bin/bash

# Union Action API Startup Script
# Starts the Union Action API service for bundled deployment

set -e

echo "Starting Union Action API service..."

# Set environment variables for bundled deployment
export INTERNAL_COMMUNICATION=true
export CHATOPS_AGENT_URL=http://localhost:8080
export UNION_ACTION_HOST=${UNION_ACTION_HOST:-0.0.0.0}
export UNION_ACTION_PORT=${UNION_ACTION_PORT:-8000}
export UNION_ACTION_LOG_LEVEL=${UNION_ACTION_LOG_LEVEL:-${LOG_LEVEL:-INFO}}
export UNION_ACTION_LOG_FORMAT=${UNION_ACTION_LOG_FORMAT:-${LOG_FORMAT:-json}}

# Set Python path to include union-action modules
export PYTHONPATH="/app/union-action:$PYTHONPATH"

# Change to union-action directory
cd /app/union-action

echo "Union Action API Configuration:"
echo "  Host: ${UNION_ACTION_HOST}"
echo "  Port: ${UNION_ACTION_PORT}"
echo "  Log Level: ${UNION_ACTION_LOG_LEVEL}"
echo "  Log Format: ${UNION_ACTION_LOG_FORMAT}"
echo "  Internal Communication: ${INTERNAL_COMMUNICATION}"
echo "  ChatOps Agent URL: ${CHATOPS_AGENT_URL}"
echo "  Python Path: ${PYTHONPATH}"

# Install dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for Union Action API..."
    python -m venv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt
else
    echo "Activating existing virtual environment..."
    source venv/bin/activate
fi

# Verify Union Action API dependencies
echo "Verifying Union Action API dependencies..."
python -c "import fastapi, uvicorn, pydantic, structlog, httpx; print('All dependencies available')"

# Start the Union Action API service
echo "Starting Union Action API on ${UNION_ACTION_HOST}:${UNION_ACTION_PORT..."
exec uvicorn xsrc.main:app --host ${UNION_ACTION_HOST} --port ${UNION_ACTION_PORT} --log-level ${UNION_ACTION_LOG_LEVEL,,}
