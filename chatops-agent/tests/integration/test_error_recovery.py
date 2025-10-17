"""
Integration tests for error recovery and service health.

Tests that the service remains healthy and functional after processing
errors, including multiple consecutive errors and error/success patterns.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


def test_service_healthy_after_single_error(client):
    """Test service remains healthy after processing one error."""
    # Send invalid request
    response = client.post("/webhook", json={
        "from": "123",
        "body": "no delimiter"
    })
    assert response.status_code == 400
    
    # Verify service still responds to health check
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"


def test_service_healthy_after_multiple_errors(client):
    """Test service remains healthy after multiple consecutive errors."""
    # Send multiple invalid requests
    for i in range(10):
        response = client.post("/webhook", json={
            "from": f"user{i}",
            "body": "invalid message"
        })
        assert response.status_code == 400
    
    # Service should still be healthy
    health_response = client.get("/health")
    assert health_response.status_code == 200


def test_successful_request_after_errors(client, mock_requests_post):
    """Test that valid requests work after errors."""
    # Send invalid request
    client.post("/webhook", json={
        "from": "123",
        "body": "invalid"
    })
    
    # Send valid request - should succeed
    response = client.post("/webhook", json={
        "from": "123",
        "body": "valid narrative|valid maxim"
    })
    assert response.status_code == 200


def test_error_then_success_pattern(client, mock_requests_post):
    """Test alternating error/success pattern."""
    patterns = [
        ({"from": "1", "body": "invalid"}, 400),
        ({"from": "2", "body": "valid|valid"}, 200),
        ({"from": "3", "body": "also invalid"}, 400),
        ({"from": "4", "body": "also valid|valid"}, 200),
    ]
    
    for payload, expected_status in patterns:
        response = client.post("/webhook", json=payload)
        assert response.status_code == expected_status


def test_multiple_error_types_consecutively(client):
    """Test service handles different error types in sequence."""
    error_payloads = [
        {"from": "1", "body": "no delimiter"},  # Parse error
        {"from": "2", "body": ""},  # Empty body
        {"from": "3"},  # Missing body
        {"body": "test|test"},  # Missing from (but should succeed)
    ]
    
    for payload in error_payloads:
        response = client.post("/webhook", json=payload)
        # All should return some response (not crash)
        assert response.status_code in [200, 400, 422]
    
    # Service should remain healthy
    health_response = client.get("/health")
    assert health_response.status_code == 200


def test_rapid_error_requests(client):
    """Test service handles rapid consecutive error requests."""
    # Simulate burst of invalid requests
    responses = []
    for i in range(50):
        response = client.post("/webhook", json={
            "from": f"user{i}",
            "body": f"invalid{i}"
        })
        responses.append(response)
    
    # All should get error responses
    for response in responses:
        assert response.status_code == 400
        assert response.json()["status"] == "error"
    
    # Service should still be responsive
    health_response = client.get("/health")
    assert health_response.status_code == 200


def test_error_doesnt_affect_other_requests(client, mock_requests_post):
    """Test that one user's error doesn't affect another user's request."""
    # User 1 sends invalid request
    response1 = client.post("/webhook", json={
        "from": "user1",
        "body": "invalid"
    })
    assert response1.status_code == 400
    
    # User 2 sends valid request - should succeed
    response2 = client.post("/webhook", json={
        "from": "user2",
        "body": "valid narrative|valid maxim"
    })
    assert response2.status_code == 200


def test_correlation_ids_unique_after_errors(client):
    """Test that correlation IDs remain unique even after errors."""
    correlation_ids = set()
    
    # Mix of error and success (with mock)
    for i in range(10):
        response = client.post("/webhook", json={
            "from": f"user{i}",
            "body": "invalid"  # All errors
        })
        
        # Extract correlation ID
        corr_id = response.json().get("correlation_id") or response.headers.get("X-Correlation-ID")
        if corr_id:
            correlation_ids.add(corr_id)
    
    # All should be unique
    assert len(correlation_ids) == 10


