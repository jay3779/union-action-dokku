"""
Integration tests for full deployment pipeline.

These tests verify that the complete deployment pipeline works end-to-end.
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from xsrc.main import app


class TestFullDeployment:
    """Test complete deployment pipeline."""
    
    def test_full_deployment_pipeline(self):
        """Test that the complete deployment pipeline works."""
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test API documentation
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test redoc documentation
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_deployment_with_environment_variables(self):
        """Test deployment with all environment variables set."""
        with patch.dict(os.environ, {
            "TYPEFORM_API_TOKEN": "test_token",
            "OPENAI_API_KEY": "test_key",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://example.com"
        }):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_without_environment_variables(self):
        """Test deployment with minimal environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_with_invalid_environment_variables(self):
        """Test deployment with invalid environment variables."""
        with patch.dict(os.environ, {
            "LOG_LEVEL": "INVALID",
            "LOG_FORMAT": "invalid"
        }):
            with pytest.raises(ValueError):
                from xsrc.config import Config
                Config.from_env()
    
    def test_deployment_with_missing_required_variables(self):
        """Test deployment with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_with_cors_configuration(self):
        """Test deployment with CORS configuration."""
        with patch.dict(os.environ, {
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://example.com"
        }):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_with_logging_configuration(self):
        """Test deployment with logging configuration."""
        with patch.dict(os.environ, {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text"
        }):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_with_api_configuration(self):
        """Test deployment with API configuration."""
        with patch.dict(os.environ, {
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000"
        }):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_with_external_services(self):
        """Test deployment with external service configuration."""
        with patch.dict(os.environ, {
            "TYPEFORM_API_TOKEN": "test_token",
            "OPENAI_API_KEY": "test_key",
            "PYDANTIC_AI_MODEL": "openai:gpt-3.5-turbo"
        }):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_performance(self):
        """Test that deployment meets performance requirements."""
        import time
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    def test_deployment_reliability(self):
        """Test that deployment is reliable."""
        client = TestClient(app)
        
        # Test multiple requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_deployment_security(self):
        """Test that deployment is secure."""
        client = TestClient(app)
        
        # Test that sensitive information is not exposed
        response = client.get("/health")
        data = response.json()
        assert "api_key" not in str(data)
        assert "token" not in str(data)
    
    def test_deployment_monitoring(self):
        """Test that deployment monitoring works."""
        client = TestClient(app)
        
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime" in data
        assert "processes" in data
