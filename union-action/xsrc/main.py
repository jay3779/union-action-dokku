"""
FastAPI application entry point for Union Action Workflow Integration.

Constitutional Compliance:
- Stateless API: No database, no filesystem persistence
- Agent-Driven: Autonomous agent orchestrates workflow, backend provides endpoints
- Human-in-the-Loop: Agent handles human decision points
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import structlog

from .config import config
from .logging_config import configure_logging
from . import __version__

# Configure logging
configure_logging(log_level=config.log_level, log_format=config.log_format)
logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Union Action Workflow Integration API",
    description=(
        "Stateless REST API connecting ComplaintCare → Kantian Ethics → CareVoice (KOERS/Typeform). "
        "Agent-driven workflow with maintainless backend."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (allow agent access from any origin for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle Pydantic validation errors with detailed error messages.
    
    Returns 422 status with field-level error details.
    """
    logger.error(
        "validation_error",
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions with structured logging.
    
    Returns 500 status with error message.
    """
    logger.error(
        "internal_server_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
        },
    )


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        "application_startup",
        version=__version__,
        log_level=config.log_level,
        log_format=config.log_format,
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("application_shutdown", version=__version__)


# Import and include routers
from .api import health, escalate, deploy
app.include_router(health.router, tags=["health"])
app.include_router(escalate.router, tags=["workflow"])
app.include_router(deploy.router, tags=["workflow"])

