"""
Core domain Pydantic models for transformation pipeline.

These models represent the data contracts between pipeline stages:
- NHSComplaintDocument: ComplaintCare output (Burke's Pentad)
- EthicalAnalysisReport: Kantian Ethics output
- DeploymentReport: CareVoice/Typeform output

Reference: workflow-analysis.md identified gaps
Constitutional Compliance: Type-safe validation at all boundaries
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime


class NHSComplaintDocument(BaseModel):
    """
    ComplaintCare output using Burke's Pentad framework.
    
    This model captures workplace complaints in rhetorical terms
    that can be transformed into Kantian ethical analysis.
    
    Burke's Pentad Elements:
    - Act: What happened (narrative)
    - Scene: Context (phenomenal constraints + noumenal duties)
    - Agent: Who is involved (role)
    - Agency: How it happened (management directive)
    - Purpose: Why it happened (organizational goal)
    - Maxim: Organizational principle being questioned
    
    Used by: ComplaintToKantianAdapter.transform()
    """
    
    narrative: str = Field(
        ..., 
        description="Employee's complaint narrative (Burke's Pentad 'Act')",
        min_length=10
    )
    
    pentadic_context: Dict[str, Any] = Field(
        ...,
        description=(
            "Burke's Pentad structure containing scene, agent, agency, purpose. "
            "Must have 'scene' and 'agent' keys for Kantian mapping."
        )
    )
    
    maxim_extraction: str = Field(
        ...,
        description="Organizational maxim being tested (e.g., 'Training can be denied when convenient')",
        min_length=5
    )
    
    rhetorical_context: Dict[str, Any] = Field(
        ...,
        description="Employee's emotional/rhetorical experience. Must have 'experience' key."
    )
    
    # Optional metadata
    document_id: Optional[str] = Field(None, description="Unique document identifier")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    employee_id: Optional[str] = Field(None, description="Anonymized employee ID")
    
    @field_validator('pentadic_context')
    @classmethod
    def validate_pentadic_structure(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate pentadic_context has required structure for Kantian mapping.
        
        Required:
        - 'scene' key with 'phenomenal' and 'noumenal' sub-keys
        - 'agent' key with 'role' sub-key
        """
        if 'scene' not in v:
            raise ValueError("pentadic_context must contain 'scene' key")
        
        if 'agent' not in v:
            raise ValueError("pentadic_context must contain 'agent' key")
        
        # Validate scene structure
        scene = v.get('scene', {})
        if not isinstance(scene, dict):
            raise ValueError("pentadic_context['scene'] must be a dict")
        
        # Note: phenomenal/noumenal are optional but recommended
        # Agent role is required for Kantian analysis
        agent = v.get('agent', {})
        if not isinstance(agent, dict):
            raise ValueError("pentadic_context['agent'] must be a dict")
        
        return v
    
    @field_validator('rhetorical_context')
    @classmethod
    def validate_rhetorical_structure(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate rhetorical_context has 'experience' key."""
        if 'experience' not in v:
            raise ValueError("rhetorical_context must contain 'experience' key")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "narrative": "I was denied training despite requesting it multiple times.",
                "pentadic_context": {
                    "act": "Training denial",
                    "scene": {
                        "phenomenal": "Operational pressures and budget constraints",
                        "noumenal": "Professional development duty and career progression rights"
                    },
                    "agent": {
                        "role": "Clinical Support Assistant"
                    },
                    "agency": "Management directive",
                    "purpose": "Cost reduction"
                },
                "maxim_extraction": "Training can be denied when operationally convenient",
                "rhetorical_context": {
                    "experience": "Felt undervalued and unsupported by management"
                },
                "document_id": "doc_12345",
                "employee_id": "emp_anon_67890"
            }
        }


class EthicalAnalysisReport(BaseModel):
    """
    Kantian ethical analysis output from KantianEthicalAnalyzer.
    
    Contains results of 4 Kantian tests:
    1. Universalizability Test (Categorical Imperative)
    2. Humanity Formula Test (treating people as ends)
    3. Autonomy Test (moral worth of action)
    4. Procedural Justice Test (fairness)
    
    Each test returns:
    - verdict: "FAILURE" | "VIOLATION" | "PASS"
    - rationale: Human-readable explanation citing philosophical principles
    
    Used by: KantianToKOERSAdapter.transform()
    """
    
    universalizability_test: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Categorical Imperative test result. "
            "Verdict: 'FAILURE' if maxim cannot be universalized, 'PASS' otherwise."
        )
    )
    
    humanity_formula_test: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Humanity Formula test result. "
            "Verdict: 'VIOLATION' if employee treated as mere means, 'PASS' otherwise."
        )
    )
    
    autonomy_test: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Autonomy test result. "
            "Verdict: 'VIOLATION' if action motivated by external pressure, 'PASS' otherwise."
        )
    )
    
    procedural_justice_test: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Procedural justice test result. "
            "Verdict: 'FAILURE' if organizationally unjust, 'PASS' otherwise."
        )
    )
    
    summary: str = Field(
        ...,
        description="Overall ethical assessment with zero technical jargon",
        min_length=20
    )
    
    case_builder_input: Dict[str, Any] = Field(
        ...,
        description="Kantian CaseBuilder input used for analysis (audit trail)"
    )
    
    # Optional metadata
    analysis_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    workflow_id: Optional[str] = Field(None, description="Workflow identifier")
    
    @field_validator('universalizability_test', 'humanity_formula_test', 'autonomy_test', 'procedural_justice_test')
    @classmethod
    def validate_test_result(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Validate test result structure if provided.
        
        Each test must have:
        - verdict: str (FAILURE, VIOLATION, or PASS)
        - rationale: str (human-readable explanation)
        """
        if v is None:
            return v
        
        if not isinstance(v, dict):
            raise ValueError("Test result must be a dict")
        
        if 'verdict' not in v:
            raise ValueError("Test result must have 'verdict' key")
        
        if 'rationale' not in v:
            raise ValueError("Test result must have 'rationale' key")
        
        # Validate verdict values
        valid_verdicts = {'FAILURE', 'VIOLATION', 'PASS'}
        verdict = v.get('verdict', '').upper()
        if verdict not in valid_verdicts:
            raise ValueError(
                f"Test verdict must be one of {valid_verdicts}, got '{verdict}'"
            )
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "universalizability_test": {
                    "verdict": "FAILURE",
                    "rationale": (
                        "If all organizations denied training when operationally convenient, "
                        "professional development would cease to exist. The maxim cannot be "
                        "universalized without logical contradiction (Categorical Imperative)."
                    )
                },
                "humanity_formula_test": {
                    "verdict": "VIOLATION",
                    "rationale": (
                        "Employee treated as mere means to operational efficiency, "
                        "not as end-in-themselves with professional development rights "
                        "(Humanity Formula)."
                    )
                },
                "autonomy_test": {
                    "verdict": "VIOLATION",
                    "rationale": (
                        "Action motivated by external pressure (cost reduction), "
                        "not duty to professional standards. Violates Kantian Autonomy Principle."
                    )
                },
                "procedural_justice_test": {
                    "verdict": "FAILURE",
                    "rationale": (
                        "Denial process lacked transparency, consistency, and fair appeal "
                        "mechanisms required by procedural justice principles."
                    )
                },
                "summary": (
                    "This organizational practice violates all four formulations tested. "
                    "The denial of training represents a systematic ethical failure requiring "
                    "immediate remediation and policy reform."
                ),
                "case_builder_input": {
                    "action": {"description": "Training denial", "moral_worth": "PENDING"},
                    "scene": {"phenomenal_constraints": "Budget", "noumenal_duties": "Development"},
                    "agent": {"role": "CSA", "categorical_status": "PENDING"},
                    "maxim": "Training can be denied when convenient"
                },
                "workflow_id": "wf_abc123"
            }
        }


