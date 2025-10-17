"""
Unit tests for logging configuration and correlation ID propagation.
"""

import pytest
from src.logging_config import (
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    add_correlation_id,
    configure_logging,
    redact_sensitive_data
)


def test_set_and_get_correlation_id():
    """Test setting and getting correlation ID."""
    test_id = "test-correlation-123"
    set_correlation_id(test_id)
    assert get_correlation_id() == test_id


def test_clear_correlation_id():
    """Test clearing correlation ID."""
    set_correlation_id("test-id")
    clear_correlation_id()
    assert get_correlation_id() is None


def test_add_correlation_id_processor():
    """Test correlation ID processor adds ID to log entries."""
    set_correlation_id("test-123")
    event_dict = {"event": "test_event"}
    
    result = add_correlation_id(None, None, event_dict)
    
    assert "correlation_id" in result
    assert result["correlation_id"] == "test-123"


def test_add_correlation_id_processor_no_id():
    """Test correlation ID processor when no ID is set."""
    clear_correlation_id()
    event_dict = {"event": "test_event"}
    
    result = add_correlation_id(None, None, event_dict)
    
    assert "correlation_id" not in result


def test_redact_sensitive_data_phone():
    """Test phone number redaction."""
    data = {"from": "1234567890", "body": "test message"}
    
    redacted = redact_sensitive_data(data)
    
    assert redacted["from"] == "***7890"
    assert redacted["body"] == "test message"


def test_redact_sensitive_data_workflow_id():
    """Test workflow ID redaction."""
    data = {"workflow_id": "9876543210", "status": "success"}
    
    redacted = redact_sensitive_data(data)
    
    assert redacted["workflow_id"] == "***3210"


def test_redact_sensitive_data_short_values():
    """Test redaction doesn't affect short values."""
    data = {"from": "123", "workflow_id": "abc"}
    
    redacted = redact_sensitive_data(data)
    
    assert redacted["from"] == "123"
    assert redacted["workflow_id"] == "abc"

