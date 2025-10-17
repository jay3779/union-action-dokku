"""
Contract tests for environment variable configuration.

These tests verify that environment variables are properly configured and used.
"""

import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

from xsrc.main import app
from xsrc.config import Config


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""
    
    def test_typeform_api_token_configuration(self):
        """Test that TYPEFORM_API_TOKEN is properly configured."""
        with patch.dict(os.environ, {"TYPEFORM_API_TOKEN": "test_token_123"}):
            config = Config.from_env()
            assert config.typeform_api_token == "test_token_123"
    
    def test_openai_api_key_configuration(self):
        """Test that OPENAI_API_KEY is properly configured."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key_456"}):
            config = Config.from_env()
            assert config.openai_api_key == "test_key_456"
    
    def test_log_level_configuration(self):
        """Test that LOG_LEVEL is properly configured."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            config = Config.from_env()
            assert config.log_level == "DEBUG"
    
    def test_log_format_configuration(self):
        """Test that LOG_FORMAT is properly configured."""
        with patch.dict(os.environ, {"LOG_FORMAT": "text"}):
            config = Config.from_env()
            assert config.log_format == "text"
    
    def test_default_configuration_values(self):
        """Test that default configuration values are set correctly."""
        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()
            assert config.log_level == "INFO"
            assert config.log_format == "json"
            assert config.api_host == "0.0.0.0"
            assert config.api_port == 8000
    
    def test_cors_origins_configuration(self):
        """Test that CORS_ALLOWED_ORIGINS is properly configured."""
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://example.com"}):
            config = Config.from_env()
            assert "http://localhost:3000" in config.cors_allowed_origins
            assert "https://example.com" in config.cors_allowed_origins
    
    def test_log_level_validation(self):
        """Test that log level validation works correctly."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError, match="log_level must be one of"):
                Config.from_env()
    
    def test_log_format_validation(self):
        """Test that log format validation works correctly."""
        with patch.dict(os.environ, {"LOG_FORMAT": "invalid"}):
            with pytest.raises(ValueError, match="log_format must be 'json' or 'text'"):
                Config.from_env()
    
    def test_environment_variables_passed_to_app(self):
        """Test that environment variables are accessible in the application."""
        with patch.dict(os.environ, {
            "TYPEFORM_API_TOKEN": "test_token",
            "OPENAI_API_KEY": "test_key",
            "LOG_LEVEL": "DEBUG"
        }):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
