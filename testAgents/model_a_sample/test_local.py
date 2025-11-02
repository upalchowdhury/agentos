#!/usr/bin/env python3
"""
Local testing script for Model A agent
Tests the handler function without deploying to AgentOS
"""
import json
from agent import handler


def test_addition():
    """Test addition operation"""
    print("Test 1: Addition")
    event = {
        "input_data": {
            "operation": "add",
            "numbers": [10, 20, 30, 40]
        },
        "context": {
            "invocation_id": "test-add-001",
            "agent_id": "calculator-agent"
        }
    }
    
    result = handler(event)
    print(json.dumps(result, indent=2))
    assert result["result"]["result"] == 100
    print("✅ Passed\n")


def test_multiplication():
    """Test multiplication operation"""
    print("Test 2: Multiplication")
    event = {
        "input_data": {
            "operation": "multiply",
            "numbers": [5, 3, 2]
        },
        "context": {
            "invocation_id": "test-mult-001",
            "agent_id": "calculator-agent"
        }
    }
    
    result = handler(event)
    print(json.dumps(result, indent=2))
    assert result["result"]["result"] == 30
    print("✅ Passed\n")


def test_average():
    """Test average operation"""
    print("Test 3: Average")
    event = {
        "input_data": {
            "operation": "average",
            "numbers": [100, 200, 300]
        },
        "context": {
            "invocation_id": "test-avg-001",
            "agent_id": "calculator-agent"
        }
    }
    
    result = handler(event)
    print(json.dumps(result, indent=2))
    assert result["result"]["result"] == 200.0
    print("✅ Passed\n")


def test_invalid_input():
    """Test error handling"""
    print("Test 4: Invalid Input (empty numbers)")
    event = {
        "input_data": {
            "operation": "add",
            "numbers": []
        },
        "context": {
            "invocation_id": "test-err-001",
            "agent_id": "calculator-agent"
        }
    }
    
    result = handler(event)
    print(json.dumps(result, indent=2))
    assert "error" in result["result"]
    print("✅ Passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Local Tests for Calculator Agent")
    print("=" * 60)
    print()
    
    try:
        test_addition()
        test_multiplication()
        test_average()
        test_invalid_input()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)
