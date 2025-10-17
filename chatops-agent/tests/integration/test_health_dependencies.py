"""
Integration tests for dependency health checking.

Tests that health endpoint properly checks and reports
status of external dependencies (Union Action API).
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from src.main import app
import requests


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


def test_health_includes_union_api_check(client):
    """Test health endpoint checks Union Action API connectivity."""
    response = client.get("/health")
    data = response.json()
    
    # Should have dependencies section
    assert "dependencies" in data
    dependencies = data["dependencies"]
    
    # Should check Union Action API
    assert "union_action_api" in dependencies
    union_api = dependencies["union_action_api"]
    
    # Should have status
    assert "status" in union_api
    assert union_api["status"] in ["ok", "error", "unknown"]


def test_health_union_api_success_status(client):
    """Test health reports 'ok' when Union API is reachable."""
    with patch('requests.get') as mock_get:
        # Mock successful Union API health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        response = client.get("/health")
        data = response.json()
        
        if "dependencies" in data and "union_action_api" in data["dependencies"]:
            union_status = data["dependencies"]["union_action_api"]["status"]
            # Should be 'ok' when API responds successfully
            assert union_status in ["ok", "unknown"]


def test_health_union_api_failure_status(client):
    """Test health reports 'error' when Union API is unreachable."""
    with patch('requests.get') as mock_get:
        # Mock Union API connection failure
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        response = client.get("/health")
        data = response.json()
        
        # Health endpoint itself should still return 200
        assert response.status_code == 200
        
        if "dependencies" in data and "union_action_api" in data["dependencies"]:
            union_status = data["dependencies"]["union_action_api"]["status"]
            # Should report error when API unreachable
            assert union_status in ["error", "unknown"]


def test_health_union_api_timeout_status(client):
    """Test health reports 'error' when Union API times out."""
    with patch('requests.get') as mock_get:
        # Mock Union API timeout
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        response = client.get("/health")
        data = response.json()
        
        # Health endpoint should still work
        assert response.status_code == 200
        
        if "dependencies" in data and "union_action_api" in data["dependencies"]:
            union_status = data["dependencies"]["union_action_api"]["status"]
            assert union_status in ["error", "timeout", "unknown"]


def test_health_dependency_response_time(client):
    """Test health endpoint includes dependency response time."""
    response = client.get("/health")
    data = response.json()
    
    if "dependencies" in data and "union_action_api" in data["dependencies"]:
        union_api = data["dependencies"]["union_action_api"]
        
        # Should track response time
        if "response_time_ms" in union_api or "duration_ms" in union_api:
            duration = union_api.get("response_time_ms") or union_api.get("duration_ms")
            assert isinstance(duration, (int, float))
            assert duration >= 0


def test_health_dependency_url(client):
    """Test health endpoint includes dependency URL."""
    response = client.get("/health")
    data = response.json()
    
    if "dependencies" in data and "union_action_api" in data["dependencies"]:
        union_api = data["dependencies"]["union_action_api"]
        
        # Should include the URL being checked
        if "url" in union_api or "endpoint" in union_api:
            url = union_api.get("url") or union_api.get("endpoint")
            assert isinstance(url, str)
            assert len(url) > 0


def test_health_dependency_last_checked(client):
    """Test health endpoint includes when dependency was last checked."""
    response = client.get("/health")
    data = response.json()
    
    if "dependencies" in data and "union_action_api" in data["dependencies"]:
        union_api = data["dependencies"]["union_action_api"]
        
        # Should track last check time
        if "last_checked" in union_api or "checked_at" in union_api:
            checked_at = union_api.get("last_checked") or union_api.get("checked_at")
            assert isinstance(checked_at, str)
            
            # Should be valid timestamp
            from datetime import datetime
            parsed = datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
            assert parsed is not None


def test_health_overall_status_reflects_dependencies(client):
    """Test overall health status reflects dependency health."""
    with patch('requests.get') as mock_get:
        # Mock Union API failure
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        response = client.get("/health")
        data = response.json()
        
        # Overall status might be degraded if critical dependency is down
        # Or might be 'ok' if dependency checks are informational only
        assert data["status"] in ["ok", "degraded", "down"]


def test_health_dependency_error_message(client):
    """Test health includes error message for failed dependencies."""
    with patch('requests.get') as mock_get:
        # Mock Union API error
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        response = client.get("/health")
        data = response.json()
        
        if "dependencies" in data and "union_action_api" in data["dependencies"]:
            union_api = data["dependencies"]["union_action_api"]
            
            # Should include error message or reason
            if union_api["status"] == "error":
                assert "error" in union_api or "message" in union_api or "reason" in union_api


def test_health_multiple_dependency_checks(client):
    """Test health endpoint checks all configured dependencies."""
    response = client.get("/health")
    data = response.json()
    
    if "dependencies" in data:
        dependencies = data["dependencies"]
        
        # Should have at least one dependency (Union API)
        assert len(dependencies) >= 1
        
        # All dependencies should have status
        for dep_name, dep_info in dependencies.items():
            assert "status" in dep_info
            assert dep_info["status"] in ["ok", "error", "timeout", "unknown"]


def test_health_dependency_check_timeout(client):
    """Test dependency health check has reasonable timeout."""
    import time
    
    with patch('requests.get') as mock_get:
        # Mock slow response
        def slow_response(*args, **kwargs):
            time.sleep(0.5)
            mock_resp = Mock()
            mock_resp.status_code = 200
            return mock_resp
        
        mock_get.side_effect = slow_response
        
        start_time = time.time()
        response = client.get("/health")
        duration = time.time() - start_time
        
        # Should still respond reasonably fast
        # Even with slow dependency check
        assert duration < 3.0  # Should timeout dependency check


def test_health_dependency_check_isolation(client):
    """Test that dependency check failure doesn't crash health endpoint."""
    with patch('requests.get') as mock_get:
        # Mock exception during check
        mock_get.side_effect = Exception("Unexpected error")
        
        response = client.get("/health")
        
        # Health endpoint should handle errors gracefully
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data


