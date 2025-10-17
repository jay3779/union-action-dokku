"""
Custom exception classes for the WhatsApp ChatOps Agent.

This module defines specific exception types for different error scenarios,
enabling better error categorization, handling, and diagnostics.
"""

from typing import Any, Dict, Optional


class ChatOpsAgentError(Exception):
    """Base exception class for all ChatOps Agent errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details for debugging
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class WebhookValidationError(ChatOpsAgentError):
    """
    Exception raised when webhook payload validation fails.
    
    This includes:
    - Missing required fields
    - Invalid data types
    - Malformed payloads
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None, received_value: Any = None):
        """
        Initialize webhook validation error.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            received_value: The value that failed validation
        """
        details = {}
        if field_name:
            details["field"] = field_name
        if received_value is not None:
            details["received_value"] = str(received_value)[:100]  # Limit length
        
        super().__init__(message, details)
        self.field_name = field_name
        self.received_value = received_value


class ParseError(ChatOpsAgentError):
    """
    Exception raised when message parsing fails.
    
    This includes:
    - Missing delimiter
    - Empty narrative or maxim
    - Invalid format
    """
    
    def __init__(self, message: str, raw_message: Optional[str] = None, parse_stage: Optional[str] = None):
        """
        Initialize parse error.
        
        Args:
            message: Error message
            raw_message: The raw message that failed to parse
            parse_stage: Stage where parsing failed (e.g., 'delimiter_check', 'extraction')
        """
        details = {}
        if raw_message:
            details["raw_message"] = raw_message[:200]  # Limit length for logging
        if parse_stage:
            details["parse_stage"] = parse_stage
        
        super().__init__(message, details)
        self.raw_message = raw_message
        self.parse_stage = parse_stage


class UnionAPIError(ChatOpsAgentError):
    """
    Exception raised when Union Action API communication fails.
    
    This includes:
    - HTTP errors (4xx, 5xx)
    - Network errors
    - Timeout errors
    - Invalid responses
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        """
        Initialize Union API error.
        
        Args:
            message: Error message
            status_code: HTTP status code from API response
            response_body: Response body from API (for debugging)
            endpoint: API endpoint that was called
        """
        details = {}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # Limit length
        if endpoint:
            details["endpoint"] = endpoint
        
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint


class NetworkError(ChatOpsAgentError):
    """
    Exception raised for network-related errors.
    
    This includes:
    - Connection refused
    - DNS resolution failures
    - Timeout errors
    - SSL/TLS errors
    """
    
    def __init__(
        self,
        message: str,
        target_url: Optional[str] = None,
        network_error_type: Optional[str] = None
    ):
        """
        Initialize network error.
        
        Args:
            message: Error message
            target_url: URL that was being accessed
            network_error_type: Type of network error (e.g., 'timeout', 'connection_refused')
        """
        details = {}
        if target_url:
            details["target_url"] = target_url
        if network_error_type:
            details["network_error_type"] = network_error_type
        
        super().__init__(message, details)
        self.target_url = target_url
        self.network_error_type = network_error_type


class ConfigurationError(ChatOpsAgentError):
    """
    Exception raised for configuration-related errors.
    
    This includes:
    - Missing required environment variables
    - Invalid configuration values
    - Startup configuration issues
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(message, details)
        self.config_key = config_key


class ValidationError(ChatOpsAgentError):
    """
    Exception raised for data validation errors.
    
    This includes:
    - Length validation failures
    - Format validation failures
    - Business rule violations
    """
    
    def __init__(
        self,
        message: str,
        validation_rule: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            validation_rule: The validation rule that failed
            expected: Expected value or format
            actual: Actual value that failed validation
        """
        details = {}
        if validation_rule:
            details["validation_rule"] = validation_rule
        if expected is not None:
            details["expected"] = str(expected)
        if actual is not None:
            details["actual"] = str(actual)[:100]  # Limit length
        
        super().__init__(message, details)
        self.validation_rule = validation_rule
        self.expected = expected
        self.actual = actual


def categorize_error(exception: Exception) -> str:
    """
    Categorize an exception for metrics and logging.
    
    Args:
        exception: The exception to categorize
        
    Returns:
        Error category string ('validation', 'parsing', 'integration', 'unknown')
    """
    if isinstance(exception, (WebhookValidationError, ValidationError)):
        return "validation"
    elif isinstance(exception, ParseError):
        return "parsing"
    elif isinstance(exception, (UnionAPIError, NetworkError)):
        return "integration"
    else:
        return "unknown"


def extract_error_context(exception: Exception) -> Dict[str, Any]:
    """
    Extract contextual information from an exception for logging.
    
    Args:
        exception: The exception to extract context from
        
    Returns:
        Dictionary of error context
    """
    context = {
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "error_category": categorize_error(exception)
    }
    
    # Add custom exception details if available
    if isinstance(exception, ChatOpsAgentError):
        context["error_details"] = exception.details
    
    return context

