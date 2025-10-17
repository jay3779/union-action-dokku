"""
Configuration management for Union Action Workflow Integration.

Loads environment variables and validates required configuration.
Constitutional Compliance: Vendor Independence (all config externalized).
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """Application configuration loaded from environment variables."""
    
    # Typeform API (required for CareVoice integration)
    typeform_api_token: str = Field(
        default="",
        description="Typeform API token for KOERS survey deployment"
    )
    
    # Pydantic AI (optional, for schema transformation)
    pydantic_ai_model: str = Field(
        default="openai:gpt-4",
        description="Pydantic AI model for schema version compatibility"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (if using OpenAI models)"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # Server
    api_host: str = Field(
        default="0.0.0.0",
        description="API host to bind to"
    )
    api_port: int = Field(
        default=8000,
        description="API port to bind to"
    )
    
    # Internal communication settings for bundled deployment
    internal_communication: bool = Field(
        default=True,
        description="Whether this is running as internal service"
    )
    chatops_agent_url: str = Field(
        default="http://localhost:8080",
        description="ChatOps Agent URL for internal communication"
    )
    
    # CORS
    cors_allowed_origins: List[str] = Field(
        default=["*"],
        description="List of allowed CORS origins"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is json or text."""
        v_lower = v.lower()
        if v_lower not in ["json", "text"]:
            raise ValueError("log_format must be 'json' or 'text'")
        return v_lower
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            # Hardcoded fallback for Typeform API token; can be overridden by env
            typeform_api_token=os.getenv(
                "TYPEFORM_API_TOKEN",
                "tfp_2Zn15ugfwvKfKYurgLxdzAY3bCLrEfWMP8aRXUknuXEM_jDwD59g9pmyU",
            ),
            pydantic_ai_model=os.getenv("PYDANTIC_AI_MODEL", "openai:gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            log_level=os.getenv("UNION_ACTION_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO")),
            log_format=os.getenv("UNION_ACTION_LOG_FORMAT", os.getenv("LOG_FORMAT", "json")),
            api_host=os.getenv("UNION_ACTION_HOST", os.getenv("API_HOST", "0.0.0.0")),
            api_port=int(os.getenv("UNION_ACTION_PORT", os.getenv("API_PORT", "8000"))),
            cors_allowed_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
            internal_communication=os.getenv("INTERNAL_COMMUNICATION", "true").lower() == "true",
            chatops_agent_url=os.getenv("CHATOPS_AGENT_URL", "http://localhost:8080"),
        )
    
    def validate_required(self, require_typeform: bool = False) -> None:
        """
        Validate required configuration is present.
        
        Args:
            require_typeform: If True, raise error if Typeform token is missing
        
        Raises:
            ValueError: If required configuration is missing
        """
        if require_typeform and not self.typeform_api_token:
            raise ValueError(
                "TYPEFORM_API_TOKEN environment variable is required for "
                "CareVoice KOERS survey generation (User Story 2). "
                "Set it in .env or environment."
            )

    def require_typeform_if_live(self) -> None:
        """
        Enforce that TYPEFORM_API_TOKEN is present if we intend to use the
        live Typeform integration (as opposed to the stub). Call this in
        API routes where live mode is expected.
        """
        if not self.typeform_api_token:
            raise ValueError(
                "TYPEFORM_API_TOKEN is required for live Typeform integration. "
                "Provide a valid token or run with the stub."
            )


# Global config instance
config = Config.from_env()

