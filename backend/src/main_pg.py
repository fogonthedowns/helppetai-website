"""
FastAPI application with PostgreSQL - HelpPet MVP
"""

import logging
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
    
    try:
        # Connect to PostgreSQL
        await database_pg.connect()
        logger.info("Database connection established successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    finally:
        # Shutdown
        await database_pg.disconnect()
        logger.info("Application shutdown complete")


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


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time to response headers"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}s"
    return response


# Add request logging middleware  
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests with CORS debugging"""
    import time
    start_time = time.time()
    
    # Log CORS related headers
    origin = request.headers.get("origin")
    if origin:
        logger.info(f"Request from origin: {origin}")
        if origin not in cors_origins:
            logger.warning(f"Origin {origin} not in allowed origins: {cors_origins}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Origin: {origin} - "
        f"Time: {process_time:.3f}s"
    )
    
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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with better error details"""
    import traceback
    
    # Get the full traceback
    tb_str = traceback.format_exc()
    
    # Log detailed error information
    logger.error(f"Global exception on {request.url.path}: {type(exc).__name__}: {exc}")
    logger.error(f"Full traceback:\n{tb_str}")
    
    # For development, include more details
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
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
