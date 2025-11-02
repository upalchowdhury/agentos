import asyncio
import builtins
import hashlib
import logging
import time
import uuid
from datetime import datetime
from math import ceil
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Executes user supplied agent code inside a tightly controlled sandbox.

    The sandbox exposes a curated set of built-ins and a custom import hook that
    only whitelists safe standard-library modules required for typical math or
    datetime logic. Access to the filesystem, operating system, and networking
    libraries remains blocked.
    """

    _ALLOWED_MODULES: frozenset[str] = frozenset(
        {
            "math",
            "random",
            "statistics",
            "time",
            "datetime",
            "decimal",
            "json",
            "os",
            "typing",
            "google",  # Allow google.generativeai
        }
    )

    _SAFE_BUILTINS: Dict[str, Any] = {
        "print": print,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "dict": dict,
        "list": list,
        "tuple": tuple,
        "set": set,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "isinstance": isinstance,
        "type": type,
        "all": all,
        "any": any,
        "Exception": Exception,
        "ValueError": ValueError,
        "RuntimeError": RuntimeError,
    }

    def __init__(self) -> None:
        self._original_import = builtins.__import__

    def _restricted_import(
        self,
        name: str,
        globals_: Optional[Dict[str, Any]] = None,
        locals_: Optional[Dict[str, Any]] = None,
        fromlist: Iterable[str] = (),
        level: int = 0,
    ) -> Any:
        top_level = name.split(".")[0]
        if top_level not in self._ALLOWED_MODULES:
            raise ImportError(f"Import of '{name}' is not permitted")
        fromlist_tuple = tuple(fromlist) if fromlist else ()
        return self._original_import(name, globals_, locals_, fromlist_tuple, level)

    def _prepare_globals(self, input_data: dict[str, Any]) -> Dict[str, Any]:
        safe_builtins = dict(self._SAFE_BUILTINS)
        safe_builtins["__import__"] = self._restricted_import

        sandbox_globals: Dict[str, Any] = {
            "__builtins__": safe_builtins,
            "input_data": input_data,
        }
        return sandbox_globals

    def _sync_execute(self, code: str, sandbox_globals: dict[str, Any]) -> Any:
        local_scope: dict[str, Any] = {}
        exec(code, sandbox_globals, local_scope)

        if "result" not in local_scope:
            raise ValueError("Agent code must set a 'result' variable")

        return local_scope["result"]

    async def execute(
        self,
        agent_id: str,
        code: str,
        input_data: dict,
        timeout: int = 30,
    ) -> dict[str, Any]:
        started_at = datetime.utcnow()
        invocation_id = hashlib.sha256(
            f"{agent_id}{started_at.isoformat()}".encode("utf-8")
        ).hexdigest()[:16]
        trace_id = uuid.uuid4().hex

        start_time = time.perf_counter()
        status = "SUCCESS"
        output = None
        error = None
        error_type: Optional[str] = None

        sandbox_globals = self._prepare_globals(input_data)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        try:
            output = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._sync_execute,
                    code,
                    sandbox_globals,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            status = "TIMEOUT"
            error = f"Execution exceeded timeout of {timeout} seconds"
            error_type = "TimeoutError"
            logger.warning("Agent %s execution timed out", agent_id)
        except Exception as exc:
            status = "ERROR"
            error = str(exc)
            error_type = exc.__class__.__name__
            logger.error("Agent %s execution error: %s", agent_id, exc)

        execution_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        ended_at = datetime.utcnow()
        cost_cents = max(1, ceil(execution_time_ms / 1000.0))

        step = {
            "step_id": f"{invocation_id}-step-1",
            "parent_step_id": None,
            "name": "agent.execute",
            "kind": "system",
            "start_ts": started_at,
            "end_ts": ended_at,
            "latency_ms": execution_time_ms,
            "status": status,
            "model_provider": None,
            "tokens_in": None,
            "tokens_out": None,
            "cost_cents": cost_cents,
            "error_type": error_type,
            "error_message": error,
            "input_excerpt": self._excerpt(input_data),
            "output_excerpt": self._excerpt(output) if output is not None else None,
        }

        trace = {
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "agent_id": agent_id,
            "start_ts": started_at,
            "end_ts": ended_at,
            "status": status,
            "execution_time_ms": execution_time_ms,
            "cost_cents": cost_cents,
            "error_message": error,
            "steps": [step],
        }

        return {
            "invocation_id": invocation_id,
            "agent_id": agent_id,
            "status": status,
            "output": output,
            "error": error,
            "execution_time_ms": execution_time_ms,
            "cost_cents": cost_cents,
            "invoked_at": started_at,
            "trace": trace,
        }

    @staticmethod
    def _excerpt(payload: Any, limit: int = 256) -> Optional[str]:
        if payload is None:
            return None
        if isinstance(payload, str):
            text = payload
        else:
            try:
                text = repr(payload)
            except Exception:  # pragma: no cover - defensive
                text = str(payload)
        return text if len(text) <= limit else f"{text[: limit - 3]}..."
