import asyncio
import builtins
import hashlib
import logging
import time
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
        invocation_id = hashlib.sha256(
            f"{agent_id}{datetime.utcnow().isoformat()}".encode("utf-8")
        ).hexdigest()[:16]

        start_time = time.perf_counter()
        status = "SUCCESS"
        output = None
        error = None

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
            logger.warning("Agent %s execution timed out", agent_id)
        except Exception as exc:
            status = "ERROR"
            error = str(exc)
            logger.error("Agent %s execution error: %s", agent_id, exc)

        execution_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        cost_cents = max(1, ceil(execution_time_ms / 1000.0))

        return {
            "invocation_id": invocation_id,
            "agent_id": agent_id,
            "status": status,
            "output": output,
            "error": error,
            "execution_time_ms": execution_time_ms,
            "cost_cents": cost_cents,
            "invoked_at": datetime.utcnow(),
        }
