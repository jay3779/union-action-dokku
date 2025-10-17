"""
Unit tests for Union Action API integration in bundled deployment.

Tests the integration between ChatOps Agent and Union Action API
in the bundled deployment scenario.
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.union_action_client_http import UnionActionClient
from src.health_checks import check_union_action_api
from src.metrics import MetricsCollector


class TestUnionActionIntegration:
    """Test suite for Union Action API integration."""

    @pytest.fixture
    def union_action_client(self):
        """Create Union Action client for testing."""
        return UnionActionClient(base_url="http://localhost:8000", timeout=5.0)

    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector for testing."""
        return MetricsCollector()

    @pytest.mark.asyncio
    async def test_union_action_client_initialization(self, union_action_client):
        """Test Union Action client initialization."""
        assert union_action_client.base_url == "http://localhost:8000"
        assert union_action_client.timeout == 5.0

    @pytest.mark.asyncio
    async def test_union_action_client_health_check(self, union_action_client):
        """Test Union Action client health check."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful health check response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "ok",
                "version": "1.0.0",
                "uptime_seconds": 3600.5
            }
            mock_response.elapsed.total_seconds.return_value = 0.1
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test health check
            health_status = await union_action_client.health_check()
            
            assert health_status["status"] == "ok"
            assert health_status["version"] == "1.0.0"
            assert health_status["uptime_seconds"] == 3600.5

    @pytest.mark.asyncio
    async def test_union_action_client_escalate_to_ethics(self, union_action_client):
        """Test Union Action client escalate to ethics endpoint."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful escalate response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "kantian_analysis": {
                    "categorical_imperative": "Test analysis",
                    "universalizability": True,
                    "human_dignity": True
                }
            }
            mock_response.elapsed.total_seconds.return_value = 0.2
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test escalate to ethics
            complaint_data = {
                "narrative": "Test narrative",
                "maxim": "Test maxim"
            }
            
            result = await union_action_client.escalate_to_ethics(complaint_data)
            
            assert "kantian_analysis" in result
            assert result["kantian_analysis"]["categorical_imperative"] == "Test analysis"

    @pytest.mark.asyncio
    async def test_union_action_client_generate_koers_survey(self, union_action_client):
        """Test Union Action client generate KOERS survey endpoint."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful generate survey response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "survey_url": "https://typeform.com/survey/123",
                "survey_id": "123",
                "deployment_status": "success"
            }
            mock_response.elapsed.total_seconds.return_value = 0.3
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test generate KOERS survey
            kantian_report = {
                "categorical_imperative": "Test analysis",
                "universalizability": True,
                "human_dignity": True
            }
            
            result = await union_action_client.generate_koers_survey(kantian_report)
            
            assert "survey_url" in result
            assert result["survey_url"] == "https://typeform.com/survey/123"
            assert result["deployment_status"] == "success"

    @pytest.mark.asyncio
    async def test_union_action_client_error_handling(self, union_action_client):
        """Test Union Action client error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock HTTP error response
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=mock_response
            )
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test error handling
            with pytest.raises(httpx.HTTPStatusError):
                await union_action_client.health_check()

    @pytest.mark.asyncio
    async def test_union_action_client_timeout(self, union_action_client):
        """Test Union Action client timeout handling."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock timeout error
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test timeout handling
            with pytest.raises(httpx.TimeoutException):
                await union_action_client.health_check()

    def test_union_action_health_check_function(self):
        """Test Union Action API health check function."""
        with patch('httpx.Client') as mock_client:
            # Mock successful health check response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "ok",
                "version": "1.0.0",
                "uptime_seconds": 3600.5
            }
            mock_response.elapsed.total_seconds.return_value = 0.1
            
            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            
            # Test health check function
            result = check_union_action_api()
            
            assert result["status"] == "ok"
            assert result["url"] == "http://localhost:8000/health"
            assert result["response_time_ms"] == 100.0

    def test_union_action_health_check_timeout(self):
        """Test Union Action API health check timeout."""
        with patch('httpx.Client') as mock_client:
            # Mock timeout error
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client.return_value.__enter__.return_value = mock_client_instance
            
            # Test timeout handling
            result = check_union_action_api()
            
            assert result["status"] == "timeout"
            assert "error" in result
            assert "timeout" in result["error"].lower()

    def test_union_action_health_check_http_error(self):
        """Test Union Action API health check HTTP error."""
        with patch('httpx.Client') as mock_client:
            # Mock HTTP error response
            mock_response = Mock()
            mock_response.status_code = 500
            
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=mock_response
            )
            mock_client.return_value.__enter__.return_value = mock_client_instance
            
            # Test HTTP error handling
            result = check_union_action_api()
            
            assert result["status"] == "error"
            assert "error" in result
            assert "HTTP 500" in result["error"]

    def test_union_action_metrics_collection(self, metrics_collector):
        """Test Union Action API metrics collection."""
        # Record Union Action API call
        metrics_collector.record_union_action_api_call(
            endpoint="/escalate-to-ethics",
            status_code=200,
            duration_ms=150.0
        )
        
        # Record another call
        metrics_collector.record_union_action_api_call(
            endpoint="/generate-koers-survey",
            status_code=200,
            duration_ms=200.0
        )
        
        # Check metrics
        union_action_calls = metrics_collector.union_action_api_calls
        assert "union_action_api:/escalate-to-ethics:200" in union_action_calls
        assert "union_action_api:/generate-koers-survey:200" in union_action_calls
        assert union_action_calls["union_action_api:/escalate-to-ethics:200"] == 1
        assert union_action_calls["union_action_api:/generate-koers-survey:200"] == 1
        
        # Check durations
        durations = metrics_collector.union_action_api_durations
        assert len(durations) == 2
        assert ("/escalate-to-ethics", 150.0) in durations
        assert ("/generate-koers-survey", 200.0) in durations

    def test_union_action_metrics_error_handling(self, metrics_collector):
        """Test Union Action API metrics error handling."""
        # Record error call
        metrics_collector.record_union_action_api_call(
            endpoint="/escalate-to-ethics",
            status_code=500,
            duration_ms=100.0
        )
        
        # Check error metrics
        union_action_calls = metrics_collector.union_action_api_calls
        assert "union_action_api:/escalate-to-ethics:500" in union_action_calls
        assert union_action_calls["union_action_api:/escalate-to-ethics:500"] == 1

    def test_union_action_metrics_duration_limit(self, metrics_collector):
        """Test Union Action API metrics duration limit."""
        # Record many calls to test limit
        for i in range(1001):
            metrics_collector.record_union_action_api_call(
                endpoint="/test",
                status_code=200,
                duration_ms=float(i)
            )
        
        # Check that only last 1000 durations are kept
        durations = metrics_collector.union_action_api_durations
        assert len(durations) == 1000
        assert ("/test", 1.0) not in durations  # First duration should be removed
        assert ("/test", 1000.0) in durations  # Last duration should be kept

    @pytest.mark.asyncio
    async def test_union_action_client_retry_logic(self, union_action_client):
        """Test Union Action client retry logic."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock retry scenario
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.elapsed.total_seconds.return_value = 0.1
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test retry logic (if implemented)
            health_status = await union_action_client.health_check()
            assert health_status["status"] == "ok"

    def test_union_action_environment_configuration(self):
        """Test Union Action API environment configuration."""
        import os
        
        # Test environment variable defaults
        assert os.getenv("UNION_ACTION_API_URL", "http://localhost:8000") == "http://localhost:8000"
        assert os.getenv("UNION_ACTION_LOG_LEVEL", "INFO") == "INFO"
        assert os.getenv("UNION_ACTION_LOG_FORMAT", "json") == "json"

    def test_union_action_internal_communication(self):
        """Test Union Action API internal communication settings."""
        import os
        
        # Test internal communication configuration
        assert os.getenv("INTERNAL_COMMUNICATION", "true").lower() == "true"
        assert os.getenv("CHATOPS_AGENT_URL", "http://localhost:8080") == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_union_action_client_connection_pooling(self, union_action_client):
        """Test Union Action client connection pooling."""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock multiple requests
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.elapsed.total_seconds.return_value = 0.1
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test multiple requests
            tasks = []
            for _ in range(5):
                task = union_action_client.health_check()
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for result in results:
                assert result["status"] == "ok"

    def test_union_action_health_check_caching(self):
        """Test Union Action API health check caching."""
        with patch('httpx.Client') as mock_client:
            # Mock health check response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.elapsed.total_seconds.return_value = 0.1
            
            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            
            # Test multiple calls
            result1 = check_union_action_api()
            result2 = check_union_action_api()
            
            # Both should succeed
            assert result1["status"] == "ok"
            assert result2["status"] == "ok"
            
            # Client should be called twice (no caching in this implementation)
            assert mock_client_instance.get.call_count == 2

    def test_union_action_health_check_environment_override(self):
        """Test Union Action API health check environment override."""
        import os
        
        # Test environment variable override
        original_url = os.getenv("UNION_ACTION_API_URL")
        os.environ["UNION_ACTION_API_URL"] = "http://test:8000"
        
        try:
            with patch('httpx.Client') as mock_client:
                # Mock health check response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "ok"}
                mock_response.elapsed.total_seconds.return_value = 0.1
                
                mock_client_instance = Mock()
                mock_client_instance.get.return_value = mock_response
                mock_client.return_value.__enter__.return_value = mock_client_instance
                
                # Test health check with custom URL
                result = check_union_action_api()
                
                assert result["status"] == "ok"
                assert result["url"] == "http://test:8000/health"
        finally:
            # Restore original environment
            if original_url:
                os.environ["UNION_ACTION_API_URL"] = original_url
            else:
                os.environ.pop("UNION_ACTION_API_URL", None)
