"""
Integration tests for error response format and content.

Tests various failure modes and verifies error response structure,
correlation IDs, and helpful error messages.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


def test_missing_delimiter_error_response(client):
    """Test error response format for missing delimiter."""
    payload = {
        "from": "1234567890",
        "body": "Message without delimiter"
    }
    
    response = client.post("/webhook", json=payload)
    
    # Verify response structure
    assert response.status_code == 400
    data = response.json()
    
    # Check required error fields
    assert "status" in data
    assert data["status"] == "error"
    assert "detail" in data
    assert "timestamp" in data
    
    # Check error message is helpful
    assert "narrative|maxim" in data["detail"] or "delimiter" in data["detail"].lower()
    
    # Verify correlation ID present
    assert "correlation_id" in data or "X-Correlation-ID" in response.headers


def test_empty_body_error_response(client):
    """Test error response for empty body field."""
    payload = {
        "from": "1234567890",
        "body": ""
    }
    
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    
    assert data["status"] == "error"
    assert "body" in data["detail"].lower() or "required" in data["detail"].lower()


def test_missing_body_field_error_response(client):
    """Test error response when body field is missing."""
    payload = {
        "from": "1234567890"
    }
    
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    
    assert data["status"] == "error"


def test_malformed_json_error_response(client):
    """Test error response for malformed JSON."""
    response = client.post(
        "/webhook",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    
    # FastAPI returns 422 for validation errors
    assert response.status_code == 422


def test_error_response_includes_correlation_id(client):
    """Test that error responses include correlation ID."""
    payload = {
        "from": "1234567890",
        "body": "no delimiter"
    }
    
    response = client.post("/webhook", json=payload)
    
    data = response.json()
    
    # Should have correlation ID in body or header
    has_correlation = (
        "correlation_id" in data or 
        "X-Correlation-ID" in response.headers
    )
    assert has_correlation


def test_error_response_with_custom_correlation_id(client):
    """Test that custom correlation ID is preserved in error responses."""
    custom_id = "test-error-correlation-123"
    payload = {
        "from": "1234567890",
        "body": "invalid message"
    }
    
    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Correlation-ID": custom_id}
    )
    
    # Verify custom correlation ID preserved
    assert response.headers.get("X-Correlation-ID") == custom_id


def test_error_response_timestamp_format(client):
    """Test that error responses include properly formatted timestamp."""
    payload = {
        "from": "1234567890",
        "body": "no delimiter"
    }
    
    response = client.post("/webhook", json=payload)
    data = response.json()
    
    # Verify timestamp exists and is ISO format
    assert "timestamp" in data
    timestamp = data["timestamp"]
    
    # Should contain date and time components
    assert "T" in timestamp or " " in timestamp
    assert ":" in timestamp


def test_error_response_structure_consistency(client):
    """Test that all error responses have consistent structure."""
    test_cases = [
        {"from": "123", "body": "no delimiter"},
        {"from": "456", "body": ""},
        {"body": "test|test"},  # missing 'from'
    ]
    
    for payload in test_cases:
        response = client.post("/webhook", json=payload)
        data = response.json()
        
        # All errors should have these fields
        assert "status" in data
        assert data["status"] == "error"
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0


def test_error_response_http_status_codes(client):
    """Test appropriate HTTP status codes for different errors."""
    # Client error (validation) - should be 400
    response = client.post("/webhook", json={
        "from": "123",
        "body": "no delimiter"
    })
    assert 400 <= response.status_code < 500
    
    # Malformed JSON - should be 422
    response = client.post(
        "/webhook",
        data="invalid",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_error_response_no_sensitive_data_leak(client):
    """Test that error responses don't leak sensitive implementation details."""
    payload = {
        "from": "1234567890",
        "body": "invalid"
    }
    
    response = client.post("/webhook", json=payload)
    data = response.json()
    
    detail = data["detail"].lower()
    
    # Should not contain implementation details
    assert "traceback" not in detail
    assert "exception" not in detail
    assert "internal" not in detail or "error" in detail  # "internal error" is OK
    
    # Should not expose file paths
    assert "/" not in detail or "narrative/maxim" in detail  # "narrative/maxim" is OK
    assert "\\" not in detail


def test_error_response_helpful_message(client):
    """Test that error messages are helpful to users."""
    payload = {
        "from": "1234567890",
        "body": "missing the pipe"
    }
    
    response = client.post("/webhook", json=payload)
    data = response.json()
    
    detail = data["detail"]
    
    # Should explain what's wrong and how to fix it
    assert len(detail) > 20  # Not just "Error"
    
    # Should mention the format or delimiter
    helpful_terms = ["narrative", "maxim", "|", "delimiter", "format"]
    assert any(term in detail.lower() for term in helpful_terms)


def test_union_api_error_response(client, mock_requests_post_error):
    """Test error response when Union Action API fails."""
    payload = {
        "from": "1234567890",
        "body": "Valid narrative|Valid maxim"
    }
    
    response = client.post("/webhook", json=payload)
    
    # Should return 500 for server/integration errors
    assert response.status_code == 500
    data = response.json()
    
    assert data["status"] == "error"
    assert "correlation_id" in data or "X-Correlation-ID" in response.headers


def test_error_response_multiple_requests_unique_correlation(client):
    """Test that multiple error requests get unique correlation IDs."""
    payload = {
        "from": "1234567890",
        "body": "invalid"
    }
    
    correlation_ids = set()
    
    for _ in range(3):
        response = client.post("/webhook", json=payload)
        data = response.json()
        
        if "correlation_id" in data:
            correlation_ids.add(data["correlation_id"])
    
    # Each request should have unique correlation ID
    assert len(correlation_ids) == 3


def test_error_response_preserves_request_context(client, captured_logs):
    """Test that error responses log with proper context."""
    payload = {
        "from": "1234567890",
        "body": "no delimiter"
    }
    
    response = client.post("/webhook", json=payload)
    
    # Verify logging occurred
    log_output = captured_logs.text
    
    # Should log the error
    assert "error" in log_output.lower() or "warning" in log_output.lower()


@pytest.mark.parametrize("invalid_body", [
    "no delimiter",
    "|",
    "",
    "   ",
])
def test_various_invalid_bodies(client, invalid_body):
    """Test error responses for various invalid body values."""
    payload = {
        "from": "1234567890",
        "body": invalid_body
    }
    
    response = client.post("/webhook", json=payload)
    
    # Should return client error
    assert 400 <= response.status_code < 500
    
    # Should have error structure
    data = response.json()
    assert data["status"] == "error"
    assert "detail" in data


def test_error_response_json_format(client):
    """Test that error responses are valid JSON."""
    import json
    
    payload = {
        "from": "1234567890",
        "body": "invalid"
    }
    
    response = client.post("/webhook", json=payload)
    
    # Should be valid JSON
    assert response.headers.get("content-type") == "application/json"
    
    # Should parse without error
    data = response.json()
    assert isinstance(data, dict)
    
    # Should be re-serializable
    json_str = json.dumps(data)
    assert len(json_str) > 0

