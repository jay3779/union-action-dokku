"""
Diagnostic utilities for debugging and observability.

This module provides utilities for request inspection, payload validation,
timing measurements, and other diagnostic capabilities.
"""

import time
import json
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


def dump_request(request_data: Dict[str, Any], redact_sensitive: bool = True) -> str:
    """
    Dump request data in a readable format for debugging.
    
    Args:
        request_data: Request data dictionary
        redact_sensitive: Whether to redact sensitive fields
        
    Returns:
        Pretty-printed JSON string
    """
    data = request_data.copy()
    
    if redact_sensitive:
        # Redact phone numbers
        if "from" in data and isinstance(data["from"], str):
            phone = data["from"]
            if len(phone) > 4:
                data["from"] = "***" + phone[-4:]
    
    return json.dumps(data, indent=2, default=str)


def dump_response(response_data: Dict[str, Any]) -> str:
    """
    Dump response data in a readable format for debugging.
    
    Args:
        response_data: Response data dictionary
        
    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(response_data, indent=2, default=str)


def validate_payload_structure(payload: Dict[str, Any], required_fields: list) -> tuple[bool, Optional[str]]:
    """
    Validate that payload contains required fields.
    
    Args:
        payload: Payload dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_fields = []
    
    for field in required_fields:
        if "." in field:
            # Support nested field checking (e.g., "source_data.narrative")
            parts = field.split(".")
            current = payload
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    missing_fields.append(field)
                    break
                current = current[part]
        else:
            if field not in payload:
                missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None


def timing_decorator(operation_name: str):
    """
    Decorator to measure and log execution time of functions.
    
    Args:
        operation_name: Name of the operation for logging
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "operation_completed",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    status="success"
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    status="error",
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "operation_completed",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    status="success"
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    status="error",
                    error=str(e)
                )
                raise
        
        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RequestTimer:
    """Context manager for timing request segments."""
    
    def __init__(self, segment_name: str):
        """
        Initialize request timer.
        
        Args:
            segment_name: Name of the request segment being timed
        """
        self.segment_name = segment_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        logger.debug("segment_started", segment=self.segment_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log duration."""
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        if exc_type is None:
            logger.info(
                "segment_completed",
                segment=self.segment_name,
                duration_ms=round(duration_ms, 2),
                status="success"
            )
        else:
            logger.error(
                "segment_failed",
                segment=self.segment_name,
                duration_ms=round(duration_ms, 2),
                status="error",
                error_type=exc_type.__name__ if exc_type else None
            )
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


class ErrorTracker:
    """Track errors by category for metrics."""
    
    def __init__(self):
        """Initialize error tracker."""
        self.errors = {
            "validation": 0,
            "parsing": 0,
            "integration": 0,
            "unknown": 0
        }
        self.recent_errors = []  # T044: Store recent error details
        self.max_recent_errors = 100
        self.last_reset = datetime.now()
    
    def track_error(self, error_category: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Track an error occurrence with optional details.
        
        Args:
            error_category: Category of error (validation, parsing, integration, unknown)
            details: Optional dictionary with error details for debugging
        """
        if error_category in self.errors:
            self.errors[error_category] += 1
        else:
            self.errors["unknown"] += 1
        
        # T044: Store recent error with details
        error_entry = {
            "category": error_category,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.recent_errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors:]
        
        # T045: Log error with context
        logger.warning(
            "error_tracked",
            category=error_category,
            total_in_category=self.errors.get(error_category, self.errors["unknown"]),
            details=details
        )
    
    def get_error_counts(self) -> Dict[str, int]:
        """
        Get current error counts.
        
        Returns:
            Dictionary of error counts by category
        """
        return self.errors.copy()
    
    def reset(self) -> None:
        """Reset error counts and clear recent errors."""
        self.errors = {key: 0 for key in self.errors}
        self.recent_errors = []
        self.last_reset = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get error summary including counts, recent errors, and time since reset.
        
        Returns:
            Dictionary with error summary
        """
        time_since_reset = (datetime.now() - self.last_reset).total_seconds()
        return {
            "errors": self.errors.copy(),
            "total_errors": sum(self.errors.values()),
            "recent_errors_count": len(self.recent_errors),
            "recent_errors": self.recent_errors[-10:],  # Last 10 errors
            "time_since_reset_seconds": round(time_since_reset, 2),
            "last_reset": self.last_reset.isoformat()
        }
    
    def get_recent_errors(self, limit: int = 20) -> list:
        """
        Get recent errors with optional limit.
        
        Args:
            limit: Maximum number of recent errors to return
            
        Returns:
            List of recent error entries
        """
        return self.recent_errors[-limit:] if limit else self.recent_errors


# Global error tracker instance
error_tracker = ErrorTracker()


def check_slow_operation(duration_ms: float, threshold_ms: float = 2000) -> bool:
    """
    Check if an operation exceeded the slow operation threshold.
    
    Args:
        duration_ms: Operation duration in milliseconds
        threshold_ms: Threshold for slow operation (default 2000ms)
        
    Returns:
        True if operation was slow, False otherwise
    """
    return duration_ms > threshold_ms


def log_slow_operation(operation: str, duration_ms: float, threshold_ms: float = 2000) -> None:
    """
    Log a warning if operation was slow.
    
    Args:
        operation: Name of the operation
        duration_ms: Operation duration in milliseconds
        threshold_ms: Threshold for slow operation (default 2000ms)
    """
    if check_slow_operation(duration_ms, threshold_ms):
        logger.warning(
            "slow_operation_detected",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            threshold_ms=threshold_ms,
            slowness_factor=round(duration_ms / threshold_ms, 2)
        )

