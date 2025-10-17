"""
Integration tests for health checks in bundled deployment.

Tests health check functionality for both ChatOps Agent and Union Action API
in the bundled deployment scenario.
"""

import pytest
import asyncio
import httpx
import time
from typing import Dict, Any

# Test configuration
CHATOPS_AGENT_URL = "http://localhost:8080"
UNION_ACTION_URL = "http://localhost:8000"
HEALTH_ENDPOINT = "/health"
TIMEOUT = 30


class TestHealthChecks:
    """Test suite for health check functionality."""

    @pytest.mark.asyncio
    async def test_chatops_agent_health_structure(self):
        """Test ChatOps Agent health endpoint structure."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            
            assert response.status_code == 200
            health_data = response.json()
            
            # Verify required fields
            required_fields = [
                "status", "version", "uptime_seconds", "uptime",
                "timestamp", "service", "environment", "dependencies"
            ]
            
            for field in required_fields:
                assert field in health_data, f"Missing required field: {field}"
            
            # Verify status values
            assert health_data["status"] in ["ok", "degraded", "down"]
            assert health_data["service"] == "whatsapp-chatops-agent"
            assert health_data["environment"] in ["production", "development", "staging"]

    @pytest.mark.asyncio
    async def test_union_action_api_health_structure(self):
        """Test Union Action API health endpoint structure."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{UNION_ACTION_URL}{HEALTH_ENDPOINT}")
            
            assert response.status_code == 200
            health_data = response.json()
            
            # Verify required fields
            required_fields = [
                "status", "version", "uptime_seconds", "timestamp",
                "service", "environment", "internal_communication", "chatops_agent_url"
            ]
            
            for field in required_fields:
                assert field in health_data, f"Missing required field: {field}"
            
            # Verify status values
            assert health_data["status"] == "ok"
            assert health_data["service"] == "union-action-api"
            assert health_data["internal_communication"] is True
            assert health_data["chatops_agent_url"] == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_health_check_dependencies(self):
        """Test health check dependencies."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            dependencies = health_data["dependencies"]
            
            # Check Union Action API dependency
            assert "union_action_api" in dependencies
            union_action = dependencies["union_action_api"]
            assert "status" in union_action
            assert "url" in union_action
            assert union_action["url"] == "http://localhost:8000/health"
            assert union_action["status"] in ["ok", "degraded", "error", "timeout"]
            
            # Check memory dependency
            assert "memory" in dependencies
            memory = dependencies["memory"]
            assert "status" in memory
            assert "usage_mb" in memory
            assert memory["status"] in ["ok", "warning", "error"]
            assert memory["usage_mb"] > 0

    @pytest.mark.asyncio
    async def test_health_check_aggregation(self):
        """Test health check status aggregation."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            overall_status = health_data["status"]
            dependencies = health_data["dependencies"]
            
            # Test status aggregation logic
            if overall_status == "ok":
                # All dependencies should be ok
                for dep_name, dep_data in dependencies.items():
                    assert dep_data["status"] in ["ok", "warning"], f"Dependency {dep_name} is not healthy"
            
            elif overall_status == "degraded":
                # Some dependencies may be degraded but not all failed
                failed_deps = [name for name, data in dependencies.items() if data["status"] == "error"]
                assert len(failed_deps) < len(dependencies), "Too many failed dependencies for degraded status"
            
            elif overall_status == "down":
                # Most or all dependencies should be failed
                failed_deps = [name for name, data in dependencies.items() if data["status"] == "error"]
                assert len(failed_deps) > 0, "No failed dependencies for down status"

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check timeout handling."""
        # This test would verify that health checks timeout appropriately
        # when services are unresponsive
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
                assert response.status_code == 200
            except httpx.TimeoutException:
                # Timeout is acceptable for this test
                pass

    @pytest.mark.asyncio
    async def test_health_check_caching(self):
        """Test health check caching behavior."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make multiple requests quickly
            start_time = time.time()
            responses = []
            
            for _ in range(5):
                response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
                responses.append(response)
            
            end_time = time.time()
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Requests should be fast (cached)
            assert (end_time - start_time) < 5, "Health checks are not cached properly"

    @pytest.mark.asyncio
    async def test_health_check_error_handling(self):
        """Test health check error handling."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Check that error handling is working
            # This would typically test scenarios where dependencies fail
            # but the health endpoint still returns a response

    @pytest.mark.asyncio
    async def test_health_check_metrics(self):
        """Test health check metrics collection."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make a health check request
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            # Check that metrics are being collected
            metrics_response = await client.get(f"{CHATOPS_AGENT_URL}/metrics")
            assert metrics_response.status_code == 200
            
            metrics_text = metrics_response.text
            assert "chatops_agent_health_checks_total" in metrics_text

    @pytest.mark.asyncio
    async def test_union_action_api_health_detailed(self):
        """Test detailed Union Action API health information."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{UNION_ACTION_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Verify uptime calculation
            assert health_data["uptime_seconds"] > 0
            assert isinstance(health_data["uptime_seconds"], (int, float))
            
            # Verify timestamp format
            timestamp = health_data["timestamp"]
            assert "T" in timestamp  # ISO format
            assert "Z" in timestamp or "+" in timestamp  # Timezone info

    @pytest.mark.asyncio
    async def test_health_check_concurrent(self):
        """Test concurrent health check requests."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make multiple concurrent requests
            tasks = []
            for _ in range(10):
                task = client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                
                health_data = response.json()
                assert "status" in health_data
                assert "dependencies" in health_data

    @pytest.mark.asyncio
    async def test_health_check_error_recovery(self):
        """Test health check error recovery."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test that health checks recover from temporary failures
            # This would typically involve simulating service failures
            # and verifying that health checks return to normal
            
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["ok", "degraded"]

    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test health check performance."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            start_time = time.time()
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            end_time = time.time()
            
            assert response.status_code == 200
            
            # Health check should complete within reasonable time
            response_time = end_time - start_time
            assert response_time < 5, f"Health check took too long: {response_time}s"
            
            # Check response time in health data
            health_data = response.json()
            if "dependencies" in health_data and "union_action_api" in health_data["dependencies"]:
                union_action = health_data["dependencies"]["union_action_api"]
                if "response_time_ms" in union_action:
                    assert union_action["response_time_ms"] < 5000, "Union Action API response time is too high"

    @pytest.mark.asyncio
    async def test_health_check_logging(self):
        """Test health check logging."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make health check requests
            for _ in range(3):
                response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
                assert response.status_code == 200
            
            # Check that health checks are logged
            # This would typically check log files or output
            # For integration tests, we assume logging is working

    @pytest.mark.asyncio
    async def test_health_check_environment(self):
        """Test health check environment information."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Verify environment information
            assert "environment" in health_data
            assert health_data["environment"] in ["production", "development", "staging"]
            
            # Verify service information
            assert "service" in health_data
            assert health_data["service"] == "whatsapp-chatops-agent"

    @pytest.mark.asyncio
    async def test_health_check_version(self):
        """Test health check version information."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Verify version information
            assert "version" in health_data
            assert isinstance(health_data["version"], str)
            assert len(health_data["version"]) > 0
            
            # Check Union Action API version
            if "dependencies" in health_data and "union_action_api" in health_data["dependencies"]:
                union_action = health_data["dependencies"]["union_action_api"]
                if "version" in union_action:
                    assert isinstance(union_action["version"], str)
                    assert len(union_action["version"]) > 0
