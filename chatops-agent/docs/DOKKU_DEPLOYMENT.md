# Dokku Deployment Guide for ChatOps Agent

This guide provides comprehensive instructions for deploying the WhatsApp ChatOps Agent to a Dokku platform with bundled Union Action API service.

## Overview

The ChatOps Agent is deployed as a single Docker container that includes:
- **ChatOps Agent**: FastAPI service for WhatsApp message processing
- **Union Action API**: Bundled ethical analysis service
- **Process Manager**: Manages both services within the container

## Prerequisites

### Dokku Server Requirements
- Ubuntu 18.04+ or compatible Linux distribution
- Dokku installed and configured
- SSH access to Dokku server
- Domain name (optional, for custom domain)

### Resource Requirements
- **CPU**: 4 cores (WAHA-optimized)
- **RAM**: 8GB minimum
- **Disk**: 50GB available space
- **Network**: Internet access for external APIs

## Quick Start

### 1. Create Dokku Application

```bash
# SSH to your Dokku server
ssh dokku@your-dokku-server.com

# Create application
dokku apps:create chatops-agent

# Set buildpack to Docker
dokku buildpacks:set chatops-agent docker
```

### 2. Configure Environment Variables

```bash
# Required environment variables
dokku config:set chatops-agent ENVIRONMENT=production
dokku config:set chatops-agent LOG_LEVEL=INFO
dokku config:set chatops-agent UNION_ACTION_API_URL=http://localhost:8000
dokku config:set chatops-agent LOG_SAMPLE_RATE=0.1
dokku config:set chatops-agent MAX_NARRATIVE_LENGTH=2000
dokku config:set chatops-agent MAX_MAXIM_LENGTH=500

# Optional environment variables
dokku config:set chatops-agent UNION_ACTION_LOG_LEVEL=INFO
dokku config:set chatops-agent UNION_ACTION_LOG_FORMAT=json
```

### 3. Configure Domain and SSL (Optional)

```bash
# Set custom domain
dokku domains:set chatops-agent your-domain.com

# Enable SSL with Let's Encrypt
dokku letsencrypt:enable chatops-agent
```

### 4. Deploy Application

```bash
# Add Dokku remote
git remote add dokku dokku@your-dokku-server.com:chatops-agent

# Deploy application
git push dokku main
```

### 5. Verify Deployment

```bash
# Check application status
dokku ps:report chatops-agent

# Check logs
dokku logs chatops-agent --tail

# Test health endpoint
curl https://your-domain.com/health
```

## Detailed Configuration

### Environment Variables

