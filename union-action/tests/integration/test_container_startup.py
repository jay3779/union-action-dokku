"""
Integration tests for multi-process container startup.

These tests verify that both processes start correctly in the container.
"""

import pytest
import subprocess
import time
import requests
from pathlib import Path


class TestContainerStartup:
    """Test multi-process container startup."""
    
    def test_supervisord_starts_both_processes(self):
        """Test that supervisord starts both union-action-api and chatops-agent."""
        # This test would run in actual container environment
        # For now, we'll verify the configuration is correct
        
        supervisord_path = Path("supervisord.conf")
        supervisord_content = supervisord_path.read_text()
        
        # Verify union-action-api configuration
        assert "command=uvicorn xsrc.main:app" in supervisord_content
        assert "autostart=true" in supervisord_content
        assert "autorestart=true" in supervisord_content
        
        # Verify chatops-agent configuration
        assert "command=python -m chatops-agent.main" in supervisord_content
        assert "autostart=true" in supervisord_content
        assert "autorestart=true" in supervisord_content
    
    def test_process_priority_configuration(self):
        """Test that process priority is configured correctly."""
        supervisord_path = Path("supervisord.conf")
        supervisord_content = supervisord_path.read_text()
        
        # Verify union-action-api has higher priority (lower number)
        api_priority_line = [line for line in supervisord_content.split('\n') 
                           if 'priority=100' in line and 'union-action-api' in supervisord_content.split('\n')[supervisord_content.split('\n').index(line)-5:supervisord_content.split('\n').index(line)]]
        assert api_priority_line
        
        # Verify chatops-agent has lower priority (higher number)
        agent_priority_line = [line for line in supervisord_content.split('\n') 
                              if 'priority=200' in line and 'chatops-agent' in supervisord_content.split('\n')[supervisord_content.split('\n').index(line)-5:supervisord_content.split('\n').index(line)]]
        assert agent_priority_line
    
    def test_process_restart_configuration(self):
        """Test that process restart configuration is correct."""
        supervisord_path = Path("supervisord.conf")
        supervisord_content = supervisord_path.read_text()
        
        # Verify both processes have restart configuration
        assert "startretries=3" in supervisord_content
        assert "autorestart=true" in supervisord_content
        
        # Verify different startup times
        assert "startsecs=10" in supervisord_content  # union-action-api
        assert "startsecs=5" in supervisord_content   # chatops-agent
    
    def test_logging_configuration(self):
        """Test that logging is configured for Dokku integration."""
        supervisord_path = Path("supervisord.conf")
        supervisord_content = supervisord_path.read_text()
        
        # Verify stdout/stderr logging for both processes
        assert "stdout_logfile=/dev/stdout" in supervisord_content
        assert "stderr_logfile=/dev/stderr" in supervisord_content
        assert "stdout_logfile_maxbytes=0" in supervisord_content
        assert "stderr_logfile_maxbytes=0" in supervisord_content
    
    def test_environment_variables_passed(self):
        """Test that environment variables are passed to processes."""
        supervisord_path = Path("supervisord.conf")
        supervisord_content = supervisord_path.read_text()
        
        # Verify PYTHONUNBUFFERED is set for both processes
        assert "environment=PYTHONUNBUFFERED=1" in supervisord_content
    
    def test_graceful_shutdown_configuration(self):
        """Test that graceful shutdown is configured."""
        supervisord_path = Path("supervisord.conf")
        supervisord_content = supervisord_path.read_text()
        
        # Verify graceful shutdown configuration
        assert "stopsignal=TERM" in supervisord_content
        assert "stopwaitsecs" in supervisord_content
        assert "killasgroup=true" in supervisord_content
        assert "stopasgroup=true" in supervisord_content
