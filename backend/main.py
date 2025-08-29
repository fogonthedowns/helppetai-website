"""
FastAPI Application Entry Point

This is the main entry point for the FastAPI application.
It imports and configures the app from the src module.
"""

import uvicorn
from src.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
