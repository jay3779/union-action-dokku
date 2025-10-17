"""
/generate-koers-survey endpoint: Kantian Ethics → CareVoice KOERS Survey

Endpoint: POST /generate-koers-survey
Reference: contracts/integration-api.yaml, spec.md User Story 2

Constitutional Compliance:
- Sequential Workflow: Step 2 of 2-step pipeline (follows /escalate-to-ethics)
- Integration Endpoint: Integration ENDS at Typeform URL generation
"""

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import structlog
import time

from ..models.workflow import TransformationRequest, TransformationResult
from ..adapters.kantian_to_koers import KantianToKOERSAdapter
from ..config import config

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/generate-koers-survey", response_model=TransformationResult)
async def generate_koers_survey(request: TransformationRequest) -> TransformationResult:
    """
    Transform Kantian report to KOERS survey via Typeform.
    
    **Step 2 of 2-step pipeline (FINAL STEP)**
    
    Transforms Kantian EthicalAnalysisReport → CareVoice SurveyDefinition → Typeform deployment → DeploymentReport (URL).
    
    **Transformation Logic**:
    - Maps ethical violations to KOERS modules (e.g., Humanity Formula → dignity_instrumentalization)
    - Generates Typeform survey via CareVoice
    - Returns Typeform URL for manual distribution (round-robin polling)
    
    **Violation → Module Mapping**:
    - Universalizability Failure → categorical_imperative
    - Humanity Formula Violation → dignity_instrumentalization
    - Autonomy Violation → autonomy_agency
    - All cases → core (7 mandatory items)
    
    **Integration End**: Survey distribution and CollectiveVoice are out of scope.
    
    **Stateless**: No persistence. Agent stores Typeform URL.
    
    Args:
        request: TransformationRequest with source_data as EthicalAnalysisReport
    
    Returns:
        TransformationResult with DeploymentReport (Typeform URL)
    
    Raises:
        HTTPException 422: Validation error or Typeform API failure
        HTTPException 500: Transformation failure
    """
    start_time = time.time()
    
    logger.info(
        "generate_koers_survey_called",
        workflow_id=request.workflow_id
    )
    
    # Validate Typeform API token if live Typeform is enabled
    try:
        # If TYPEFORM_API_TOKEN is set, enforce that it is valid (non-empty)
        if config.typeform_api_token:
            config.require_typeform_if_live()
        else:
            # MVP fallback: continue with stub when token missing
            config.validate_required(require_typeform=False)
    except ValueError as e:
        logger.warning(
            "typeform_token_missing_or_invalid",
            workflow_id=request.workflow_id,
            message=str(e)
        )
        # Continue with stub behavior when token missing
    
    try:
        # Step 1: Transform Kantian report → KOERS survey via CareVoice
        adapter = KantianToKOERSAdapter()
        deployment_report = adapter.transform(request.source_data)
        
        logger.info(
            "kantian_to_koers_transformation_success",
            workflow_id=request.workflow_id,
            source_schema=adapter.source_schema,
            target_schema=adapter.target_schema,
            survey_url=deployment_report["survey_url"],
            modules=deployment_report["module_list"]
        )
        
        transformation_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "generate_koers_survey_success",
            workflow_id=request.workflow_id,
            transformation_time_ms=transformation_time_ms,
            typeform_url=deployment_report["survey_url"]
        )
        
        return TransformationResult(
            workflow_id=request.workflow_id,
            transformed_data=deployment_report,
            schema_version="DeploymentReport_v1",
            transformation_time_ms=transformation_time_ms,
            pydantic_ai_used=False
        )
    
    except ValidationError as e:
        logger.error(
            "validation_error",
            workflow_id=request.workflow_id,
            errors=e.errors()
        )
        raise HTTPException(status_code=422, detail=e.errors())
    
    except ValueError as e:
        logger.error(
            "transformation_error",
            workflow_id=request.workflow_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "TRANSFORMATION_FAILED",
                "message": str(e)
            }
        )
    
    except Exception as e:
        logger.error(
            "internal_server_error",
            workflow_id=request.workflow_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": str(e),
                "details": "Typeform API deployment failed or transformation error"
            }
        )

