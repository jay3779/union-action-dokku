#!/bin/bash

# Process Manager for Bundled Services
# Manages both ChatOps Agent and Union Action API processes

set -e

# Configuration
CHATOPS_AGENT_PORT=${PORT:-8080}
UNION_ACTION_PORT=${UNION_ACTION_PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-INFO}
ENVIRONMENT=${ENVIRONMENT:-production}

# Process IDs
CHATOPS_AGENT_PID=""
UNION_ACTION_PID=""

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Signal handler for graceful shutdown
cleanup() {
    log "Received shutdown signal, stopping services..."
    
    if [ -n "$CHATOPS_AGENT_PID" ]; then
        log "Stopping ChatOps Agent (PID: $CHATOPS_AGENT_PID)"
        kill -TERM "$CHATOPS_AGENT_PID" 2>/dev/null || true
        wait "$CHATOPS_AGENT_PID" 2>/dev/null || true
    fi
    
    if [ -n "$UNION_ACTION_PID" ]; then
        log "Stopping Union Action API (PID: $UNION_ACTION_PID)"
        kill -TERM "$UNION_ACTION_PID" 2>/dev/null || true
        wait "$UNION_ACTION_PID" 2>/dev/null || true
    fi
    
    log "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start Union Action API
start_union_action_api() {
    log "Starting Union Action API on port $UNION_ACTION_PORT"
    
    # Set environment variables for Union Action API
    export INTERNAL_COMMUNICATION=true
    export CHATOPS_AGENT_URL="http://localhost:$CHATOPS_AGENT_PORT"
    export UNION_ACTION_HOST=0.0.0.0
    export UNION_ACTION_PORT=$UNION_ACTION_PORT
    export UNION_ACTION_LOG_LEVEL=$LOG_LEVEL
    export UNION_ACTION_LOG_FORMAT=json
    
    # Start Union Action API in background
    cd /app/union-action
    /app/union-action/scripts/start.sh &
    UNION_ACTION_PID=$!
    
    log "Union Action API started with PID: $UNION_ACTION_PID"
    
    # Wait for Union Action API to be ready
    log "Waiting for Union Action API to be ready..."
    for i in {1..30}; do
        if curl -s -f "http://localhost:$UNION_ACTION_PORT/health" > /dev/null 2>&1; then
            log "Union Action API is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log "Warning: Union Action API did not start within 30 seconds"
        fi
        sleep 1
    done
}

# Start ChatOps Agent
start_chatops_agent() {
    log "Starting ChatOps Agent on port $CHATOPS_AGENT_PORT"
    
    # Set environment variables for ChatOps Agent
    export UNION_ACTION_API_URL="http://localhost:$UNION_ACTION_PORT"
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    
    # Start ChatOps Agent
    cd /app
    uvicorn src.main:app --host 0.0.0.0 --port $CHATOPS_AGENT_PORT &
    CHATOPS_AGENT_PID=$!
    
    log "ChatOps Agent started with PID: $CHATOPS_AGENT_PID"
}

# Health check function
health_check() {
    local chatops_healthy=false
    local union_action_healthy=false
    
    # Check ChatOps Agent health
    if curl -s -f "http://localhost:$CHATOPS_AGENT_PORT/health" > /dev/null 2>&1; then
        chatops_healthy=true
    fi
    
    # Check Union Action API health
    if curl -s -f "http://localhost:$UNION_ACTION_PORT/health" > /dev/null 2>&1; then
        union_action_healthy=true
    fi
    
    if [ "$chatops_healthy" = true ] && [ "$union_action_healthy" = true ]; then
        return 0
    else
        return 1
    fi
}

# Monitor processes
monitor_processes() {
    log "Starting process monitoring..."
    
    while true; do
        # Check if ChatOps Agent is still running
        if [ -n "$CHATOPS_AGENT_PID" ] && ! kill -0 "$CHATOPS_AGENT_PID" 2>/dev/null; then
            log "ChatOps Agent process died, restarting..."
            start_chatops_agent
        fi
        
        # Check if Union Action API is still running
        if [ -n "$UNION_ACTION_PID" ] && ! kill -0 "$UNION_ACTION_PID" 2>/dev/null; then
            log "Union Action API process died, restarting..."
            start_union_action_api
        fi
        
        # Perform health check
        if ! health_check; then
            log "Health check failed, services may be unhealthy"
        fi
        
        sleep 10
    done
}

# Main execution
main() {
    log "Starting bundled services process manager"
    log "Environment: $ENVIRONMENT"
    log "Log Level: $LOG_LEVEL"
    log "ChatOps Agent Port: $CHATOPS_AGENT_PORT"
    log "Union Action API Port: $UNION_ACTION_PORT"
    
    # Start Union Action API first
    start_union_action_api
    
    # Start ChatOps Agent
    start_chatops_agent
    
    # Wait for both services to be ready
    log "Waiting for services to be ready..."
    for i in {1..60}; do
        if health_check; then
            log "All services are ready and healthy"
            break
        fi
        if [ $i -eq 60 ]; then
            log "Warning: Services did not become healthy within 60 seconds"
        fi
        sleep 1
    done
    
    # Start monitoring
    monitor_processes
}

# Run main function
main "$@"