#### Required Variables
- `ENVIRONMENT`: Application environment (production, development, staging)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `UNION_ACTION_API_URL`: Internal URL for Union Action API (http://localhost:8000)
- `PORT`: Port number (set automatically by Dokku)

#### Optional Variables
- `LOG_SAMPLE_RATE`: Log sampling rate (0.0 to 1.0, default: 0.1)
- `MAX_NARRATIVE_LENGTH`: Maximum narrative length (100 to 10000, default: 2000)
- `MAX_MAXIM_LENGTH`: Maximum maxim length (10 to 1000, default: 500)
- `UNION_ACTION_LOG_LEVEL`: Union Action API log level (default: INFO)
- `UNION_ACTION_LOG_FORMAT`: Union Action API log format (default: json)

### Resource Configuration

```bash
# Set memory limit
dokku resource:limit chatops-agent --memory 1g

# Set CPU limit
dokku resource:limit chatops-agent --cpu 0.5

# Set build timeout
dokku config:set chatops-agent DOKKU_BUILD_TIMEOUT=600
```

### Health Checks

```bash
# Configure health checks
dokku checks:set chatops-agent web /health
dokku checks:set chatops-agent web --timeout 30 --interval 30
```

## Architecture

### Container Structure
```
/app/
├── src/                    # ChatOps Agent source
├── union-action/          # Union Action API source
├── scripts/               # Process management scripts
│   ├── process-manager.sh # Main process manager
│   └── health-check.sh    # Health check script
└── Dockerfile             # Multi-service container
```

### Service Communication
- **ChatOps Agent**: Runs on port 8080 (external)
- **Union Action API**: Runs on port 8000 (internal)
- **Process Manager**: Manages both services
- **Health Checks**: Monitors both services

### Process Flow
1. **Startup**: Process manager starts Union Action API first
2. **Health Check**: Waits for Union Action API to be ready
3. **ChatOps Agent**: Starts ChatOps Agent with Union Action API URL
4. **Monitoring**: Continuous health monitoring and restart if needed

## Monitoring and Logs

### View Logs
```bash
# View all logs
dokku logs chatops-agent --tail

# View specific service logs
dokku logs chatops-agent --tail | grep "chatops-agent"
dokku logs chatops-agent --tail | grep "union-action-api"
```

### Health Monitoring
```bash
# Check application health
curl https://your-domain.com/health

# Check Union Action API health
curl https://your-domain.com/health | jq '.dependencies.union_action_api'

# Check memory usage
curl https://your-domain.com/health | jq '.dependencies.memory'
```

### Metrics
```bash
# View Prometheus metrics
curl https://your-domain.com/metrics

# View error metrics
curl https://your-domain.com/health/errors
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs for errors
dokku logs chatops-agent --tail

# Check resource limits
dokku resource:report chatops-agent

# Restart application
dokku ps:restart chatops-agent
```

#### Union Action API Not Responding
```bash
# Check if Union Action API is running
dokku logs chatops-agent --tail | grep "union-action-api"

# Check internal communication
dokku logs chatops-agent --tail | grep "UNION_ACTION_API_URL"
```

#### Health Checks Failing
```bash
# Check health endpoint manually
curl -v https://your-domain.com/health

# Check health check configuration
dokku checks:report chatops-agent
```

### Debug Commands

```bash
# Enter container for debugging
dokku enter chatops-agent

# Check environment variables
dokku config:show chatops-agent

# Check application status
dokku ps:report chatops-agent

# Check proxy configuration
dokku proxy:report chatops-agent
```

## Maintenance

### Updates
```bash
# Deploy new version
git push dokku main

# Rollback to previous version
dokku git:from-archive chatops-agent < previous-version.tar.gz
```

### Backup
```bash
# Backup application configuration
dokku config:export chatops-agent > chatops-agent-config.txt

# Backup application
dokku git:from-archive chatops-agent > chatops-agent-backup.tar.gz
```

### Scaling
```bash
# Scale application (if supported by Dokku)
dokku ps:scale chatops-agent web=2
```

## Security Considerations

### Environment Variables
- Never commit sensitive data to version control
- Use Dokku config:set for production secrets
- Rotate secrets regularly

### Network Security
- Internal communication between services
- HTTPS-only external access
- SSL certificates automatically provisioned

### Access Control
- SSH key-based access to Dokku
- Git-based deployment authentication
- Environment variable access restricted to application

## Performance Optimization

### Resource Tuning
```bash
# Increase memory limit for high load
dokku resource:limit chatops-agent --memory 2g

# Increase CPU limit for processing
dokku resource:limit chatops-agent --cpu 1.0
```

### Logging Optimization
```bash
# Reduce log sampling for production
dokku config:set chatops-agent LOG_SAMPLE_RATE=0.01

# Set appropriate log level
dokku config:set chatops-agent LOG_LEVEL=WARNING
```

## Support

### Documentation
- [Dokku Documentation](https://dokku.com/docs/)
- [ChatOps Agent README](../README.md)
- [Union Action API Documentation](../union-action/README.md)

### Troubleshooting
- Check application logs: `dokku logs chatops-agent --tail`
- Verify health endpoint: `curl https://your-domain.com/health`
- Check resource usage: `dokku resource:report chatops-agent`

### Contact
- GitHub Issues: [Repository Issues](https://github.com/your-org/chatops-agent/issues)
- Documentation: [Project Documentation](https://github.com/your-org/chatops-agent/docs)
