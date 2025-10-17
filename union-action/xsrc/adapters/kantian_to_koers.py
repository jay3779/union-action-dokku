"""
KantianToKOERSAdapter: Transform Kantian Ethics → CareVoice KOERS Survey

Maps Kantian ethical violations to KOERS modules and deploys Typeform survey.
Reference: data-model.md section 4, spec.md User Story 2

Constitutional Compliance:
- Vendor Independence: Typeform deployment via CareVoice abstraction
- Stateless: Returns Typeform URL, no persistence
"""

from typing import Any, Dict, List
import structlog
from pathlib import Path

from ..models.adapters import TransformationAdapter
from ..config import config

logger = structlog.get_logger(__name__)

# Prefer live Typeform API when token is configured; otherwise prefer CareVoice if available; else stub
if config.typeform_api_token:
    from ..services.typeform_live import deploy_survey  # type: ignore
    CAREVOICE_AVAILABLE = False
    logger.info("typeform_live_enabled", status="using_typeform_api")
else:
    try:
        from carevoice.commands.deploy import deploy_survey  # type: ignore
        CAREVOICE_AVAILABLE = True
        logger.info("carevoice_library_detected", status="using_real_carevoice")
    except ImportError:
        from ..services.carevoice_stub import deploy_survey  # type: ignore
        CAREVOICE_AVAILABLE = False
        logger.warning(
            "carevoice_not_available_using_stub",
            message="CareVoice library not found and TYPEFORM_API_TOKEN not set; using stub."
        )


class ViolationToModuleMapper:
    """
    Maps Kantian ethical violations to KOERS modules.
    
    KOERS = Kantian Organizational Ethics Rating Scale
    
    Mapping:
    - Universalizability Failure → categorical_imperative
    - Humanity Formula Violation → dignity_instrumentalization
    - Autonomy Violation → autonomy_agency
    - Procedural Justice Failure → procedural_justice
    - All cases → core (7 mandatory items)
    """
    
    VIOLATION_MODULE_MAP = {
        "Universalizability Failure": "categorical_imperative",
        "Humanity Formula Violation": "dignity_instrumentalization",
        "Autonomy Violation": "autonomy_agency",
        "Procedural Justice Failure": "procedural_justice"
    }
    
    @classmethod
    def map_violations(cls, ethical_report: Dict[str, Any]) -> List[str]:
        """
        Extract KOERS modules from ethical violations.
        
        Args:
            ethical_report: EthicalAnalysisReport as dict
        
        Returns:
            List of KOERS module names (always includes "core")
        
        Example:
            Input: {
                "universalizability_test": {"verdict": "FAILURE"},
                "humanity_formula_test": {"verdict": "VIOLATION"},
                "autonomy_test": {"verdict": "VIOLATION"}
            }
            
            Output: ["core", "categorical_imperative", "dignity_instrumentalization", "autonomy_agency"]
        """
        modules = ["core"]  # Always include core (7 mandatory KOERS items)
        
        # Check each Kantian test for violations
        test_to_violation = {
            "universalizability_test": "Universalizability Failure",
            "humanity_formula_test": "Humanity Formula Violation",
            "autonomy_test": "Autonomy Violation",
            "procedural_justice_test": "Procedural Justice Failure"
        }
        
        for test_name, violation_name in test_to_violation.items():
            if test_name in ethical_report:
                test_result = ethical_report[test_name]
                verdict = test_result.get("verdict", "").upper()
                
                # Map FAILURE or VIOLATION to KOERS module
                if verdict in ["FAILURE", "VIOLATION"]:
                    module = cls.VIOLATION_MODULE_MAP.get(violation_name)
                    if module and module not in modules:
                        modules.append(module)
                        logger.info(
                            "violation_mapped_to_module",
                            violation=violation_name,
                            module=module
                        )
        
        # Default to core only if no violations found
        if len(modules) == 1:
            logger.info("no_violations_found_defaulting_to_core_module")
        
        return modules


class KantianToKOERSAdapter(TransformationAdapter):
    """
    Transforms EthicalAnalysisReport → KOERS survey via Typeform.
    
    Workflow:
    1. Map ethical violations to KOERS modules
    2. Call CareVoice deploy_survey() with modules
    3. Return DeploymentReport with Typeform URL
    
    User Story 2: Enable KOERS survey generation for worker polling
    """
    
    source_schema: str = "EthicalAnalysisReport_v1"
    target_schema: str = "DeploymentReport_v1"
    pydantic_ai_enabled: bool = True  # May need schema adaptation for CareVoice versions
    
    def transform(self, ethical_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform EthicalAnalysisReport to Typeform DeploymentReport.
        
        Args:
            ethical_report: Kantian Ethics output as dict
        
        Returns:
            CareVoice DeploymentReport as dict (with Typeform URL)
        
        Raises:
            ValueError: If transformation fails
        
        Example Input:
            {
                "universalizability_test": {"verdict": "FAILURE"},
                "humanity_formula_test": {"verdict": "VIOLATION"},
                "autonomy_test": {"verdict": "VIOLATION"}
            }
        
        Example Output:
            {
                "survey_id": "tf_xyz789",
                "survey_url": "https://typeform.com/to/abc123",
                "item_count": 15,
                "module_list": ["core", "dignity_instrumentalization", "autonomy_agency"],
                "validation_status": "passed"
            }
        """
        logger.info(
            "kantian_to_koers_transformation_started",
            source_schema=self.source_schema,
            target_schema=self.target_schema
        )
        
        # Validate required fields
        if not self.validate(ethical_report):
            raise ValueError("Ethical report validation failed")
        
        # Step 1: Map violations to KOERS modules
        modules = ViolationToModuleMapper.map_violations(ethical_report)
        
        logger.info(
            "koers_modules_determined",
            modules=modules,
            module_count=len(modules)
        )
        
        # Step 2: Deploy survey via CareVoice
        spec_path = Path("carevoice-data/koers_spec.md")
        
        deployment_report = deploy_survey(
            spec_path=spec_path,
            deployment_mode="employee_self",
            scale_type="0-4",
            modules=modules,
            api_token=config.typeform_api_token,
        )
        
        logger.info(
            "kantian_to_koers_transformation_complete",
            source_schema=self.source_schema,
            target_schema=self.target_schema,
            survey_url=deployment_report["survey_url"]
        )
        
        return deployment_report
    
    def validate(self, ethical_report: Dict[str, Any]) -> bool:
        """
        Validate EthicalAnalysisReport has test results.
        
        Args:
            ethical_report: Kantian Ethics output as dict
        
        Returns:
            True if validation passes
        
        Raises:
            ValueError: If report has no test results
        """
        # Check for at least one Kantian test result
        test_fields = [
            "universalizability_test",
            "humanity_formula_test",
            "autonomy_test",
            "procedural_justice_test"
        ]
        
        has_test_results = any(field in ethical_report for field in test_fields)
        
        if not has_test_results:
            raise ValueError(
                "Ethical report must contain at least one Kantian test result. "
                "Cannot generate KOERS survey without ethical analysis."
            )
        
        return True