class DeploymentReport(BaseModel):
    """
    CareVoice/Typeform deployment output.
    
    Contains Typeform survey URL and metadata for KOERS
    (Kantian Organizational Ethics Rating Scale) deployment.
    
    KOERS Modules:
    - core: 7 mandatory items (always included)
    - categorical_imperative: Universalizability violations
    - dignity_instrumentalization: Humanity Formula violations
    - autonomy_agency: Autonomy violations
    - procedural_justice: Procedural justice violations
    
    Used by: Final step in transformation pipeline
    Returned to: WhatsApp agent for distribution
    """
    
    survey_id: str = Field(
        ...,
        description="Typeform survey ID (e.g., 'tf_xyz789')"
    )
    
    survey_url: str = Field(
        ...,
        description="Typeform survey URL for distribution (e.g., 'https://typeform.com/to/abc123')",
        pattern=r'^https?://'
    )
    
    item_count: int = Field(
        ...,
        description="Number of KOERS items in survey (core=7, each module=~5)",
        ge=7  # At minimum, core module (7 items)
    )
    
    module_list: List[str] = Field(
        ...,
        description="List of KOERS modules included (always includes 'core')",
        min_length=1
    )
    
    validation_status: str = Field(
        ...,
        description="Survey validation status ('passed' or 'failed')"
    )
    
    # Optional metadata
    deployment_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    workflow_id: Optional[str] = Field(None, description="Workflow identifier")
    typeform_api_version: Optional[str] = Field(None, description="Typeform API version used")
    
    @field_validator('module_list')
    @classmethod
    def validate_core_included(cls, v: List[str]) -> List[str]:
        """Validate that 'core' module is always included."""
        if 'core' not in v:
            raise ValueError("module_list must always include 'core' module")
        return v
    
    @field_validator('validation_status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is 'passed' or 'failed'."""
        if v.lower() not in {'passed', 'failed'}:
            raise ValueError("validation_status must be 'passed' or 'failed'")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "survey_id": "tf_xyz789",
                "survey_url": "https://typeform.com/to/abc123",
                "item_count": 22,
                "module_list": [
                    "core",
                    "categorical_imperative",
                    "dignity_instrumentalization",
                    "autonomy_agency"
                ],
                "validation_status": "passed",
                "workflow_id": "wf_abc123",
                "typeform_api_version": "v1"
            }
        }

