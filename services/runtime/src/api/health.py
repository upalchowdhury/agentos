import logging
from datetime import datetime
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..database import db
from ..models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def _run_health_checks() -> Tuple[Dict[str, bool], str]:
    checks: Dict[str, bool] = {
        "database": False,
        "executor": True,
    }

    try:
        await db.fetchrow("SELECT 1")
        checks["database"] = True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)

    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    return checks, overall_status


@router.get("/health", response_model=HealthResponse)
async def health_check():
    checks, overall_status = await _run_health_checks()

    response = HealthResponse(
        status=overall_status,
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow(),
        checks=checks,
    )

    if overall_status != "healthy":
        raise HTTPException(status_code=503, detail=response.model_dump())

    return response


@router.get("/v1/health")
async def v1_health():
    _, overall_status = await _run_health_checks()

    if overall_status != "healthy":
        raise HTTPException(status_code=503, detail={"status": "unhealthy"})

    return {"status": "ok"}


@router.get("/v1/health/ready")
async def v1_health_ready():
    _, overall_status = await _run_health_checks()

    if overall_status != "healthy":
        raise HTTPException(status_code=503, detail={"status": "not_ready"})

    return {"status": "ready"}
