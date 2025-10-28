"""
Integration tests for end-to-end API flows
Tests the complete user journey from agent creation to invocation
"""

import pytest
import httpx
from datetime import datetime


pytestmark = pytest.mark.skip(reason="Requires running runtime service and backing Postgres database")

BASE_URL = "http://localhost:8000"
TEST_TOKEN = "test_user_token"


@pytest.fixture
async def client():
    """HTTP client for testing"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authentication headers"""
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


class TestModelAFlow:
    """Test complete Model A (code upload) flow"""
    
    @pytest.mark.asyncio
    async def test_create_model_a_agent(self, client, auth_headers):
        """Test creating Model A agent"""
        
        # Step 1: Create agent
        response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={
                "name": "test-langchain-agent",
                "runtime": "python3.11",
                "requirements": ["langchain", "openai"],
                "env": {"OPENAI_API_KEY": "sk-test"},
                "resources": {"cpu": "500m", "mem": "1Gi"}
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "agent_id" in data
        assert "upload_url" in data
        assert "deployment_id" in data
        
        agent_id = data["agent_id"]
        
        # Step 2: Get agent details
        response = await client.get(
            f"/v1/agents/{agent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        agent = response.json()
        
        assert agent["name"] == "test-langchain-agent"
        assert agent["model_type"] == "A"
        assert agent["status"] == "PENDING"
        assert agent["runtime"] == "python3.11"
    
    @pytest.mark.asyncio
    async def test_upload_artifact_and_build(self, client, auth_headers):
        """Test artifact upload and build process"""
        
        # Create agent first
        create_response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={
                "name": "test-build-agent",
                "runtime": "python3.11",
                "requirements": []
            }
        )
        
        agent_id = create_response.json()["agent_id"]
        
        # Upload artifact (stub - in real test, upload actual file)
        files = {"file": ("agent.py", b"result = {'hello': 'world'}", "text/plain")}
        
        response = await client.put(
            f"/v1/agents/{agent_id}/artifact",
            headers=auth_headers,
            files=files,
            data={"checksum": "abc123"}
        )
        
        assert response.status_code == 202
        build_status = response.json()
        
        assert build_status["agent_id"] == agent_id
        assert build_status["status"] == "IN_PROGRESS"
    
    @pytest.mark.asyncio
    async def test_get_build_status(self, client, auth_headers):
        """Test retrieving build status"""
        
        # Create and trigger build
        create_response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={"name": "test-status-agent", "runtime": "python3.11"}
        )
        
        agent_id = create_response.json()["agent_id"]
        
        # Get build status
        response = await client.get(
            f"/v1/agents/{agent_id}/build",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        status = response.json()
        
        assert "status" in status
        assert "logs" in status


class TestModelBFlow:
    """Test complete Model B (registry) flow"""
    
    @pytest.mark.asyncio
    async def test_register_external_agent(self, client, auth_headers):
        """Test registering external agent endpoint"""
        
        response = await client.post(
            "/v1/agents/modelB",
            headers=auth_headers,
            json={
                "name": "external-openai-agent",
                "endpoint_url": "https://api.openai.com/v1/assistants",
                "auth": {
                    "type": "bearer",
                    "value": "sk-test-token"
                },
                "rate_limit": {
                    "rps": 10.0,
                    "burst": 20
                }
            }
        )
        
        assert response.status_code == 201
        agent = response.json()
        
        assert agent["name"] == "external-openai-agent"
        assert agent["model_type"] == "B"
        assert agent["status"] == "RUNNING"
        assert agent["endpoint_url"] == "https://api.openai.com/v1/assistants"
    
    @pytest.mark.asyncio
    async def test_register_mcp_agent(self, client, auth_headers):
        """Test registering MCP agent"""
        
        response = await client.post(
            "/v1/agents/modelB",
            headers=auth_headers,
            json={
                "name": "mcp-filesystem-agent",
                "endpoint_url": "https://mcp.example.com/agent",
                "auth": {
                    "type": "header",
                    "header_name": "X-MCP-Token",
                    "value": "token_123"
                }
            }
        )
        
        assert response.status_code == 201
        agent = response.json()
        
        assert agent["model_type"] == "B"


class TestInvocationFlow:
    """Test agent invocation flows"""
    
    @pytest.mark.asyncio
    async def test_invoke_nonexistent_agent(self, client, auth_headers):
        """Test invoking non-existent agent returns 404"""
        
        response = await client.post(
            "/v1/agents/00000000-0000-0000-0000-000000000000/invoke",
            headers=auth_headers,
            json={"input_data": {"message": "test"}}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invocation_timeout_validation(self, client, auth_headers):
        """Test timeout validation"""
        
        # Create agent first
        create_response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={"name": "timeout-test", "runtime": "python3.11"}
        )
        
        agent_id = create_response.json()["agent_id"]
        
        # Test invalid timeout
        response = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=auth_headers,
            json={
                "input_data": {"test": "data"},
                "timeout": 500  # Exceeds max of 300
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestObservability:
    """Test observability endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_agent_metrics(self, client, auth_headers):
        """Test retrieving agent metrics"""
        
        # Create agent
        create_response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={"name": "metrics-test", "runtime": "python3.11"}
        )
        
        agent_id = create_response.json()["agent_id"]
        
        # Get metrics
        response = await client.get(
            f"/v1/agents/{agent_id}/metrics?range=1d",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        metrics = response.json()
        
        assert "agent_id" in metrics
        assert "total_invocations" in metrics
        assert "avg_execution_time_ms" in metrics
        assert "total_cost_usd" in metrics
    
    @pytest.mark.asyncio
    async def test_get_agent_costs(self, client, auth_headers):
        """Test retrieving cost breakdown"""
        
        # Create agent
        create_response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={"name": "cost-test", "runtime": "python3.11"}
        )
        
        agent_id = create_response.json()["agent_id"]
        
        # Get costs
        response = await client.get(
            f"/v1/agents/{agent_id}/costs?period=monthly",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        costs = response.json()
        
        assert "agent_id" in costs
        assert "total_cost_usd" in costs
        assert "breakdown" in costs
        assert "compute" in costs["breakdown"]


class TestAgentManagement:
    """Test agent CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_list_agents(self, client, auth_headers):
        """Test listing agents"""
        
        response = await client.get(
            "/v1/agents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert "total" in data
        assert isinstance(data["agents"], list)
    
    @pytest.mark.asyncio
    async def test_delete_agent(self, client, auth_headers):
        """Test deleting agent"""
        
        # Create agent
        create_response = await client.post(
            "/v1/agents/modelA",
            headers=auth_headers,
            json={"name": "delete-test", "runtime": "python3.11"}
        )
        
        agent_id = create_response.json()["agent_id"]
        
        # Delete agent
        response = await client.delete(
            f"/v1/agents/{agent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify agent is terminated
        get_response = await client.get(
            f"/v1/agents/{agent_id}",
            headers=auth_headers
        )
        
        if get_response.status_code == 200:
            agent = get_response.json()
            assert agent["status"] == "TERMINATED"


class TestHealthCheck:
    """Test system health endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint (no auth required)"""
        
        response = await client.get("/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "service" in health
        assert "timestamp" in health
        assert "checks" in health


@pytest.mark.asyncio
async def test_complete_user_journey(client, auth_headers):
    """
    Test complete user journey:
    1. Create Model A agent
    2. Upload code
    3. Wait for build
    4. Invoke agent
    5. Check metrics
    6. Delete agent
    """
    
    # Step 1: Create agent
    create_response = await client.post(
        "/v1/agents/modelA",
        headers=auth_headers,
        json={
            "name": "journey-test-agent",
            "runtime": "python3.11",
            "requirements": ["requests"],
            "env": {"API_KEY": "test"}
        }
    )
    
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]
    
    # Step 2: Upload artifact (simplified)
    files = {"file": ("agent.py", b"result = {'status': 'ok'}", "text/plain")}
    upload_response = await client.put(
        f"/v1/agents/{agent_id}/artifact",
        headers=auth_headers,
        files=files
    )
    
    assert upload_response.status_code == 202
    
    # Step 3: Check build status (in real test, poll until SUCCESS)
    build_response = await client.get(
        f"/v1/agents/{agent_id}/build",
        headers=auth_headers
    )
    
    assert build_response.status_code == 200
    
    # Step 4: Get metrics
    metrics_response = await client.get(
        f"/v1/agents/{agent_id}/metrics",
        headers=auth_headers
    )
    
    assert metrics_response.status_code == 200
    
    # Step 5: Delete agent
    delete_response = await client.delete(
        f"/v1/agents/{agent_id}",
        headers=auth_headers
    )
    
    assert delete_response.status_code == 204
