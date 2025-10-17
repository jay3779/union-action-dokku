"""
Structured logging configuration using structlog.

Provides JSON-formatted logs for audit trails and constitutional compliance validation.
Reference: research.md section 4 (Structured Logging)
"""

import structlog
import logging
import sys
from typing import Any, Dict


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configure structlog with JSON output for audit trails.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" or "text")
    
    Constitutional Compliance:
    - Audit Trail: JSON logs enable constitutional compliance validation (Checkpoint 3.5)
    - Transparency: All transformation decisions logged with rationale
    - Stateless: No database needed - logs provide audit trail
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # Processors for structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add appropriate renderer based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """
    Get a structlog logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_transformation(
    logger: structlog.stdlib.BoundLogger,
    workflow_id: str,
    adapter: str,
    source_schema: str,
    target_schema: str,
    transformation_time_ms: int,
    pydantic_ai_used: bool = False,
    pydantic_ai_transformation: str = None,
) -> None:
    """
    Log a transformation event with standard fields.
    
    Args:
        logger: Structlog logger instance
        workflow_id: Workflow identifier
        adapter: Adapter name (e.g., "ComplaintToKantianAdapter")
        source_schema: Source schema name and version
        target_schema: Target schema name and version
        transformation_time_ms: Transformation duration in milliseconds
        pydantic_ai_used: Whether Pydantic AI was used
        pydantic_ai_transformation: AI transformation rationale (if used)
    """
    log_data: Dict[str, Any] = {
        "event": "transformation_complete",
        "workflow_id": workflow_id,
        "adapter": adapter,
        "source_schema": source_schema,
        "target_schema": target_schema,
        "transformation_time_ms": transformation_time_ms,
        "pydantic_ai_used": pydantic_ai_used,
    }
    
    if pydantic_ai_transformation:
        log_data["pydantic_ai_transformation"] = pydantic_ai_transformation
    
    logger.info(**log_data)


def log_constitutional_compliance(
    logger: structlog.stdlib.BoundLogger,
    workflow_id: str,
    gate_results: Dict[str, str],
    overall_status: str,
) -> None:
    """
    Log constitutional compliance validation (Checkpoint 3.5).
    
    Args:
        logger: Structlog logger instance
        workflow_id: Workflow identifier
        gate_results: Dict of gate_name -> status (PASS/FAIL)
        overall_status: Overall compliance status (PASS/FAIL)
    """
    logger.info(
        "constitutional_compliance_check",
        workflow_id=workflow_id,
        gate_results=gate_results,
        overall_status=overall_status,
    )

