"""
/escalate-to-ethics endpoint: ComplaintCare → Kantian Ethics

Endpoint: POST /escalate-to-ethics
Reference: contracts/integration-api.yaml, spec.md User Story 1

Constitutional Compliance:
- Sequential Workflow: Entry point for ethical analysis (enforces starting from ComplaintCare)
- Non-negotiable Data Integrity: Contract tests before escalation
"""

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import structlog
import time

from ..models.workflow import TransformationRequest, TransformationResult
from ..adapters.complaint_to_kantian import ComplaintToKantianAdapter
from ..services.kantian_analyzer import KantianEthicalAnalyzer

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/escalate-to-ethics", response_model=TransformationResult)
async def escalate_to_ethics(request: TransformationRequest) -> TransformationResult:
    """
    Transform ComplaintCare document to Kantian ethical analysis.
    
    **Step 1 of 2-step pipeline**
    
    Transforms ComplaintCare NHSComplaintDocument → Kantian EthicalAnalysisReport.
    
    **Transformation Logic**:
    - Maps Burke's Pentad elements to Kantian framework
    - Executes Kantian ethical analysis (Universalizability, Humanity Formula, Autonomy tests)
    - Returns report with zero technical jargon, citing philosophical principles by name
    
    **Schema Handling**:
    - Returns 422 if source data fails Pydantic validation
    - Uses Pydantic AI if schema version mismatch detected
    
    **Stateless**: No persistence. Agent stores result for next step.
    
    Args:
        request: TransformationRequest with source_data as NHSComplaintDocument
    
    Returns:
        TransformationResult with EthicalAnalysisReport
    
    Raises:
        HTTPException 422: Validation error (malformed source data)
        HTTPException 500: Transformation failure
    """
    start_time = time.time()
    
    logger.info(
        "escalate_to_ethics_called",
        workflow_id=request.workflow_id
    )
    
    try:
        # Step 1: Transform ComplaintCare → Kantian CaseBuilder
        adapter = ComplaintToKantianAdapter()
        case_builder_input = adapter.transform(request.source_data)
        
        logger.info(
            "complaint_to_kantian_transformation_success",
            workflow_id=request.workflow_id,
            source_schema=adapter.source_schema,
            target_schema=adapter.target_schema
        )
        
        # Step 2: Execute Kantian ethical analysis
        analyzer = KantianEthicalAnalyzer()
        ethical_analysis = analyzer.analyze(case_builder_input)
        
        logger.info(
            "kantian_analysis_complete",
            workflow_id=request.workflow_id,
            verdicts={
                "universalizability": ethical_analysis.universalizability_test["verdict"],
                "humanity_formula": ethical_analysis.humanity_formula_test["verdict"],
                "autonomy": ethical_analysis.autonomy_test["verdict"],
                "procedural_justice": ethical_analysis.procedural_justice_test["verdict"]
            }
        )
        
        # Convert to dict for TransformationResult
        ethical_report = ethical_analysis.dict()
        
        transformation_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "escalate_to_ethics_success",
            workflow_id=request.workflow_id,
            transformation_time_ms=transformation_time_ms
        )
        
        return TransformationResult(
            workflow_id=request.workflow_id,
            transformed_data=ethical_report,
            schema_version="EthicalAnalysisReport_v1",
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
                "message": str(e)
            }
        )

