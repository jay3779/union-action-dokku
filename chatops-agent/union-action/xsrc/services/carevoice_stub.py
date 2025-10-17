"""
CareVoice stub for MVP deployment.

This stub replaces the actual CareVoice library for MVP testing.
Returns mock DeploymentReport data without calling real Typeform API.

TODO: Replace with actual CareVoice library when available.

Reference: kantian_to_koers.py line 17 imports carevoice.commands.deploy
Constitutional Compliance: Vendor Independence (abstraction over Typeform)
"""

from pathlib import Path
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


def deploy_survey(
    spec_path: Path,
    deployment_mode: str,
    scale_type: str,
    modules: List[str],
    api_token: str,
) -> Dict[str, Any]:
    """
    STUB: Mock CareVoice deploy_survey for MVP.
    
    This is a temporary implementation that returns mock data
    without calling the real Typeform API or CareVoice library.
    
    Args:
        spec_path: Path to KOERS spec file (e.g., "carevoice-data/koers_spec.md")
        deployment_mode: Deployment mode (e.g., "employee_self")
        scale_type: Scale type (e.g., "0-4" for 5-point Likert)
        modules: List of KOERS modules to include (e.g., ["core", "categorical_imperative"])
        api_token: Typeform API token (not used in stub)
    
    Returns:
        DeploymentReport dict with mock survey URL and metadata
        
    Note:
        This stub logs a warning every time it's called to make it clear
        this is NOT production-ready and needs to be replaced.
    """
    logger.warning(
        "carevoice_stub_used",
        message="Using mock CareVoice deployment - NOT PRODUCTION READY",
        modules=modules,
        deployment_mode=deployment_mode,
        scale_type=scale_type
    )
    
    # Calculate item count: core=7, each additional module=5
    # Based on KOERS structure described in kantian_to_koers.py
    item_count = 7  # Core module always has 7 items
    for module in modules:
        if module != "core":
            item_count += 5  # Each additional module adds ~5 items
    
    # Generate mock survey ID (deterministic based on modules)
    # This ensures same modules = same ID for testing consistency
    module_hash = hash(tuple(sorted(modules))) % 1000000
    survey_id = f"mock_tf_{module_hash}"
    
    # Generate mock survey URL
    # Include first non-core module in URL for visual differentiation
    non_core_modules = [m for m in modules if m != "core"]
    url_suffix = non_core_modules[0].upper() if non_core_modules else "CORE"
    survey_url = f"https://typeform.com/to/MOCK_{url_suffix}_{module_hash}"
    
    logger.info(
        "carevoice_stub_deployment_complete",
        survey_id=survey_id,
        survey_url=survey_url,
        item_count=item_count,
        modules=modules
    )
    
    # Return DeploymentReport-compatible dict
    return {
        "survey_id": survey_id,
        "survey_url": survey_url,
        "item_count": item_count,
        "module_list": modules,
        "validation_status": "passed"  # Stub always passes validation
    }


def is_stub() -> bool:
    """
    Helper function to check if CareVoice stub is being used.
    
    Returns:
        True (always, since this is the stub implementation)
    """
    return True

