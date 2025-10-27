import asyncio
import httpx
import json
from datetime import datetime


async def deploy_with_monitoring():
    base_url = "http://localhost:8000/api/v1/agents"
    
    # Meal planning agent code (AgentOS compatible)
    agent_code = """
# Meal Recommendation Agent
meal_type = input_data.get('meal_type', 'lunch')
dietary = input_data.get('dietary', 'balanced')
servings = input_data.get('servings', 2)

meals = {
    'breakfast': {
        'balanced': {'name': 'Oatmeal with berries and nuts', 'calories': 320, 'protein': 12},
        'vegetarian': {'name': 'Veggie scramble with toast', 'calories': 280, 'protein': 18},
        'low-carb': {'name': 'Greek yogurt with almonds', 'calories': 250, 'protein': 20}
    },
    'lunch': {
        'balanced': {'name': 'Quinoa bowl with chicken', 'calories': 450, 'protein': 25},
        'vegetarian': {'name': 'Lentil soup with salad', 'calories': 380, 'protein': 18},
        'low-carb': {'name': 'Grilled salmon with vegetables', 'calories': 420, 'protein': 35}
    },
    'dinner': {
        'balanced': {'name': 'Grilled chicken with rice', 'calories': 520, 'protein': 32},
        'vegetarian': {'name': 'Vegetable curry with quinoa', 'calories': 450, 'protein': 15},
        'low-carb': {'name': 'Steak with roasted vegetables', 'calories': 480, 'protein': 40}
    }
}

recommendation = meals.get(meal_type, {}).get(dietary, {'name': 'Healthy mixed salad', 'calories': 200, 'protein': 8})

result = {
    'meal_type': meal_type,
    'dietary_preference': dietary,
    'servings': servings,
    'recommendation': recommendation['name'],
    'nutrition': {
        'calories_per_serving': recommendation['calories'],
        'protein_grams': recommendation['protein'],
        'total_calories': recommendation['calories'] * servings
    },
    'timestamp': 'executed'
}
"""
    
    # Deployment configuration
    deploy_payload = {
        "agent_id": "meal-planner-agent-v1",
        "code": agent_code,
        "requirements": [],
        "environment": {
            "LOG_LEVEL": "INFO",
            "AGENT_TYPE": "meal_planner",
            "VERSION": "1.0.0"
        },
        "max_memory": "256m",
        "max_cpu": "0.25"
    }
    
    print("=" * 100)
    print("DEPLOYING AGENT WITH SECURITY & LOGGING MONITORING")
    print("=" * 100)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Agent ID: {deploy_payload['agent_id']}")
    print(f"Memory Limit: {deploy_payload['max_memory']}")
    print(f"CPU Limit: {deploy_payload['max_cpu']}")
    print()
    
    async with httpx.AsyncClient() as client:
        # Step 1: Deploy Agent
        print("[STEP 1] DEPLOYING AGENT...")
        print("-" * 100)
        
        try:
            deploy_response = await client.post(
                f"{base_url}/deploy",
                json=deploy_payload,
                timeout=30.0
            )
            
            if deploy_response.status_code != 200:
                print(f"❌ Deployment failed with status {deploy_response.status_code}")
                print(f"Response: {deploy_response.text}")
                return
            
            deploy_result = deploy_response.json()
            deployment_id = deploy_result['deployment_id']
            
            print(f"✅ Deployment successful!")
            print(f"   Deployment ID: {deployment_id}")
            print(f"   Status: {deploy_result['status']}")
            print(f"   Deployed At: {deploy_result['deployed_at']}")
            print()
            
        except httpx.ConnectError:
            print("❌ ERROR: Could not connect to runtime service")
            print("   Make sure the service is running:")
            print("   cd services/runtime && python -m src.main")
            return
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return
        
        # Step 2: Test Agent Invocations
        print("[STEP 2] TESTING AGENT INVOCATIONS...")
        print("-" * 100)
        
        test_cases = [
            {"meal_type": "breakfast", "dietary": "balanced", "servings": 2},
            {"meal_type": "lunch", "dietary": "vegetarian", "servings": 4},
            {"meal_type": "dinner", "dietary": "low-carb", "servings": 3},
        ]
        
        invocation_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}/{len(test_cases)}: {test_case}")
            
            try:
                invoke_response = await client.post(
                    f"{base_url}/invoke",
                    json={
                        "agent_id": "meal-planner-agent-v1",
                        "input_data": test_case,
                        "timeout": 10
                    },
                    timeout=30.0
                )
                
                if invoke_response.status_code == 200:
                    result = invoke_response.json()
                    invocation_results.append(result)
                    
                    print(f"   ✅ Status: {result['status']}")
                    print(f"      Invocation ID: {result['invocation_id']}")
                    print(f"      Output: {json.dumps(result['output'], indent=6)}")
                    print(f"      Execution Time: {result['execution_time_ms']}ms")
                    print(f"      Cost: ${result['cost_cents']/100:.2f}")
                else:
                    print(f"   ❌ Invocation failed: {invoke_response.status_code}")
                    print(f"      Error: {invoke_response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error during invocation: {e}")
        
        # Step 3: Check Agent Status
        print("\n[STEP 3] CHECKING AGENT STATUS...")
        print("-" * 100)
        
        try:
            status_response = await client.get(
                f"{base_url}/meal-planner-agent-v1/status",
                timeout=30.0
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ Agent Status Retrieved")
                print(f"   Agent ID: {status['agent_id']}")
                print(f"   Status: {status['status']}")
                print(f"   Deployed At: {status['deployed_at']}")
                print(f"   Total Invocations: {status['invocation_count']}")
                print(f"   Last Invocation: {status.get('last_invocation', 'N/A')}")
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking status: {e}")
        
        # Step 4: Performance Summary
        print("\n[STEP 4] PERFORMANCE SUMMARY...")
        print("-" * 100)
        
        if invocation_results:
            total_time = sum(r['execution_time_ms'] for r in invocation_results)
            total_cost = sum(r['cost_cents'] for r in invocation_results)
            avg_time = total_time / len(invocation_results)
            
            print(f"📊 Total Invocations: {len(invocation_results)}")
            print(f"📊 Average Execution Time: {avg_time:.2f}ms")
            print(f"📊 Total Execution Time: {total_time}ms")
            print(f"📊 Total Cost: ${total_cost/100:.2f}")
            print(f"📊 Success Rate: {len([r for r in invocation_results if r['status'] == 'SUCCESS'])}/{len(invocation_results)}")
        
        print("\n" + "=" * 100)
        print("DEPLOYMENT & TESTING COMPLETE")
        print("=" * 100)
        print("\n📋 Next Steps:")
        print("   1. Check server logs: tail -f logs/runtime.log")
        print("   2. Monitor database: python monitor_agent.py")
        print("   3. View RBAC audit logs: ./check_security.sh")
        print("   4. Query metrics: SELECT * FROM agent_stats WHERE agent_did = 'meal-planner-agent-v1';")
        print()


if __name__ == "__main__":
    print("\n🚀 AgentOS - Agent Deployment with Monitoring\n")
    asyncio.run(deploy_with_monitoring())
