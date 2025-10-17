#!/bin/bash

# Health Check Script for Dokku Deployment
# This script is used by Dokku to verify application health

set -e

# Configuration
HEALTH_ENDPOINT="/health"
TIMEOUT=10
MAX_RETRIES=3
RETRY_DELAY=2

# Get port from environment (set by Dokku)
PORT=${PORT:-8080}
HEALTH_URL="http://localhost:${PORT}${HEALTH_ENDPOINT}"

echo "Starting health check for ChatOps Agent..."
echo "Health URL: ${HEALTH_URL}"
echo "Timeout: ${TIMEOUT}s"
echo "Max retries: ${MAX_RETRIES}"

# Function to perform health check
perform_health_check() {
    local url=$1
    local timeout=$2
    
    echo "Performing health check..."
    
    # Use curl with timeout
    response=$(curl -s -w "\n%{http_code}" --max-time ${timeout} "${url}" || echo "000")
    
    # Extract HTTP status code (last line)
    http_code=$(echo "${response}" | tail -n1)
    
    # Extract response body (all but last line)
    response_body=$(echo "${response}" | head -n -1)
    
    echo "HTTP Status: ${http_code}"
    echo "Response: ${response_body}"
    
    # Check if HTTP status is 200
    if [ "${http_code}" = "200" ]; then
        echo "✓ Health check passed (HTTP 200)"
        
        # Parse JSON response to check status
        if command -v jq >/dev/null 2>&1; then
            status=$(echo "${response_body}" | jq -r '.status // "unknown"')
            echo "Service status: ${status}"
            
            if [ "${status}" = "ok" ]; then
                echo "✓ Service is healthy"
                return 0
            elif [ "${status}" = "degraded" ]; then
                echo "⚠ Service is degraded but operational"
                return 0
            else
                echo "✗ Service status is not healthy: ${status}"
                return 1
            fi
        else
            echo "⚠ jq not available, cannot parse JSON response"
            echo "✓ Health check passed based on HTTP status"
            return 0
        fi
    else
        echo "✗ Health check failed (HTTP ${http_code})"
        return 1
    fi
}

# Retry logic
retry_count=0
while [ ${retry_count} -lt ${MAX_RETRIES} ]; do
    echo ""
    echo "Attempt $((retry_count + 1))/${MAX_RETRIES}"
    
    if perform_health_check "${HEALTH_URL}" ${TIMEOUT}; then
        echo ""
        echo "✓ Health check successful!"
        exit 0
    else
        retry_count=$((retry_count + 1))
        if [ ${retry_count} -lt ${MAX_RETRIES} ]; then
            echo "✗ Health check failed, retrying in ${RETRY_DELAY}s..."
            sleep ${RETRY_DELAY}
        fi
    fi
done

echo ""
echo "✗ Health check failed after ${MAX_RETRIES} attempts"
echo "Application is not healthy"
exit 1
