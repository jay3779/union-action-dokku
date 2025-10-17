"""
Health check endpoint.

Reference: contracts/integration-api.yaml - GET /health
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import structlog

from .. import __version__

router = APIRouter()
logger = structlog.get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with status="healthy", version, and timestamp
    
    Constitutional Compliance:
        - Stateless: No database or external dependencies to check
        - Simple verification that API is running
    """
    logger.debug("health_check_called")
    
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.utcnow(),
    )