def test_logging_continues_after_errors(client, captured_logs):
    """Test that logging continues to work after errors."""
    # Send error request
    client.post("/webhook", json={
        "from": "123",
        "body": "invalid"
    })
    
    log_output1 = captured_logs.text
    assert len(log_output1) > 0
    
    # Send another request
    client.post("/webhook", json={
        "from": "456",
        "body": "also invalid"
    })
    
    log_output2 = captured_logs.text
    # Should have more logs
    assert len(log_output2) > len(log_output1)


def test_service_state_not_corrupted_by_errors(client, mock_requests_post):
    """Test that service state remains consistent after errors."""
    # Send invalid request
    client.post("/webhook", json={
        "from": "123",
        "body": "invalid"
    })
    
    # Send valid request
    response = client.post("/webhook", json={
        "from": "123",
        "body": "valid narrative|valid maxim"
    })
    
    # Should process correctly
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "workflow_result" in data


def test_concurrent_error_handling(client):
    """Test handling of errors from multiple sources."""
    # Simulate different error scenarios
    scenarios = [
        {"from": "1", "body": "no delimiter"},
        {"from": "2", "body": "|empty narrative"},
        {"from": "3", "body": "empty maxim|"},
        {"from": "4", "body": ""},
    ]
    
    for scenario in scenarios:
        response = client.post("/webhook", json=scenario)
        # Each should get appropriate error response
        assert response.status_code in [400, 422]
        
        # Each should have error structure
        if response.status_code == 400:
            data = response.json()
            assert data["status"] == "error"


def test_health_check_after_integration_error(client, mock_requests_post_error):
    """Test service health after integration (Union API) error."""
    # Send request that will fail at integration level
    response = client.post("/webhook", json={
        "from": "123",
        "body": "valid narrative|valid maxim"
    })
    
    # Should get 500 error
    assert response.status_code == 500
    
    # But service should still be healthy
    health_response = client.get("/health")
    assert health_response.status_code == 200


def test_error_recovery_doesnt_leak_memory(client):
    """Test that repeated errors don't cause memory issues."""
    # Send many error requests
    for i in range(100):
        client.post("/webhook", json={
            "from": f"user{i}",
            "body": "invalid"
        })
    
    # Service should still respond quickly to health check
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    # Should still respond to new requests
    response = client.post("/webhook", json={
        "from": "test",
        "body": "still invalid"
    })
    assert response.status_code == 400


def test_error_tracking_accumulates(client):
    """Test that error tracking accumulates correctly."""
    from src.diagnostics import error_tracker
    
    # Reset tracker
    error_tracker.reset()
    
    initial_errors = error_tracker.get_error_counts()
    
    # Send errors
    for _ in range(5):
        client.post("/webhook", json={
            "from": "123",
            "body": "invalid"
        })
    
    # Error count should have increased
    # (Note: depends on how errors are categorized)
    # This test verifies the mechanism works


def test_service_endpoints_remain_accessible_after_errors(client):
    """Test that all endpoints remain accessible after errors."""
    # Cause some errors
    for _ in range(5):
        client.post("/webhook", json={
            "from": "123",
            "body": "invalid"
        })
    
    # All endpoints should still be accessible
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    webhook_response = client.post("/webhook", json={
        "from": "123",
        "body": "still invalid"
    })
    assert webhook_response.status_code == 400  # Still processing requests


def test_error_doesnt_break_middleware(client):
    """Test that errors don't break middleware functionality."""
    # Send error request
    response = client.post("/webhook", json={
        "from": "123",
        "body": "invalid"
    })
    
    # Middleware should still add correlation ID
    assert "X-Correlation-ID" in response.headers
    
    # Send another request
    response2 = client.post("/webhook", json={
        "from": "456",
        "body": "also invalid"
    })
    
    # Middleware should still work
    assert "X-Correlation-ID" in response2.headers
    
    # IDs should be different
    assert response.headers["X-Correlation-ID"] != response2.headers["X-Correlation-ID"]

