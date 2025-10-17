"""
Core Pydantic models for workflow execution and transformation.

Reference: data-model.md Core Entities section
Constitutional Compliance: Type-safe validation at all boundaries
"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class WorkflowStatus(str, Enum):
    """Status of workflow execution."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED_FOR_REVIEW = "paused_for_review"


class WorkflowExecution(BaseModel):
    """
    Represents a complete 2-step pipeline run (agent-maintained context).
    
    This model is maintained by the autonomous agent, not stored in backend.
    Backend is stateless - agent stores workflow results.
    """
    
    workflow_id: str = Field(..., description="Unique workflow identifier")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: WorkflowStatus = WorkflowStatus.IN_PROGRESS
    
    # Component outputs (agent stores these)
    complaint_document: Optional[Dict[str, Any]] = Field(
        None, 
        description="ComplaintCare output (NHSComplaintDocument)"
    )
    ethical_report: Optional[Dict[str, Any]] = Field(
        None, 
        description="Kantian Ethics output (EthicalAnalysisReport)"
    )
    deployment_report: Optional[Dict[str, Any]] = Field(
        None, 
        description="CareVoice output (DeploymentReport with Typeform URL)"
    )
    
    # Audit trail (structured logs parsed by agent)
    audit_log_entries: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Constitutional compliance
    constitutional_compliance_status: Dict[str, str] = Field(
        default_factory=lambda: {
            "solidarity_check": "PENDING",
            "cycle_check": "PENDING",
            "human_approval": "PENDING",
            "vendor_independence": "PENDING",
            "model_justification": "PENDING",
            "representation": "PENDING",
            "validation": "PENDING"
        }
    )


class TransformationRequest(BaseModel):
    """
    Standard request for transformation endpoints.
    
    Constitutional Compliance: Enforces sequential workflow integrity
    (workflow_id maintained throughout 2-step pipeline)
    """
    
    workflow_id: str = Field(..., description="Workflow identifier (agent-maintained)")
    source_data: Dict[str, Any] = Field(..., description="Source data (Pydantic model as dict)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf_abc123",
                "source_data": {
                    "narrative": "I was denied training...",
                    "pentadic_context": {"act": "Training denial"},
                    "maxim_extraction": "Training is optional..."
                }
            }
        }


class TransformationResult(BaseModel):
    """
    Standard response for transformation endpoints.
    
    Constitutional Compliance: Audit trail via transformation metadata
    """
    
    workflow_id: str = Field(..., description="Workflow identifier from request")
    transformed_data: Dict[str, Any] = Field(..., description="Transformed output (Pydantic model as dict)")
    schema_version: str = Field(..., description="Target schema version")
    transformation_time_ms: int = Field(..., description="Transformation duration in milliseconds")
    pydantic_ai_used: bool = Field(default=False, description="Whether Pydantic AI was used")
    pydantic_ai_rationale: Optional[str] = Field(
        None, 
        description="AI transformation rationale if used"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf_abc123",
                "transformed_data": {
                    "survey_url": "https://typeform.com/to/xyz",
                    "validation_status": "passed"
                },
                "schema_version": "DeploymentReport_v1",
                "transformation_time_ms": 1234,
                "pydantic_ai_used": False
            }
        }

