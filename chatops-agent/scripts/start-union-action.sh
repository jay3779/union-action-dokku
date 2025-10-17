#!/bin/bash

# Union Action API Startup Script
# Starts the Union Action API service within the container

set -e

echo "Starting Union Action API service..."

# Change to union-action directory
cd /app/union-action

# Install Union Action API dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for Union Action API..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Activating existing virtual environment..."
    source venv/bin/activate
fi

# Set environment variables for Union Action API
export PYTHONPATH="/app/union-action:$PYTHONPATH"
export UNION_ACTION_PORT=${UNION_ACTION_PORT:-8000}
export UNION_ACTION_HOST=${UNION_ACTION_HOST:-0.0.0.0}

echo "Starting Union Action API on ${UNION_ACTION_HOST}:${UNION_ACTION_PORT}..."

# Start the Union Action API service
exec uvicorn xsrc.main:app --host ${UNION_ACTION_HOST} --port ${UNION_ACTION_PORT}
