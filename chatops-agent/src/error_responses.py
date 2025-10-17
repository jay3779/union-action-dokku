"""
Standardized error response builders for the WhatsApp ChatOps Agent.

This module provides consistent error response formatting with correlation IDs,
timestamps, and contextual information for debugging.
"""

from typing import Any, Dict, Optional
from datetime import datetime
import structlog

from .logging_config import get_correlation_id

logger = structlog.get_logger(__name__)


def build_error_response(
    detail: str,
    error_code: Optional[str] = None,
    correlation_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a standardized error response.
    
    Args:
        detail: Human-readable error message
        error_code: Optional error code for categorization
        correlation_id: Optional correlation ID (will use current if not provided)
        additional_context: Optional additional context for debugging
        
    Returns:
        Standardized error response dictionary
    """
    # Get correlation ID from context if not provided
    if correlation_id is None:
        correlation_id = get_correlation_id()
    
    response = {
        "status": "error",
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if correlation_id:
        response["correlation_id"] = correlation_id
    
    if error_code:
        response["error_code"] = error_code
    
    if additional_context:
        response["context"] = additional_context
    
    return response


def build_validation_error_response(
    message: str,
    field_name: Optional[str] = None,
    expected_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an error response for validation failures.
    
    Args:
        message: Error message
        field_name: Name of the field that failed validation
        expected_format: Description of expected format
        
    Returns:
        Validation error response
    """
    context = {}
    if field_name:
        context["field"] = field_name
    if expected_format:
        context["expected_format"] = expected_format
    
    return build_error_response(
        detail=message,
        error_code="VALIDATION_ERROR",
        additional_context=context if context else None
    )


def build_parse_error_response(
    message: str = "Invalid message format. Use 'narrative|maxim'",
    parse_stage: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an error response for message parsing failures.
    
    Args:
        message: Error message
        parse_stage: Stage where parsing failed
        
    Returns:
        Parse error response
    """
    context = {}
    if parse_stage:
        context["parse_stage"] = parse_stage
    
    context["expected_format"] = "narrative|maxim"
    context["example"] = "I observed X happening|Act according to principle Y"
    
    return build_error_response(
        detail=message,
        error_code="PARSE_ERROR",
        additional_context=context
    )


def build_integration_error_response(
    message: str = "Error communicating with upstream service",
    service_name: Optional[str] = None,
    retry_advice: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an error response for integration/API errors.
    
    Args:
        message: Error message
        service_name: Name of the service that failed
        retry_advice: Advice for retry behavior
        
    Returns:
        Integration error response
    """
    context = {}
    if service_name:
        context["service"] = service_name
    if retry_advice:
        context["retry_advice"] = retry_advice
    
    return build_error_response(
        detail=message,
        error_code="INTEGRATION_ERROR",
        additional_context=context if context else None
    )


def build_network_error_response(
    message: str = "Network error occurred",
    target_service: Optional[str] = None,
    error_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an error response for network errors.
    
    Args:
        message: Error message
        target_service: Service that was being contacted
        error_type: Type of network error (e.g., 'timeout', 'connection_refused')
        
    Returns:
        Network error response
    """
    context = {}
    if target_service:
        context["target_service"] = target_service
    if error_type:
        context["error_type"] = error_type
    
    context["troubleshooting"] = "Check service connectivity and network configuration"
    
    return build_error_response(
        detail=message,
        error_code="NETWORK_ERROR",
        additional_context=context
    )


def build_server_error_response(
    message: str = "Internal server error occurred",
    operation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an error response for server/internal errors.
    
    Args:
        message: Error message
        operation: Operation that was being performed
        
    Returns:
        Server error response
    """
    context = {}
    if operation:
        context["operation"] = operation
    
    correlation_id = get_correlation_id()
    if correlation_id:
        context["support_reference"] = f"Please provide correlation ID {correlation_id} when contacting support"
    
    return build_error_response(
        detail=message,
        error_code="INTERNAL_ERROR",
        additional_context=context if context else None
    )


def sanitize_error_for_client(error: Exception, include_details: bool = False) -> str:
    """
    Sanitize an exception for client-facing error messages.
    
    Args:
        error: The exception to sanitize
        include_details: Whether to include exception details (only in development)
        
    Returns:
        Sanitized error message
    """
    import os
    
    # In development, optionally include more details
    if include_details or os.getenv("ENVIRONMENT", "dev") == "dev":
        return f"Error: {str(error)}"
    
    # In production, return generic message
    return "An error occurred while processing your request"


def log_error_with_context(
    error: Exception,
    context: Dict[str, Any],
    severity: str = "error"
) -> None:
    """
    Log an error with full context for debugging.
    
    Args:
        error: The exception to log
        context: Additional context about the error
        severity: Log severity level (error, warning, critical)
    """
    log_method = getattr(logger, severity, logger.error)
    
    # Remove error_type and error_message from context to avoid duplicate keyword arguments
    context_copy = context.copy()
    context_copy.pop('error_type', None)
    context_copy.pop('error_message', None)
    
    log_method(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context_copy
    )


def build_success_response(
    workflow_result: Dict[str, Any],
    processing_time_ms: Optional[float] = None
) -> Dict[str, Any]:
    """
    Build a standardized success response.
    
    Args:
        workflow_result: Result from the workflow processing
        processing_time_ms: Optional processing time in milliseconds
        
    Returns:
        Success response dictionary
    """
    response = {
        "status": "received",
        "workflow_result": workflow_result,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    correlation_id = get_correlation_id()
    if correlation_id:
        response["correlation_id"] = correlation_id
    
    if processing_time_ms is not None:
        response["processing_time_ms"] = round(processing_time_ms, 2)
    
    return response


def build_rate_limit_response(
    retry_after_seconds: int = 60,
    current_usage: Optional[int] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build an error response for rate limiting.
    
    Args:
        retry_after_seconds: Seconds to wait before retrying
        current_usage: Current usage count
        limit: Rate limit threshold
        
    Returns:
        Rate limit error response
    """
    context = {
        "retry_after_seconds": retry_after_seconds
    }
    
    if current_usage is not None and limit is not None:
        context["current_usage"] = current_usage
        context["limit"] = limit
    
    return build_error_response(
        detail=f"Rate limit exceeded. Please retry after {retry_after_seconds} seconds.",
        error_code="RATE_LIMIT_EXCEEDED",
        additional_context=context
    )

