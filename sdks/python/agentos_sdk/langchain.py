import uuid
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from .client import AgentOSClient
from .instrumentation import SpanRecorder, SpanData, Span, _current_recorder

class AgentOSCallbackHandler(BaseCallbackHandler):
    """
    LangChain CallbackHandler for AgentOS.
    
    Automatically captures traces, spans, and costs from LangChain executions.
    """

    def __init__(self, client: AgentOSClient):
        self.client = client
        self.run_map: Dict[UUID, Span] = {}
        self.root_run_id: Optional[UUID] = None
        self.recorder: Optional[SpanRecorder] = None
        self.owns_recorder = False

    def _get_or_create_recorder(self, run_id: UUID) -> SpanRecorder:
        """Get active recorder or create one if this is a new root trace"""
        # Check if there's already an active recorder (from context manager)
        if _current_recorder.recorder:
            return _current_recorder.recorder
        
        # If we already created one for this callback instance
        if self.recorder:
            return self.recorder

        # Create new recorder for this root run
        self.owns_recorder = True
        trace_id = str(uuid.uuid4())
        invocation_id = str(run_id)
        
        self.recorder = SpanRecorder(
            trace_id=trace_id,
            invocation_id=invocation_id,
            agent_id=self.client.agent_id,
            version_id=self.client.version_id
        )
        return self.recorder

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        recorder = self._get_or_create_recorder(run_id)
        
        parent_span_id = None
        if parent_run_id:
            parent_span = self.run_map.get(parent_run_id)
            if parent_span:
                parent_span_id = parent_span.data.span_id
        
        name = serialized.get("name", "chain")
        span_id = str(uuid.uuid4())
        
        span_data = SpanData(
            span_id=span_id,
            trace_id=recorder.trace_id,
            parent_span_id=parent_span_id,
            invocation_id=recorder.invocation_id,
            agent_id=self.client.agent_id,
            version_id=self.client.version_id,
            name=name,
            kind="chain",
            start_ts=self._now()
        )
        
        span = Span(span_data, recorder)
        span.set_io(inputs)
        self.run_map[run_id] = span

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        span = self.run_map.get(run_id)
        if span:
            span.set_io(None, outputs)
            span.finish("success")
            self._cleanup_run(run_id)

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        span = self.run_map.get(run_id)
        if span:
            span.set_error(error)
            span.finish("error")
            self._cleanup_run(run_id)

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        recorder = self._get_or_create_recorder(run_id)
        
        parent_span_id = None
        if parent_run_id:
            parent_span = self.run_map.get(parent_run_id)
            if parent_span:
                parent_span_id = parent_span.data.span_id

        name = "llm_call"
        invocation_params = kwargs.get("invocation_params", {})
        model_name = invocation_params.get("model_name") or invocation_params.get("model")
        
        span_id = str(uuid.uuid4())
        span_data = SpanData(
            span_id=span_id,
            trace_id=recorder.trace_id,
            parent_span_id=parent_span_id,
            invocation_id=recorder.invocation_id,
            agent_id=self.client.agent_id,
            version_id=self.client.version_id,
            name=name,
            kind="llm",
            start_ts=self._now()
        )
        
        span = Span(span_data, recorder)
        span.set_model("unknown", model_name or "unknown", invocation_params)
        # For simplicity, just taking the first prompt if multiple
        span.set_io(prompts[0] if prompts else "")
        
        self.run_map[run_id] = span

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        span = self.run_map.get(run_id)
        if span:
            # Aggregate token usage
            token_usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
            tokens_in = token_usage.get("prompt_tokens")
            tokens_out = token_usage.get("completion_tokens")
            
            # Get generation text
            generations = response.generations[0]
            text = generations[0].text if generations else ""
            
            span.set_io(None, text, tokens_in, tokens_out)
            
            # Simple cost estimation (mock)
            if tokens_in and tokens_out:
                # Assume generic $0.01 per 1k tokens for demo
                cost = ((tokens_in + tokens_out) / 1000) * 0.01 * 100 # cents
                span.set_cost(int(cost))

            span.finish("success")
            self._cleanup_run(run_id)

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        span = self.run_map.get(run_id)
        if span:
            span.set_error(error)
            span.finish("error")
            self._cleanup_run(run_id)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        recorder = self._get_or_create_recorder(run_id)
        
        parent_span_id = None
        if parent_run_id:
            parent_span = self.run_map.get(parent_run_id)
            if parent_span:
                parent_span_id = parent_span.data.span_id

        name = serialized.get("name", "tool")
        
        span_id = str(uuid.uuid4())
        span_data = SpanData(
            span_id=span_id,
            trace_id=recorder.trace_id,
            parent_span_id=parent_span_id,
            invocation_id=recorder.invocation_id,
            agent_id=self.client.agent_id,
            version_id=self.client.version_id,
            name=name,
            kind="tool",
            start_ts=self._now()
        )
        
        span = Span(span_data, recorder)
        span.set_tool(str(run_id), name, args=input_str)
        self.run_map[run_id] = span

    def on_tool_end(self, output: str, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        span = self.run_map.get(run_id)
        if span:
            span.set_tool(str(run_id), span.data.tool_name, result=output)
            span.finish("success")
            self._cleanup_run(run_id)

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        span = self.run_map.get(run_id)
        if span:
            span.set_error(error)
            span.finish("error")
            self._cleanup_run(run_id)

    def _cleanup_run(self, run_id: UUID):
        """Remove run from map and flush if it's the root and we own the recorder"""
        if run_id in self.run_map:
            del self.run_map[run_id]
        
        # If we own the recorder and map is empty (or close to it), we might want to flush
        # But simpler: flush when the recorder was created by us and we are done?
        # Actually, with LangChain, we don't easily know when the *entire* trace is done unless we track the root run ID.
        # For now, we'll rely on explicit flush or auto-flush in client if we used the context manager.
        # If we created the recorder, we should flush it.
        
        if self.owns_recorder and self.recorder:
             # In a real implementation, we'd check if this was the root run ending
             pass

    def flush(self):
        """Explicitly flush spans"""
        if self.recorder:
            self.client.flush_spans(self.recorder)

    @staticmethod
    def _now():
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
