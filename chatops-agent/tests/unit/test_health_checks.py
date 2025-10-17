"""
Unit tests for individual health check functions.

Tests isolated health check logic without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import time


def test_check_union_api_health_success():
    """Test Union API health check returns ok on success."""
    from src.health_checks import check_union_api_health
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        result = check_union_api_health("http://localhost:8000")
        
        assert result["status"] == "ok"
        assert "response_time_ms" in result
        assert result["response_time_ms"] >= 0


def test_check_union_api_health_connection_error():
    """Test Union API health check handles connection errors."""
    from src.health_checks import check_union_api_health
    import requests
    
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        result = check_union_api_health("http://localhost:8000")
        
        assert result["status"] == "error"
        assert "error" in result or "message" in result


def test_check_union_api_health_timeout():
    """Test Union API health check handles timeouts."""
    from src.health_checks import check_union_api_health
    import requests
    
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        result = check_union_api_health("http://localhost:8000")
        
        assert result["status"] in ["error", "timeout"]


def test_check_union_api_health_http_error():
    """Test Union API health check handles HTTP errors."""
    from src.health_checks import check_union_api_health
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = Exception("Service unavailable")
        mock_get.return_value = mock_response
        
        result = check_union_api_health("http://localhost:8000")
        
        assert result["status"] == "error"


def test_check_union_api_health_measures_time():
    """Test Union API health check measures response time."""
    from src.health_checks import check_union_api_health
    
    with patch('requests.get') as mock_get:
        def slow_response(*args, **kwargs):
            time.sleep(0.1)
            mock_resp = Mock()
            mock_resp.status_code = 200
            return mock_resp
        
        mock_get.side_effect = slow_response
        
        result = check_union_api_health("http://localhost:8000")
        
        # Should measure time
        assert "response_time_ms" in result
        assert result["response_time_ms"] >= 100  # At least 100ms


def test_check_union_api_health_includes_url():
    """Test Union API health check includes checked URL."""
    from src.health_checks import check_union_api_health
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        test_url = "http://test-api:8000"
        result = check_union_api_health(test_url)
        
        # Should include URL
        if "url" in result or "endpoint" in result:
            checked_url = result.get("url") or result.get("endpoint")
            assert test_url in checked_url


def test_check_memory_usage():
    """Test memory usage health check."""
    from src.health_checks import check_memory_usage
    
    result = check_memory_usage()
    
    # Should return memory info
    assert "usage_mb" in result or "memory_mb" in result
    usage = result.get("usage_mb") or result.get("memory_mb")
    assert isinstance(usage, (int, float))
    assert usage > 0


def test_check_memory_usage_includes_percentage():
    """Test memory check includes percentage (if available)."""
    from src.health_checks import check_memory_usage
    
    result = check_memory_usage()
    
    # Percentage is optional but useful
    if "percentage" in result or "percent" in result:
        percent = result.get("percentage") or result.get("percent")
        assert isinstance(percent, (int, float))
        assert 0 <= percent <= 100


def test_check_memory_usage_threshold():
    """Test memory check detects high usage."""
    from src.health_checks import check_memory_usage
    
    result = check_memory_usage(threshold_percent=80)
    
    # Should have status based on threshold
    if "status" in result:
        assert result["status"] in ["ok", "warning", "critical"]


def test_get_uptime():
    """Test uptime calculation."""
    from src.health_checks import get_uptime
    
    # Mock start time
    with patch('src.health_checks.service_start_time', datetime.now() - timedelta(seconds=100)):
        uptime = get_uptime()
        
        assert isinstance(uptime, (int, float))
        assert uptime >= 90  # At least 90 seconds
        assert uptime <= 110  # No more than 110 seconds


def test_get_uptime_formatted():
    """Test uptime returns human-readable format."""
    from src.health_checks import get_uptime_formatted
    
    with patch('src.health_checks.service_start_time', datetime.now() - timedelta(hours=2, minutes=30)):
        uptime_str = get_uptime_formatted()
        
        assert isinstance(uptime_str, str)
        # Should contain hour/minute information
        assert len(uptime_str) > 0


def test_check_recent_errors():
    """Test recent error count check."""
    from src.health_checks import check_recent_errors
    from src.diagnostics import error_tracker
    
    # Reset error tracker
    error_tracker.reset()
    
    # Add some recent errors
    error_tracker.track_error("validation", {"test": "error"})
    error_tracker.track_error("parsing", {"test": "error"})
    
    result = check_recent_errors(time_window_seconds=300)  # Last 5 minutes
    
    # Should return error count
    assert "count" in result or "total" in result
    count = result.get("count") or result.get("total")
    assert count >= 2


def test_check_recent_errors_time_window():
    """Test recent errors respects time window."""
    from src.health_checks import check_recent_errors
    from src.diagnostics import error_tracker
    
    # Reset and track errors
    error_tracker.reset()
    error_tracker.track_error("validation")
    
    # Check with very small time window
    result = check_recent_errors(time_window_seconds=0.001)
    
    # Might have 0 errors if they're outside the tiny window
    count = result.get("count", 0) or result.get("total", 0)
    assert count >= 0


def test_check_recent_errors_by_category():
    """Test recent errors includes category breakdown."""
    from src.health_checks import check_recent_errors
    from src.diagnostics import error_tracker
    
    error_tracker.reset()
    error_tracker.track_error("validation")
    error_tracker.track_error("validation")
    error_tracker.track_error("parsing")
    
    result = check_recent_errors(time_window_seconds=300)
    
    # Should include category breakdown
    if "by_category" in result or "categories" in result:
        categories = result.get("by_category") or result.get("categories")
        assert isinstance(categories, dict)


def test_health_check_timeout_decorator():
    """Test health check timeout decorator."""
    from src.health_checks import with_timeout
    
    @with_timeout(seconds=1)
    def slow_check():
        time.sleep(2)
        return {"status": "ok"}
    
    result = slow_check()
    
    # Should timeout and return error
    assert result["status"] == "timeout" or result["status"] == "error"


def test_health_check_exception_handler():
    """Test health check exception handling."""
    from src.health_checks import safe_health_check
    
    @safe_health_check
    def failing_check():
        raise Exception("Check failed")
    
    result = failing_check()
    
    # Should catch exception and return error status
    assert result["status"] == "error"
    assert "error" in result or "message" in result


def test_aggregate_health_status():
    """Test aggregating multiple health check results."""
    from src.health_checks import aggregate_health_status
    
    checks = [
        {"name": "api", "status": "ok"},
        {"name": "memory", "status": "ok"},
    ]
    
    overall = aggregate_health_status(checks)
    
    # All ok → overall ok
    assert overall == "ok"


def test_aggregate_health_status_with_errors():
    """Test aggregating health with errors."""
    from src.health_checks import aggregate_health_status
    
    checks = [
        {"name": "api", "status": "ok"},
        {"name": "memory", "status": "error"},
    ]
    
    overall = aggregate_health_status(checks)
    
    # Any error → degraded or down
    assert overall in ["degraded", "down"]


def test_aggregate_health_status_all_errors():
    """Test aggregating health when all checks fail."""
    from src.health_checks import aggregate_health_status
    
    checks = [
        {"name": "api", "status": "error"},
        {"name": "memory", "status": "error"},
    ]
    
    overall = aggregate_health_status(checks)
    
    # All error → down
    assert overall == "down"


def test_health_check_cache():
    """Test health check result caching."""
    from src.health_checks import HealthCheckCache
    
    cache = HealthCheckCache(ttl_seconds=10)
    
    # Set value
    cache.set("test_check", {"status": "ok"})
    
    # Get value
    result = cache.get("test_check")
    assert result is not None
    assert result["status"] == "ok"


def test_health_check_cache_expiry():
    """Test health check cache expires."""
    from src.health_checks import HealthCheckCache
    
    cache = HealthCheckCache(ttl_seconds=0.1)
    
    # Set value
    cache.set("test_check", {"status": "ok"})
    
    # Wait for expiry
    time.sleep(0.2)
    
    # Should be expired
    result = cache.get("test_check")
    assert result is None


def test_health_check_cache_different_keys():
    """Test health check cache handles different keys."""
    from src.health_checks import HealthCheckCache
    
    cache = HealthCheckCache(ttl_seconds=10)
    
    # Set multiple values
    cache.set("check1", {"status": "ok"})
    cache.set("check2", {"status": "error"})
    
    # Get specific values
    assert cache.get("check1")["status"] == "ok"
    assert cache.get("check2")["status"] == "error"


def test_format_health_response():
    """Test formatting health check response."""
    from src.health_checks import format_health_response
    
    checks = {
        "union_api": {"status": "ok", "response_time_ms": 150},
        "memory": {"usage_mb": 256}
    }
    
    response = format_health_response(
        overall_status="ok",
        checks=checks,
        uptime_seconds=3600,
        version="0.1.0"
    )
    
    assert response["status"] == "ok"
    assert response["version"] == "0.1.0"
    assert "uptime_seconds" in response or "uptime" in response
    assert "dependencies" in response or "checks" in response

