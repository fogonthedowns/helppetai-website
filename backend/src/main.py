"""
FastAPI application instance with configuration and middleware setup.
This is the main FastAPI application that gets imported by the entry point.
"""

import logging
import json
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .routes import router
from .models.base import ErrorResponse
from .database import Database

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Custom JSON response class that handles datetime serialization
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=DateTimeEncoder
        ).encode("utf-8")

# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    description="A modern FastAPI application with best practices",
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    default_response_class=CustomJSONResponse,
)

# Add CORS middleware
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
cors_methods = [method.strip() for method in settings.cors_methods.split(",")]
cors_headers = [header.strip() for header in settings.cors_headers.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

# Add trusted host middleware for security
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.host, "localhost", "127.0.0.1"]
    )


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions and return consistent error responses."""
    return CustomJSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            details={
                "method": request.method,
                "url": str(request.url),
                "status_code": exc.status_code
            }
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors and return detailed error responses."""
    return CustomJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            message="Validation error in request data",
            error_code="VALIDATION_ERROR",
            details={
                "method": request.method,
                "url": str(request.url),
                "errors": exc.errors()
            }
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions and return generic error responses."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return CustomJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            details={
                "method": request.method,
                "url": str(request.url)
            } if settings.debug else None
        ).dict()
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Execute startup operations."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API documentation available at: {settings.docs_url}")
    
    # Initialize database connection
    try:
        await Database.connect_db()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        # Don't raise the exception to allow the app to start
        # but log the error so developers know there's an issue


@app.on_event("shutdown")
async def shutdown_event():
    """Execute shutdown operations."""
    logger.info(f"Shutting down {settings.app_name}")
    
    # Close database connection
    try:
        await Database.close_db()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.utcnow()
    
    # Call the next middleware/endpoint
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = settings.app_version
    
    return response


# Include all routes
app.include_router(router)


# Root endpoint
@app.get(
    "/",
    summary="Root Endpoint",
    description="Returns basic information about the API"
)
async def root():
    """
    Root endpoint that provides basic API information.
    
    Returns:
        dict: Basic API information
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": settings.docs_url,
        "health_check": "/health",
        "api_prefix": "/api/v1"
    }
