# WhatsApp ChatOps Agent - Render Deployment Guide

**Deploy and debug the WhatsApp ChatOps Agent on Render with MCP integration.**

**Last Updated**: October 13, 2025

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deploy](#quick-deploy)
- [Configuration](#configuration)
- [MCP Integration for Production Debugging](#mcp-integration-for-production-debugging)
- [Monitoring on Render](#monitoring-on-render)
- [Debugging Production Issues](#debugging-production-issues)
- [Zero-Downtime Deployments](#zero-downtime-deployments)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Render account (free or paid)
- GitHub repository with your code
- Union Action API deployed (or URL available)
- Render MCP configured in Cursor (optional, for production debugging)

---

## Quick Deploy

### Option 1: Deploy via Render Dashboard

1. **Connect Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the repository and branch

2. **Configure Service**
   ```
   Name: whatsapp-chatops-agent
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables**
   ```
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   LOG_SAMPLE_RATE=0.1
   UNION_ACTION_API_URL=https://your-union-api.onrender.com
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (2-5 minutes)

### Option 2: Deploy via Blueprint (Recommended)

The included `render.yaml` provides infrastructure-as-code deployment:

1. **Push to GitHub**
   ```bash
   git add render.yaml
   git commit -m "Add Render blueprint"
   git push origin main
   ```

2. **Deploy from Blueprint**
   - Go to Render Dashboard → "Blueprints"
   - Click "New Blueprint Instance"
   - Connect repository
   - Review configuration
   - Click "Apply"

3. **Set Secret Environment Variables**
   - After deployment, go to service settings
   - Add `UNION_ACTION_API_URL` (not in blueprint for security)

### Option 3: Deploy via Render MCP (from Cursor)

With Render MCP configured, deploy directly from Cursor:

```python
# In Cursor chat, use MCP tools:
# 1. List services
mcp_render_list_services()

# 2. Create service (if new)
mcp_render_create_web_service(
    name="whatsapp-chatops-agent",
    runtime="python",
    buildCommand="pip install -r requirements.txt",
    startCommand="uvicorn src.main:app --host 0.0.0.0 --port $PORT",
    repo="https://github.com/your-org/whatsapp-chatops-union",
    branch="main",
    envVars=[
        {"key": "ENVIRONMENT", "value": "production"},
        {"key": "LOG_LEVEL", "value": "INFO"}
    ]
)

# 3. Check deployment status
mcp_render_get_service(serviceId="srv-xxx")
mcp_render_list_deploys(serviceId="srv-xxx")
```

---

## Configuration

### Required Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `ENVIRONMENT` | `production` | Enables production mode (JSON logs, sampling) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `UNION_ACTION_API_URL` | `https://...` | Union Action API endpoint |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_SAMPLE_RATE` | `0.1` | Sample 10% of info/debug logs |
| `MAX_NARRATIVE_LENGTH` | `2000` | Max narrative characters |
| `MAX_MAXIM_LENGTH` | `500` | Max maxim characters |
| `SLOW_OPERATION_THRESHOLD_MS` | `2000` | Slow operation warning threshold |

### Health Check Configuration

Render automatically configures health checks using `/health`:
- **Path**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Healthy Threshold**: 2 consecutive successes
- **Unhealthy Threshold**: 3 consecutive failures

---

## MCP Integration for Production Debugging

Render MCP enables **rapid debugging and iteration in live production** directly from Cursor.

### Setup Render MCP

1. **Get Render API Key**
   - Go to [Render Account Settings](https://dashboard.render.com/account/api-keys)
   - Create API key
   - Copy key

2. **Configure MCP in Cursor**
   
   In `~/.cursor/mcp.json` (or your MCP config):
   ```json
   {
     "mcpServers": {
       "render": {
         "url": "https://mcp.render.com/mcp",
         "headers": {
           "Authorization": "Bearer YOUR_RENDER_API_KEY"
         }
       }
     }
   }
   ```

3. **Restart Cursor** to load MCP configuration

### Production Debugging Workflow

#### 1. Check Service Health

```python
# In Cursor chat, use MCP:
# Get service details
service = mcp_render_get_service(serviceId="srv-xxx")
print(service["status"])  # "running", "degraded", etc.

# Check recent deploys
deploys = mcp_render_list_deploys(serviceId="srv-xxx", limit=5)
```

#### 2. View Production Logs

```python
# Stream logs in real-time
logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    limit=100,
    direction="backward"
)

# Filter logs by level
error_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    level=["error"],
    limit=50
)

# Find logs with specific text
webhook_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["webhook_received"],
    limit=20
)
```

#### 3. Query Metrics

```python
# Get service metrics
metrics = mcp_render_get_metrics(
    resourceId="srv-xxx",
    metricTypes=["cpu_usage", "memory_usage", "http_request_count"],
    startTime="2025-10-13T00:00:00Z",
    resolution=300  # 5-minute buckets
)

# Check error rates
http_metrics = mcp_render_get_metrics(
    resourceId="srv-xxx",
    metricTypes=["http_request_count"],
    aggregateHttpRequestCountsBy="statusCode"
)
```

#### 4. Rapid Iteration

```bash
# Local development
1. Make code changes
2. Test locally: python scripts/test_webhook.py
3. Git commit and push
4. Render auto-deploys (if enabled)
5. Monitor in Cursor via MCP

# Or manual trigger:
# Use Render MCP to trigger deploy
```

#### 5. Debug Production Issues

```python
# Find errors in last hour
recent_errors = mcp_render_list_logs(
    resource=["srv-xxx"],
    level=["error"],
    startTime="2025-10-13T09:00:00Z",  # Last hour
    limit=50
)

# Find specific correlation ID
trace = mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["correlation_id=abc-123"]
)

# Check if issue is systemic
status_codes = mcp_render_list_log_label_values(
    resource=["srv-xxx"],
    label="statusCode",
    startTime="2025-10-13T09:00:00Z"
)
```

---

## Monitoring on Render

### Built-in Render Monitoring

Render provides:
- **Metrics Dashboard**: CPU, memory, request counts
- **Logs**: Centralized log aggregation
- **Health Checks**: Automated health monitoring
- **Alerts**: Email/Slack notifications on failures

### Application-Level Monitoring

#### Via /health Endpoint

```bash
# Check from external monitor (UptimeRobot, Pingdom, etc.)
curl https://your-app.onrender.com/health

# Expected response:
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "dependencies": {
    "union_action_api": {"status": "ok", ...},
    "memory": {"status": "ok", "usage_mb": 256.5}
  },
  "error_metrics": {
    "total_errors": 5,
    "recent_errors_last_5min": 0
  }
}
```

#### Via /metrics Endpoint (Prometheus)

Set up Prometheus scraping:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'whatsapp-chatops-agent'
    static_configs:
      - targets: ['your-app.onrender.com']
    metrics_path: '/metrics'
    scheme: https
```

### Error Rate Alerting

Monitor error rates via Render MCP:
```python
# Check error rate every 5 minutes
import time

while True:
    health = mcp_render_get_service(serviceId="srv-xxx")
    metrics = mcp_render_get_metrics(
        resourceId="srv-xxx",
        metricTypes=["http_request_count"],
        aggregateHttpRequestCountsBy="statusCode",
        startTime="-5m"  # Last 5 minutes
    )
    
    error_rate = calculate_error_rate(metrics)
    if error_rate > 0.05:  # > 5%
        alert("High error rate detected!", error_rate)
    
    time.sleep(300)  # Check every 5 minutes
```

---

## Debugging Production Issues

### Scenario 1: High Error Rate

```python
# 1. Check service health
service = mcp_render_get_service(serviceId="srv-xxx")
print(service["status"])

# 2. Get recent error logs
errors = mcp_render_list_logs(
    resource=["srv-xxx"],
    level=["error"],
    limit=50
)

# 3. Identify pattern
for log in errors:
    print(log["message"], log.get("error_type"))

# 4. Check if Union API issue
union_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["union_api_error"],
    limit=20
)
```

### Scenario 2: Slow Response Times

```python
# 1. Check latency metrics
latency = mcp_render_get_metrics(
    resourceId="srv-xxx",
    metricTypes=["http_latency"],
    httpLatencyQuantile=0.95,  # p95
    startTime="-1h"
)

# 2. Find slow operations in logs
slow_ops = mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["slow_operation_detected"],
    limit=20
)

# 3. Check memory usage
memory = mcp_render_get_metrics(
    resourceId="srv-xxx",
    metricTypes=["memory_usage"],
    startTime="-1h"
)
```

### Scenario 3: Deployment Issue

```python
# 1. Check recent deploys
deploys = mcp_render_list_deploys(serviceId="srv-xxx", limit=5)
latest = deploys[0]

# 2. Get deploy details
deploy = mcp_render_get_deploy(
    serviceId="srv-xxx",
    deployId=latest["id"]
)

# 3. If failed, check logs during deploy
deploy_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    startTime=deploy["createdAt"],
    endTime=deploy["finishedAt"]
)
```

---

## Zero-Downtime Deployments

Render provides zero-downtime deployments automatically:

### How It Works

1. **New instance starts** with your updated code
2. **Health checks run** on new instance
3. **Once healthy**, traffic routes to new instance
4. **Old instance drains** in-flight requests (30s timeout)
5. **Old instance terminates** after draining

### Graceful Shutdown (Implemented)

The service includes graceful shutdown handlers:
```python
@app.on_event("shutdown")
async def graceful_shutdown():
    # Log final metrics
    # Allow in-flight requests to complete
    # Clean up resources
```

### Deployment Best Practices

```bash
# 1. Test locally first
pytest
python scripts/test_webhook.py
python scripts/load_test.py

# 2. Deploy to Render
git push origin main

# 3. Monitor deployment via MCP
deploy_status = mcp_render_get_deploy(serviceId="srv-xxx", deployId="dep-xxx")

# 4. Watch logs during deployment
logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    startTime="2025-10-13T10:00:00Z",  # Deploy start time
    type=["build", "app"]
)

# 5. Verify health after deployment
curl https://your-app.onrender.com/health
```

---

## Troubleshooting

### Issue: Service Won't Start

```python
# Check build logs
build_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    type=["build"],
    limit=100
)

# Common causes:
# - Missing dependencies in requirements.txt
# - Wrong start command
# - Port binding issues (use $PORT)
```

### Issue: Health Check Failing

```bash
# Test health endpoint directly
curl https://your-app.onrender.com/health

# Check logs for errors
mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["health_check", "startup"],
    limit=50
)
```

### Issue: High Memory Usage

```python
# Monitor memory over time
memory_metrics = mcp_render_get_metrics(
    resourceId="srv-xxx",
    metricTypes=["memory_usage", "memory_limit"],
    startTime="-24h",
    resolution=300
)

# Check for memory leaks
# If memory continuously grows, restart service:
# Via Render dashboard or MCP
```

### Issue: Union API Connection Errors (Legacy - No Longer Applicable)

_Note: As of October 2025, the service uses local xsrc integration. This section is kept for historical reference._

```python
# Old approach (no longer used):
# union_logs = mcp_render_list_logs(
#     resource=["srv-xxx"],
#     text=["union_api_connection_error", "union_api_timeout"],
#     limit=20
# )
```

### Issue: xsrc Import Errors

**Symptom**: Build fails with `ImportError: No module named 'xsrc'`

**Cause**: xsrc path not accessible during build or runtime

**Fix**:
```python
# Check build logs for xsrc verification
build_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    type=["build"],
    text=["xsrc"],
    limit=50
)

