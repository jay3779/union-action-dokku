"""
Contract tests for API documentation endpoints.

These tests verify the API documentation endpoints (/docs and /redoc) are accessible.
"""

import pytest
from fastapi.testclient import TestClient

from xsrc.main import app


class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_docs_endpoint_returns_200(self):
        """Test that /docs endpoint returns 200 status."""
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_docs_endpoint_returns_html(self):
        """Test that /docs endpoint returns HTML content."""
        client = TestClient(app)
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_redoc_endpoint_returns_200(self):
        """Test that /redoc endpoint returns 200 status."""
        client = TestClient(app)
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_redoc_endpoint_returns_html(self):
        """Test that /redoc endpoint returns HTML content."""
        client = TestClient(app)
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.text.lower()
    
    def test_docs_endpoint_contains_health_endpoint(self):
        """Test that /docs endpoint contains health endpoint documentation."""
        client = TestClient(app)
        response = client.get("/docs")
        
        assert response.status_code == 200
        # Should contain health endpoint in the documentation
        assert "/health" in response.text
    
    def test_docs_endpoint_contains_workflow_endpoints(self):
        """Test that /docs endpoint contains workflow endpoints documentation."""
        client = TestClient(app)
        response = client.get("/docs")
        
        assert response.status_code == 200
        # Should contain workflow endpoints in the documentation
        assert "/escalate" in response.text
        assert "/deploy" in response.text
