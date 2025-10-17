"""
Health check endpoint.

Reference: contracts/integration-api.yaml - GET /health
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import structlog
import os
import time

from .. import __version__
from ..config import config

router = APIRouter()
logger = structlog.get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    service: str
    environment: str
    internal_communication: bool
    chatops_agent_url: str


# Service start time for uptime calculation
service_start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for bundled Union Action API.
    
    Returns:
        HealthResponse with comprehensive health information
    
    Constitutional Compliance:
        - Stateless: No database or external dependencies to check
        - Simple verification that API is running
        - Includes bundled deployment information
    """
    logger.debug("union_action_health_check_called")
    
    # Calculate uptime
    uptime_seconds = time.time() - service_start_time
    
    return HealthResponse(
        status="ok",
        version=__version__,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime_seconds,
        service="union-action-api",
        environment=os.getenv("ENVIRONMENT", "development"),
        internal_communication=config.internal_communication,
        chatops_agent_url=config.chatops_agent_url,
    )

