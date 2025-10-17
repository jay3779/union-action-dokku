# Union Action Workflow Integration

A stateless REST API connecting ComplaintCare → Kantian Ethics → CareVoice (KOERS/Typeform) with agent-driven workflow and maintainless backend.

## Features

- **Multi-process Container**: Runs both `union-action-api` and `chatops-agent` in a single Docker container
- **Process Management**: Uses supervisord for process control, restart, and monitoring
- **Health Monitoring**: Comprehensive health checks for both processes
- **Environment Configuration**: Full environment variable support for external services
- **Dokku Deployment**: Ready for Dokku deployment with proper logging and health checks
- **Constitutional Compliance**: Structured logging and audit trails

## Architecture

### Multi-Process Container

The application runs two processes within a single Docker container:

1. **union-action-api**: FastAPI application on port 8000
2. **chatops-agent**: Autonomous agent for workflow orchestration

### Process Management

- **Supervisord**: Manages both processes with automatic restart
- **Priority**: API process has higher priority (100) than agent (200)
- **Health Checks**: Docker health check verifies both processes are running
- **Logging**: Both processes log to stdout/stderr for Dokku integration

## Quick Start

### Prerequisites

- Docker
- Python 3.9+
- Environment variables (see Configuration)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd union-action
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   export TYPEFORM_API_TOKEN="your_token"
   export OPENAI_API_KEY="your_key"
   export LOG_LEVEL="INFO"
   export LOG_FORMAT="json"
   ```

4. **Run locally**:
   ```bash
   # Start both processes
   supervisord -c supervisord.conf
   
   # Or run API only for development
   uvicorn xsrc.main:app --host 0.0.0.0 --port 8000
   ```

5. **Test endpoints**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/docs
   ```

### Docker Deployment

1. **Build image**:
   ```bash
   docker build -t union-action .
   ```

2. **Run container**:
   ```bash
   docker run -p 8000:8000 \
     -e TYPEFORM_API_TOKEN="your_token" \
     -e OPENAI_API_KEY="your_key" \
     union-action
   ```

3. **Check health**:
   ```bash
   curl http://localhost:8000/health
   ```

### Dokku Deployment

1. **Create app**:
   ```bash
   dokku apps:create union-action
   ```

2. **Set environment variables**:
   ```bash
   dokku config:set union-action \
     TYPEFORM_API_TOKEN="your_token" \
     OPENAI_API_KEY="your_key" \
     LOG_LEVEL="INFO" \
     LOG_FORMAT="json"
   ```

3. **Deploy**:
   ```bash
   git push dokku main
   ```

4. **Check logs**:
   ```bash
   dokku logs union-action
   ```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TYPEFORM_API_TOKEN` | `""` | Typeform API token for KOERS survey deployment |
| `OPENAI_API_KEY` | `None` | OpenAI API key for Pydantic AI transformer |
| `PYDANTIC_AI_MODEL` | `"openai:gpt-4"` | Pydantic AI model for schema transformation |
| `LOG_LEVEL` | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | `"json"` | Log format (json or text) |
| `API_HOST` | `"0.0.0.0"` | API host to bind to |
| `API_PORT` | `8000` | API port to bind to |
| `CORS_ALLOWED_ORIGINS` | `["*"]` | List of allowed CORS origins |

### External Services

#### Typeform Integration

- **Purpose**: Deploy KOERS surveys via Typeform API
- **Required**: `TYPEFORM_API_TOKEN` environment variable
- **Usage**: Automatically used by `/deploy` endpoint

#### OpenAI Integration

- **Purpose**: Schema transformation via Pydantic AI
- **Required**: `OPENAI_API_KEY` environment variable
- **Usage**: Automatically used by `/escalate` endpoint

## API Endpoints

### Health Monitoring

- **GET** `/health` - Application health status
  - Returns: `{"status": "healthy", "timestamp": "...", "uptime": 123, "processes": {...}}`
  - Status codes: 200 (healthy), 503 (unhealthy)

### Workflow Endpoints

- **POST** `/escalate` - Escalate complaint to Kantian ethics analysis
- **POST** `/deploy` - Deploy KOERS survey to Typeform

### Documentation

- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/redoc` - Alternative API documentation (ReDoc)

## Health Monitoring

### Process Status

The health endpoint monitors both processes:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime": 123.45,
  "processes": {
    "api": {
      "status": "running",
      "pid": 123,
      "uptime": 120.5
    },
    "chatops-agent": {
      "status": "running", 
      "pid": 124,
      "uptime": 120.0
    }
  }
}
```

### Health Check Script

The Docker health check script (`healthcheck.sh`) verifies:

1. FastAPI health endpoint responds with 200
2. Supervisord is running
3. Both processes are in RUNNING state

### Logging

- **Format**: Structured JSON logs for audit trails
- **Output**: stdout/stderr for Dokku integration
- **Level**: Configurable via `LOG_LEVEL` environment variable
- **Process Identification**: Each log includes process context

## Development

### Project Structure

```
union-action/
├── xsrc/                    # Application source
│   ├── api/                 # API endpoints
│   ├── services/            # External service integrations
│   ├── models/              # Data models
│   ├── config.py            # Configuration management
│   └── main.py              # FastAPI application
├── chatops-agent/           # Autonomous agent
├── tests/                   # Test suite
├── supervisord.conf         # Process management
├── healthcheck.sh           # Health check script
├── Dockerfile               # Multi-process container
└── requirements.txt         # Python dependencies
```

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/contract/       # Contract tests
pytest tests/integration/    # Integration tests
pytest tests/unit/          # Unit tests
```

### Code Quality

- **Linting**: `pylint xsrc/`
- **Formatting**: `black xsrc/`
- **Type Checking**: `mypy xsrc/`

## Troubleshooting

### Common Issues

1. **Health check failures**:
   - Check that both processes are running: `supervisorctl status`
   - Verify API endpoint: `curl http://localhost:8000/health`

2. **Process crashes**:
   - Check logs: `dokku logs union-action`
   - Restart processes: `supervisorctl restart all`

3. **Environment variables**:
   - Verify all required variables are set
   - Check variable names and values

4. **External service errors**:
   - Verify API tokens are valid
   - Check network connectivity
   - Review service-specific error messages

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="text"
```

### Process Management

```bash
# Check process status
supervisorctl status

# Restart processes
supervisorctl restart all

# Stop processes
supervisorctl stop all

# Start processes
supervisorctl start all
```

## Production Deployment

### Resource Requirements

- **CPU**: 1 core minimum, 2 cores recommended
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 1GB for application and logs

### Scaling

- **Horizontal**: Deploy multiple instances behind load balancer
- **Vertical**: Increase CPU/memory for higher throughput
- **Process**: Adjust supervisord process limits

### Monitoring

- **Health Checks**: Use `/health` endpoint for monitoring
- **Logs**: Monitor stdout/stderr for errors
- **Metrics**: Track response times and error rates

## License

[License information]

## Support

[Support information]