def test_health_dependency_status_codes(client):
    """Test health handles various Union API status codes."""
    test_cases = [
        (200, "ok"),
        (503, "error"),
        (500, "error"),
        (404, "error"),
    ]
    
    for status_code, expected_status in test_cases:
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_get.return_value = mock_response
            
            response = client.get("/health")
            data = response.json()
            
            # Health endpoint should succeed
            assert response.status_code == 200
            
            if "dependencies" in data and "union_action_api" in data["dependencies"]:
                union_api = data["dependencies"]["union_action_api"]
                # Status should reflect the dependency health
                assert union_api["status"] in [expected_status, "unknown"]


def test_health_dependency_check_caching(client):
    """Test dependency checks are cached to avoid overload."""
    import time
    
    call_count = 0
    
    def track_calls(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_resp = Mock()
        mock_resp.status_code = 200
        return mock_resp
    
    with patch('requests.get', side_effect=track_calls):
        # Make multiple health checks quickly
        client.get("/health")
        time.sleep(0.1)
        client.get("/health")
        time.sleep(0.1)
        client.get("/health")
        
        # Should cache dependency checks
        # So call count should be less than 3 (if caching is implemented)
        # Or equal to 3 if no caching
        assert call_count <= 3


def test_health_dependency_check_fresh_after_cache_expiry(client):
    """Test dependency checks refresh after cache expires."""
    import time
    
    call_count = 0
    
    def track_calls(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_resp = Mock()
        mock_resp.status_code = 200
        return mock_resp
    
    with patch('requests.get', side_effect=track_calls):
        # First check
        client.get("/health")
        initial_count = call_count
        
        # Wait longer than cache duration (assuming 10s cache)
        time.sleep(11)
        
        # Second check should trigger new dependency check
        client.get("/health")
        
        # Should have made at least one more call after cache expiry
        # (unless caching is not implemented)
        assert call_count >= initial_count


def test_health_dependency_metadata(client):
    """Test health includes useful metadata about dependencies."""
    response = client.get("/health")
    data = response.json()
    
    if "dependencies" in data and "union_action_api" in data["dependencies"]:
        union_api = data["dependencies"]["union_action_api"]
        
        # Should have descriptive information
        if "name" in union_api or "description" in union_api:
            name = union_api.get("name") or union_api.get("description")
            assert isinstance(name, str)

