"""
FastAPI application with PostgreSQL - HelpPet MVP
"""

import logging
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .config import settings
from .database_pg import database_pg
from .routes_pg import router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomJSONResponse(JSONResponse):
    """Custom JSON response with mobile-optimized headers"""
    
    def __init__(self, content=None, status_code: int = 200, **kwargs):
        super().__init__(content, status_code, **kwargs)
        
        # API metadata
        self.headers["X-API-Version"] = settings.app_version
        self.headers["X-Process-Time"] = "0.000s"  # Will be updated by middleware
        
        # Mobile-optimized caching (prevent stale data in iOS)
        self.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        self.headers["Pragma"] = "no-cache"
        self.headers["Expires"] = "0"
        
        # CORS exposure for mobile apps
        self.headers["Access-Control-Expose-Headers"] = "X-API-Version, X-Process-Time"
        
        # Mobile optimization
        self.headers["Vary"] = "Accept, Authorization, Origin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API documentation available at: {settings.docs_url}")
    
    # Initialize database connection with retries
    max_connection_attempts = 5
    connection_established = False
    
    for attempt in range(max_connection_attempts):
        try:
            # Connect to PostgreSQL
            await database_pg.connect()
            logger.info("Database connection established successfully")
            connection_established = True
            break
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_connection_attempts} failed: {e}")
            if attempt < max_connection_attempts - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s, 8s
            else:
                logger.error(f"Failed to connect to database after {max_connection_attempts} attempts: {e}")
                # Don't raise here - let the app start with degraded functionality
                logger.error("Starting application with degraded database functionality")
    
    try:
        yield
    finally:
        # Shutdown
        if connection_established:
            await database_pg.disconnect()
            logger.info("Application shutdown complete")
        else:
            logger.info("Application shutdown complete (database was not connected)")


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    description="A modern FastAPI application with PostgreSQL and best practices",
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    default_response_class=CustomJSONResponse,
    redirect_slashes=False,  # Prevent automatic trailing slash redirects
    lifespan=lifespan
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

# Log CORS configuration for debugging
logger.info(f"CORS origins: {cors_origins}")
logger.info(f"CORS methods: {cors_methods}")
logger.info(f"CORS headers: {cors_headers}")

# Additional CORS debugging
logger.info(f"Environment: {settings.environment}")
logger.info(f"Raw CORS_ORIGINS setting: {settings.cors_origins}")


# Add request timing middleware (simplified since we have comprehensive tracking above)
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}s"
    return response


# Add request logging middleware (CORS-focused since error tracking is handled above)
@app.middleware("http")
async def log_cors_requests(request, call_next):
    """Log CORS-related request information"""
    # Log CORS related headers
    origin = request.headers.get("origin")
    if origin:
        logger.debug(f"Request from origin: {origin}")
        if origin not in cors_origins:
            logger.warning(f"Origin {origin} not in allowed origins: {cors_origins}")
    
    response = await call_next(request)
    
    return response


# Include all routes
app.include_router(router)


# Pydantic validation error handler
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    """Handle Pydantic validation errors with detailed information"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.error(f"Validation error on {request.url}: {error_details}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": error_details
        }
    )

# Enhanced middleware for request tracking
@app.middleware("http")
async def track_request_errors(request, call_next):
    """Track requests and catch unhandled exceptions with full context"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        logger.info(f"[{request_id}] Starting {request.method} {request.url.path}")
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"[{request_id}] Completed {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response
        
    except Exception as exc:
        process_time = time.time() - start_time
        
        # Get comprehensive error information
        tb_str = traceback.format_exc()
        exc_type = type(exc).__name__
        exc_message = str(exc)
        
        # Log with request context
        logger.error(f"[{request_id}] UNHANDLED EXCEPTION in {request.method} {request.url.path}")
        logger.error(f"[{request_id}] Exception Type: {exc_type}")
        logger.error(f"[{request_id}] Exception Message: {exc_message}")
        logger.error(f"[{request_id}] Request Headers: {dict(request.headers)}")
        logger.error(f"[{request_id}] Process Time: {process_time:.3f}s")
        logger.error(f"[{request_id}] Full Traceback:\n{tb_str}")
        
        # For development, include more details
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                    "error_type": exc_type,
                    "error_message": exc_message,
                    "endpoint": f"{request.method} {request.url.path}",
                    "traceback": tb_str.split('\n')
                }
            )
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id
            }
        )


# Global exception handler (fallback)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler - should rarely be reached due to middleware above"""
    # Get the full traceback
    tb_str = traceback.format_exc()
    
    # Log detailed error information
    logger.error(f"GLOBAL HANDLER: Exception on {request.url.path}: {type(exc).__name__}: {exc}")
    logger.error(f"GLOBAL HANDLER: Full traceback:\n{tb_str}")
    
    # For development, include more details
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error (global handler)",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": tb_str.split('\n')
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_pg:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
