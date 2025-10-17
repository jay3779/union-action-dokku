FROM python:3.9-slim AS builder

WORKDIR /tmp

# Copy requirements and install to a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

# Install supervisord
RUN apt-get update && apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/*

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user and app directory
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Bring in virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser xsrc/ ./xsrc/
COPY --chown=appuser:appuser chatops-agent/ ./chatops-agent/
COPY --chown=appuser:appuser requirements.txt ./
COPY --chown=appuser:appuser supervisord.conf ./

# Create health check script
COPY --chown=appuser:appuser healthcheck.sh ./
RUN chmod +x healthcheck.sh

# Drop privileges
USER appuser

# Health check against FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ./healthcheck.sh

# Expose API port
EXPOSE 8000

# Start both processes with supervisord
CMD ["supervisord", "-c", "supervisord.conf"]

