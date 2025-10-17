"""
Centralized logging configuration with correlation ID support and structured output.

This module provides comprehensive logging setup for the WhatsApp ChatOps Agent,
including correlation ID propagation, structured output formatting, and context management.
"""

import logging
import sys
import os
from typing import Any, Dict, Optional
import structlog
from contextvars import ContextVar


# Context variable for correlation ID propagation
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    correlation_id_var.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    correlation_id_var.set(None)


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor that adds correlation ID to all log entries.
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method being called
        event_dict: Current log event dictionary
        
    Returns:
        Updated event dictionary with correlation_id added
    """
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def redact_sensitive_data(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor that redacts sensitive data from log entries (T065).
    
    Redacts:
    - Phone numbers (show only last 4 digits)
    - Workflow IDs (if they are phone numbers)
    - Long message bodies and previews
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method being called
        event_dict: Current log event dictionary
        
    Returns:
        Updated event dictionary with sensitive data redacted
    """
    # Fields that might contain phone numbers
    phone_fields = ["from", "from_user", "workflow_id", "phone_number", "phone"]
    
    for field in phone_fields:
        if field in event_dict:
            value = str(event_dict[field])
            # If it looks like a phone number (digits only, 7+ chars)
            if value.isdigit() and len(value) >= 7:
                # Show only last 4 digits
                event_dict[field] = "***" + value[-4:]
    
    # Redact long message bodies (keep preview only)
    if "message" in event_dict and isinstance(event_dict.get("message"), str):
        msg = event_dict["message"]
        if len(msg) > 200:
            event_dict["message"] = msg[:200] + "...[redacted]"
    
    # Redact from narrative_preview and maxim_preview if they're long
    for preview_field in ["narrative_preview", "maxim_preview", "raw_message"]:
        if preview_field in event_dict:
            preview = str(event_dict[preview_field])
            if len(preview) > 100:
                event_dict[preview_field] = preview[:100] + "...[redacted]"
    
    return event_dict


def add_log_sampling(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor that implements log sampling in production (T064).
    
    In development: Log everything
    In production: Sample verbose logs (keep errors and warnings)
    
    Returns None to drop the log entry, or event_dict to keep it.
    """
    import random
    
    environment = os.getenv("ENVIRONMENT", "dev")
    
    # In development, log everything
    if environment == "dev":
        return event_dict
    
    # In production, always log errors and warnings
    log_level = event_dict.get("level", "info")
    if log_level in ["error", "warning", "critical"]:
        return event_dict
    
    # Sample info and debug logs (10% sampling rate)
    if log_level in ["info", "debug"]:
        sample_rate = float(os.getenv("LOG_SAMPLE_RATE", "0.1"))
        if random.random() > sample_rate:
            # Drop this log entry
            raise structlog.DropEvent
    
    return event_dict


def add_service_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor that adds service-level context to all log entries (T067).
    
    Adds:
    - service_name
    - environment
    - version (if available)
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method being called
        event_dict: Current log event dictionary
        
    Returns:
        Updated event dictionary with service context
    """
    event_dict["service_name"] = "whatsapp-chatops-agent"
    event_dict["environment"] = os.getenv("ENVIRONMENT", "dev")
    return event_dict


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure structured logging for the application and bundled Union Action API.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format (True) or human-readable (False)
    """
    # Set log level from environment or parameter
    level = os.getenv("LOG_LEVEL", log_level).upper()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level, logging.INFO),
    )
    
    # Determine processors based on environment
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_correlation_id,
        add_service_context,
        redact_sensitive_data,  # T065: Redact sensitive data
        add_log_sampling,  # T064: Sample logs in production
    ]
    
    # T085: Environment-specific logging configuration
    # Add renderer based on output format
    environment = os.getenv("ENVIRONMENT", "dev")
    
    if json_logs or environment in ["production", "staging"]:
        # JSON output for production/log aggregation (Render logs)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable output for development
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure Union Action API logging
    configure_union_action_logging()


def configure_union_action_logging() -> None:
    """
    Configure logging for the bundled Union Action API service.
    
    Sets up separate logging configuration for Union Action API
    to ensure proper log separation and correlation.
    """
    # Set Union Action API specific environment variables
    union_action_log_level = os.getenv("UNION_ACTION_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO"))
    union_action_log_format = os.getenv("UNION_ACTION_LOG_FORMAT", "json")
    
    # Configure Union Action API logging
    union_action_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_correlation_id,
        add_service_context,
    ]
    
    # Add Union Action API specific context
    def add_union_action_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Add Union Action API specific context to log entries."""
        event_dict["service_name"] = "union-action-api"
        event_dict["service_type"] = "bundled"
        event_dict["environment"] = os.getenv("ENVIRONMENT", "dev")
        return event_dict
    
    union_action_processors.append(add_union_action_context)
    
    # Configure Union Action API structlog
    structlog.configure(
        processors=union_action_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Sample rate for logging (1.0 = log everything, 0.1 = log 10%)
def should_sample_log(sample_rate: Optional[float] = None) -> bool:
    """
    Determine if a log entry should be sampled based on configured rate.
    
    Args:
        sample_rate: Sample rate override (None uses env var)
        
    Returns:
        True if log should be emitted, False otherwise
    """
    import random
    
    if sample_rate is None:
        sample_rate = float(os.getenv("LOG_SAMPLE_RATE", "1.0"))
    
    return random.random() < sample_rate


# Initialize logging on module import
configure_logging()

