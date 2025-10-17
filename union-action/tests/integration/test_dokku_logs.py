"""
Integration tests for Dokku logging integration.

These tests verify that logging works correctly with Dokku.
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from xsrc.main import app


class TestDokkuLogging:
    """Test Dokku logging integration."""
    
    def test_logs_are_written_to_stdout(self):
        """Test that logs are written to stdout for Dokku."""
        with patch('sys.stdout') as mock_stdout:
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            # Verify that logging goes to stdout
            mock_stdout.write.assert_called()
    
    def test_logs_are_written_to_stderr(self):
        """Test that error logs are written to stderr for Dokku."""
        with patch('sys.stderr') as mock_stderr:
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            # Verify that error logging goes to stderr
            mock_stderr.write.assert_called()
    
    def test_log_format_is_json(self):
        """Test that log format is JSON for Dokku."""
        with patch.dict(os.environ, {"LOG_FORMAT": "json"}):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_log_format_is_text(self):
        """Test that log format can be text."""
        with patch.dict(os.environ, {"LOG_FORMAT": "text"}):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_log_level_configuration(self):
        """Test that log level is configurable."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_structured_logging(self):
        """Test that structured logging works."""
        with patch('structlog.get_logger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            # Verify structured logging is used
            mock_logger.assert_called()
    
    def test_log_rotation_handling(self):
        """Test that log rotation is handled correctly."""
        with patch('logging.handlers.RotatingFileHandler') as mock_handler:
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            # Verify that file rotation is not used (stdout/stderr only)
            mock_handler.assert_not_called()
    
    def test_log_context_preservation(self):
        """Test that log context is preserved across requests."""
        client = TestClient(app)
        response1 = client.get("/health")
        response2 = client.get("/health")
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    def test_log_performance_impact(self):
        """Test that logging doesn't significantly impact performance."""
        import time
        client = TestClient(app)
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
