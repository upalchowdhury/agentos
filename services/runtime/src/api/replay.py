"""
Replay API Endpoints
US-D1: Deterministic replay
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..replay import replay_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/replay", tags=["replay"])


class ReplayRequest(BaseModel):
    """Request to replay an invocation"""
    invocation_id: str
    replay_mode: str = "strict"  # "strict" or "permissive"
    override_temperature: Optional[float] = None
    override_seed: Optional[int] = None


class ReplayConfigResponse(BaseModel):
    """Replay configuration"""
    original_invocation_id: str
    agent_id: str
    agent_name: str
    input_data: dict
    model_provider: Optional[str]
    model_name: Optional[str]
    temperature: float
    seed: int
    replay_mode: str


@router.post("/prepare")
async def prepare_replay(request: ReplayRequest):
    """
    Prepare replay configuration from original invocation
    Returns configuration that will be used for replay
    """
    try:
        invocation_uuid = UUID(request.invocation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invocation_id format")
    
    try:
        override_config = {}
        
        if request.override_temperature is not None:
            override_config["temperature"] = request.override_temperature
        
        if request.override_seed is not None:
            override_config["seed"] = request.override_seed
        
        override_config["replay_mode"] = request.replay_mode
        
        config = await replay_engine.prepare_replay(
            invocation_id=invocation_uuid,
            override_config=override_config,
        )
        
        return ReplayConfigResponse(**config)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to prepare replay: {e}")
        raise HTTPException(status_code=500, detail=f"Replay preparation failed: {str(e)}")


@router.post("/execute")
async def execute_replay(request: ReplayRequest):
    """
    Execute deterministic replay
    
    US-D1: Reproduce identical step graph unless nondeterminism detected
    """
    try:
        invocation_uuid = UUID(request.invocation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invocation_id format")
    
    try:
        # Prepare config
        override_config = {
            "replay_mode": request.replay_mode,
        }
        
        if request.override_temperature is not None:
            override_config["temperature"] = request.override_temperature
        
        if request.override_seed is not None:
            override_config["seed"] = request.override_seed
        
        config = await replay_engine.prepare_replay(
            invocation_id=invocation_uuid,
            override_config=override_config,
        )
        
        # Execute replay
        result = await replay_engine.execute_replay(
            replay_config=config,
            requester_id="system:replay",
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Replay execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(e)}")


@router.get("/history/{invocation_id}")
async def get_replay_history(invocation_id: str):
    """
    Get all replays of an invocation
    """
    try:
        invocation_uuid = UUID(invocation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invocation_id format")
    
    try:
        from ..database import db
        
        rows = await db.fetch(
            """
            SELECT id, status, started_at, execution_time_ms, metadata
            FROM invocations
            WHERE metadata->>'original_invocation_id' = $1
            ORDER BY started_at DESC
            """,
            str(invocation_uuid),
        )
        
        replays = []
        for row in rows:
            import json
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            
            replays.append({
                "replay_id": str(row["id"]),
                "status": row["status"],
                "started_at": row["started_at"].isoformat(),
                "execution_time_ms": row["execution_time_ms"],
                "nondeterminism_detected": metadata.get("nondeterminism_detected", False),
                "differences_count": len(metadata.get("differences", [])),
            })
        
        return {
            "original_invocation_id": invocation_id,
            "replay_count": len(replays),
            "replays": replays,
        }
    
    except Exception as e:
        logger.error(f"Failed to get replay history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
