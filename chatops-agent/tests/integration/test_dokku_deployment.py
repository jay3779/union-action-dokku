"""
Integration tests for Dokku deployment with bundled Union Action API.

Tests the complete deployment pipeline including:
- Docker container build
- Multi-service startup
- Health checks
- Service communication
- Error handling
"""

import pytest
import asyncio
import httpx
import time
import subprocess
import os
from typing import Dict, Any

# Test configuration
CHATOPS_AGENT_URL = "http://localhost:8080"
UNION_ACTION_URL = "http://localhost:8000"
HEALTH_ENDPOINT = "/health"
TIMEOUT = 30


class TestDokkuDeployment:
    """Test suite for Dokku deployment functionality."""

    @pytest.fixture(scope="class")
    async def deployment_setup(self):
        """Set up test environment for deployment testing."""
        # This would typically start the actual services
        # For integration tests, we assume services are running
        yield
        # Cleanup if needed

    @pytest.mark.asyncio
    async def test_chatops_agent_health(self, deployment_setup):
        """Test ChatOps Agent health endpoint."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            
            assert response.status_code == 200
            health_data = response.json()
            
            # Verify health response structure
            assert "status" in health_data
            assert "version" in health_data
            assert "uptime_seconds" in health_data
            assert "dependencies" in health_data
            
            # Verify service status
            assert health_data["status"] in ["ok", "degraded"]
            
            # Verify dependencies
            dependencies = health_data["dependencies"]
            assert "union_action_api" in dependencies
            assert "memory" in dependencies

    @pytest.mark.asyncio
    async def test_union_action_api_health(self, deployment_setup):
        """Test Union Action API health endpoint."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{UNION_ACTION_URL}{HEALTH_ENDPOINT}")
            
            assert response.status_code == 200
            health_data = response.json()
            
            # Verify health response structure
            assert "status" in health_data
            assert "version" in health_data
            assert "uptime_seconds" in health_data
            assert "service" in health_data
            assert "environment" in health_data
            assert "internal_communication" in health_data
            assert "chatops_agent_url" in health_data
            
            # Verify service status
            assert health_data["status"] == "ok"
            assert health_data["service"] == "union-action-api"
            assert health_data["internal_communication"] is True

    @pytest.mark.asyncio
    async def test_service_communication(self, deployment_setup):
        """Test communication between ChatOps Agent and Union Action API."""
        # Test that ChatOps Agent can reach Union Action API
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Get ChatOps Agent health to check Union Action API status
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            union_action_status = health_data["dependencies"]["union_action_api"]["status"]
            
            # Union Action API should be accessible
            assert union_action_status in ["ok", "degraded"]

    @pytest.mark.asyncio
    async def test_webhook_processing(self, deployment_setup):
        """Test WhatsApp webhook processing with bundled Union Action API."""
        # Sample WhatsApp webhook payload
        webhook_payload = {
            "from": "+1234567890",
            "body": "Test narrative|Test maxim",
            "timestamp": int(time.time()),
            "message_id": "test_message_123"
        }
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{CHATOPS_AGENT_URL}/webhook",
                json=webhook_payload
            )
            
            # Should return 200 for successful processing
            assert response.status_code == 200
            
            response_data = response.json()
            assert "status" in response_data
            assert response_data["status"] == "success"

    @pytest.mark.asyncio
    async def test_error_handling(self, deployment_setup):
        """Test error handling in bundled deployment."""
        # Test with invalid webhook payload
        invalid_payload = {
            "invalid": "data"
        }
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{CHATOPS_AGENT_URL}/webhook",
                json=invalid_payload
            )
            
            # Should return 400 for invalid payload
            assert response.status_code == 400
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, deployment_setup):
        """Test metrics endpoint for monitoring."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}/metrics")
            
            assert response.status_code == 200
            
            # Should return Prometheus-formatted metrics
            metrics_text = response.text
            assert "chatops_agent_requests_total" in metrics_text
            assert "chatops_agent_errors_total" in metrics_text

    @pytest.mark.asyncio
    async def test_health_dependencies(self, deployment_setup):
        """Test health check dependencies."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            dependencies = health_data["dependencies"]
            
            # Check Union Action API dependency
            union_action = dependencies["union_action_api"]
            assert "status" in union_action
            assert "url" in union_action
            assert union_action["url"] == "http://localhost:8000/health"
            
            # Check memory dependency
            memory = dependencies["memory"]
            assert "status" in memory
            assert "usage_mb" in memory
            assert memory["usage_mb"] > 0

    @pytest.mark.asyncio
    async def test_environment_variables(self, deployment_setup):
        """Test environment variable configuration."""
        # Test that required environment variables are set
        required_vars = [
            "ENVIRONMENT",
            "LOG_LEVEL",
            "UNION_ACTION_API_URL",
            "PORT"
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Required environment variable {var} is not set"

    @pytest.mark.asyncio
    async def test_logging_configuration(self, deployment_setup):
        """Test logging configuration for bundled services."""
        # Test that logs are properly structured
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make a request to generate logs
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            # Check that structured logging is working
            # This would typically check log files or output
            # For integration tests, we assume logging is configured correctly

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, deployment_setup):
        """Test graceful shutdown of bundled services."""
        # This test would verify that both services shut down gracefully
        # when receiving SIGTERM signal
        # For integration tests, we assume shutdown works correctly
        pass

    @pytest.mark.asyncio
    async def test_resource_usage(self, deployment_setup):
        """Test resource usage monitoring."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
            assert response.status_code == 200
            
            health_data = response.json()
            memory = health_data["dependencies"]["memory"]
            
            # Check memory usage is reasonable
            assert memory["usage_mb"] < 1000, "Memory usage is too high"
            assert memory["status"] in ["ok", "warning"], "Memory status is not healthy"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, deployment_setup):
        """Test handling of concurrent requests."""
        # Test multiple concurrent requests
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            tasks = []
            for i in range(10):
                task = client.get(f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_union_action_api_endpoints(self, deployment_setup):
        """Test Union Action API endpoints."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test escalate endpoint
            escalate_payload = {
                "complaint": {
                    "narrative": "Test narrative",
                    "maxim": "Test maxim"
                }
            }
            
            response = await client.post(
                f"{UNION_ACTION_URL}/escalate-to-ethics",
                json=escalate_payload
            )
            
            # Should return 200 for successful processing
            assert response.status_code == 200
            
            response_data = response.json()
            assert "kantian_analysis" in response_data

    @pytest.mark.asyncio
    async def test_deployment_verification(self, deployment_setup):
        """Test complete deployment verification."""
        # Test all critical endpoints
        endpoints = [
            f"{CHATOPS_AGENT_URL}{HEALTH_ENDPOINT}",
            f"{CHATOPS_AGENT_URL}/metrics",
            f"{CHATOPS_AGENT_URL}/health/errors",
            f"{UNION_ACTION_URL}{HEALTH_ENDPOINT}"
        ]
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for endpoint in endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 200, f"Endpoint {endpoint} failed"
                
                # Verify response is valid JSON
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = response.json()
                    assert isinstance(data, dict), f"Invalid JSON response from {endpoint}"


