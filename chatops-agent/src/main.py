from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import os
import time
import uuid
import threading
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from .union_action_client_http import UnionActionClient
from .logging_config import configure_logging, set_correlation_id, clear_correlation_id, get_correlation_id
from .error_handlers import (
    ChatOpsAgentError,
    WebhookValidationError,
    ParseError,
    ValidationError,
    categorize_error,
    extract_error_context
)
from .error_responses import (
    build_error_response,
    build_parse_error_response,
    build_validation_error_response,
    build_integration_error_response,
    build_server_error_response,
    build_success_response,
    log_error_with_context
)
from .diagnostics import error_tracker, log_slow_operation
from .validation import (
    validate_webhook_payload,
    validate_message_format,
    validate_workflow_id,
    get_validation_summary
)
from .health_checks import (
    check_memory_usage,
    check_union_action_api,
    get_uptime,
    check_recent_errors,
    aggregate_health_status,
    format_health_response,
    health_cache
)
from .metrics import (
    metrics_collector,
    format_prometheus_metrics,
    format_json_metrics
)

load_dotenv()

# Configure logging with enhanced diagnostic features
configure_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("ENVIRONMENT", "dev") != "dev"
)

app = FastAPI(
    title="WhatsApp ChatOps Agent",
    description="An agent to orchestrate the Union Action Workflow Integration API via WhatsApp with comprehensive diagnostics.",
    version="0.1.0",
)

logger = structlog.get_logger(__name__)

# Initialize the Union Action Client (HTTP API integration)
union_action_client = UnionActionClient(
    base_url=os.getenv("UNION_ACTION_API_URL", "http://localhost:8000"),
    timeout=float(os.getenv("UNION_ACTION_TIMEOUT", "30.0"))
)


# T060: Startup health check and bundled service startup
@app.on_event("startup")
async def startup_health_check():
    """
    Perform health checks on startup and start bundled Union Action API.

    Verifies:
    - Union Action Service is accessible via HTTP
    - Required configuration is present
    - Bundled Union Action API is started
    """
    logger.info("startup_health_check_starting")

    # Start bundled Union Action API if running in bundled mode
    union_action_url = os.getenv("UNION_ACTION_API_URL", "http://localhost:8000")
    if union_action_url.startswith("http://localhost") or union_action_url.startswith("http://127.0.0.1"):
        logger.info("starting_bundled_union_action_api")
        try:
            # Start Union Action API in background
            import subprocess
            import threading
            
            def start_union_action_api():
                try:
                    subprocess.run([
                        "/app/union-action/scripts/start.sh"
                    ], check=True)
                except subprocess.CalledProcessError as e:
                    logger.error("failed_to_start_union_action_api", error=str(e))
            
            # Start in background thread
            union_action_thread = threading.Thread(target=start_union_action_api, daemon=True)
            union_action_thread.start()
            
            # Wait a moment for startup
            await asyncio.sleep(2)
            
            logger.info("bundled_union_action_api_started")
        except Exception as e:
            logger.error("failed_to_start_bundled_union_action_api", error=str(e))

    try:
        # Check Union Action Service health
        health_status = await union_action_client.health_check()
        logger.info(
            "startup_health_check_success",
            union_action_service_status=health_status.get("status", "unknown"),
            union_action_service_version=health_status.get("version", "unknown")
        )
    except Exception as e:
        logger.error(
            "startup_health_check_failed",
            error=str(e),
            error_type=type(e).__name__,
            message="Union Action Service is not accessible"
        )
        # Don't fail startup - service might start later
        logger.warning("startup_continuing_without_union_action_service")

    logger.info("startup_complete", uptime_seconds=0, integration="http_api")


# T086: Graceful shutdown handler for Render deployments
@app.on_event("shutdown")
async def graceful_shutdown():
    """
    Handle graceful shutdown for zero-downtime deployments on Render.

    - Log shutdown signal
    - Allow in-flight requests to complete
    - Close connections cleanly
    """
    logger.info(
        "graceful_shutdown_initiated",
        reason="shutdown_signal_received",
        uptime_seconds=get_uptime()
    )

    # Close HTTP client
    try:
        await union_action_client.close()
        logger.info("union_action_client_closed")
    except Exception as e:
        logger.error("union_action_client_close_error", error=str(e))

    # Log final metrics before shutdown
    from .metrics import metrics_collector, format_json_metrics
    final_metrics = format_json_metrics(metrics_collector)
    logger.info(
        "final_metrics_before_shutdown",
        total_requests=final_metrics["requests"]["count"],
        total_errors=final_metrics["errors"]["count"],
        uptime_seconds=final_metrics["uptime_seconds"]
    )

    logger.info("graceful_shutdown_complete")


