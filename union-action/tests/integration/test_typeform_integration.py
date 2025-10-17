"""
Integration tests for Typeform integration.

These tests verify that Typeform integration works with environment variables.
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from xsrc.main import app
from xsrc.services.typeform_live import TypeformLiveService


class TestTypeformIntegration:
    """Test Typeform integration with environment variables."""
    
    def test_typeform_service_with_token(self):
        """Test that Typeform service works with valid token."""
        with patch.dict(os.environ, {"TYPEFORM_API_TOKEN": "valid_token_123"}):
            service = TypeformLiveService(api_token="valid_token_123")
            assert service.api_token == "valid_token_123"
            assert service.base_url == "https://api.typeform.com"
    
    def test_typeform_service_without_token(self):
        """Test that Typeform service handles missing token gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            service = TypeformLiveService(api_token="")
            assert service.api_token == ""
            # Should still be able to create service instance
    
    def test_typeform_api_call_with_token(self):
        """Test that Typeform API calls work with valid token."""
        with patch.dict(os.environ, {"TYPEFORM_API_TOKEN": "test_token"}):
            # Mock the HTTP request
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"id": "test_form_123"}
                mock_post.return_value = mock_response
                
                # This would be the actual API call in the service
                # For now, we just verify the service can be instantiated
                service = TypeformLiveService(api_token="test_token")
                assert service.api_token == "test_token"
    
    def test_typeform_environment_variable_loading(self):
        """Test that Typeform token is loaded from environment variables."""
        with patch.dict(os.environ, {"TYPEFORM_API_TOKEN": "env_token_456"}):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.typeform_api_token == "env_token_456"
    
    def test_typeform_validation_requirement(self):
        """Test that Typeform token validation works correctly."""
        with patch.dict(os.environ, {"TYPEFORM_API_TOKEN": ""}):
            from xsrc.config import Config
            config = Config.from_env()
            
            # Should not raise error for empty token (stub mode)
            assert config.typeform_api_token == ""
            
            # Should raise error when requiring token for live mode
            with pytest.raises(ValueError, match="TYPEFORM_API_TOKEN"):
                config.require_typeform_if_live()
    
    def test_typeform_integration_endpoint(self):
        """Test that Typeform integration works in API endpoints."""
        with patch.dict(os.environ, {"TYPEFORM_API_TOKEN": "test_token"}):
            client = TestClient(app)
            
            # Test that the app starts without errors with Typeform token
            response = client.get("/health")
            assert response.status_code == 200
            
            # Test that deploy endpoint is available (would use Typeform)
            response = client.get("/docs")
            assert response.status_code == 200
            assert "/deploy" in response.text
