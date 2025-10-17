"""
Unit tests for custom exception classes and error handling.
"""

import pytest
from src.error_handlers import (
    ChatOpsAgentError,
    WebhookValidationError,
    ParseError,
    UnionAPIError,
    NetworkError,
    categorize_error,
    extract_error_context
)


def test_chatops_agent_error_basic():
    """Test base ChatOpsAgentError."""
    error = ChatOpsAgentError("Test error")
    assert str(error) == "Test error"
    assert error.details == {}


def test_chatops_agent_error_with_details():
    """Test ChatOpsAgentError with details."""
    details = {"key": "value", "count": 42}
    error = ChatOpsAgentError("Test error", details=details)
    
    assert error.details == details
    error_dict = error.to_dict()
    assert error_dict["error_type"] == "ChatOpsAgentError"
    assert error_dict["message"] == "Test error"
    assert error_dict["details"] == details


def test_webhook_validation_error():
    """Test WebhookValidationError."""
    error = WebhookValidationError(
        "Missing field",
        field_name="from",
        received_value=None
    )
    
    assert error.field_name == "from"
    assert error.received_value is None
    assert "field" in error.details


def test_parse_error():
    """Test ParseError."""
    error = ParseError(
        "Missing delimiter",
        raw_message="invalid message",
        parse_stage="delimiter_check"
    )
    
    assert error.raw_message == "invalid message"
    assert error.parse_stage == "delimiter_check"
    assert "parse_stage" in error.details


def test_union_api_error():
    """Test UnionAPIError."""
    error = UnionAPIError(
        "API error",
        status_code=500,
        response_body='{"error": "Internal error"}',
        endpoint="/escalate-to-ethics"
    )
    
    assert error.status_code == 500
    assert error.endpoint == "/escalate-to-ethics"
    assert "status_code" in error.details
    assert "endpoint" in error.details


def test_network_error():
    """Test NetworkError."""
    error = NetworkError(
        "Connection failed",
        target_url="http://api.example.com",
        network_error_type="connection_refused"
    )
    
    assert error.target_url == "http://api.example.com"
    assert error.network_error_type == "connection_refused"


def test_categorize_error_validation():
    """Test error categorization for validation errors."""
    error = WebhookValidationError("Test")
    assert categorize_error(error) == "validation"


def test_categorize_error_parsing():
    """Test error categorization for parsing errors."""
    error = ParseError("Test")
    assert categorize_error(error) == "parsing"


def test_categorize_error_integration():
    """Test error categorization for integration errors."""
    error = UnionAPIError("Test")
    assert categorize_error(error) == "integration"
    
    network_error = NetworkError("Test")
    assert categorize_error(network_error) == "integration"


def test_categorize_error_unknown():
    """Test error categorization for unknown errors."""
    error = Exception("Generic error")
    assert categorize_error(error) == "unknown"


def test_extract_error_context():
    """Test extracting context from exception."""
    error = WebhookValidationError("Missing field", field_name="from")
    context = extract_error_context(error)
    
    assert context["error_type"] == "WebhookValidationError"
    assert context["error_message"] == "Missing field"
    assert context["error_category"] == "validation"
    assert "error_details" in context


def test_extract_error_context_generic():
    """Test extracting context from generic exception."""
    error = ValueError("Test value error")
    context = extract_error_context(error)
    
    assert context["error_type"] == "ValueError"
    assert context["error_message"] == "Test value error"
    assert context["error_category"] == "unknown"

