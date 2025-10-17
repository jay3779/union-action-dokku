"""
Union Action API client for chatops-agent.

This module provides a client for communicating with the union-action API
via localhost HTTP requests.
"""

import asyncio
from typing import Dict, Any, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


class UnionActionClient:
    """Client for communicating with union-action API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize the client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the union-action API."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Health check request failed", error=str(e))
            raise
        except httpx.HTTPStatusError as e:
            logger.error("Health check failed", status_code=e.response.status_code)
            raise
    
    async def escalate_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate a complaint to the ethics system."""
        try:
            response = await self.client.post(
                f"{self.base_url}/escalate",
                json=complaint_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Escalate complaint request failed", error=str(e))
            raise
        except httpx.HTTPStatusError as e:
            logger.error("Escalate complaint failed", status_code=e.response.status_code)
            raise
    
    async def create_survey(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a KOERS survey."""
        try:
            response = await self.client.post(
                f"{self.base_url}/deploy",
                json=survey_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Create survey request failed", error=str(e))
            raise
        except httpx.HTTPStatusError as e:
            logger.error("Create survey failed", status_code=e.response.status_code)
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
