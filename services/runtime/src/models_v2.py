"""
Enhanced models for Agent Economy OS
Supports Model A (code upload) and Model B (registry) patterns
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ConfigDict


class ModelType(str, Enum):
    """Agent deployment model"""
    A = "A"  # Code upload - runs on our infrastructure
    B = "B"  # Registry - proxies to external endpoint


class AgentStatus(str, Enum):
    """Agent lifecycle status"""
    PENDING = "PENDING"  # Awaiting artifact upload
    BUILDING = "BUILDING"  # Image building
    DEPLOYING = "DEPLOYING"  # Kubernetes deployment in progress
    RUNNING = "RUNNING"  # Active and ready
    STOPPED = "STOPPED"  # Stopped by user
    FAILED = "FAILED"  # Build or deployment failed
    TERMINATED = "TERMINATED"  # Permanently removed


class InvocationStatus(str, Enum):
    """Single invocation result"""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    DENIED = "DENIED"  # RBAC/OPA denied


class Runtime(str, Enum):
    """Supported runtimes for Model A"""
    PYTHON_3_11 = "python3.11"
    PYTHON_3_10 = "python3.10"
    # NODEJS_18 = "nodejs18"  # Phase 2


class AuthScheme(str, Enum):
    """Authentication schemes for Model B"""
    BEARER = "bearer"
    HEADER = "header"
    NONE = "none"


class AlertsConfig(BaseModel):
    """Alert thresholds per agent"""

    error_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Error rate threshold (0-1).",
    )
    latency_ms: Optional[int] = Field(
        default=None,
        ge=1,
        description="Latency threshold in milliseconds.",
    )
    sample_window: Optional[int] = Field(
        default=None,
        ge=1,
        le=200,
        description="Number of invocations considered when evaluating alerts.",
    )


# ============================================================================
# MODEL A - CODE UPLOAD
# ============================================================================

class CreateModelARequest(BaseModel):
    """Create agent via code upload (Model A)"""
    name: str = Field(..., min_length=3, max_length=100, description="Agent name")
    runtime: Runtime = Field(default=Runtime.PYTHON_3_11, description="Runtime environment")
    requirements: list[str] = Field(default_factory=list, max_length=50, description="Package dependencies")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables (masked)")
    resources: dict[str, str] = Field(
        default_factory=lambda: {"cpu": "500m", "mem": "512Mi"},
        description="Resource limits: {cpu: '500m', mem: '1Gi'}"
    )
    concurrency_limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent invocations allowed for this agent"
    )
    alerts: Optional[AlertsConfig] = Field(default=None, description="Optional alert thresholds")
    
    @field_validator('requirements')
    @classmethod
    def validate_requirements(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("Requirements must not exceed 50 packages")
        for req in v:
            if len(req) > 200:
                raise ValueError("Package requirement too long")
        return v
    
    @field_validator('resources')
    @classmethod
    def validate_resources(cls, v: dict[str, str]) -> dict[str, str]:
        # Validate CPU format
        cpu = v.get('cpu', '500m')
        if not (cpu.endswith('m') or cpu.replace('.', '').isdigit()):
            raise ValueError("Invalid CPU format (use '500m' or '0.5')")
        # Validate memory format
        mem = v.get('mem', '512Mi')
        if not any(mem.endswith(unit) for unit in ['Mi', 'Gi', 'M', 'G']):
            raise ValueError("Invalid memory format (use '512Mi' or '1Gi')")
        return {
            'cpu': cpu,
            'mem': mem,
        }


class UploadArtifactResponse(BaseModel):
    """Response after creating Model A agent"""
    agent_id: str = Field(..., description="Unique agent identifier")
    upload_url: str = Field(..., description="Signed URL for uploading code artifact")
    deployment_id: str = Field(..., description="Deployment tracking ID")
    expires_at: datetime = Field(..., description="Upload URL expiration")


# ============================================================================
# MODEL B - REGISTRY
# ============================================================================

class AuthConfig(BaseModel):
    """Authentication configuration for Model B"""
    type: AuthScheme = Field(..., description="Auth scheme")
    value: Optional[str] = Field(None, description="Token value for bearer auth")
    header_name: Optional[str] = Field(None, description="Header name for header auth")

    @model_validator(mode="after")
    def validate_combination(self) -> "AuthConfig":
        if self.type == AuthScheme.BEARER and not self.value:
            raise ValueError("Bearer auth requires 'value'")
        if self.type == AuthScheme.HEADER:
            if not self.header_name:
                raise ValueError("Header auth requires 'header_name'")
            if not self.value:
                raise ValueError("Header auth requires 'value'")
        return self


class RateLimitConfig(BaseModel):
    """Rate limiting for Model B agents"""
    rps: float = Field(default=10.0, gt=0, description="Requests per second")
    burst: int = Field(default=20, gt=0, description="Burst capacity")


class AlertsConfig(BaseModel):
    """Alert thresholds per agent"""

    error_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Error rate threshold (0-1).",
    )
    latency_ms: Optional[int] = Field(
        default=None,
        ge=1,
        description="Latency threshold in milliseconds.",
    )
    sample_window: Optional[int] = Field(
        default=None,
        ge=1,
        le=200,
        description="Number of invocations considered when evaluating alerts.",
    )


class CreateModelBRequest(BaseModel):
    """Register external agent endpoint (Model B)"""
    name: str = Field(..., min_length=3, max_length=100, description="Agent name")
    endpoint_url: HttpUrl = Field(..., description="External agent HTTPS endpoint")
    auth: AuthConfig = Field(..., description="Authentication configuration")
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig, description="Rate limiting")
    health_check_path: Optional[str] = Field(default="/health", description="Health check endpoint")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Request timeout")
    alerts: Optional[AlertsConfig] = Field(default=None, description="Optional alert thresholds")


# ============================================================================
# UNIFIED RESPONSES
# ============================================================================

class AgentResponse(BaseModel):
    """Unified agent representation"""
    model_config = ConfigDict(protected_namespaces=())
    agent_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Agent name")
    owner_id: str = Field(..., description="Owner user/team ID")
    model_type: ModelType = Field(..., description="Deployment model (A or B)")
    status: AgentStatus = Field(..., description="Current status")
    telemetry_quality: Optional[str] = Field(None, description="Telemetry fidelity badge (verified|partial)")
    
    # Model A specific
    runtime: Optional[Runtime] = Field(None, description="Runtime for Model A")
    image_ref: Optional[str] = Field(None, description="Container image reference")
    
    # Model B specific
    endpoint_url: Optional[str] = Field(None, description="External endpoint for Model B")
    health_status: Optional[str] = Field(None, description="Last health check result")
    
    # Common fields
    created_at: datetime = Field(..., description="Creation timestamp")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")
    invocation_count: int = Field(default=0, description="Total invocations")
    cost_to_date: float = Field(default=0.0, description="Accumulated cost in USD")


class ObservabilityAgentSummary(BaseModel):
    """Aggregated metrics for observability dashboards"""

    agent_id: str
    name: str
    model_type: str = Field(..., description="Model type (A or B)")
    status: str = Field(..., description="Agent status")
    telemetry_quality: str
    total_invocations: int
    success_rate: float
    error_rate: float
    p95_latency_ms: Optional[float]
    cost_usd: float
    denied_invocations: int
    policy_alerts_count: int
    time_range_start: datetime
    time_range_end: datetime


class ObservabilityTraceStep(BaseModel):
    step_id: str
    parent_step_id: Optional[str]
    name: str
    kind: str
    status: str
    start_ts: Optional[datetime]
    end_ts: Optional[datetime]
    latency_ms: Optional[int]
    error_type: Optional[str]
    error_message: Optional[str]
    input_excerpt: Optional[str]
    output_excerpt: Optional[str]


class ObservabilityTrace(BaseModel):
    trace_id: str
    invocation_id: str
    agent_id: str
    agent_name: str
    telemetry_quality: str
    status: str
    start_ts: Optional[datetime]
    end_ts: Optional[datetime]
    execution_time_ms: Optional[int]
    cost_usd: float
    requester_id: Optional[str]
    caller_agent_id: Optional[str]
    actor: Optional[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    policy_alerts: Optional[Dict[str, Any]]
    steps: List[ObservabilityTraceStep]
    logs: List[Dict[str, Any]]


class InvocationRequest(BaseModel):
    """Invoke agent (works for both Model A and B)"""
    input_data: dict[str, Any] = Field(..., description="Input payload")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout")
    caller_agent_id: Optional[str] = Field(None, description="For A2A invocations")


class InvocationResult(BaseModel):
    """Standardized invocation response envelope"""
    invocation_id: str = Field(..., description="Unique invocation ID")
    agent_id: str = Field(..., description="Agent that processed the request")
    status: InvocationStatus = Field(..., description="Execution status")
    
    # Output data
    result: Optional[dict[str, Any]] = Field(None, description="Agent output")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Metrics
    execution_time_ms: int = Field(..., description="Execution duration")
    cost: float = Field(..., description="Cost in USD")
    
    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional info")
    invoked_at: datetime = Field(..., description="Invocation timestamp")


class AgentMetricsResponse(BaseModel):
    """Agent performance metrics"""
    agent_id: str
    period_start: datetime
    period_end: datetime
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    denied_invocations: int
    avg_execution_time_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_cost_usd: float
    error_rate: float


class AgentLogsRequest(BaseModel):
    """Query agent logs"""
    range: str = Field(default="1h", description="Time range: 1h, 1d, 7d")
    level: Optional[str] = Field(None, description="Log level filter: error, warn, info")
    limit: int = Field(default=100, ge=1, le=1000, description="Max log entries")


class AgentCostResponse(BaseModel):
    """Agent cost breakdown"""
    agent_id: str
    period: str = Field(..., description="Billing period: daily, monthly")
    total_cost_usd: float
    invocations: int
    cost_per_invocation_usd: float
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Cost by category: compute, llm_api, storage"
    )


# ============================================================================
# ARTIFACT UPLOAD (Model A)
# ============================================================================

class UploadArtifactRequest(BaseModel):
    """Metadata for artifact upload"""
    agent_id: str
    artifact_type: str = Field(default="zip", description="zip or single_file")
    checksum: Optional[str] = Field(None, description="SHA256 checksum")


# ============================================================================
# BUILD STATUS (Model A)
# ============================================================================

class BuildStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class BuildStatusResponse(BaseModel):
    """Build job status"""
    agent_id: str
    deployment_id: str
    status: BuildStatus
    logs: list[str] = Field(default_factory=list, description="Build log lines")
    image_ref: Optional[str] = Field(None, description="Built image reference")
    error: Optional[str] = Field(None, description="Build error if failed")
    started_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================================
# HEALTH & STATUS
# ============================================================================

class HealthResponse(BaseModel):
    """Service health check"""
    status: str = Field(..., description="healthy, degraded, unhealthy")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict[str, bool] = Field(default_factory=dict, description="Component health")
    uptime_seconds: Optional[int] = None


class DeploymentRequest(BaseModel):
    """Legacy model - kept for backwards compatibility"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    code: str = Field(..., min_length=10, max_length=50000, description="Agent code to deploy")
    requirements: list[str] = Field(default_factory=list, max_length=50)
    environment: Optional[dict[str, str]] = Field(default=None)
    max_memory: str = Field(default="512m")
    max_cpu: str = Field(default="0.5")


class DeploymentResponse(BaseModel):
    """Legacy model - kept for backwards compatibility"""
    deployment_id: str
    agent_id: str
    status: AgentStatus
    container_id: Optional[str] = None
    endpoint: Optional[str] = None
    deployed_at: datetime
    message: Optional[str] = None