# Should see: "✓ xsrc import successful" in build logs

# Verify rootDir is set correctly in render.yaml:
# rootDir: whatsapp-chatops-agent
```

**Manual Verification**:
```bash
# SSH into Render shell (if on paid plan) or check logs:
cd whatsapp-chatops-agent
python -c "import sys; from pathlib import Path; xsrc_path = Path('../xunion-action-integration'); print(f'xsrc exists: {xsrc_path.exists()}')"
```

### Issue: CareVoice Stub Warnings in Logs

**Symptom**: Logs show `carevoice_stub_used` warnings

**Expected Behavior**: MVP uses stub, not production CareVoice

**Log Message**:
```json
{
  "event": "carevoice_stub_used",
  "message": "Using mock CareVoice deployment - NOT PRODUCTION READY",
  "modules": ["core", "categorical_imperative"]
}
```

**Action**: Monitor for stub usage. Replace with real CareVoice before production launch.

**Check Stub Usage**:
```python
stub_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["carevoice_stub_used"],
    limit=100
)

# Count stub calls
print(f"Stub called {len(stub_logs)} times in recent logs")
```

### Issue: Kantian Analysis Returns Same Verdict

**Symptom**: All complaints return similar ethical analysis verdicts

**Cause**: Keyword-based heuristics are simplistic (MVP limitation)

**Check Analysis Patterns**:
```python
analysis_logs = mcp_render_list_logs(
    resource=["srv-xxx"],
    text=["kantian_analysis_complete"],
    limit=50
)