# Correlation ID Middleware (T010)
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests for tracing."""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        try:
            response = await call_next(request)
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            # Clear correlation ID after request
            clear_correlation_id()


# Request/Response Logging Middleware (T015)
class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with timing."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log incoming request
        logger.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            correlation_id=get_correlation_id()
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                correlation_id=get_correlation_id()
            )

            # Check for slow requests
            log_slow_operation(f"{request.method} {request.url.path}", duration_ms)

            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2),
                correlation_id=get_correlation_id()
            )
            raise


# Add middleware to app
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(RequestResponseLoggingMiddleware)


# Global Exception Handler (T014)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that logs unhandled exceptions with full context.

    This ensures all errors are logged before returning to the client,
    even if they escape route handlers.
    """
    # Extract error context
    error_context = extract_error_context(exc)
    error_context.update({
        "path": request.url.path,
        "method": request.method,
        "correlation_id": get_correlation_id()
    })

    # Log error with full context
    log_error_with_context(exc, error_context, severity="error")

    # Track error for metrics
    error_category = categorize_error(exc)
    error_tracker.track_error(error_category)

    # Build appropriate error response
    if isinstance(exc, ChatOpsAgentError):
        # Use custom error response for known errors
        response = build_error_response(
            detail=exc.message,
            error_code=error_context.get("error_category", "UNKNOWN").upper(),
            additional_context=exc.details
        )
        status_code = 400 if error_category == "validation" or error_category == "parsing" else 500
    elif isinstance(exc, HTTPException):
        # FastAPI HTTPException
        response = build_error_response(
            detail=exc.detail,
            error_code="HTTP_ERROR"
        )
        status_code = exc.status_code
    else:
        # Unknown error - return generic message
        response = build_server_error_response(
            message="An unexpected error occurred",
            operation=f"{request.method} {request.url.path}"
        )
        status_code = 500

    return JSONResponse(content=response, status_code=status_code)


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handles incoming WhatsApp messages from the WAHA client with comprehensive diagnostics.

    Enhanced with:
    - Comprehensive validation using validation module (T038)
    - Detailed payload logging
    - Step-by-step parsing diagnostics
    - Timing metrics
    - Error context tracking
    """
    webhook_start_time = time.time()

    try:
        # Parse and log incoming payload (T023)
        data = await request.json()
        logger.info(
            "webhook_received",
            from_user=data.get("from", "unknown"),
            message_length=len(data.get("body", "")),
            has_timestamp=bool(data.get("timestamp")),
            correlation_id=get_correlation_id()
        )

        # T038: Validate webhook payload structure
        is_valid, error_message = validate_webhook_payload(data)
        if not is_valid:
            logger.warning(
                "webhook_payload_validation_failed",
                reason=error_message,
                payload_keys=list(data.keys()),
                correlation_id=get_correlation_id()
            )
            # Track validation error
            error_tracker.track_error("validation", {"reason": error_message})

            return JSONResponse(
                content=build_validation_error_response(
                    message=error_message,
                    field_name="body",
                    expected_format="non-empty string"
                ),
                status_code=400
            )

        # Extract message body
        message = data.get("body", "")

        # T039: Log validation summary for diagnostics
        validation_summary = get_validation_summary(message)
        logger.debug(
            "message_validation_summary",
            **validation_summary,
            correlation_id=get_correlation_id()
        )

        # T040: Validate message format using validation module
        is_valid, error_message, parsed_components = validate_message_format(message)
        if not is_valid:
            logger.warning(
                "message_format_validation_failed",
                reason=error_message,
                message_preview=message[:200],
                validation_summary=validation_summary,
                correlation_id=get_correlation_id()
            )
            # Track parse error
            error_tracker.track_error("parsing", {"reason": error_message})

            return JSONResponse(
                content=build_parse_error_response(
                    message=error_message,
                    parse_stage="format_validation"
                ),
                status_code=400
            )

        # Extract parsed components
        narrative = parsed_components["narrative"]
        maxim = parsed_components["maxim"]

        logger.info(
            "message_validated_successfully",
            narrative_length=len(narrative),
            maxim_length=len(maxim),
            correlation_id=get_correlation_id()
        )

        # T041: Extract and validate workflow_id
        workflow_id = data.get("from", "unknown_user")
        is_valid, error_message = validate_workflow_id(workflow_id)
        if not is_valid:
            logger.warning(
                "workflow_id_validation_failed",
                workflow_id=workflow_id,
                reason=error_message,
                correlation_id=get_correlation_id()
            )
            # Track validation error
            error_tracker.track_error("validation", {"reason": error_message, "field": "workflow_id"})

            return JSONResponse(
                content=build_validation_error_response(
                    message=error_message,
                    field_name="from",
                    expected_format="non-empty phone number"
                ),
                status_code=400
            )

        logger.info(
            "workflow_data_validated",
            workflow_id=workflow_id,
            narrative_length=len(narrative),
            maxim_length=len(maxim)
        )

        # Timing: parsing complete
        parse_duration_ms = (time.time() - webhook_start_time) * 1000
        logger.debug("parsing_completed", duration_ms=round(parse_duration_ms, 2))

        # Orchestrate the workflow with error context (T025)
        api_call_start_time = time.time()
        try:
            # Step 1: Escalate to ethics via Union Action Service
            ethical_report = await union_action_client.escalate_to_ethics(
                workflow_id=workflow_id,
                narrative=narrative,
                maxim=maxim
            )

            # Step 2: Generate KOERS survey via Union Action Service
            deployment_report = await union_action_client.generate_koers_survey(
                workflow_id=workflow_id,
                ethical_report=ethical_report
            )

            # Combine results
            result = {
                "status": "success",
                "ethical_analysis": ethical_report,
                "deployment_report": deployment_report,
                "survey_url": deployment_report.get("survey_url"),
                "module_list": deployment_report.get("module_list", [])
            }

            api_call_duration_ms = (time.time() - api_call_start_time) * 1000

            logger.info(
                "workflow_orchestrated",
                workflow_id=workflow_id,
                result_status=result.get("status"),
                survey_url=result.get("survey_url"),
                module_count=len(result.get("module_list", [])),
                api_call_duration_ms=round(api_call_duration_ms, 2)
            )
        except Exception as api_error:
            api_call_duration_ms = (time.time() - api_call_start_time) * 1000

            # Enhanced error context (T025)
            logger.error(
                "workflow_orchestration_failed",
                workflow_id=workflow_id,
                narrative_preview=narrative[:100] if narrative else "",
                maxim_preview=maxim[:100] if maxim else "",
                error_type=type(api_error).__name__,
                error_message=str(api_error),
                api_call_duration_ms=round(api_call_duration_ms, 2),
                correlation_id=get_correlation_id()
            )

            # Track error for metrics
            error_tracker.track_error("integration")

            # Re-raise to be handled by global exception handler
            raise

        # Timing metrics for complete webhook processing (T026)
        total_duration_ms = (time.time() - webhook_start_time) * 1000
        logger.info(
            "webhook_processing_complete",
            workflow_id=workflow_id,
            total_duration_ms=round(total_duration_ms, 2),
            parse_duration_ms=round(parse_duration_ms, 2),
            api_call_duration_ms=round(api_call_duration_ms, 2),
            correlation_id=get_correlation_id()
        )

        # Check for slow processing
        log_slow_operation("webhook_processing", total_duration_ms)

        # Build success response with timing (T042)
        return JSONResponse(
            content=build_success_response(result, total_duration_ms),
            status_code=200
        )

    except HTTPException:
        # Let FastAPI handle HTTPExceptions
        raise
    except Exception as e:
        total_duration_ms = (time.time() - webhook_start_time) * 1000

        # Log unhandled exception with full context
        logger.error(
            "webhook_error",
            error_type=type(e).__name__,
            error_message=str(e),
            total_duration_ms=round(total_duration_ms, 2),
            correlation_id=get_correlation_id(),
            exc_info=True  # Include traceback
        )

        # Track error
        error_tracker.track_error("unknown")

        # Re-raise to be handled by global exception handler
        raise

@app.get("/health")
def health_check():
    """
    Comprehensive health check endpoint (T052-T056).

    Returns:
    - Service version, uptime, timestamp (T052)
    - Dependency health checks - Union Action API (T053)
    - System resource checks - memory usage (T054)
    - Recent error count (last 5 minutes) (T055)
    - Cached results (10 second TTL) to prevent overload (T056)
    """
    # Check cache first (T056)
    cached_result = health_cache.get("health_check")
    if cached_result is not None:
        logger.debug("health_check_cache_hit")
        return cached_result

    logger.debug("health_check_cache_miss_running_checks")

    # T054: Check system resources (memory)
    memory_check = check_memory_usage(threshold_percent=80.0)

    # Check Union Action API health
    union_action_check = check_union_action_api()

    # T055: Get recent error count (last 5 minutes)
    recent_errors = check_recent_errors(time_window_seconds=300)

    # Get error tracker summary for overall metrics
    error_summary = error_tracker.get_summary()

    # Aggregate overall health status
    checks_list = [memory_check, union_action_check]
    overall_status = aggregate_health_status(checks_list)

    # If too many recent errors, degrade status
    if recent_errors["count"] > 10:
        overall_status = "degraded"

    # T052: Build response with version, uptime, timestamp
    response = format_health_response(
        overall_status=overall_status,
        checks={
            "union_action_api": union_action_check,
            "memory": memory_check
        },
        uptime_seconds=get_uptime(),
        version="0.1.0",  # TODO: Get from package metadata
        error_metrics={
            "total_errors": error_summary["total_errors"],
            "errors_by_category": error_summary["errors"],
            "recent_errors_count": error_summary["recent_errors_count"],
            "recent_errors_last_5min": recent_errors["count"],
            "time_since_reset_seconds": error_summary["time_since_reset_seconds"]
        }
    )

    # Cache result for 10 seconds (T056)
    health_cache.set("health_check", response)

    logger.info(
        "health_check_complete",
        status=overall_status,
        union_action_api_status=union_action_check["status"],
        memory_status=memory_check["status"],
        recent_errors_5min=recent_errors["count"]
    )

    return response


@app.get("/health/errors")
def health_errors():
    """
    Detailed error information endpoint (T047).

    Returns recent error details for debugging.
    """
    error_summary = error_tracker.get_summary()

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "error_metrics": error_summary["errors"],
        "total_errors": error_summary["total_errors"],
        "recent_errors": error_tracker.get_recent_errors(limit=50),  # Get last 50 errors
        "time_since_reset": error_summary["time_since_reset_seconds"],
        "last_reset": error_summary["last_reset"]
    }


@app.get("/metrics")
def metrics(format: str = "prometheus"):
    """
    Prometheus-compatible metrics endpoint (T058).

    Returns service metrics in Prometheus text format or JSON.

    Args:
        format: Response format ('prometheus' or 'json')

    Returns:
        Metrics in requested format
    """
    if format.lower() == "json":
        # Return JSON format
        return format_json_metrics(metrics_collector)
    else:
        # Return Prometheus text format
        from fastapi.responses import PlainTextResponse
        metrics_text = format_prometheus_metrics(metrics_collector)
        return PlainTextResponse(content=metrics_text, media_type="text/plain")


@app.get("/debug")
def debug_endpoint():
    """
    Debug endpoint with system state (T063).

    Only enabled in development mode.
    Returns recent requests, errors, and system state for debugging.

    Returns:
        Debug information or 403 if not in dev mode
    """
    # Only allow in dev mode
    if os.getenv("ENVIRONMENT", "dev") != "dev":
        raise HTTPException(
            status_code=403,
            detail="Debug endpoint only available in development mode"
        )

    # Get error tracker data
    error_summary = error_tracker.get_summary()
    recent_errors = error_tracker.get_recent_errors(limit=20)

    # Get metrics
    metrics_data = format_json_metrics(metrics_collector)

    # Get system info
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()

    return {
        "status": "debug",
        "timestamp": datetime.now().isoformat() + "Z",
        "service": {
            "name": "whatsapp-chatops-agent",
            "version": "0.1.0",
            "uptime_seconds": get_uptime(),
            "environment": os.getenv("ENVIRONMENT", "dev")
        },
        "system": {
            "memory_mb": round(memory_info.rss / (1024 * 1024), 2),
            "threads": threading.active_count() if hasattr(threading, 'active_count') else None,
            "pid": os.getpid()
        },
        "errors": {
            "total": error_summary["total_errors"],
            "by_category": error_summary["errors"],
            "recent": recent_errors
        },
        "metrics": {
            "requests": metrics_data.get("requests", {}),
            "errors": metrics_data.get("errors", {}),
            "response_times": metrics_data.get("response_times", {})
        },
        "configuration": {
            "union_api_url": os.getenv("UNION_ACTION_API_URL", "not_set"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "environment": os.getenv("ENVIRONMENT", "dev")
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
