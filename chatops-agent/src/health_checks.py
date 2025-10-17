"""
Health check functions for monitoring service and dependency health.

Provides individual health check functions that can be composed
for comprehensive service health monitoring.
"""

import os
import time
import psutil
import structlog
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps

logger = structlog.get_logger(__name__)

# Service start time for uptime calculation
service_start_time = datetime.now()


def with_timeout(seconds: float):
    """
    Decorator to add timeout to health check functions.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function that times out
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Health check timed out after {seconds}s")
            
            # Set alarm (Unix only, for Windows we'd need threading)
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(seconds))
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                return result
            except AttributeError:
                # Windows doesn't have SIGALRM, just run without timeout
                return func(*args, **kwargs)
            except TimeoutError:
                return {
                    "status": "timeout",
                    "error": f"Check exceeded {seconds}s timeout"
                }
        return wrapper
    return decorator


def safe_health_check(func: Callable) -> Callable:
    """
    Decorator to wrap health checks with exception handling.
    
    Ensures health checks never crash the health endpoint.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                "health_check_failed",
                check=func.__name__,
                error=str(e),
                exc_info=True
            )
            return {
                "status": "error",
                "error": str(e),
                "check": func.__name__
            }
    return wrapper


@safe_health_check
@with_timeout(5.0)
def check_union_action_api() -> Dict[str, Any]:
    """
    Check Union Action API health.
    
    Returns:
        Dictionary with Union Action API health status
    """
    try:
        # Get Union Action API URL from environment
        union_action_url = os.getenv("UNION_ACTION_API_URL", "http://localhost:8000")
        health_url = f"{union_action_url}/health"
        
        # Make HTTP request to Union Action API health endpoint
        with httpx.Client(timeout=5.0) as client:
            response = client.get(health_url)
            response.raise_for_status()
            
            health_data = response.json()
            
            # Extract status from Union Action API response
            union_status = health_data.get("status", "unknown")
            
            result = {
                "status": union_status,
                "url": health_url,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
            # Add additional info if available
            if "version" in health_data:
                result["version"] = health_data["version"]
            if "uptime_seconds" in health_data:
                result["uptime_seconds"] = health_data["uptime_seconds"]
            
            logger.debug(
                "union_action_api_check_complete",
                status=union_status,
                response_time_ms=result["response_time_ms"]
            )
            
            return result
            
    except httpx.TimeoutException:
        logger.warning("union_action_api_timeout", url=health_url)
        return {
            "status": "timeout",
            "error": "Union Action API health check timed out",
            "url": health_url
        }
    except httpx.HTTPStatusError as e:
        logger.warning(
            "union_action_api_http_error",
            status_code=e.response.status_code,
            url=health_url
        )
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}",
            "url": health_url
        }
    except Exception as e:
        logger.error("union_action_api_check_failed", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }


@safe_health_check
def check_memory_usage(threshold_percent: float = 80.0) -> Dict[str, Any]:
    """
    Check current memory usage.
    
    Args:
        threshold_percent: Percentage threshold for warning
        
    Returns:
        Dictionary with memory usage info and status
    """
    try:
        # Get process memory info
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        
        # Get system memory if available
        try:
            system_memory = psutil.virtual_memory()
            memory_percent = system_memory.percent
        except:
            memory_percent = None
        
        # Determine status based on threshold
        if memory_percent and memory_percent > threshold_percent:
            status = "warning"
        else:
            status = "ok"
        
        result = {
            "status": status,
            "usage_mb": round(memory_mb, 2),
        }
        
        if memory_percent is not None:
            result["percent"] = round(memory_percent, 2)
        
        logger.debug(
            "memory_check_complete",
            usage_mb=result["usage_mb"],
            status=status
        )
        
        return result
        
    except Exception as e:
        logger.error("memory_check_failed", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }


def get_uptime() -> float:
    """
    Get service uptime in seconds.
    
    Returns:
        Uptime in seconds
    """
    uptime = (datetime.now() - service_start_time).total_seconds()
    return uptime


def get_uptime_formatted() -> str:
    """
    Get human-readable uptime string.
    
    Returns:
        Formatted uptime string (e.g., "2h 30m 15s")
    """
    uptime_seconds = get_uptime()
    
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def check_recent_errors(time_window_seconds: int = 300) -> Dict[str, Any]:
    """
    Check for recent errors within a time window.
    
    Args:
        time_window_seconds: Time window in seconds (default 5 minutes)
        
    Returns:
        Dictionary with recent error count and breakdown
    """
    from .diagnostics import error_tracker
    
    # Get recent errors from tracker
    recent_errors = error_tracker.get_recent_errors(limit=1000)  # Get many
    
    # Filter to time window
    cutoff_time = datetime.now() - timedelta(seconds=time_window_seconds)
    
    errors_in_window = []
    for error in recent_errors:
        try:
            error_time = datetime.fromisoformat(error["timestamp"])
            if error_time > cutoff_time:
                errors_in_window.append(error)
        except:
            # Skip errors with invalid timestamps
            continue
    
    # Count by category
    by_category = {}
    for error in errors_in_window:
        category = error.get("category", "unknown")
        by_category[category] = by_category.get(category, 0) + 1
    
    return {
        "count": len(errors_in_window),
        "time_window_seconds": time_window_seconds,
        "by_category": by_category
    }


def aggregate_health_status(checks: List[Dict[str, Any]]) -> str:
    """
    Aggregate multiple health check results into overall status.
    
    Args:
        checks: List of health check results with 'status' field
        
    Returns:
        Overall status: 'ok', 'degraded', or 'down'
    """
    statuses = [check.get("status", "unknown") for check in checks]
    
    # Count status types
    error_count = statuses.count("error")
    timeout_count = statuses.count("timeout")
    unknown_count = statuses.count("unknown")
    
    total_checks = len(statuses)
    
    if total_checks == 0:
        return "unknown"
    
    # All checks ok
    if error_count == 0 and timeout_count == 0:
        return "ok"
    
    # All checks failed
    if error_count == total_checks:
        return "down"
    
    # Some checks failed - degraded
    if error_count > 0 or timeout_count > 0:
        return "degraded"
    
    # Unknown state
    return "unknown"


class HealthCheckCache:
    """Simple cache for health check results to avoid overload."""
    
    def __init__(self, ttl_seconds: int = 10):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cached results
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/missing
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                # Expired - remove
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set cached value with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cached values."""
        self.cache.clear()


# Global health check cache
health_cache = HealthCheckCache(ttl_seconds=10)


def format_health_response(
    overall_status: str,
    checks: Dict[str, Any],
    uptime_seconds: float,
    version: str,
    error_metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a comprehensive health response.
    
    Args:
        overall_status: Overall health status ('ok', 'degraded', 'down')
        checks: Dictionary of health check results
        uptime_seconds: Service uptime in seconds
        version: Service version
        error_metrics: Optional error tracking metrics
        
    Returns:
        Formatted health response dictionary
    """
    response = {
        "status": overall_status,
        "version": version,
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime": get_uptime_formatted(),
        "timestamp": datetime.now().isoformat() + "Z",
        "service": "whatsapp-chatops-agent",
        "environment": os.getenv("ENVIRONMENT", "dev")
    }
    
    # Add dependencies
    if checks:
        response["dependencies"] = checks
    
    # Add error metrics
    if error_metrics:
        response["error_metrics"] = error_metrics
    
    return response

