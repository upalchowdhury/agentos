import pytest
from services.runtime.src.agents.executor import AgentExecutor


@pytest.mark.asyncio
async def test_simple_execution():
    executor = AgentExecutor()
    code = """
result = input_data['x'] + input_data['y']
"""
    result = await executor.execute(
        agent_id="test-agent",
        code=code,
        input_data={'x': 10, 'y': 20},
        timeout=5
    )
    
    assert result['status'] == 'SUCCESS'
    assert result['output'] == 30
    assert result['error'] is None
    assert result['agent_id'] == 'test-agent'
    assert result['execution_time_ms'] > 0
    assert result['cost_cents'] >= 1
    trace = result['trace']
    assert trace['status'] == 'SUCCESS'
    assert len(trace['steps']) == 1
    assert trace['steps'][0]['status'] == 'SUCCESS'


@pytest.mark.asyncio
async def test_string_operations():
    executor = AgentExecutor()
    code = """
message = input_data['text']
result = message.upper() + '!'
"""
    result = await executor.execute(
        agent_id="string-agent",
        code=code,
        input_data={'text': 'hello world'},
        timeout=5
    )
    
    assert result['status'] == 'SUCCESS'
    assert result['output'] == 'HELLO WORLD!'
    assert result['error'] is None
    assert result['trace']['status'] == 'SUCCESS'


@pytest.mark.asyncio
async def test_timeout():
    executor = AgentExecutor()
    code = """
import time
time.sleep(10)
result = 'done'
"""
    result = await executor.execute(
        agent_id="slow-agent",
        code=code,
        input_data={},
        timeout=1
    )
    
    assert result['status'] == 'TIMEOUT'
    assert result['output'] is None
    assert 'timeout' in result['error'].lower()
    trace = result['trace']
    assert trace['status'] == 'TIMEOUT'
    assert trace['steps'][0]['status'] == 'TIMEOUT'


@pytest.mark.asyncio
async def test_error_handling():
    executor = AgentExecutor()
    code = """
result = 1 / 0
"""
    result = await executor.execute(
        agent_id="error-agent",
        code=code,
        input_data={},
        timeout=5
    )
    
    assert result['status'] == 'ERROR'
    assert result['output'] is None
    assert 'division' in result['error'].lower() or 'zero' in result['error'].lower()
    trace = result['trace']
    assert trace['status'] == 'ERROR'
    assert trace['steps'][0]['status'] == 'ERROR'


@pytest.mark.asyncio
async def test_safe_environment():
    executor = AgentExecutor()
    code = """
import os
result = os.listdir('/')
"""
    result = await executor.execute(
        agent_id="unsafe-agent",
        code=code,
        input_data={},
        timeout=5
    )
    
    assert result['status'] == 'ERROR'
    assert result['output'] is None
    assert result['error'] is not None
    assert result['trace']['status'] == 'ERROR'


@pytest.mark.asyncio
async def test_cost_estimation():
    executor = AgentExecutor()
    
    quick_code = """
result = input_data['x'] * 2
"""
    quick_result = await executor.execute(
        agent_id="quick-agent",
        code=quick_code,
        input_data={'x': 5},
        timeout=5
    )
    
    assert quick_result['cost_cents'] >= 1
    assert quick_result['execution_time_ms'] >= 0
    assert quick_result['trace']['steps'][0]['latency_ms'] >= 0
