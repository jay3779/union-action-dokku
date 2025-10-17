"""
Configuration settings for chatops-agent.
"""

import os
from typing import Optional


class Config:
    """Configuration class for chatops-agent."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Union Action API configuration
        self.union_action_url = os.getenv(
            "UNION_ACTION_URL", 
            "http://localhost:8000"
        )
        
        # Request configuration
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Polling configuration
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "5"))
        self.error_retry_interval = int(os.getenv("ERROR_RETRY_INTERVAL", "10"))
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        
        # External service configuration
        self.typeform_api_token = os.getenv("TYPEFORM_API_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def validate(self) -> bool:
        """Validate configuration."""
        # Check required environment variables
        if not self.union_action_url:
            raise ValueError("UNION_ACTION_URL must be set")
        
        # Validate URL format
        if not self.union_action_url.startswith(("http://", "https://")):
            raise ValueError("UNION_ACTION_URL must be a valid HTTP URL")
        
        return True
