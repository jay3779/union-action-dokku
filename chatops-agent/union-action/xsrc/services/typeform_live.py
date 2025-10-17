"""
Live Typeform integration for KOERS survey deployment.

Creates a Typeform form via the public API based on the requested
KOERS modules and returns a DeploymentReport-compatible dict.

This module is used when a valid TYPEFORM_API_TOKEN is configured.
It intentionally keeps the same deploy_survey signature as the stub
to provide a drop-in replacement.
"""

from pathlib import Path
from typing import Any, Dict, List
import httpx
import structlog


logger = structlog.get_logger(__name__)


TYPEFORM_API_BASE = "https://api.typeform.com"


def _build_scale_choices(scale_type: str) -> List[Dict[str, str]]:
    """
    Build a list of Typeform multiple-choice options from a scale string like "0-4".
    Defaults to 0-4 if parsing fails.
    """
    try:
        lower_str, upper_str = scale_type.split("-")
        lower = int(lower_str)
        upper = int(upper_str)
        if lower > upper:
            raise ValueError
    except Exception:
        lower, upper = 0, 4

    return [{"label": str(i)} for i in range(lower, upper + 1)]


def _question(title: str, scale_type: str) -> Dict[str, Any]:
    """Create a minimal multiple_choice field for Typeform."""
    return {
        "type": "multiple_choice",
        "title": title,
        "properties": {
            "choices": _build_scale_choices(scale_type),
        },
    }


def _module_display_name(module: str) -> str:
    mapping = {
        "core": "Core",
        "categorical_imperative": "Categorical Imperative",
        "dignity_instrumentalization": "Humanity Formula / Dignity",
        "autonomy_agency": "Autonomy & Agency",
        "procedural_justice": "Procedural Justice",
    }
    return mapping.get(module, module.replace("_", " ").title())


def _generate_fields_for_modules(modules: List[str], scale_type: str) -> List[Dict[str, Any]]:
    """
    Generate a minimal but structured set of questions:
    - Core: 7 items
    - Each non-core module: 5 items
    """
    fields: List[Dict[str, Any]] = []

    # Core questions (7)
    if "core" in modules:
        for idx in range(1, 8):
            fields.append(
                _question(
                    f"Core Q{idx}: Please rate this KOERS core item (0-4)",
                    scale_type,
                )
            )

    # Each additional module contributes 5 questions
    for module in modules:
        if module == "core":
            continue
        display = _module_display_name(module)
        for idx in range(1, 6):
            fields.append(
                _question(
                    f"{display} Q{idx}: Please rate this item (0-4)",
                    scale_type,
                )
            )

    return fields


def deploy_survey(
    spec_path: Path,
    deployment_mode: str,
    scale_type: str,
    modules: List[str],
    api_token: str,
) -> Dict[str, Any]:
    """
    Create a Typeform form for the KOERS survey and return deployment info.

    Args:
        spec_path: Path to KOERS spec file (currently informational; not parsed here)
        deployment_mode: Deployment mode (e.g., "employee_self")
        scale_type: Scale type string (e.g., "0-4")
        modules: KOERS modules, must include "core"
        api_token: Typeform API token (required)

    Returns:
        DeploymentReport-like dict with survey_id, survey_url, item_count, module_list
    """
    if not api_token:
        raise ValueError(
            "TYPEFORM_API_TOKEN is required for live Typeform deployment. "
            "Provide it via environment or configuration."
        )

    # Build fields from modules
    fields = _generate_fields_for_modules(modules, scale_type)
    item_count = len(fields)

    payload = {
        "title": f"KOERS Survey ({deployment_mode})",
        "fields": fields,
        # Keep other properties minimal for broad compatibility
        "settings": {
            "is_public": True,
        },
    }

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    logger.info(
        "typeform_live_create_form_start",
        module_count=len(modules),
        item_count=item_count,
        deployment_mode=deployment_mode,
    )

    url = f"{TYPEFORM_API_BASE}/forms"
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, json=payload, headers=headers)
    except Exception as exc:
        logger.error("typeform_live_http_error", error=str(exc))
        raise

    if response.status_code not in (200, 201):
        logger.error(
            "typeform_live_create_form_failed",
            status_code=response.status_code,
            body=response.text,
        )
        raise RuntimeError(
            f"Typeform create form failed: {response.status_code} {response.text}"
        )

    data = response.json()
    form_id = data.get("id")
    if not form_id:
        logger.error("typeform_live_missing_form_id", response=data)
        raise RuntimeError("Typeform response missing form id")

    # Standard share URL
    survey_url = f"https://typeform.com/to/{form_id}"

    logger.info(
        "typeform_live_create_form_success",
        survey_id=form_id,
        survey_url=survey_url,
        item_count=item_count,
    )

    return {
        "survey_id": form_id,
        "survey_url": survey_url,
        "item_count": item_count,
        "module_list": modules,
        "validation_status": "passed",
    }
