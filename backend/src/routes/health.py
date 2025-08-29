"""
Health check endpoints for monitoring application status.
Provides basic health checks and system information.
"""

import time
from datetime import datetime, timedelta
from fastapi import APIRouter, status
from ..config import settings
from ..models.base import HealthResponse, BaseResponse

# Router for health check endpoints
router = APIRouter()

# Track application start time for uptime calculation
app_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the current health status of the application"
)
async def health_check() -> HealthResponse:
    """
    Perform a basic health check of the application.
    
    Returns:
        HealthResponse: Current application health status
    """
    current_time = time.time()
    uptime = current_time - app_start_time
    
    return HealthResponse(
        message="Application is healthy",
        status="healthy",
        version=settings.app_version,
        uptime=uptime,
        environment=settings.environment
    )

@router.get(
    "/version",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Version Information",
    description="Returns the current version of the application"
)
async def get_version() -> BaseResponse:
    """
    Get the current version of the application.
    
    Returns:
        BaseResponse: Version information
    """
    return BaseResponse(
        message=f"Application version: {settings.app_version}"
    )
