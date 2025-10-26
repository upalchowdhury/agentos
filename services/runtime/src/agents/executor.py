import asyncio
import hashlib
import logging
import time
from datetime import datetime
from math import ceil
from typing import Any

logger = logging.getLogger(__name__)


class AgentExecutor:
    SAFE_BUILTINS = {
        'print': print,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'dict': dict,
        'list': list,
        'tuple': tuple,
        'set': set,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'isinstance': isinstance,
        'type': type,
    }
    
    def _sync_execute(self, code: str, safe_globals: dict[str, Any]) -> Any:
        local_scope: dict[str, Any] = {}
        exec(code, safe_globals, local_scope)
        
        if 'result' not in local_scope:
            raise ValueError("Agent code must set 'result' variable")
        
        return local_scope['result']
    
    async def execute(
        self,
        agent_id: str,
        code: str,
        input_data: dict,
        timeout: int = 30
    ) -> dict[str, Any]:
        invocation_id = hashlib.sha256(
            f"{agent_id}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        start_time = time.time()
        status = "SUCCESS"
        output = None
        error = None
        
        safe_globals = self.SAFE_BUILTINS.copy()
        safe_globals['input_data'] = input_data
        
        try:
            loop = asyncio.get_event_loop()
            output = await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_execute, code, safe_globals),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            status = "TIMEOUT"
            error = f"Execution exceeded timeout of {timeout} seconds"
            logger.warning(f"Agent {agent_id} execution timed out")
        except Exception as e:
            status = "ERROR"
            error = str(e)
            logger.error(f"Agent {agent_id} execution error: {e}")
        
        end_time = time.time()
        execution_time_ms = int((end_time - start_time) * 1000)
        
        cost_cents = ceil(execution_time_ms / 1000.0) * 1
        
        return {
            'invocation_id': invocation_id,
            'agent_id': agent_id,
            'status': status,
            'output': output,
            'error': error,
            'execution_time_ms': execution_time_ms,
            'cost_cents': cost_cents,
            'invoked_at': datetime.utcnow()
        }
