import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..database import db
from ..models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    checks = {
        "database": False,
        "executor": True
    }
    
    try:
        await db.fetchrow("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    response = HealthResponse(
        status=overall_status,
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow(),
        checks=checks
    )
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    return response
