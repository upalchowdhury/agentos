from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class AgentStatus(str, Enum):
    DEPLOYING = "DEPLOYING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class InvocationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class DeploymentRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    code: str = Field(..., min_length=10, max_length=50000, description="Agent code to deploy")
    requirements: list[str] = Field(default_factory=list, max_length=50, description="Python package requirements")
    environment: Optional[dict[str, str]] = Field(default=None, description="Environment variables")
    max_memory: str = Field(default="512m", description="Maximum memory limit")
    max_cpu: str = Field(default="0.5", description="Maximum CPU limit")
    
    @field_validator('code')
    @classmethod
    def validate_code_length(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Code must be at least 10 characters")
        if len(v) > 50000:
            raise ValueError("Code must not exceed 50000 characters")
        return v
    
    @field_validator('requirements')
    @classmethod
    def validate_requirements(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("Requirements list must not exceed 50 items")
        return v


class InvocationRequest(BaseModel):
    agent_id: str = Field(..., description="Agent to invoke")
    input_data: dict = Field(..., description="Input data for the agent")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v < 1 or v > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v


class DeploymentResponse(BaseModel):
    deployment_id: str = Field(..., description="Unique deployment identifier")
    agent_id: str = Field(..., description="Agent identifier")
    status: AgentStatus = Field(..., description="Current deployment status")
    container_id: Optional[str] = Field(None, description="Container ID if containerized")
    endpoint: Optional[str] = Field(None, description="Agent endpoint URL")
    deployed_at: datetime = Field(..., description="Deployment timestamp")
    message: Optional[str] = Field(None, description="Additional deployment information")


class InvocationResponse(BaseModel):
    invocation_id: str = Field(..., description="Unique invocation identifier")
    agent_id: str = Field(..., description="Agent identifier")
    status: InvocationStatus = Field(..., description="Invocation status")
    output: Optional[Any] = Field(None, description="Agent output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    cost_cents: int = Field(..., description="Estimated cost in cents")
    invoked_at: datetime = Field(..., description="Invocation timestamp")


class AgentStatusResponse(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    status: AgentStatus = Field(..., description="Current agent status")
    container_id: Optional[str] = Field(None, description="Container ID if containerized")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")
    last_invocation: Optional[datetime] = Field(None, description="Last invocation timestamp")
    invocation_count: int = Field(default=0, description="Total invocation count")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_mb: Optional[int] = Field(None, description="Memory usage in MB")
    uptime_seconds: Optional[int] = Field(None, description="Uptime in seconds")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(..., description="Health check timestamp")
    checks: dict[str, bool] = Field(..., description="Individual health checks")
