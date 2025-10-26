import asyncio
import httpx


async def test_invoke():
    url = "http://localhost:8000/api/v1/agents/invoke"
    
    payload = {
        "agent_id": "test-math-agent",
        "input_data": {"x": 10, "y": 20},
        "timeout": 10
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {result}")
            print(f"\nExpected output: 30")
            print(f"Actual output: {result.get('output')}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_invoke())
