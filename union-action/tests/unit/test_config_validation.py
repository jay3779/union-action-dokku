"""
Unit tests for configuration validation.

These tests verify that configuration validation works correctly.
"""

import pytest
import os
from unittest.mock import patch

from xsrc.config import Config


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_config_validation_success(self):
        """Test that valid configuration passes validation."""
        config = Config(
            typeform_api_token="test_token",
            openai_api_key="test_key",
            log_level="INFO",
            log_format="json",
            api_host="0.0.0.0",
            api_port=8000,
            cors_allowed_origins=["*"]
        )
        assert config.typeform_api_token == "test_token"
        assert config.openai_api_key == "test_key"
        assert config.log_level == "INFO"
        assert config.log_format == "json"
    
    def test_config_validation_log_level_invalid(self):
        """Test that invalid log level raises validation error."""
        with pytest.raises(ValueError, match="log_level must be one of"):
            Config(log_level="INVALID")
    
    def test_config_validation_log_format_invalid(self):
        """Test that invalid log format raises validation error."""
        with pytest.raises(ValueError, match="log_format must be 'json' or 'text'"):
            Config(log_format="invalid")
    
    def test_config_validation_log_level_case_insensitive(self):
        """Test that log level validation is case insensitive."""
        config = Config(log_level="debug")
        assert config.log_level == "DEBUG"
    
    def test_config_validation_log_format_case_insensitive(self):
        """Test that log format validation is case insensitive."""
        config = Config(log_format="JSON")
        assert config.log_format == "json"
    
    def test_config_validation_defaults(self):
        """Test that configuration has correct defaults."""
        config = Config()
        assert config.log_level == "INFO"
        assert config.log_format == "json"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.cors_allowed_origins == ["*"]
    
    def test_config_validation_from_env(self):
        """Test that configuration loads from environment variables."""
        with patch.dict(os.environ, {
            "TYPEFORM_API_TOKEN": "env_token",
            "OPENAI_API_KEY": "env_key",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://example.com"
        }):
            config = Config.from_env()
            assert config.typeform_api_token == "env_token"
            assert config.openai_api_key == "env_key"
            assert config.log_level == "DEBUG"
            assert config.log_format == "text"
            assert config.api_host == "127.0.0.1"
            assert config.api_port == 9000
            assert "http://localhost:3000" in config.cors_allowed_origins
            assert "https://example.com" in config.cors_allowed_origins
    
    def test_config_validation_require_typeform(self):
        """Test that require_typeform validation works."""
        config = Config(typeform_api_token="")
        with pytest.raises(ValueError, match="TYPEFORM_API_TOKEN"):
            config.require_typeform_if_live()
    
    def test_config_validation_require_typeform_success(self):
        """Test that require_typeform validation passes with token."""
        config = Config(typeform_api_token="valid_token")
        # Should not raise error
        config.require_typeform_if_live()
    
    def test_config_validation_cors_origins_parsing(self):
        """Test that CORS origins are parsed correctly."""
        with patch.dict(os.environ, {
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://example.com,https://test.com"
        }):
            config = Config.from_env()
            assert len(config.cors_allowed_origins) == 3
            assert "http://localhost:3000" in config.cors_allowed_origins
            assert "https://example.com" in config.cors_allowed_origins
            assert "https://test.com" in config.cors_allowed_origins
    
    def test_config_validation_api_port_conversion(self):
        """Test that API port is converted to integer."""
        with patch.dict(os.environ, {"API_PORT": "9000"}):
            config = Config.from_env()
            assert config.api_port == 9000
            assert isinstance(config.api_port, int)
    
    def test_config_validation_api_port_invalid(self):
        """Test that invalid API port raises error."""
        with patch.dict(os.environ, {"API_PORT": "invalid"}):
            with pytest.raises(ValueError):
                Config.from_env()
    
    def test_config_validation_pydantic_ai_model_default(self):
        """Test that Pydantic AI model has correct default."""
        config = Config()
        assert config.pydantic_ai_model == "openai:gpt-4"
    
    def test_config_validation_pydantic_ai_model_override(self):
        """Test that Pydantic AI model can be overridden."""
        with patch.dict(os.environ, {"PYDANTIC_AI_MODEL": "openai:gpt-3.5-turbo"}):
            config = Config.from_env()
            assert config.pydantic_ai_model == "openai:gpt-3.5-turbo"
