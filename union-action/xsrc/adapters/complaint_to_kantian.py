"""
ComplaintToKantianAdapter: Transform ComplaintCare → Kantian Ethics

Maps NHSComplaintDocument (Burke's Pentad) to Kantian CaseBuilder input.
Reference: data-model.md section 3, spec.md User Story 1

Constitutional Compliance:
- Non-negotiable Data Integrity: Enforces contract tests before escalation
- Sequential Workflow: Entry point for all ethical analysis workflows
"""

from typing import Any, Dict
import structlog

from ..models.adapters import TransformationAdapter

logger = structlog.get_logger(__name__)


class ComplaintToKantianAdapter(TransformationAdapter):
    """
    Transforms NHSComplaintDocument → Kantian CaseBuilder input.
    
    Mapping (Burke's Pentad → Kantian Framework):
    - Act → action.description (narrative)
    - Scene → scene (phenomenal/noumenal constraints/duties)
    - Agent → agent.role 
    - Maxim → maxim text (organizational maxim being tested)
    - Rhetoric → employee.experience
    
    User Story 1: Enable "Escalate to Ethical Analysis" button in ComplaintCare
    """
    
    source_schema: str = "NHSComplaintDocument_v1"
    target_schema: str = "CaseBuilder_v1"
    pydantic_ai_enabled: bool = False  # Direct schema mapping (no AI needed)
    
    def transform(self, complaint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform NHSComplaintDocument to Kantian CaseBuilder input.
        
        Args:
            complaint: ComplaintCare output as dict
        
        Returns:
            Kantian CaseBuilder input as dict
        
        Raises:
            ValueError: If required fields are missing
        
        Example Input:
            {
                "narrative": "I was denied training...",
                "pentadic_context": {
                    "act": "Training denial",
                    "scene": {
                        "phenomenal": "Operational pressures",
                        "noumenal": "Professional development duty"
                    },
                    "agent": {"role": "Clinical Support Assistant"},
                    "agency": "Management directive",
                    "purpose": "Cost reduction"
                },
                "maxim_extraction": "Training can be denied when operational needs arise",
                "rhetorical_context": {
                    "experience": "Felt undervalued and unsupported"
                }
            }
        
        Example Output:
            {
                "action": {
                    "description": "I was denied training...",
                    "moral_worth": "PENDING"
                },
                "scene": {
                    "phenomenal_constraints": "Operational pressures",
                    "noumenal_duties": "Professional development duty"
                },
                "agent": {
                    "role": "Clinical Support Assistant",
                    "categorical_status": "PENDING"
                },
                "maxim": "Training can be denied when operational needs arise",
                "employee_experience": "Felt undervalued and unsupported"
            }
        """
        logger.info(
            "complaint_to_kantian_transformation_started",
            source_schema=self.source_schema,
            target_schema=self.target_schema
        )
        
        # Validate required fields
        if not self.validate(complaint):
            raise ValueError("Complaint document validation failed")
        
        # Extract pentadic context
        pentadic_context = complaint.get("pentadic_context", {})
        scene = pentadic_context.get("scene", {})
        agent = pentadic_context.get("agent", {})
        
        # Extract rhetorical context
        rhetorical_context = complaint.get("rhetorical_context", {})
        
        # Build Kantian CaseBuilder input
        case_builder_input = {
            "action": {
                "description": complaint["narrative"],
                "moral_worth": "PENDING"  # Kantian analyzer fills this
            },
            "scene": {
                "phenomenal_constraints": scene.get("phenomenal", ""),
                "noumenal_duties": scene.get("noumenal", "")
            },
            "agent": {
                "role": agent.get("role", "Employee"),
                "categorical_status": "PENDING"  # Kantian analyzer fills this
            },
            "maxim": complaint["maxim_extraction"],
            "employee_experience": rhetorical_context.get("experience", "")
        }
        
        logger.info(
            "complaint_to_kantian_transformation_complete",
            source_schema=self.source_schema,
            target_schema=self.target_schema
        )
        
        return case_builder_input
    
    def validate(self, complaint: Dict[str, Any]) -> bool:
        """
        Validate NHSComplaintDocument has required fields for Kantian analysis.
        
        Args:
            complaint: ComplaintCare output as dict
        
        Returns:
            True if validation passes
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "narrative",
            "maxim_extraction",
            "pentadic_context"
        ]
        
        for field in required_fields:
            if field not in complaint or not complaint[field]:
                raise ValueError(
                    f"Required field '{field}' is missing or empty. "
                    f"Kantian analysis cannot proceed without explicit {field}."
                )
        
        # Validate pentadic_context has required structure
        pentadic = complaint.get("pentadic_context", {})
        if "scene" not in pentadic or "agent" not in pentadic:
            raise ValueError(
                "pentadic_context must contain 'scene' and 'agent' for Kantian mapping."
            )
        
        return True