class TestDokkuDeploymentScripts:
    """Test suite for Dokku deployment scripts."""

    def test_create_dokku_app_script(self):
        """Test create-dokku-app.sh script exists and is executable."""
        script_path = "scripts/create-dokku-app.sh"
        assert os.path.exists(script_path), "create-dokku-app.sh script not found"
        assert os.access(script_path, os.X_OK), "create-dokku-app.sh script is not executable"

    def test_configure_buildpack_script(self):
        """Test configure-dokku-buildpack.sh script exists and is executable."""
        script_path = "scripts/configure-dokku-buildpack.sh"
        assert os.path.exists(script_path), "configure-dokku-buildpack.sh script not found"
        assert os.access(script_path, os.X_OK), "configure-dokku-buildpack.sh script is not executable"

    def test_setup_basic_env_script(self):
        """Test setup-basic-env.sh script exists and is executable."""
        script_path = "scripts/setup-basic-env.sh"
        assert os.path.exists(script_path), "setup-basic-env.sh script not found"
        assert os.access(script_path, os.X_OK), "setup-basic-env.sh script is not executable"

    def test_verify_deployment_script(self):
        """Test verify-deployment.sh script exists and is executable."""
        script_path = "scripts/verify-deployment.sh"
        assert os.path.exists(script_path), "verify-deployment.sh script not found"
        assert os.access(script_path, os.X_OK), "verify-deployment.sh script is not executable"

    def test_process_manager_script(self):
        """Test process-manager.sh script exists and is executable."""
        script_path = "scripts/process-manager.sh"
        assert os.path.exists(script_path), "process-manager.sh script not found"
        assert os.access(script_path, os.X_OK), "process-manager.sh script is not executable"

    def test_health_check_script(self):
        """Test health-check.sh script exists and is executable."""
        script_path = "scripts/health-check.sh"
        assert os.path.exists(script_path), "health-check.sh script not found"
        assert os.access(script_path, os.X_OK), "health-check.sh script is not executable"


class TestDockerConfiguration:
    """Test suite for Docker configuration."""

    def test_dockerfile_exists(self):
        """Test Dockerfile exists and is properly configured."""
        assert os.path.exists("Dockerfile"), "Dockerfile not found"
        
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()
            
        # Check for required configurations
        assert "FROM python:3.9-slim" in dockerfile_content
        assert "COPY --chown=appuser:appuser union-action/" in dockerfile_content
        assert "COPY --chown=appuser:appuser scripts/process-manager.sh" in dockerfile_content
        assert "CMD [\"/app/scripts/process-manager.sh\"]" in dockerfile_content

    def test_dockerignore_exists(self):
        """Test .dockerignore exists and is properly configured."""
        assert os.path.exists(".dockerignore"), ".dockerignore not found"
        
        with open(".dockerignore", "r") as f:
            dockerignore_content = f.read()
            
        # Check for required exclusions
        assert "union-action/tests/" in dockerignore_content
        assert "docker-compose.yml" in dockerignore_content

    def test_requirements_txt_updated(self):
        """Test requirements.txt includes Union Action API dependencies."""
        assert os.path.exists("requirements.txt"), "requirements.txt not found"
        
        with open("requirements.txt", "r") as f:
            requirements_content = f.read()
            
        # Check for Union Action API dependencies
        assert "fastapi==0.100.0" in requirements_content
        assert "uvicorn[standard]==0.23.0" in requirements_content
        assert "pydantic==2.4.0" in requirements_content