# Review verdicts distribution
# Should see variation based on complaint content
```

**Fix**: Enhance analyzer heuristics in `xsrc/services/kantian_analyzer.py`:
- Adjust keyword lists
- Add contextual analysis
- Consider AI integration for production

### Issue: Mock NHSComplaintDocument Warnings

**Symptom**: Logs show `mock_complaint_document_used` warnings

**Expected Behavior**: MVP uses generic pentadic structure

**Log Message**:
```json
{
  "event": "mock_complaint_document_used",
  "message": "Using mock NHSComplaintDocument - NOT PRODUCTION READY",
  "production_todo": "Implement real Burke's Pentad NLP extraction"
}
```

**Action**: Acceptable for MVP. Implement real NLP parsing before production.

---

## Performance Optimization on Render

### Vertical Scaling

Upgrade Render plan for better performance:
- **Starter**: 512MB RAM, 0.5 CPU
- **Standard**: 2GB RAM, 1 CPU
- **Pro**: 4GB RAM, 2 CPU

### Horizontal Scaling

For high traffic, enable multiple instances:
- Go to Service Settings → Scaling
- Set min/max instances
- Render auto-scales based on CPU/memory

### Caching

The service includes:
- Health check caching (10s TTL)
- Can add Redis for distributed caching if needed

---

## See Also

- [Render Documentation](https://render.com/docs)
- [Render MCP Documentation](https://render.com/docs/mcp)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Application troubleshooting
- [RUNBOOK.md](RUNBOOK.md) - Operational procedures
- [LOGGING.md](LOGGING.md) - Log event reference

---

## Support

- **Render Support**: https://render.com/support
- **Application Issues**: See TROUBLESHOOTING.md
- **MCP Issues**: Check Cursor MCP configuration

---

**With Render MCP, you can rapidly debug and iterate on production deployments directly from Cursor!** 🚀

