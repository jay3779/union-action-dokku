"""
Pydantic models for Union Action Workflow Integration.

Exports core entities for use across the application.
"""

from .workflow import (
    WorkflowStatus,
    WorkflowExecution,
    TransformationRequest,
    TransformationResult,
)

from .domain import (
    NHSComplaintDocument,
    EthicalAnalysisReport,
    DeploymentReport,
)

from .adapters import TransformationAdapter

__all__ = [
    # Workflow orchestration models
    "WorkflowStatus",
    "WorkflowExecution",
    "TransformationRequest",
    "TransformationResult",
    
    # Core domain models (transformation pipeline)
    "NHSComplaintDocument",
    "EthicalAnalysisReport",
    "DeploymentReport",
    
    # Adapter base class
    "TransformationAdapter",
]

