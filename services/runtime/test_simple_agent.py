import asyncio
import httpx


async def test_simple_agent():
    base_url = "http://localhost:8000/api/v1/agents"
    
    # Simple calculator agent
    agent_code = """
operation = input_data.get('operation', 'add')
a = input_data.get('a', 0)
b = input_data.get('b', 0)

if operation == 'add':
    result = a + b
elif operation == 'subtract':
    result = a - b
elif operation == 'multiply':
    result = a * b
elif operation == 'divide':
    result = a / b if b != 0 else 'error: division by zero'
else:
    result = 'error: unknown operation'

result = {
    'operation': operation,
    'inputs': {'a': a, 'b': b},
    'result': result
}
"""
    
    deploy_payload = {
        "agent_id": "simple-calculator",
        "code": agent_code,
        "requirements": [],
        "environment": None,
        "max_memory": "256m",
        "max_cpu": "0.25"
    }
    
    test_cases = [
        {"operation": "add", "a": 5, "b": 3},
        {"operation": "multiply", "a": 4, "b": 7},
        {"operation": "subtract", "a": 10, "b": 3},
        {"operation": "divide", "a": 20, "b": 4}
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            print("=" * 60)
            print("DEPLOYING SIMPLE CALCULATOR AGENT")
            print("=" * 60)
            
            deploy_response = await client.post(
                f"{base_url}/deploy",
                json=deploy_payload,
                timeout=30.0
            )
            
            if deploy_response.status_code != 200:
                print(f"Deployment failed with status {deploy_response.status_code}")
                print(deploy_response.text)
                return
            
            deploy_result = deploy_response.json()
            print(f"Deploy Status: {deploy_response.status_code}")
            print(f"Deployment ID: {deploy_result.get('deployment_id')}")
            print(f"Status: {deploy_result.get('status')}")
            print(f"Message: {deploy_result.get('message')}")
            
            print("\n" + "=" * 60)
            print("TESTING CALCULATIONS")
            print("=" * 60)
            
            for i, test_input in enumerate(test_cases, 1):
                op = test_input['operation']
                a = test_input['a']
                b = test_input['b']
                
                print(f"\n[{i}] Testing: {op.capitalize()} {a} {'+' if op == 'add' else '-' if op == 'subtract' else '*' if op == 'multiply' else '/'} {b}")
                
                invoke_payload = {
                    "agent_id": "simple-calculator",
                    "input_data": test_input,
                    "timeout": 10
                }
                
                invoke_response = await client.post(
                    f"{base_url}/invoke",
                    json=invoke_payload,
                    timeout=30.0
                )
                
                if invoke_response.status_code == 200:
                    invoke_result = invoke_response.json()
                    print(f"    Status: {invoke_result.get('status')}")
                    print(f"    Output: {invoke_result.get('output')}")
                    print(f"    Execution Time: {invoke_result.get('execution_time_ms')}ms")
                    print(f"    Cost: {invoke_result.get('cost_cents')} cents")
                else:
                    print(f"    Invocation failed with status {invoke_response.status_code}")
                    print(f"    Error: {invoke_response.text}")
            
            print("\n" + "=" * 60)
            print("CHECKING AGENT STATUS")
            print("=" * 60)
            
            status_response = await client.get(
                f"{base_url}/simple-calculator/status",
                timeout=30.0
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"Agent ID: {status_result.get('agent_id')}")
                print(f"Status: {status_result.get('status')}")
                print(f"Deployed At: {status_result.get('deployed_at')}")
                print(f"Total Invocations: {status_result.get('invocation_count')}")
                print(f"Last Invocation: {status_result.get('last_invocation')}")
            else:
                print(f"Status check failed with code {status_response.status_code}")
            
            print("\n" + "=" * 60)
            print("TEST COMPLETED")
            print("=" * 60)
            print("\nCheck the server logs for these entries:")
            print("  - Deployed agent simple-calculator with deployment_id <uuid>")
            print("  - Invoked agent simple-calculator, invocation_id <uuid>, status SUCCESS")
            
        except httpx.ConnectError:
            print("\nERROR: Could not connect to runtime service")
            print("Make sure the service is running:")
            print("  cd services/runtime")
            print("  python -m src.main")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AGENT RUNTIME TEST - LOGGING VERIFICATION")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Deploy a simple calculator agent")
    print("  2. Invoke it with test calculations")
    print("  3. Check agent status")
    print("\nWatch the server logs for deployment and invocation messages!")
    print("=" * 60 + "\n")
    
    asyncio.run(test_simple_agent())
