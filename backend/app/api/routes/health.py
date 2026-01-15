"""
Health Check Routes
Simple endpoint to verify API is running
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cerebro API",
        "version": "0.1.0"
    }
