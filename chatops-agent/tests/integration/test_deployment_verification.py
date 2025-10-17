"""
Integration tests for deployment verification.

Tests the complete deployment verification process including:
- Application startup
- Service health
- Endpoint availability
- Configuration validation
- Error handling
"""

import pytest
import asyncio
import httpx
import time
import os
from typing import Dict, Any, List

# Test configuration
CHATOPS_AGENT_URL = "http://localhost:8080"
UNION_ACTION_URL = "http://localhost:8000"
TIMEOUT = 30


class TestDeploymentVerification:
    """Test suite for deployment verification."""

    @pytest.mark.asyncio
    async def test_application_startup(self):
        """Test application startup process."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test ChatOps Agent startup
            response = await client.get(f"{CHATOPS_AGENT_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["ok", "degraded"]
            assert health_data["service"] == "whatsapp-chatops-agent"
            
            # Test Union Action API startup
            response = await client.get(f"{UNION_ACTION_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "ok"
            assert health_data["service"] == "union-action-api"

    @pytest.mark.asyncio
    async def test_service_communication(self):
        """Test communication between services."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test ChatOps Agent can reach Union Action API
            response = await client.get(f"{CHATOPS_AGENT_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            dependencies = health_data["dependencies"]
            
            # Verify Union Action API is accessible
            assert "union_action_api" in dependencies
            union_action = dependencies["union_action_api"]
            assert union_action["status"] in ["ok", "degraded"]
            assert union_action["url"] == "http://localhost:8000/health"

    @pytest.mark.asyncio
    async def test_endpoint_availability(self):
        """Test all critical endpoints are available."""
        endpoints = [
            f"{CHATOPS_AGENT_URL}/health",
            f"{CHATOPS_AGENT_URL}/metrics",
            f"{CHATOPS_AGENT_URL}/health/errors",
            f"{UNION_ACTION_URL}/health",
            f"{UNION_ACTION_URL}/docs",
            f"{UNION_ACTION_URL}/redoc"
        ]
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for endpoint in endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 200, f"Endpoint {endpoint} is not available"
                
                # Verify response content type
                content_type = response.headers.get("content-type", "")
                if endpoint.endswith("/health"):
                    assert "application/json" in content_type, f"Health endpoint {endpoint} should return JSON"
                elif endpoint.endswith("/docs") or endpoint.endswith("/redoc"):
                    assert "text/html" in content_type, f"Documentation endpoint {endpoint} should return HTML"

    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test environment variable validation
            response = await client.get(f"{CHATOPS_AGENT_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Verify environment configuration
            assert "environment" in health_data
            assert health_data["environment"] in ["production", "development", "staging"]
            
            # Verify service configuration
            assert "service" in health_data
            assert health_data["service"] == "whatsapp-chatops-agent"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in deployment."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test invalid endpoint
            response = await client.get(f"{CHATOPS_AGENT_URL}/invalid-endpoint")
            assert response.status_code == 404
            
            # Test invalid webhook payload
            response = await client.post(
                f"{CHATOPS_AGENT_URL}/webhook",
                json={"invalid": "data"}
            )
            assert response.status_code == 400
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test metrics endpoint
            response = await client.get(f"{CHATOPS_AGENT_URL}/metrics")
            assert response.status_code == 200
            
            metrics_text = response.text
            
            # Verify Prometheus metrics format
            assert "chatops_agent_requests_total" in metrics_text
            assert "chatops_agent_errors_total" in metrics_text
            assert "chatops_agent_response_time_seconds" in metrics_text

    @pytest.mark.asyncio
    async def test_health_check_comprehensive(self):
        """Test comprehensive health check."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test ChatOps Agent health
            response = await client.get(f"{CHATOPS_AGENT_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Verify health check structure
            required_fields = [
                "status", "version", "uptime_seconds", "timestamp",
                "service", "environment", "dependencies"
            ]
            
            for field in required_fields:
                assert field in health_data, f"Missing health check field: {field}"
            
            # Verify dependencies
            dependencies = health_data["dependencies"]
            assert "union_action_api" in dependencies
            assert "memory" in dependencies
            
            # Verify Union Action API health
            union_action = dependencies["union_action_api"]
            assert "status" in union_action
            assert "url" in union_action
            assert union_action["url"] == "http://localhost:8000/health"

    @pytest.mark.asyncio
    async def test_logging_configuration(self):
        """Test logging configuration."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make requests to generate logs
            endpoints = [
                f"{CHATOPS_AGENT_URL}/health",
                f"{CHATOPS_AGENT_URL}/metrics",
                f"{UNION_ACTION_URL}/health"
            ]
            
            for endpoint in endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 200
            
            # Verify structured logging is working
            # This would typically check log files or output
            # For integration tests, we assume logging is configured correctly

    @pytest.mark.asyncio
    async def test_resource_usage(self):
        """Test resource usage monitoring."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{CHATOPS_AGENT_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            dependencies = health_data["dependencies"]
            
            # Check memory usage
            if "memory" in dependencies:
                memory = dependencies["memory"]
                assert "status" in memory
                assert "usage_mb" in memory
                assert memory["usage_mb"] > 0
                assert memory["status"] in ["ok", "warning", "error"]

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Make multiple concurrent requests
            tasks = []
            for _ in range(20):
                task = client.get(f"{CHATOPS_AGENT_URL}/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                
                health_data = response.json()
                assert "status" in health_data
                assert health_data["status"] in ["ok", "degraded"]

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when services fail."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test that application continues to work even if some dependencies fail
            response = await client.get(f"{CHATOPS_AGENT_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Application should still respond even if degraded
            assert health_data["status"] in ["ok", "degraded"]
            
            # Health endpoint should always return a response
            assert "status" in health_data
            assert "dependencies" in health_data

    @pytest.mark.asyncio
    async def test_environment_variables(self):
        """Test environment variable configuration."""
        # Test required environment variables
        required_vars = [
            "ENVIRONMENT",
            "LOG_LEVEL",
            "UNION_ACTION_API_URL",
            "PORT"
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Required environment variable {var} is not set"
        
        # Test environment variable values
        assert os.getenv("ENVIRONMENT") in ["production", "development", "staging"]
        assert os.getenv("LOG_LEVEL") in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert os.getenv("UNION_ACTION_API_URL") == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_docker_configuration(self):
        """Test Docker configuration."""
        # Test Dockerfile exists
        assert os.path.exists("Dockerfile"), "Dockerfile not found"
        
        # Test required scripts exist
        required_scripts = [
            "scripts/process-manager.sh",
            "scripts/health-check.sh",
            "union-action/scripts/start.sh"
        ]
        
        for script in required_scripts:
            assert os.path.exists(script), f"Required script {script} not found"
            assert os.access(script, os.X_OK), f"Script {script} is not executable"

    @pytest.mark.asyncio
    async def test_deployment_scripts(self):
        """Test deployment scripts."""
        # Test deployment scripts exist and are executable
        deployment_scripts = [
            "scripts/create-dokku-app.sh",
            "scripts/configure-dokku-buildpack.sh",
            "scripts/setup-basic-env.sh",
            "scripts/verify-deployment.sh"
        ]
        
        for script in deployment_scripts:
            assert os.path.exists(script), f"Deployment script {script} not found"
            assert os.access(script, os.X_OK), f"Deployment script {script} is not executable"

    @pytest.mark.asyncio
    async def test_documentation(self):
        """Test documentation availability."""
        # Test documentation files exist
        documentation_files = [
            "docs/DOKKU_DEPLOYMENT.md",
            "README.md",
            "union-action/README.md"
        ]
        
        for doc_file in documentation_files:
            assert os.path.exists(doc_file), f"Documentation file {doc_file} not found"

    @pytest.mark.asyncio
    async def test_api_documentation(self):
        """Test API documentation endpoints."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test OpenAPI documentation
            response = await client.get(f"{CHATOPS_AGENT_URL}/docs")
            assert response.status_code == 200
            
            # Test Union Action API documentation
            response = await client.get(f"{UNION_ACTION_URL}/docs")
            assert response.status_code == 200
            
            # Test ReDoc documentation
            response = await client.get(f"{UNION_ACTION_URL}/redoc")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_deployment_verification_complete(self):
        """Test complete deployment verification."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test all critical functionality
            test_cases = [
                ("ChatOps Agent Health", f"{CHATOPS_AGENT_URL}/health"),
                ("ChatOps Agent Metrics", f"{CHATOPS_AGENT_URL}/metrics"),
                ("Union Action API Health", f"{UNION_ACTION_URL}/health"),
                ("Union Action API Docs", f"{UNION_ACTION_URL}/docs")
            ]
            
            for test_name, endpoint in test_cases:
                response = await client.get(endpoint)
                assert response.status_code == 200, f"{test_name} failed: {endpoint}"
                
                # Verify response is valid
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = response.json()
                    assert isinstance(data, dict), f"Invalid JSON response from {endpoint}"
            
            # Test webhook processing
            webhook_payload = {
                "from": "+1234567890",
                "body": "Test narrative|Test maxim",
                "timestamp": int(time.time()),
                "message_id": "test_message_123"
            }
            
            response = await client.post(
                f"{CHATOPS_AGENT_URL}/webhook",
                json=webhook_payload
            )
            
            assert response.status_code == 200, "Webhook processing failed"
            
            response_data = response.json()
            assert "status" in response_data
            assert response_data["status"] == "success"


class TestDeploymentVerificationScripts:
    """Test suite for deployment verification scripts."""

    def test_verify_deployment_script_structure(self):
        """Test verify-deployment.sh script structure."""
        script_path = "scripts/verify-deployment.sh"
        assert os.path.exists(script_path), "verify-deployment.sh script not found"
        
        with open(script_path, "r") as f:
            script_content = f.read()
        
        # Check for required functionality
        assert "health_check" in script_content
        assert "curl" in script_content
        assert "dokku" in script_content
        assert "APP_NAME" in script_content

    def test_health_check_script_structure(self):
        """Test health-check.sh script structure."""
        script_path = "scripts/health-check.sh"
        assert os.path.exists(script_path), "health-check.sh script not found"
        
        with open(script_path, "r") as f:
            script_content = f.read()
        
        # Check for required functionality
        assert "health_check" in script_content
        assert "curl" in script_content
        assert "jq" in script_content
        assert "HEALTH_ENDPOINT" in script_content

    def test_process_manager_script_structure(self):
        """Test process-manager.sh script structure."""
        script_path = "scripts/process-manager.sh"
        assert os.path.exists(script_path), "process-manager.sh script not found"
        
        with open(script_path, "r") as f:
            script_content = f.read()
        
        # Check for required functionality
        assert "start_union_action_api" in script_content
        assert "start_chatops_agent" in script_content
        assert "health_check" in script_content
        assert "monitor_processes" in script_content
