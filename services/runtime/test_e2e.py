import asyncio
import httpx


async def test_e2e():
    base_url = "http://localhost:8000/api/v1/agents"
    
    agent_code = """
sentiment = "neutral"
if "bad" in input_data['message'].lower():
    sentiment = "negative"
elif "great" in input_data['message'].lower():
    sentiment = "positive"
result = {
    "message": input_data['message'],
    "sentiment": sentiment,
    "response": f"I understand your {sentiment} feedback"
}
"""
    
    deploy_payload = {
        "agent_id": "customer-support-agent",
        "code": agent_code,
        "requirements": [],
        "environment": None,
        "max_memory": "512m",
        "max_cpu": "0.5"
    }
    
    test_messages = [
        "This product is great!",
        "I had a bad experience",
        "Everything is fine",
        "Great service!",
        "Bad quality"
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            print("=" * 60)
            print("DEPLOYING CUSTOMER SUPPORT AGENT")
            print("=" * 60)
            deploy_response = await client.post(
                f"{base_url}/deploy",
                json=deploy_payload,
                timeout=30.0
            )
            print(f"Deploy Status: {deploy_response.status_code}")
            deploy_result = deploy_response.json()
            print(f"Deployment ID: {deploy_result.get('deployment_id')}")
            print(f"Status: {deploy_result.get('status')}")
            
            print("\n" + "=" * 60)
            print("INVOKING AGENT WITH TEST MESSAGES")
            print("=" * 60)
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n[{i}] Testing message: '{message}'")
                invoke_payload = {
                    "agent_id": "customer-support-agent",
                    "input_data": {"message": message},
                    "timeout": 10
                }
                
                invoke_response = await client.post(
                    f"{base_url}/invoke",
                    json=invoke_payload,
                    timeout=30.0
                )
                invoke_result = invoke_response.json()
                
                print(f"    Status: {invoke_result.get('status')}")
                print(f"    Output: {invoke_result.get('output')}")
                print(f"    Execution Time: {invoke_result.get('execution_time_ms')}ms")
                print(f"    Cost: {invoke_result.get('cost_cents')} cents")
            
            print("\n" + "=" * 60)
            print("CHECKING AGENT STATUS")
            print("=" * 60)
            
            status_response = await client.get(
                f"{base_url}/customer-support-agent/status",
                timeout=30.0
            )
            status_result = status_response.json()
            
            print(f"Agent ID: {status_result.get('agent_id')}")
            print(f"Status: {status_result.get('status')}")
            print(f"Deployed At: {status_result.get('deployed_at')}")
            print(f"Total Invocations: {status_result.get('invocation_count')}")
            print(f"Last Invocation: {status_result.get('last_invocation')}")
            
            print("\n" + "=" * 60)
            print("E2E TEST COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(test_e2e())
