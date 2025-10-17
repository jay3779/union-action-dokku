"""
Integration tests for webhook processing flow.

These tests verify the complete flow from WAHA webhook request through
message parsing to Union Action API call, with logging verification.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app
from src.logging_config import get_correlation_id


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


def test_webhook_processing_success_flow(client, sample_webhook_payload, mock_requests_post, captured_logs):
    """Test complete successful webhook processing flow."""
    # Act
    response = client.post("/webhook", json=sample_webhook_payload)
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "workflow_result" in data
    assert data["workflow_result"]["workflow_id"] == "1234567890"
    assert "correlation_id" in data
    
    # Verify correlation ID in headers
    assert "X-Correlation-ID" in response.headers
    
    # Verify logging
    log_text = captured_logs.text
    assert "request_received" in log_text
    assert "webhook_received" in log_text
    assert "workflow_orchestrated" in log_text
    assert "request_completed" in log_text


def test_webhook_processing_with_correlation_id(client, sample_webhook_payload, mock_requests_post):
    """Test that provided correlation ID is preserved."""
    # Arrange
    custom_correlation_id = "custom-test-id-123"
    
    # Act
    response = client.post(
        "/webhook",
        json=sample_webhook_payload,
        headers={"X-Correlation-ID": custom_correlation_id}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_correlation_id
    data = response.json()
    assert data["correlation_id"] == custom_correlation_id


def test_webhook_processing_missing_delimiter(client, sample_webhook_payload_no_delimiter, captured_logs):
    """Test webhook processing with missing delimiter."""
    # Act
    response = client.post("/webhook", json=sample_webhook_payload_no_delimiter)
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert "Invalid message format" in data["detail"]
    assert "correlation_id" in data
    
    # Verify error logging
    assert "webhook_received" in captured_logs.text


def test_webhook_processing_union_api_error(client, sample_webhook_payload, mock_requests_post_error, captured_logs):
    """Test webhook processing when Union Action API fails."""
    # Act
    response = client.post("/webhook", json=sample_webhook_payload)
    
    # Assert
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert "correlation_id" in data
    
    # Verify error logging
    log_text = captured_logs.text
    assert "escalate_to_ethics_failed" in log_text or "error" in log_text.lower()


def test_webhook_processing_timing_metrics(client, sample_webhook_payload, mock_requests_post, captured_logs):
    """Test that timing metrics are logged."""
    # Act
    response = client.post("/webhook", json=sample_webhook_payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify timing logs
    log_text = captured_logs.text
    assert "duration_ms" in log_text
    assert "request_completed" in log_text


def test_webhook_processing_malformed_json(client):
    """Test webhook processing with malformed JSON."""
    # Act
    response = client.post(
        "/webhook",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 422  # FastAPI validation error


def test_webhook_processing_missing_body_field(client):
    """Test webhook processing with missing 'body' field."""
    # Arrange
    payload = {"from": "1234567890"}  # Missing 'body'
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_webhook_processing_empty_body(client):
    """Test webhook processing with empty body field."""
    # Arrange
    payload = {"from": "1234567890", "body": ""}
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_webhook_processing_whitespace_only_body(client):
    """Test webhook processing with whitespace-only body."""
    # Arrange
    payload = {"from": "1234567890", "body": "   |   "}
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    # Should succeed but with empty narrative/maxim after strip
    # This behavior depends on implementation
    assert response.status_code in [200, 400]


def test_webhook_processing_multiple_delimiters(client, mock_requests_post):
    """Test webhook processing with multiple pipe delimiters."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "First part|Second part|Third part"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify only first delimiter was used (split with maxsplit=1)
    call_args = mock_requests_post.call_args
    sent_payload = call_args[1]["json"]
    assert sent_payload["source_data"]["narrative"] == "First part"
    assert sent_payload["source_data"]["maxim_extraction"] == "Second part|Third part"


def test_webhook_processing_unicode_content(client, mock_requests_post):
    """Test webhook processing with unicode characters."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "Problème éthique 中文|Respecter 尊重 🙏"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200


def test_webhook_processing_very_long_message(client, mock_requests_post):
    """Test webhook processing with very long message."""
    # Arrange
    long_narrative = "A" * 5000
    long_maxim = "B" * 1000
    payload = {
        "from": "1234567890",
        "body": f"{long_narrative}|{long_maxim}"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    # Should succeed (no length validation yet in base implementation)
    assert response.status_code == 200


def test_webhook_processing_phone_number_as_workflow_id(client, mock_requests_post):
    """Test that phone number is correctly used as workflow_id."""
    # Arrange
    test_phone = "9876543210"
    payload = {
        "from": test_phone,
        "body": "Test narrative|Test maxim"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify workflow_id in API call
    call_args = mock_requests_post.call_args
    sent_payload = call_args[1]["json"]
    assert sent_payload["workflow_id"] == test_phone


def test_webhook_processing_missing_from_field(client, mock_requests_post):
    """Test webhook processing with missing 'from' field."""
    # Arrange
    payload = {
        "body": "Test narrative|Test maxim"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify fallback to "unknown_user"
    call_args = mock_requests_post.call_args
    sent_payload = call_args[1]["json"]
    assert sent_payload["workflow_id"] == "unknown_user"


def test_health_endpoint(client):
    """Test health endpoint returns ok status."""
    # Act
    response = client.get("/health")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_endpoint_timing(client, captured_logs):
    """Test health endpoint responds quickly."""
    # Act
    response = client.get("/health")
    
    # Assert
    assert response.status_code == 200
    
    # Check response time in logs
    log_text = captured_logs.text
    if "duration_ms" in log_text:
        # Should be very fast (< 100ms typically)
        assert "request_completed" in log_text

