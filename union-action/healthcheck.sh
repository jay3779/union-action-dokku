#!/bin/bash

# Health check script for multi-process container
# Verifies both union-action API and chatops-agent processes are running

set -e

# Check if union-action API is responding
API_HEALTH_URL="http://localhost:8000/health"
if ! curl -f -s "$API_HEALTH_URL" > /dev/null; then
    echo "ERROR: Union-action API health check failed"
    exit 1
fi

# Check if supervisord is managing both processes
if ! pgrep -f "uvicorn xsrc.main:app" > /dev/null; then
    echo "ERROR: Union-action API process not running"
    exit 1
fi

if ! pgrep -f "python -m chatops-agent.main" > /dev/null; then
    echo "ERROR: Chatops-agent process not running"
    exit 1
fi

# Check if supervisord is running
if ! pgrep supervisord > /dev/null; then
    echo "ERROR: Supervisord process manager not running"
    exit 1
fi

echo "SUCCESS: All processes are healthy"
exit 0
