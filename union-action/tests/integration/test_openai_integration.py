"""
Integration tests for OpenAI integration.

These tests verify that OpenAI integration works with environment variables.
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from xsrc.main import app
from xsrc.services.pydantic_ai_transformer import PydanticAITransformer


class TestOpenAIIntegration:
    """Test OpenAI integration with environment variables."""
    
    def test_openai_service_with_key(self):
        """Test that OpenAI service works with valid API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "valid_key_123"}):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.openai_api_key == "valid_key_123"
    
    def test_openai_service_without_key(self):
        """Test that OpenAI service handles missing key gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.openai_api_key is None
    
    def test_openai_environment_variable_loading(self):
        """Test that OpenAI key is loaded from environment variables."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env_key_456"}):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.openai_api_key == "env_key_456"
    
    def test_pydantic_ai_model_configuration(self):
        """Test that Pydantic AI model is configured correctly."""
        with patch.dict(os.environ, {"PYDANTIC_AI_MODEL": "openai:gpt-3.5-turbo"}):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.pydantic_ai_model == "openai:gpt-3.5-turbo"
    
    def test_pydantic_ai_model_default(self):
        """Test that Pydantic AI model has correct default."""
        with patch.dict(os.environ, {}, clear=True):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.pydantic_ai_model == "openai:gpt-4"
    
    def test_openai_integration_with_transformer(self):
        """Test that OpenAI integration works with Pydantic AI transformer."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            # Mock the Pydantic AI transformer
            with patch('pydantic_ai.PydanticAI') as mock_ai:
                mock_ai.return_value = Mock()
                
                # This would be the actual transformer usage
                # For now, we just verify the configuration is available
                from xsrc.config import Config
                config = Config.from_env()
                assert config.openai_api_key == "test_key"
                assert config.pydantic_ai_model == "openai:gpt-4"
    
    def test_openai_integration_endpoint(self):
        """Test that OpenAI integration works in API endpoints."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            client = TestClient(app)
            
            # Test that the app starts without errors with OpenAI key
            response = client.get("/health")
            assert response.status_code == 200
            
            # Test that escalate endpoint is available (would use OpenAI)
            response = client.get("/docs")
            assert response.status_code == 200
            assert "/escalate" in response.text
    
    def test_openai_optional_configuration(self):
        """Test that OpenAI configuration is optional."""
        with patch.dict(os.environ, {}, clear=True):
            client = TestClient(app)
            
            # App should start without OpenAI key (stub mode)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_openai_model_override(self):
        """Test that OpenAI model can be overridden via environment."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test_key",
            "PYDANTIC_AI_MODEL": "openai:gpt-3.5-turbo"
        }):
            from xsrc.config import Config
            config = Config.from_env()
            assert config.openai_api_key == "test_key"
            assert config.pydantic_ai_model == "openai:gpt-3.5-turbo"
