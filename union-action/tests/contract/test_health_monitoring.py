"""
Contract tests for health monitoring endpoints.

These tests verify that health monitoring works correctly.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from xsrc.main import app


class TestHealthMonitoring:
    """Test health monitoring functionality."""
    
    def test_health_endpoint_returns_200(self):
        """Test that /health endpoint returns 200 status."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_json(self):
        """Test that /health endpoint returns JSON response."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_health_endpoint_includes_status(self):
        """Test that /health endpoint includes status field."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint_includes_timestamp(self):
        """Test that /health endpoint includes timestamp."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
    
    def test_health_endpoint_includes_version(self):
        """Test that /health endpoint includes version."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "version" in data
    
    def test_health_endpoint_includes_uptime(self):
        """Test that /health endpoint includes uptime."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))
    
    def test_health_endpoint_includes_processes(self):
        """Test that /health endpoint includes process information."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "processes" in data
        assert isinstance(data["processes"], dict)
    
    def test_health_endpoint_processes_include_api(self):
        """Test that processes include API process."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "api" in data["processes"]
        assert data["processes"]["api"]["status"] == "running"
    
    def test_health_endpoint_processes_include_agent(self):
        """Test that processes include chatops-agent."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "chatops-agent" in data["processes"]
        assert data["processes"]["chatops-agent"]["status"] == "running"
    
    def test_health_endpoint_handles_process_failure(self):
        """Test that health endpoint handles process failure gracefully."""
        with patch('supervisorctl.status') as mock_status:
            mock_status.return_value = "chatops-agent STOPPED"
            client = TestClient(app)
            response = client.get("/health")
            data = response.json()
            assert data["processes"]["chatops-agent"]["status"] == "stopped"
    
    def test_health_endpoint_returns_503_on_unhealthy(self):
        """Test that health endpoint returns 503 when unhealthy."""
        with patch('supervisorctl.status') as mock_status:
            mock_status.return_value = "union-action-api STOPPED"
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 503
