"""AgentOS Client for external agents"""

import logging
from typing import Any, Dict, Optional

import httpx

from .models import TraceData
from .telemetry import TelemetryBuilder

logger = logging.getLogger(__name__)


class AgentOSClient:
    """
    Client for external agents (Model B) to interact with AgentOS platform.
    
    Features:
    - Register agent with platform
    - Emit ATP v0 telemetry
    - Send step-level traces
    - Automatic telemetry quality = 'verified'
    
    Example:
        ```python
        client = AgentOSClient(
            base_url="https://agentos.example.com",
            api_key="your-agent-token"
        )
        
        # Start invocation with telemetry
        with client.trace(
            org_id="org-123",
            project_id="proj-456",
            agent_id="agent-789"
        ) as telemetry:
            # Add steps
            with telemetry.step("fetch_data", StepKind.TOOL) as step:
                result = fetch_data()
                step.set_input("query params").set_output(str(result))
            
            # Telemetry automatically sent on context exit
        ```
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Lazy HTTP client initialization"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "AgentOS-Python-SDK/0.1.0",
                },
            )
        return self._client

    def close(self):
        """Close HTTP client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def register_agent(
        self,
        name: str,
        endpoint: str,
        owner_id: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register external agent (Model B) with platform.
        
        Returns agent registration details including agent_id.
        """
        payload = {
            "name": name,
            "model_type": "B",
            "endpoint": endpoint,
            "owner_id": owner_id,
            "description": description or "",
            "metadata": metadata or {},
        }
        
        response = self.client.post("/v1/agents/modelB", json=payload)
        response.raise_for_status()
        return response.json()

    def send_telemetry(self, trace: TraceData) -> Dict[str, Any]:
        """
        Send ATP v0 telemetry to AgentOS platform.
        
        Marks agent with 'verified' telemetry quality badge.
        """
        payload = {
            "trace": trace.to_dict(),
            "telemetry_quality": "verified",
        }
        
        try:
            response = self.client.post(
                "/v1/telemetry/ingest",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send telemetry: {e}")
            return {"status": "error", "message": str(e)}

    def trace(
        self,
        org_id: str,
        project_id: str,
        agent_id: str,
        version_id: str = "v1",
        auto_send: bool = True,
    ) -> "TelemetryContext":
        """
        Create telemetry context for an invocation.
        
        Args:
            org_id: Organization identifier
            project_id: Project identifier
            agent_id: Agent identifier
            version_id: Version identifier
            auto_send: Automatically send telemetry on context exit
            
        Returns:
            TelemetryContext that auto-sends on exit
        """
        return TelemetryContext(
            client=self,
            org_id=org_id,
            project_id=project_id,
            agent_id=agent_id,
            version_id=version_id,
            auto_send=auto_send,
        )

    def health_check(self) -> bool:
        """Check if AgentOS platform is reachable"""
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class TelemetryContext:
    """Context manager that auto-sends telemetry on exit"""

    def __init__(
        self,
        client: AgentOSClient,
        org_id: str,
        project_id: str,
        agent_id: str,
        version_id: str,
        auto_send: bool,
    ):
        self.client = client
        self.builder = TelemetryBuilder(
            org_id=org_id,
            project_id=project_id,
            agent_id=agent_id,
            version_id=version_id,
        )
        self.auto_send = auto_send
        self.trace_data: Optional[TraceData] = None

    def __enter__(self) -> TelemetryBuilder:
        return self.builder

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.builder.fail(str(exc_val))
        
        self.trace_data = self.builder.finish()
        
        if self.auto_send:
            try:
                self.client.send_telemetry(self.trace_data)
            except Exception as e:
                logger.error(f"Failed to auto-send telemetry: {e}")
        
        return False

    def send_now(self):
        """Manually send telemetry before context exit"""
        if self.trace_data:
            self.client.send_telemetry(self.trace_data)
