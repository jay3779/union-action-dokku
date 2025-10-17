"""
Contract tests for health endpoint.

These tests verify the health endpoint contract as defined in the API specification.
"""

import pytest
import httpx
from fastapi.testclient import TestClient

from xsrc.main import app


class TestHealthEndpoint:
    """Test health endpoint contract."""
    
    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200 status."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_health_response(self):
        """Test that health endpoint returns proper health response structure."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        
        # Verify status is healthy
        assert data["status"] == "healthy"
        
        # Verify timestamp is present
        assert data["timestamp"] is not None
    
    def test_health_endpoint_response_time(self):
        """Test that health endpoint responds within 2 seconds."""
        import time
        
        client = TestClient(app)
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds
    
    def test_health_endpoint_content_type(self):
        """Test that health endpoint returns JSON content type."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
