"""
Enhanced error handling utilities for better debugging
"""
import functools
import logging
import traceback
from typing import Any, Callable
from fastapi import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def log_endpoint_errors(endpoint_name: str = None):
    """
    Decorator to add enhanced error logging to specific endpoints.
    
    Usage:
    @log_endpoint_errors("webhook_handler")
    async def my_endpoint():
        ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            endpoint = endpoint_name or f"{func.__module__}.{func.__name__}"
            
            try:
                logger.debug(f"[{endpoint}] Starting execution")
                result = await func(*args, **kwargs)
                logger.debug(f"[{endpoint}] Completed successfully")
                return result
                
            except HTTPException as e:
                # HTTP exceptions are expected - log but re-raise
                logger.info(f"[{endpoint}] HTTP {e.status_code}: {e.detail}")
                raise
                
            except Exception as e:
                # Unexpected exceptions - log with full context
                tb_str = traceback.format_exc()
                
                logger.error(f"[{endpoint}] UNHANDLED EXCEPTION")
                logger.error(f"[{endpoint}] Exception Type: {type(e).__name__}")
                logger.error(f"[{endpoint}] Exception Message: {str(e)}")
                logger.error(f"[{endpoint}] Args: {args}")
                logger.error(f"[{endpoint}] Kwargs: {kwargs}")
                logger.error(f"[{endpoint}] Full Traceback:\n{tb_str}")
                
                # Re-raise the original exception so it can be handled by the global handler
                raise
        
        return wrapper
    return decorator


def safe_endpoint_call(endpoint_name: str, fallback_response: Any = None):
    """
    Decorator that catches all exceptions and returns a safe response.
    
    Usage:
    @safe_endpoint_call("critical_webhook", {"status": "error", "message": "Processing failed"})
    async def webhook():
        ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                tb_str = traceback.format_exc()
                
                logger.error(f"[{endpoint_name}] SAFE FALLBACK TRIGGERED")
                logger.error(f"[{endpoint_name}] Exception: {type(e).__name__}: {str(e)}")
                logger.error(f"[{endpoint_name}] Full Traceback:\n{tb_str}")
                
                if fallback_response is not None:
                    if isinstance(fallback_response, dict):
                        return JSONResponse(
                            status_code=500,
                            content=fallback_response
                        )
                    return fallback_response
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": "Internal server error",
                        "endpoint": endpoint_name
                    }
                )
        
        return wrapper
    return decorator