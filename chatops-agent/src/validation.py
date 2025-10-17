"""
Message validation functions for WhatsApp ChatOps Agent.

Provides comprehensive validation for webhook payloads, message format,
field presence, and length limits with detailed error reporting.
"""

import os
from typing import Tuple, Optional, Dict, Any
import structlog

from .error_handlers import WebhookValidationError, ParseError, ValidationError

logger = structlog.get_logger(__name__)

# Configuration from environment with sensible defaults
MAX_NARRATIVE_LENGTH = int(os.getenv("MAX_NARRATIVE_LENGTH", "2000"))
MAX_MAXIM_LENGTH = int(os.getenv("MAX_MAXIM_LENGTH", "500"))


def validate_delimiter(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that message contains the required delimiter.
    
    Args:
        message: Message string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if "|" not in message:
        logger.warning(
            "validation_failed_delimiter",
            message_preview=message[:100] if len(message) > 100 else message,
            reason="missing_delimiter"
        )
        return False, "Invalid message format. Use 'narrative|maxim'"
    
    return True, None


def validate_non_empty(field_name: str, value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a field is not empty after stripping whitespace.
    
    Args:
        field_name: Name of the field being validated
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or len(value.strip()) == 0:
        logger.warning(
            "validation_failed_empty_field",
            field_name=field_name,
            value_length=len(value) if value else 0
        )
        return False, f"{field_name.capitalize()} cannot be empty"
    
    return True, None


def validate_length(
    field_name: str,
    value: str,
    max_length: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a field does not exceed maximum length.
    
    Args:
        field_name: Name of the field being validated
        value: Value to validate
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    actual_length = len(value)
    
    if actual_length > max_length:
        logger.warning(
            "validation_failed_length_exceeded",
            field_name=field_name,
            actual_length=actual_length,
            max_length=max_length,
            excess_chars=actual_length - max_length
        )
        return False, (
            f"{field_name.capitalize()} too long "
            f"({actual_length} characters, maximum {max_length})"
        )
    
    return True, None


def validate_message_format(message: str) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Comprehensive validation of message format.
    
    Args:
        message: Message string to validate
        
    Returns:
        Tuple of (is_valid, error_message, parsed_components)
        If valid, parsed_components contains {narrative, maxim}
    """
    # Check delimiter
    is_valid, error = validate_delimiter(message)
    if not is_valid:
        return False, error, None
    
    # Parse message
    narrative, maxim = message.split("|", 1)
    original_narrative = narrative
    original_maxim = maxim
    
    # Strip whitespace
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    logger.debug(
        "message_validation_parsing",
        narrative_length=len(narrative),
        maxim_length=len(maxim),
        whitespace_removed=(
            len(original_narrative) - len(narrative) +
            len(original_maxim) - len(maxim)
        )
    )
    
    # Validate non-empty (optional - depends on requirements)
    # Uncomment if empty fields should be rejected:
    # is_valid, error = validate_non_empty("narrative", narrative)
    # if not is_valid:
    #     return False, error, None
    # 
    # is_valid, error = validate_non_empty("maxim", maxim)
    # if not is_valid:
    #     return False, error, None
    
    # Validate lengths
    is_valid, error = validate_length("narrative", narrative, MAX_NARRATIVE_LENGTH)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validate_length("maxim", maxim, MAX_MAXIM_LENGTH)
    if not is_valid:
        return False, error, None
    
    # All validations passed
    return True, None, {"narrative": narrative, "maxim": maxim}


def validate_webhook_payload(payload: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate webhook payload structure.
    
    Args:
        payload: Webhook payload dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if "body" not in payload:
        logger.warning(
            "validation_failed_missing_field",
            field="body",
            available_fields=list(payload.keys())
        )
        return False, "Missing required field: body"
    
    # Check body is not empty
    body = payload.get("body", "")
    if not body:
        logger.warning(
            "validation_failed_empty_body",
            body_type=type(body).__name__
        )
        return False, "Message body cannot be empty"
    
    # Check from field (optional but logged if missing)
    if "from" not in payload:
        logger.info(
            "validation_warning_missing_from",
            note="will use fallback workflow_id"
        )
    
    return True, None


def validate_workflow_id(workflow_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate workflow ID format.
    
    Args:
        workflow_id: Workflow ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not workflow_id:
        logger.warning("validation_failed_empty_workflow_id")
        return False, "Workflow ID cannot be empty"
    
    if workflow_id == "unknown_user":
        logger.info(
            "validation_using_fallback_workflow_id",
            note="no phone number provided"
        )
    
    # Could add more specific validation (phone number format, etc.)
    # For now, just check it's not empty
    
    return True, None


def get_validation_summary(message: str) -> dict:
    """
    Get a summary of validation results without raising errors.
    
    Useful for logging and diagnostics.
    
    Args:
        message: Message to validate
        
    Returns:
        Dictionary with validation results
    """
    summary = {
        "message_length": len(message),
        "has_delimiter": "|" in message,
        "is_empty": len(message) == 0,
        "is_whitespace_only": message.isspace() if message else True,
    }
    
    if summary["has_delimiter"]:
        parts = message.split("|", 1)
        narrative = parts[0].strip()
        maxim = parts[1].strip() if len(parts) > 1 else ""
        
        summary.update({
            "narrative_length": len(narrative),
            "maxim_length": len(maxim),
            "narrative_empty": len(narrative) == 0,
            "maxim_empty": len(maxim) == 0,
            "narrative_exceeds_limit": len(narrative) > MAX_NARRATIVE_LENGTH,
            "maxim_exceeds_limit": len(maxim) > MAX_MAXIM_LENGTH,
        })
    
    return summary


def log_validation_failure(
    validation_type: str,
    details: dict,
    message_preview: Optional[str] = None
) -> None:
    """
    Log a validation failure with context.
    
    Args:
        validation_type: Type of validation that failed
        details: Dictionary of failure details
        message_preview: Optional preview of message that failed
    """
    log_data = {
        "validation_failure": validation_type,
        **details
    }
    
    if message_preview:
        log_data["message_preview"] = message_preview[:200]
    
    logger.warning("validation_failed", **log_data)


def create_validation_error_response(
    validation_type: str,
    field_name: Optional[str] = None,
    expected: Optional[str] = None,
    actual: Optional[str] = None
) -> dict:
    """
    Create a structured validation error response.
    
    Args:
        validation_type: Type of validation error
        field_name: Field that failed validation
        expected: Expected value/format
        actual: Actual value received
        
    Returns:
        Error response dictionary
    """
    from .error_responses import build_validation_error_response
    
    message = f"Validation failed: {validation_type}"
    if field_name:
        message += f" for field '{field_name}'"
    
    return build_validation_error_response(
        message=message,
        field_name=field_name,
        expected_format=expected
    )


def validate_environment_variables() -> Dict[str, Any]:
    """
    Validate all required environment variables for Dokku deployment.
    
    Returns:
        Dictionary with validation results and missing/invalid variables
    """
    validation_results = {
        "valid": True,
        "missing_variables": [],
        "invalid_variables": [],
        "warnings": [],
        "variables": {}
    }
    
    # Required environment variables
    required_vars = {
        "ENVIRONMENT": {
            "required": True,
            "valid_values": ["production", "development", "staging"],
            "default": "development"
        },
        "LOG_LEVEL": {
            "required": True,
            "valid_values": ["DEBUG", "INFO", "WARNING", "ERROR"],
            "default": "INFO"
        },
        "UNION_ACTION_API_URL": {
            "required": True,
            "pattern": r"^https?://",
            "default": "http://localhost:8000"
        },
        "PORT": {
            "required": False,  # Set by Dokku
            "type": "int",
            "min": 1,
            "max": 65535
        }
    }
    
    # Optional environment variables
    optional_vars = {
        "LOG_SAMPLE_RATE": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": "0.1"
        },
        "MAX_NARRATIVE_LENGTH": {
            "type": "int",
            "min": 100,
            "max": 10000,
            "default": "2000"
        },
        "MAX_MAXIM_LENGTH": {
            "type": "int",
            "min": 10,
            "max": 1000,
            "default": "500"
        }
    }
    
    # Validate required variables
    for var_name, config in required_vars.items():
        value = os.getenv(var_name)
        validation_results["variables"][var_name] = {
            "value": value,
            "required": config["required"],
            "valid": True,
            "error": None
        }
        
        if config["required"] and not value:
            validation_results["valid"] = False
            validation_results["missing_variables"].append(var_name)
            validation_results["variables"][var_name]["valid"] = False
            validation_results["variables"][var_name]["error"] = "Required variable not set"
            continue
        
        if value:
            # Check valid values if specified
            if "valid_values" in config and value not in config["valid_values"]:
                validation_results["valid"] = False
                validation_results["invalid_variables"].append(var_name)
                validation_results["variables"][var_name]["valid"] = False
                validation_results["variables"][var_name]["error"] = f"Invalid value. Must be one of: {config['valid_values']}"
                continue
            
            # Check pattern if specified
            if "pattern" in config:
                import re
                if not re.match(config["pattern"], value):
                    validation_results["valid"] = False
                    validation_results["invalid_variables"].append(var_name)
                    validation_results["variables"][var_name]["valid"] = False
                    validation_results["variables"][var_name]["error"] = f"Invalid format. Must match pattern: {config['pattern']}"
                    continue
            
            # Check type and range if specified
            if "type" in config:
                try:
                    if config["type"] == "int":
                        int_value = int(value)
                        if "min" in config and int_value < config["min"]:
                            raise ValueError(f"Value {int_value} is below minimum {config['min']}")
                        if "max" in config and int_value > config["max"]:
                            raise ValueError(f"Value {int_value} is above maximum {config['max']}")
                    elif config["type"] == "float":
                        float_value = float(value)
                        if "min" in config and float_value < config["min"]:
                            raise ValueError(f"Value {float_value} is below minimum {config['min']}")
                        if "max" in config and float_value > config["max"]:
                            raise ValueError(f"Value {float_value} is above maximum {config['max']}")
                except ValueError as e:
                    validation_results["valid"] = False
                    validation_results["invalid_variables"].append(var_name)
                    validation_results["variables"][var_name]["valid"] = False
                    validation_results["variables"][var_name]["error"] = str(e)
                    continue
    
    # Validate optional variables
    for var_name, config in optional_vars.items():
        value = os.getenv(var_name, config.get("default"))
        validation_results["variables"][var_name] = {
            "value": value,
            "required": False,
            "valid": True,
            "error": None
        }
        
        if value and "type" in config:
            try:
                if config["type"] == "int":
                    int_value = int(value)
                    if "min" in config and int_value < config["min"]:
                        validation_results["warnings"].append(f"{var_name}: Value {int_value} is below recommended minimum {config['min']}")
                    if "max" in config and int_value > config["max"]:
                        validation_results["warnings"].append(f"{var_name}: Value {int_value} is above recommended maximum {config['max']}")
                elif config["type"] == "float":
                    float_value = float(value)
                    if "min" in config and float_value < config["min"]:
                        validation_results["warnings"].append(f"{var_name}: Value {float_value} is below recommended minimum {config['min']}")
                    if "max" in config and float_value > config["max"]:
                        validation_results["warnings"].append(f"{var_name}: Value {float_value} is above recommended maximum {config['max']}")
            except ValueError as e:
                validation_results["warnings"].append(f"{var_name}: Invalid value format - {str(e)}")
    
    logger.info(
        "environment_validation_complete",
        valid=validation_results["valid"],
        missing_count=len(validation_results["missing_variables"]),
        invalid_count=len(validation_results["invalid_variables"]),
        warnings_count=len(validation_results["warnings"])
    )
    
    return validation_results


def get_environment_summary() -> Dict[str, Any]:
    """
    Get a summary of current environment configuration.
    
    Returns:
        Dictionary with environment summary
    """
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "union_action_api_url": os.getenv("UNION_ACTION_API_URL", "http://localhost:8000"),
        "port": os.getenv("PORT", "8080"),
        "log_sample_rate": os.getenv("LOG_SAMPLE_RATE", "0.1"),
        "max_narrative_length": os.getenv("MAX_NARRATIVE_LENGTH", "2000"),
        "max_maxim_length": os.getenv("MAX_MAXIM_LENGTH", "500"),
        "python_path": os.getenv("PYTHONPATH", ""),
        "working_directory": os.getcwd()
    }

