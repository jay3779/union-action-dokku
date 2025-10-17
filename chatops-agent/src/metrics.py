"""
Metrics collection for Prometheus-compatible monitoring.

Provides request count, error count, and response time metrics
in a format compatible with Prometheus scraping.
"""

import time
import structlog
from collections import defaultdict
from typing import Dict, List
from datetime import datetime

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """
    Collects service metrics for monitoring and alerting.
    
    Tracks:
    - Request counts by endpoint and status
    - Error counts by category
    - Response times (histogram buckets)
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.request_total = defaultdict(int)  # By endpoint, status
        self.error_total = defaultdict(int)    # By category
        self.request_durations = []  # List of (endpoint, duration_ms)
        self.union_action_api_calls = defaultdict(int)  # Union Action API calls
        self.union_action_api_durations = []  # Union Action API response times
        self.start_time = time.time()
        
        logger.info("metrics_collector_initialized")
    
    def record_request(self, endpoint: str, status_code: int, duration_ms: float):
        """
        Record a completed request.
        
        Args:
            endpoint: Endpoint path (e.g., '/webhook', '/health')
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        # Increment request counter
        key = f"{endpoint}:{status_code}"
        self.request_total[key] += 1
        
        # Record duration
        self.request_durations.append((endpoint, duration_ms))
        
        # Keep only recent durations (last 1000)
        if len(self.request_durations) > 1000:
            self.request_durations = self.request_durations[-1000:]
        
        logger.debug(
            "metrics_request_recorded",
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=round(duration_ms, 2)
        )
    
    def record_error(self, error_category: str):
        """
        Record an error occurrence.
        
        Args:
            error_category: Error category (validation, parsing, integration, unknown)
        """
        self.error_total[error_category] += 1
        
        logger.debug(
            "metrics_error_recorded",
            category=error_category,
            total=self.error_total[error_category]
        )
    
    def record_union_action_api_call(self, endpoint: str, status_code: int, duration_ms: float):
        """
        Record a Union Action API call.
        
        Args:
            endpoint: Union Action API endpoint (e.g., '/escalate-to-ethics', '/generate-koers-survey')
            status_code: HTTP status code
            duration_ms: Call duration in milliseconds
        """
        # Increment Union Action API call counter
        key = f"union_action_api:{endpoint}:{status_code}"
        self.union_action_api_calls[key] += 1
        
        # Record duration
        self.union_action_api_durations.append((endpoint, duration_ms))
        
        # Keep only last 1000 durations to prevent memory growth
        if len(self.union_action_api_durations) > 1000:
            self.union_action_api_durations = self.union_action_api_durations[-1000:]
        
        logger.debug(
            "union_action_api_call_recorded",
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=round(duration_ms, 2)
        )
    
    def get_request_total(self) -> Dict[str, int]:
        """
        Get total request counts.
        
        Returns:
            Dictionary of request counts by endpoint and status
        """
        return dict(self.request_total)
    
    def get_error_total(self) -> Dict[str, int]:
        """
        Get total error counts.
        
        Returns:
            Dictionary of error counts by category
        """
        return dict(self.error_total)
    
    def get_request_duration_histogram(self, endpoint: str = None) -> Dict[str, int]:
        """
        Get request duration histogram in Prometheus format.
        
        Args:
            endpoint: Optional endpoint filter
            
        Returns:
            Dictionary with bucket counts (le=0.1, le=0.5, le=1.0, etc.)
        """
        # Define histogram buckets (in seconds)
        buckets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf')]
        histogram = {f"le_{b}": 0 for b in buckets}
        
        # Filter durations
        durations = self.request_durations
        if endpoint:
            durations = [(ep, dur) for ep, dur in durations if ep == endpoint]
        
        # Count into buckets
        for _, duration_ms in durations:
            duration_s = duration_ms / 1000.0
            for bucket in buckets:
                if duration_s <= bucket:
                    histogram[f"le_{bucket}"] += 1
        
        return histogram
    
    def get_uptime_seconds(self) -> float:
        """
        Get service uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time
    
    def reset(self):
        """Reset all metrics (useful for testing)."""
        self.request_total.clear()
        self.error_total.clear()
        self.request_durations.clear()
        logger.info("metrics_reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()


def format_prometheus_metrics(collector: MetricsCollector) -> str:
    """
    Format metrics in Prometheus text format.
    
    Args:
        collector: MetricsCollector instance
        
    Returns:
        Prometheus-formatted metrics string
    """
    lines = []
    
    # Add help text
    lines.append("# HELP whatsapp_chatops_agent_requests_total Total number of HTTP requests")
    lines.append("# TYPE whatsapp_chatops_agent_requests_total counter")
    
    # Request totals
    for endpoint_status, count in collector.get_request_total().items():
        endpoint, status = endpoint_status.split(":", 1)
        lines.append(
            f'whatsapp_chatops_agent_requests_total{{endpoint="{endpoint}",status="{status}"}} {count}'
        )
    
    lines.append("")
    lines.append("# HELP whatsapp_chatops_agent_errors_total Total number of errors by category")
    lines.append("# TYPE whatsapp_chatops_agent_errors_total counter")
    
    # Error totals
    for category, count in collector.get_error_total().items():
        lines.append(
            f'whatsapp_chatops_agent_errors_total{{category="{category}"}} {count}'
        )
    
    lines.append("")
    lines.append("# HELP whatsapp_chatops_agent_request_duration_seconds Request duration histogram")
    lines.append("# TYPE whatsapp_chatops_agent_request_duration_seconds histogram")
    
    # Duration histogram for /webhook endpoint
    histogram = collector.get_request_duration_histogram("/webhook")
    for bucket_label, count in histogram.items():
        bucket_value = bucket_label.replace("le_", "")
        lines.append(
            f'whatsapp_chatops_agent_request_duration_seconds_bucket{{endpoint="/webhook",le="{bucket_value}"}} {count}'
        )
    
    # Add sum and count (required for histogram)
    total_duration = sum(dur for _, dur in collector.request_durations) / 1000.0
    total_count = len(collector.request_durations)
    lines.append(
        f'whatsapp_chatops_agent_request_duration_seconds_sum{{endpoint="/webhook"}} {total_duration:.3f}'
    )
    lines.append(
        f'whatsapp_chatops_agent_request_duration_seconds_count{{endpoint="/webhook"}} {total_count}'
    )
    
    lines.append("")
    lines.append("# HELP whatsapp_chatops_agent_uptime_seconds Service uptime in seconds")
    lines.append("# TYPE whatsapp_chatops_agent_uptime_seconds gauge")
    lines.append(f'whatsapp_chatops_agent_uptime_seconds {collector.get_uptime_seconds():.0f}')
    
    return "\n".join(lines) + "\n"


def format_json_metrics(collector: MetricsCollector) -> Dict:
    """
    Format metrics as JSON (alternative to Prometheus format).
    
    Args:
        collector: MetricsCollector instance
        
    Returns:
        Dictionary with all metrics
    """
    return {
        "timestamp": datetime.now().isoformat() + "Z",
        "uptime_seconds": round(collector.get_uptime_seconds(), 2),
        "requests": {
            "total": collector.get_request_total(),
            "count": sum(collector.get_request_total().values())
        },
        "errors": {
            "by_category": collector.get_error_total(),
            "count": sum(collector.get_error_total().values())
        },
        "response_times": {
            "histogram": collector.get_request_duration_histogram(),
            "sample_size": len(collector.request_durations)
        }
    }


class MetricsMiddleware:
    """
    Middleware to automatically record request metrics.
    
    Can be added to FastAPI app to track all requests.
    """
    
    def __init__(self, app, collector: MetricsCollector):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI app
            collector: MetricsCollector instance
        """
        self.app = app
        self.collector = collector
    
    async def __call__(self, request, call_next):
        """
        Process request and record metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Record successful request
            self.collector.record_request(
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record failed request (500)
            self.collector.record_request(
                endpoint=request.url.path,
                status_code=500,
                duration_ms=duration_ms
            )
            
            # Re-raise exception
            raise

