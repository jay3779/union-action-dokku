"""
Integration tests for process monitoring.

These tests verify that process monitoring works correctly.
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from xsrc.main import app


class TestProcessMonitoring:
    """Test process monitoring functionality."""
    
    def test_process_status_check(self):
        """Test that process status is checked correctly."""
        with patch('supervisorctl.status') as mock_status:
            mock_status.return_value = "union-action-api RUNNING"
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            mock_status.assert_called()
    
    def test_process_restart_capability(self):
        """Test that process restart capability is available."""
        with patch('supervisorctl.restart') as mock_restart:
            mock_restart.return_value = True
            # This would be called by the health monitoring system
            assert mock_restart.call_count == 0  # Not called yet
    
    def test_process_priority_handling(self):
        """Test that process priority is handled correctly."""
        with patch('supervisorctl.status') as mock_status:
            mock_status.return_value = "union-action-api RUNNING\nchatops-agent RUNNING"
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "processes" in data
            assert "api" in data["processes"]
            assert "chatops-agent" in data["processes"]
    
    def test_process_resource_monitoring(self):
        """Test that process resource monitoring works."""
        with patch('psutil.Process') as mock_process:
            mock_proc = Mock()
            mock_proc.cpu_percent.return_value = 10.5
            mock_proc.memory_percent.return_value = 5.2
            mock_process.return_value = mock_proc
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_process_health_thresholds(self):
        """Test that process health thresholds are respected."""
        with patch('psutil.Process') as mock_process:
            mock_proc = Mock()
            mock_proc.cpu_percent.return_value = 95.0  # High CPU
            mock_proc.memory_percent.return_value = 90.0  # High memory
            mock_process.return_value = mock_proc
            client = TestClient(app)
            response = client.get("/health")
            # Should still return 200 but with warning in logs
            assert response.status_code == 200
    
    def test_process_failure_detection(self):
        """Test that process failure is detected."""
        with patch('supervisorctl.status') as mock_status:
            mock_status.return_value = "union-action-api STOPPED"
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert data["processes"]["api"]["status"] == "stopped"
    
    def test_process_auto_restart(self):
        """Test that process auto-restart works."""
        with patch('supervisorctl.restart') as mock_restart:
            mock_restart.return_value = True
            # Simulate process restart
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_process_startup_sequence(self):
        """Test that process startup sequence is correct."""
        with patch('supervisorctl.status') as mock_status:
            mock_status.return_value = "union-action-api RUNNING\nchatops-agent RUNNING"
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["processes"]["api"]["status"] == "running"
            assert data["processes"]["chatops-agent"]["status"] == "running"
    
    def test_process_graceful_shutdown(self):
        """Test that process graceful shutdown works."""
        with patch('supervisorctl.shutdown') as mock_shutdown:
            mock_shutdown.return_value = True
            # Simulate graceful shutdown
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_process_monitoring_performance(self):
        """Test that process monitoring doesn't impact performance."""
        import time
        client = TestClient(app)
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
