import asyncio
import httpx


async def test_deploy():
    url = "http://localhost:8000/api/v1/agents/deploy"
    
    payload = {
        "agent_id": "test-math-agent",
        "code": "result = input_data['x'] + input_data['y']",
        "requirements": [],
        "environment": None,
        "max_memory": "512m",
        "max_cpu": "0.5"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_deploy())
