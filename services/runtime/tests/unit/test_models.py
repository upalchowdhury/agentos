"""
Unit tests for models_v2
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from services.runtime.src.models_v2 import (
    ModelType,
    AgentStatus,
    Runtime,
    CreateModelARequest,
    CreateModelBRequest,
    AuthConfig,
    AuthScheme,
    RateLimitConfig,
    InvocationRequest,
)


class TestCreateModelARequest:
    """Test Model A agent creation request"""
    
    def test_valid_request(self):
        """Valid Model A request should pass validation"""
        request = CreateModelARequest(
            name="test-agent",
            runtime=Runtime.PYTHON_3_11,
            requirements=["langchain", "openai"],
            env={"OPENAI_API_KEY": "sk-test"},
            resources={"cpu": "500m", "mem": "1Gi"}
        )
        
        assert request.name == "test-agent"
        assert request.runtime == Runtime.PYTHON_3_11
        assert len(request.requirements) == 2
    
    def test_name_too_short(self):
        """Name must be at least 3 characters"""
        with pytest.raises(ValidationError):
            CreateModelARequest(
                name="ab",  # Too short
                runtime=Runtime.PYTHON_3_11
            )
    
    def test_too_many_requirements(self):
        """Should reject more than 50 requirements"""
        with pytest.raises(ValidationError):
            CreateModelARequest(
                name="test-agent",
                runtime=Runtime.PYTHON_3_11,
                requirements=["pkg" + str(i) for i in range(51)]  # 51 packages
            )
    
    def test_default_resources(self):
        """Should provide default resources"""
        request = CreateModelARequest(
            name="test-agent",
            runtime=Runtime.PYTHON_3_11
        )
        
        assert request.resources == {"cpu": "500m", "mem": "512Mi"}
    
    def test_invalid_cpu_format(self):
        """Should reject invalid CPU format"""
        with pytest.raises(ValidationError):
            CreateModelARequest(
                name="test-agent",
                runtime=Runtime.PYTHON_3_11,
                resources={"cpu": "invalid", "mem": "1Gi"}
            )
    
    def test_invalid_mem_format(self):
        """Should reject invalid memory format"""
        with pytest.raises(ValidationError):
            CreateModelARequest(
                name="test-agent",
                runtime=Runtime.PYTHON_3_11,
                resources={"cpu": "500m", "mem": "1TB"}  # TB not supported
            )


class TestCreateModelBRequest:
    """Test Model B agent registration request"""
    
    def test_valid_bearer_auth(self):
        """Valid Model B with bearer auth should pass"""
        request = CreateModelBRequest(
            name="external-agent",
            endpoint_url="https://api.example.com/agent",
            auth=AuthConfig(type=AuthScheme.BEARER, value="token_123")
        )
        
        assert request.name == "external-agent"
        assert str(request.endpoint_url) == "https://api.example.com/agent"
        assert request.auth.type == AuthScheme.BEARER
    
    def test_valid_header_auth(self):
        """Valid Model B with custom header auth should pass"""
        request = CreateModelBRequest(
            name="external-agent",
            endpoint_url="https://api.example.com/agent",
            auth=AuthConfig(type=AuthScheme.HEADER, header_name="X-API-Key", value="key_123")
        )
        
        assert request.auth.type == AuthScheme.HEADER
        assert request.auth.header_name == "X-API-Key"
    
    def test_bearer_auth_requires_value(self):
        """Bearer auth must have value"""
        with pytest.raises(ValidationError):
            CreateModelBRequest(
                name="external-agent",
                endpoint_url="https://api.example.com/agent",
                auth=AuthConfig(type=AuthScheme.BEARER)  # Missing value
            )
    
    def test_header_auth_requires_header_name(self):
        """Header auth must have header_name"""
        with pytest.raises(ValidationError):
            CreateModelBRequest(
                name="external-agent",
                endpoint_url="https://api.example.com/agent",
                auth=AuthConfig(type=AuthScheme.HEADER, value="token")  # Missing header_name
            )
    
    def test_default_rate_limit(self):
        """Should provide default rate limit"""
        request = CreateModelBRequest(
            name="external-agent",
            endpoint_url="https://api.example.com/agent",
            auth=AuthConfig(type=AuthScheme.NONE)
        )
        
        assert request.rate_limit.rps == 10.0
        assert request.rate_limit.burst == 20
    
    def test_custom_rate_limit(self):
        """Should accept custom rate limit"""
        request = CreateModelBRequest(
            name="external-agent",
            endpoint_url="https://api.example.com/agent",
            auth=AuthConfig(type=AuthScheme.NONE),
            rate_limit=RateLimitConfig(rps=100.0, burst=200)
        )
        
        assert request.rate_limit.rps == 100.0
        assert request.rate_limit.burst == 200
    
    def test_invalid_url(self):
        """Should reject invalid URLs"""
        with pytest.raises(ValidationError):
            CreateModelBRequest(
                name="external-agent",
                endpoint_url="not-a-url",  # Invalid URL
                auth=AuthConfig(type=AuthScheme.NONE)
            )


class TestInvocationRequest:
    """Test invocation request"""
    
    def test_valid_request(self):
        """Valid invocation request should pass"""
        request = InvocationRequest(
            input_data={"message": "Hello"},
            timeout=30
        )
        
        assert request.input_data == {"message": "Hello"}
        assert request.timeout == 30
    
    def test_default_timeout(self):
        """Should provide default timeout"""
        request = InvocationRequest(input_data={})
        assert request.timeout == 30
    
    def test_timeout_bounds(self):
        """Timeout must be between 1 and 300 seconds"""
        with pytest.raises(ValidationError):
            InvocationRequest(input_data={}, timeout=0)
        
        with pytest.raises(ValidationError):
            InvocationRequest(input_data={}, timeout=301)
    
    def test_a2a_invocation(self):
        """Should accept caller_agent_id for A2A"""
        request = InvocationRequest(
            input_data={"task": "process"},
            caller_agent_id="agent-a-uuid"
        )
        
        assert request.caller_agent_id == "agent-a-uuid"
