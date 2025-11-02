"""
Deterministic Replay System
US-D1: Reproduce bugs with identical inputs/tools/models
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .database import db

logger = logging.getLogger(__name__)


class ReplaySession:
    """Manages a replay session"""
    
    def __init__(
        self,
        original_invocation_id: UUID,
        replay_id: UUID,
        replay_mode: str = "strict",
    ):
        self.original_invocation_id = original_invocation_id
        self.replay_id = replay_id
        self.replay_mode = replay_mode  # "strict" or "permissive"
        self.differences: List[Dict] = []
        self.nondeterminism_detected = False
    
    def record_difference(self, step_name: str, expected: Any, actual: Any):
        """Record a difference between original and replay"""
        self.differences.append({
            "step": step_name,
            "expected": str(expected),
            "actual": str(actual),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        if self.replay_mode == "strict":
            logger.warning(f"Replay difference in {step_name}: expected={expected}, actual={actual}")
    
    def mark_nondeterministic(self, reason: str):
        """Mark replay as having nondeterminism"""
        self.nondeterminism_detected = True
        logger.info(f"Nondeterminism detected: {reason}")


class ReplayEngine:
    """Engine for deterministic replay of agent invocations"""
    
    async def prepare_replay(
        self,
        invocation_id: UUID,
        override_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Prepare replay configuration from original invocation
        
        Args:
            invocation_id: Original invocation to replay
            override_config: Optional overrides for replay
        
        Returns:
            Replay configuration dict
        """
        # Get original invocation
        row = await db.fetchrow(
            """
            SELECT i.*, a.name as agent_name, a.model_type, 
                   av.artifact_uri, av.requirements_json
            FROM invocations i
            JOIN agents a ON i.agent_id = a.id
            LEFT JOIN agent_versions av ON i.version_id = av.id
            WHERE i.id = $1
            """,
            invocation_id,
        )
        
        if not row:
            raise ValueError(f"Invocation not found: {invocation_id}")
        
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        input_data = json.loads(row["input_data"]) if row["input_data"] else {}
        
        # Build replay config
        replay_config = {
            "original_invocation_id": str(invocation_id),
            "agent_id": str(row["agent_id"]),
            "agent_name": row["agent_name"],
            "version_id": str(row["version_id"]) if row["version_id"] else None,
            "input_data": input_data,
            "requirements": row["requirements_json"],
            "model_provider": metadata.get("provider_adapter"),
            "model_name": metadata.get("model_name"),
            "temperature": metadata.get("temperature", 0.0),  # Force deterministic
            "seed": metadata.get("seed", 42),
            "tools": metadata.get("tools", []),
            "original_steps": metadata.get("steps", []),
            "original_output": json.loads(row["output_data"]) if row["output_data"] else None,
            "replay_mode": override_config.get("replay_mode", "strict") if override_config else "strict",
        }
        
        # Apply overrides
        if override_config:
            replay_config.update(override_config)
        
        logger.info(f"Prepared replay config for invocation {invocation_id}")
        
        return replay_config
    
    async def execute_replay(
        self,
        replay_config: Dict[str, Any],
        requester_id: str,
    ) -> Dict[str, Any]:
        """
        Execute replay with deterministic configuration
        
        Returns:
            Replay result with comparison to original
        """
        replay_id = uuid4()
        agent_id = UUID(replay_config["agent_id"])
        original_invocation_id = UUID(replay_config["original_invocation_id"])
        
        session = ReplaySession(
            original_invocation_id=original_invocation_id,
            replay_id=replay_id,
            replay_mode=replay_config["replay_mode"],
        )
        
        # Store replay invocation
        started_at = datetime.utcnow()
        
        try:
            # Execute agent with deterministic config
            # For now, we'll simulate execution - in production, call actual agent
            result = await self._execute_agent_deterministic(replay_config, session)
            
            ended_at = datetime.utcnow()
            execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)
            
            # Compare with original
            comparison = await self._compare_with_original(
                result,
                replay_config["original_steps"],
                replay_config["original_output"],
                session,
            )
            
            # Store replay invocation
            await db.execute(
                """
                INSERT INTO invocations (
                    id, agent_id, requester_id, status, 
                    started_at, ended_at, execution_time_ms,
                    input_data, output_data, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                replay_id,
                agent_id,
                requester_id,
                "SUCCESS" if result["success"] else "ERROR",
                started_at,
                ended_at,
                execution_time_ms,
                json.dumps(replay_config["input_data"]),
                json.dumps(result.get("output")),
                json.dumps({
                    "replay": True,
                    "original_invocation_id": str(original_invocation_id),
                    "replay_mode": replay_config["replay_mode"],
                    "nondeterminism_detected": session.nondeterminism_detected,
                    "differences": session.differences,
                    "comparison": comparison,
                }),
            )
            
            return {
                "replay_id": str(replay_id),
                "original_invocation_id": str(original_invocation_id),
                "status": "success" if result["success"] else "error",
                "nondeterminism_detected": session.nondeterminism_detected,
                "differences_count": len(session.differences),
                "differences": session.differences,
                "comparison": comparison,
                "result": result,
            }
        
        except Exception as e:
            logger.error(f"Replay execution failed: {e}")
            
            ended_at = datetime.utcnow()
            execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)
            
            await db.execute(
                """
                INSERT INTO invocations (
                    id, agent_id, requester_id, status, 
                    started_at, ended_at, execution_time_ms,
                    input_data, error_message, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                replay_id,
                agent_id,
                requester_id,
                "ERROR",
                started_at,
                ended_at,
                execution_time_ms,
                json.dumps(replay_config["input_data"]),
                str(e),
                json.dumps({
                    "replay": True,
                    "original_invocation_id": str(original_invocation_id),
                    "error": str(e),
                }),
            )
            
            return {
                "replay_id": str(replay_id),
                "original_invocation_id": str(original_invocation_id),
                "status": "error",
                "error": str(e),
            }
    
    async def _execute_agent_deterministic(
        self,
        config: Dict[str, Any],
        session: ReplaySession,
    ) -> Dict[str, Any]:
        """
        Execute agent with deterministic configuration
        
        In production, this would:
        1. Restore exact agent version
        2. Mock external calls with recorded responses
        3. Set fixed random seeds
        4. Capture all steps
        """
        # For now, simulate execution
        logger.info(f"Executing replay with config: {config['agent_name']}")
        
        # Simulate steps
        steps = []
        for original_step in config.get("original_steps", []):
            step = {
                "step_id": original_step.get("step_id"),
                "name": original_step.get("name"),
                "kind": original_step.get("kind"),
                "status": "success",
                "latency_ms": original_step.get("latency_ms", 0),
            }
            steps.append(step)
        
        # Check for nondeterminism sources
        if config.get("model_provider") in ["openai", "anthropic"] and config.get("temperature", 0) > 0:
            session.mark_nondeterministic("Non-zero temperature in LLM call")
        
        if "random" in str(config.get("tools", [])).lower():
            session.mark_nondeterministic("Random tool usage detected")
        
        return {
            "success": True,
            "steps": steps,
            "output": config.get("original_output"),
        }
    
    async def _compare_with_original(
        self,
        result: Dict[str, Any],
        original_steps: List[Dict],
        original_output: Any,
        session: ReplaySession,
    ) -> Dict[str, Any]:
        """Compare replay result with original"""
        comparison = {
            "steps_match": True,
            "output_match": True,
            "step_count_original": len(original_steps),
            "step_count_replay": len(result.get("steps", [])),
        }
        
        # Compare step count
        if len(original_steps) != len(result.get("steps", [])):
            comparison["steps_match"] = False
            session.record_difference(
                "step_count",
                len(original_steps),
                len(result.get("steps", [])),
            )
        
        # Compare steps
        for i, (orig, replay) in enumerate(zip(original_steps, result.get("steps", []))):
            if orig.get("name") != replay.get("name"):
                comparison["steps_match"] = False
                session.record_difference(
                    f"step_{i}_name",
                    orig.get("name"),
                    replay.get("name"),
                )
            
            if orig.get("status") != replay.get("status"):
                comparison["steps_match"] = False
                session.record_difference(
                    f"step_{i}_status",
                    orig.get("status"),
                    replay.get("status"),
                )
        
        # Compare output (simplified - in production, use deep comparison)
        if original_output != result.get("output"):
            comparison["output_match"] = False
            session.record_difference(
                "output",
                original_output,
                result.get("output"),
            )
        
        return comparison


# Global replay engine
replay_engine = ReplayEngine()
