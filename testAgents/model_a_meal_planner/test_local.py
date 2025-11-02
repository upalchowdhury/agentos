#!/usr/bin/env python3
"""Test meal planner locally before deploying"""
import os
from agent import handler

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not set")
    print("Set it with: export GOOGLE_API_KEY='your-key-here'")
    exit(1)

print("🍽️  Testing Meal Planner Agent Locally")
print("=" * 60)

test_event = {
    "input_data": {
        "prompt": "Suggest a quick healthy breakfast"
    },
    "context": {
        "invocation_id": "local-test",
        "agent_id": "meal-planner"
    }
}

result = handler(test_event)

if "error" in result.get("result", {}):
    print(f"❌ Error: {result['result']['error']}")
else:
    print(f"✅ Response:\n{result['result']['response']}\n")
    print(f"⏱️  Execution: {result['telemetry']['trace']['execution_time_ms']}ms")
    print(f"💰 Cost: ${result['cost']:.6f}")

print("=" * 60)
