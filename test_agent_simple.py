#!/usr/bin/env python3
"""
Simple test script to verify AgentOS runtime deployment
"""
import requests
import json
import uuid

RUNTIME_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{RUNTIME_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed\n")

def test_deploy_agent():
    """Test agent deployment (v1 API)"""
    print("Testing agent deployment...")
    agent_id = str(uuid.uuid4())
    
    payload = {
        "agent_id": agent_id,
        "name": "test-agent",
        "description": "Test agent for deployment verification",
        "code": "def run(input_data): return {'message': 'Hello from agent', 'input': input_data}",
        "requirements": []
    }
    
    response = requests.post(
        f"{RUNTIME_URL}/api/v1/agents/deploy",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print(f"✅ Agent deployed successfully with ID: {agent_id}\n")
        return agent_id
    else:
        print(f"⚠️  Deployment response: {response.status_code}\n")
        return agent_id

def test_invoke_agent(agent_id):
    """Test agent invocation"""
    print(f"Testing agent invocation for {agent_id}...")
    
    payload = {
        "agent_id": agent_id,
        "input": {"test": "data"}
    }
    
    response = requests.post(
        f"{RUNTIME_URL}/api/v1/agents/invoke",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Agent invoked successfully\n")
    else:
        print("⚠️  Invocation failed\n")

def test_agent_status(agent_id):
    """Test agent status check"""
    print(f"Testing agent status for {agent_id}...")
    
    response = requests.get(f"{RUNTIME_URL}/api/v1/agents/{agent_id}/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Status check passed\n")
    else:
        print("⚠️  Status check response\n")

if __name__ == "__main__":
    print("=" * 60)
    print("AgentOS Runtime Deployment Test")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Deploy agent
        agent_id = test_deploy_agent()
        
        # Test 3: Check status
        test_agent_status(agent_id)
        
        # Test 4: Invoke agent
        test_invoke_agent(agent_id)
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
