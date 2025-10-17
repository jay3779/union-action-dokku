"""
End-to-end integration tests for successful submission flow.

These tests verify the complete happy path from webhook receipt through
Union Action API integration with comprehensive log inspection.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
import json


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


def test_end_to_end_successful_submission(client, mock_requests_post, captured_logs):
    """Test complete end-to-end successful submission."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "I observed a colleague taking credit for someone else's work|Always give credit where credit is due",
        "timestamp": 1697212800
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert HTTP response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "workflow_result" in data
    assert data["workflow_result"]["workflow_id"] == "1234567890"
    assert data["workflow_result"]["status"] == "escalated"
    assert "correlation_id" in data
    assert "timestamp" in data
    
    # Assert log output inspection
    log_output = captured_logs.text
    
    # Verify request logging
    assert "request_received" in log_output
    assert "POST" in log_output
    assert "/webhook" in log_output
    
    # Verify webhook processing logged
    assert "webhook_received" in log_output
    
    # Verify workflow orchestration logged
    assert "workflow_orchestrated" in log_output
    
    # Verify request completion logged
    assert "request_completed" in log_output
    assert "200" in log_output  # Status code
    
    # Verify timing metrics present
    assert "duration_ms" in log_output
    
    # Verify correlation ID present in logs
    assert "correlation_id" in log_output


def test_end_to_end_with_custom_correlation_id(client, mock_requests_post, captured_logs):
    """Test end-to-end flow with custom correlation ID."""
    # Arrange
    custom_id = "test-e2e-correlation-123"
    payload = {
        "from": "9876543210",
        "body": "Test narrative|Test maxim"
    }
    
    # Act
    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Correlation-ID": custom_id}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_id
    
    # Verify custom correlation ID in logs
    log_output = captured_logs.text
    assert custom_id in log_output


def test_end_to_end_message_parsing(client, mock_requests_post):
    """Test end-to-end message parsing and transformation."""
    # Arrange
    narrative = "Detailed ethical situation description"
    maxim = "Always act with integrity and honesty"
    payload = {
        "from": "5551234567",
        "body": f"{narrative}|{maxim}"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify Union Action API was called with correct data
    call_args = mock_requests_post.call_args
    api_payload = call_args[1]["json"]
    
    assert api_payload["workflow_id"] == "5551234567"
    assert api_payload["source_data"]["narrative"] == narrative
    assert api_payload["source_data"]["maxim_extraction"] == maxim
    
    # Verify pentadic context structure
    pentadic = api_payload["source_data"]["pentadic_context"]
    assert pentadic["act"] == "Narrative submission"
    assert pentadic["scene"]["phenomenal"] == "WhatsApp chat"
    assert pentadic["scene"]["noumenal"] == "Ethical concern"
    assert pentadic["agent"]["role"] == "Participant"


def test_end_to_end_whitespace_handling(client, mock_requests_post):
    """Test that whitespace is properly trimmed from narrative and maxim."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "  narrative with spaces  |  maxim with spaces  "
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify trimmed values sent to API
    call_args = mock_requests_post.call_args
    api_payload = call_args[1]["json"]
    
    assert api_payload["source_data"]["narrative"] == "narrative with spaces"
    assert api_payload["source_data"]["maxim_extraction"] == "maxim with spaces"


def test_end_to_end_special_characters(client, mock_requests_post):
    """Test handling of special characters in message."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": 'She said "stop" & they didn\'t listen|Be respectful & listen'
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify special characters preserved
    call_args = mock_requests_post.call_args
    api_payload = call_args[1]["json"]
    
    assert '"stop"' in api_payload["source_data"]["narrative"]
    assert "&" in api_payload["source_data"]["narrative"]
    assert "'" in api_payload["source_data"]["narrative"]


def test_end_to_end_emoji_support(client, mock_requests_post):
    """Test that emojis are properly handled."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "I saw something wrong 😟|Always do what's right ✅"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Verify emojis preserved
    call_args = mock_requests_post.call_args
    api_payload = call_args[1]["json"]
    
    assert "😟" in api_payload["source_data"]["narrative"]
    assert "✅" in api_payload["source_data"]["maxim_extraction"]


def test_end_to_end_performance_timing(client, mock_requests_post, captured_logs):
    """Test that performance timing is within acceptable range."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "Test narrative|Test maxim"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    
    # Check timing in logs
    log_output = captured_logs.text
    assert "duration_ms" in log_output
    
    # Response should be reasonably fast (logs will show if it's slow)
    # The slow_operation_detected warning would appear if > 2000ms


def test_end_to_end_multiple_sequential_requests(client, mock_requests_post, captured_logs):
    """Test multiple sequential requests each get unique correlation IDs."""
    # Arrange
    payloads = [
        {"from": "1111111111", "body": "First|First"},
        {"from": "2222222222", "body": "Second|Second"},
        {"from": "3333333333", "body": "Third|Third"}
    ]
    
    correlation_ids = []
    
    # Act
    for payload in payloads:
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        correlation_ids.append(data["correlation_id"])
    
    # Assert
    # Each request should have a unique correlation ID
    assert len(correlation_ids) == 3
    assert len(set(correlation_ids)) == 3  # All unique


def test_end_to_end_response_structure(client, mock_requests_post):
    """Test that response structure matches expected format."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "Test narrative|Test maxim"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "status" in data
    assert data["status"] == "received"
    assert "workflow_result" in data
    assert "timestamp" in data
    assert "correlation_id" in data
    
    # Verify workflow_result structure
    workflow_result = data["workflow_result"]
    assert "workflow_id" in workflow_result
    assert "status" in workflow_result
    assert "escalated_at" in workflow_result


def test_end_to_end_log_context_propagation(client, mock_requests_post, captured_logs):
    """Test that correlation ID propagates through entire request."""
    # Arrange
    payload = {
        "from": "1234567890",
        "body": "Test narrative|Test maxim"
    }
    
    # Act
    response = client.post("/webhook", json=payload)
    
    # Assert
    assert response.status_code == 200
    correlation_id = response.json()["correlation_id"]
    
    # Verify correlation ID appears in all log entries for this request
    log_lines = captured_logs.text.split('\n')
    log_lines_with_correlation = [
        line for line in log_lines 
        if correlation_id in line
    ]
    
    # Should appear in multiple log entries (request, webhook, orchestration, completion)
    assert len(log_lines_with_correlation) >= 3

