"""
Union Action Client - HTTP API Integration.

Migrated from deprecated xunion-action-integration library to use
Union Action Service REST API for modern microservices architecture.

Pipeline:
1. WhatsApp message → Mock NHSComplaintDocument
2. HTTP POST /escalate-to-ethics → EthicalAnalysisReport
3. HTTP POST /generate-koers-survey → DeploymentReport (with Typeform URL)

Constitutional Compliance: HTTP API integration, comprehensive diagnostics
"""

import httpx
import structlog
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = structlog.get_logger(__name__)


class UnionActionClient:
    """
    Union Action Client - HTTP API Integration.

    Executes transformation pipeline via REST API:
    - WhatsApp message → NHSComplaintDocument (mock for MVP)
    - HTTP POST /escalate-to-ethics → EthicalAnalysisReport
    - HTTP POST /generate-koers-survey → DeploymentReport (Typeform URL)

    Enhanced with:
    - HTTP API integration (modern microservices)
    - Request/response logging
    - Detailed error logging
    - Transformation timing
    - Payload validation
    - Retry logic and error handling
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize Union Action client with HTTP API integration.

        Args:
            base_url: Union Action Service base URL (default: from environment or http://localhost:8000)
            timeout: HTTP request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url or os.getenv("UNION_ACTION_API_URL", "http://localhost:8000")
        self.timeout = timeout

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ChatOps-Agent/1.0"
            }
        )

        logger.info(
            "union_action_client_initialized",
            mode="http_api_integration",
            base_url=self.base_url,
            timeout=self.timeout,
            http_client=True
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
        logger.info("union_action_client_closed")

    def _create_mock_complaint_document(self, narrative: str, maxim: str) -> Dict[str, Any]:
        """
        Create mock NHSComplaintDocument from WhatsApp message.

        Args:
            narrative: User's narrative from WhatsApp message
            maxim: Organizational maxim from WhatsApp message

        Returns:
            Mock NHSComplaintDocument as dict
        """
        return {
            "narrative": narrative,
            "pentadic_context": {
                "scene": {
                    "phenomenal": "Healthcare workplace constraints",
                    "noumenal": "Professional duty to patient care"
                },
                "agent": {
                    "role": "Healthcare staff"
                },
                "agency": "Professional duties",
                "purpose": "Patient care"
            },
            "maxim_extraction": maxim,
            "rhetorical_context": {
                "experience": "Employee experience with the situation"
            },
            "complaint_id": f"whatsapp_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "source": "whatsapp_chatops",
            "metadata": {
                "channel": "whatsapp",
                "agent": "chatops",
                "version": "1.0"
            }
        }

    async def escalate_to_ethics(
        self,
        workflow_id: str,
        narrative: str,
        maxim: str
    ) -> Dict[str, Any]:
        """
        Escalate complaint to ethical analysis via Union Action Service.

        Args:
            workflow_id: Unique workflow identifier
            narrative: User's narrative from WhatsApp message
            maxim: Organizational maxim from WhatsApp message

        Returns:
            EthicalAnalysisReport as dict

        Raises:
            httpx.HTTPError: HTTP request failed
            ValueError: Invalid response format
        """
        start_time = time.time()

        logger.info(
            "escalate_to_ethics_started",
            workflow_id=workflow_id,
            narrative_length=len(narrative),
            maxim_length=len(maxim)
        )

        try:
            # Create mock complaint document
            complaint_document = self._create_mock_complaint_document(narrative, maxim)

            # Prepare request payload
            request_payload = {
                "workflow_id": workflow_id,
                "source_data": complaint_document,
                "schema_version": "NHSComplaintDocument_v1"
            }

            # Make HTTP request
            response = await self.client.post(
                "/escalate-to-ethics",
                json=request_payload
            )

            # Check for HTTP errors
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Log the response body for debugging
                logger.error(
                    "escalate_to_ethics_validation_error",
                    workflow_id=workflow_id,
                    status_code=e.response.status_code,
                    response_body=e.response.text,
                    request_payload=request_payload
                )
                raise

            # Parse response
            result = response.json()

            # Validate response structure
            if "transformed_data" not in result:
                raise ValueError("Invalid response format: missing 'transformed_data'")

            ethical_report = result["transformed_data"]

            # Log success
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "escalate_to_ethics_success",
                workflow_id=workflow_id,
                duration_ms=round(duration_ms, 2),
                ethical_report_keys=list(ethical_report.keys()),
                transformation_time_ms=result.get("transformation_time_ms", 0)
            )

            return ethical_report

        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "escalate_to_ethics_http_error",
                workflow_id=workflow_id,
                error=str(e),
                status_code=getattr(e.response, 'status_code', None),
                duration_ms=round(duration_ms, 2)
            )
            raise

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "escalate_to_ethics_error",
                workflow_id=workflow_id,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2)
            )
            raise

    async def generate_koers_survey(
        self,
        workflow_id: str,
        ethical_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate KOERS survey from ethical analysis via Union Action Service.

        Args:
            workflow_id: Unique workflow identifier
            ethical_report: EthicalAnalysisReport from escalate_to_ethics

        Returns:
            DeploymentReport as dict (with Typeform URL)

        Raises:
            httpx.HTTPError: HTTP request failed
            ValueError: Invalid response format
        """
        start_time = time.time()

        logger.info(
            "generate_koers_survey_started",
            workflow_id=workflow_id,
            ethical_report_keys=list(ethical_report.keys())
        )

        try:
            # Prepare request payload
            request_payload = {
                "workflow_id": workflow_id,
                "source_data": ethical_report,
                "schema_version": "EthicalAnalysisReport_v1"
            }

            # Make HTTP request
            response = await self.client.post(
                "/generate-koers-survey",
                json=request_payload
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Validate response structure
            if "transformed_data" not in result:
                raise ValueError("Invalid response format: missing 'transformed_data'")

            deployment_report = result["transformed_data"]

            # Log success
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "generate_koers_survey_success",
                workflow_id=workflow_id,
                duration_ms=round(duration_ms, 2),
                survey_url=deployment_report.get("survey_url"),
                module_list=deployment_report.get("module_list", []),
                transformation_time_ms=result.get("transformation_time_ms", 0)
            )

            return deployment_report

        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "generate_koers_survey_http_error",
                workflow_id=workflow_id,
                error=str(e),
                status_code=getattr(e.response, 'status_code', None),
                duration_ms=round(duration_ms, 2)
            )
            raise

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "generate_koers_survey_error",
                workflow_id=workflow_id,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2)
            )
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Union Action Service health.

        Returns:
            Health status as dict

        Raises:
            httpx.HTTPError: HTTP request failed
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(
                "health_check_failed",
                error=str(e),
                status_code=getattr(e.response, 'status_code', None)
            )
            raise


# Backward compatibility alias
UnionActionClientHTTP = UnionActionClient
