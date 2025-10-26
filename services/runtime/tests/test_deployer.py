import pytest
from services.runtime.src.agents.deployer import AgentDeployer


def test_deployer_import():
    """Test that deployer module can be imported."""
    deployer = AgentDeployer()
    assert deployer is not None
    assert deployer.docker_client is None


@pytest.mark.asyncio
async def test_deploy_container_not_implemented():
    """Test that deploy_container raises NotImplementedError."""
    deployer = AgentDeployer()
    
    with pytest.raises(NotImplementedError):
        await deployer.deploy_container(
            agent_id="test-agent",
            code="result = 42",
            requirements=[],
            resource_limits={"max_memory": "512m", "max_cpu": "0.5"}
        )


@pytest.mark.asyncio
async def test_stop_container_not_implemented():
    """Test that stop_container raises NotImplementedError."""
    deployer = AgentDeployer()
    
    with pytest.raises(NotImplementedError):
        await deployer.stop_container(container_id="test-container-id")
