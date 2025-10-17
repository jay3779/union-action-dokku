"""
Integration tests for /health endpoint.

Tests health endpoint response format, timing, structure,
and monitoring capabilities.
"""

import pytest
import time
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


def test_health_endpoint_exists(client):
    """Test that /health endpoint is accessible."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_response_format(client):
    """Test health endpoint returns proper JSON structure."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Required fields
    assert "status" in data
    assert "timestamp" in data
    
    # Status should be 'ok' or 'degraded' or 'down'
    assert data["status"] in ["ok", "degraded", "down"]


def test_health_endpoint_response_time(client):
    """Test health endpoint responds within 1 second."""
    start_time = time.time()
    response = client.get("/health")
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert duration < 1.0  # Must respond within 1 second


def test_health_endpoint_includes_error_metrics(client):
    """Test health endpoint includes error metrics."""
    response = client.get("/health")
    data = response.json()
    
    assert "error_metrics" in data
    error_metrics = data["error_metrics"]
    
    # Should have error tracking info
    assert "total_errors" in error_metrics
    assert isinstance(error_metrics["total_errors"], int)
    assert error_metrics["total_errors"] >= 0


def test_health_endpoint_includes_uptime(client):
    """Test health endpoint includes uptime information."""
    response = client.get("/health")
    data = response.json()
    
    # Should have uptime field
    assert "uptime_seconds" in data or "uptime" in data


def test_health_endpoint_includes_version(client):
    """Test health endpoint includes service version."""
    response = client.get("/health")
    data = response.json()
    
    # Should have version field
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


def test_health_endpoint_timestamp_format(client):
    """Test health endpoint timestamp is properly formatted."""
    response = client.get("/health")
    data = response.json()
    
    timestamp = data["timestamp"]
    
    # Should be ISO format
    assert "T" in timestamp
    assert ":" in timestamp
    
    # Should parse as valid datetime
    from datetime import datetime
    parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    assert parsed is not None


def test_health_endpoint_multiple_calls_consistent(client):
    """Test health endpoint returns consistent structure across calls."""
    response1 = client.get("/health")
    response2 = client.get("/health")
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Same structure
    assert set(data1.keys()) == set(data2.keys())
    
    # Status should be same (assuming no errors between calls)
    assert data1["status"] == data2["status"]


def test_health_endpoint_after_errors(client):
    """Test health endpoint works after application errors."""
    # Cause an error by sending invalid webhook
    client.post("/webhook", json={"from": "123", "body": "invalid"})
    
    # Health check should still work
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["ok", "degraded", "down"]
    
    # Error count should have increased
    assert data["error_metrics"]["total_errors"] > 0


def test_health_endpoint_json_content_type(client):
    """Test health endpoint returns JSON content type."""
    response = client.get("/health")
    
    assert response.headers["content-type"] == "application/json"


def test_health_endpoint_no_auth_required(client):
    """Test health endpoint does not require authentication."""
    # Should work without any auth headers
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_includes_dependencies(client):
    """Test health endpoint includes dependency status."""
    response = client.get("/health")
    data = response.json()
    
    # Should have dependencies section
    if "dependencies" in data:
        dependencies = data["dependencies"]
        assert isinstance(dependencies, dict)
        
        # Should check Union Action API
        if "union_action_api" in dependencies:
            union_status = dependencies["union_action_api"]
            assert "status" in union_status
            assert union_status["status"] in ["ok", "error", "unknown"]


def test_health_endpoint_caching_behavior(client):
    """Test health endpoint caching (if implemented)."""
    response1 = client.get("/health")
    time.sleep(0.1)  # Small delay
    response2 = client.get("/health")
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Timestamps might be same (cached) or different
    # Either is acceptable depending on cache implementation


def test_health_endpoint_concurrent_requests(client):
    """Test health endpoint handles concurrent requests."""
    import concurrent.futures
    
    def check_health():
        response = client.get("/health")
        return response.status_code
    
    # Make 10 concurrent health checks
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_health) for _ in range(10)]
        results = [f.result() for f in futures]
    
    # All should succeed
    assert all(status == 200 for status in results)


def test_health_endpoint_memory_info(client):
    """Test health endpoint includes memory information (if implemented)."""
    response = client.get("/health")
    data = response.json()
    
    # Memory info is optional but check if present
    if "memory" in data:
        memory = data["memory"]
        assert isinstance(memory, dict)
        
        # Should have useful memory metrics
        if "usage_mb" in memory:
            assert isinstance(memory["usage_mb"], (int, float))
            assert memory["usage_mb"] > 0


def test_health_endpoint_recent_error_count(client):
    """Test health endpoint includes recent error count."""
    response = client.get("/health")
    data = response.json()
    
    error_metrics = data["error_metrics"]
    
    # Should track recent errors
    if "recent_errors_count" in error_metrics:
        assert isinstance(error_metrics["recent_errors_count"], int)
        assert error_metrics["recent_errors_count"] >= 0


def test_health_endpoint_errors_by_category(client):
    """Test health endpoint breaks down errors by category."""
    response = client.get("/health")
    data = response.json()
    
    error_metrics = data["error_metrics"]
    
    # Should have category breakdown
    if "errors_by_category" in error_metrics:
        categories = error_metrics["errors_by_category"]
        assert isinstance(categories, dict)
        
        # Expected categories
        expected_categories = ["validation", "parsing", "integration", "unknown"]
        for category in expected_categories:
            if category in categories:
                assert isinstance(categories[category], int)
                assert categories[category] >= 0


def test_health_endpoint_degraded_status(client):
    """Test health endpoint returns degraded status when appropriate."""
    # Generate multiple errors to potentially trigger degraded state
    for _ in range(10):
        client.post("/webhook", json={"from": "123", "body": "invalid"})
    
    response = client.get("/health")
    data = response.json()
    
    # Status might be ok or degraded depending on thresholds
    assert data["status"] in ["ok", "degraded"]
    
    # Should still return 200 even if degraded
    assert response.status_code == 200


def test_health_endpoint_service_name(client):
    """Test health endpoint includes service name."""
    response = client.get("/health")
    data = response.json()
    
    # Should identify the service
    if "service" in data or "name" in data:
        service_name = data.get("service") or data.get("name")
        assert isinstance(service_name, str)
        assert "whatsapp" in service_name.lower() or "chatops" in service_name.lower()


def test_health_endpoint_environment(client):
    """Test health endpoint includes environment information."""
    response = client.get("/health")
    data = response.json()
    
    # Environment is useful for debugging
    if "environment" in data:
        env = data["environment"]
        assert env in ["dev", "test", "staging", "production"]

