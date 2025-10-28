"""
Deploy test meal planning agent using new Model A API
Tests the enhanced runtime service with OpenTelemetry tracing
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test agent code - simplified version of your meal planner
AGENT_CODE = """
# Meal Planning Agent (Model A - Code Upload)
# This runs on AgentOS infrastructure

meal_type = input_data.get('meal_type', 'lunch')
dietary = input_data.get('dietary', 'balanced')
servings = input_data.get('servings', 2)

# Meal database
meals = {
    'breakfast': {
        'balanced': {'name': 'Oatmeal with berries and nuts', 'calories': 320, 'protein': 12},
        'vegetarian': {'name': 'Veggie scramble with toast', 'calories': 280, 'protein': 18},
        'low-carb': {'name': 'Greek yogurt with almonds', 'calories': 250, 'protein': 20},
        'vegan': {'name': 'Avocado toast with seeds', 'calories': 290, 'protein': 10}
    },
    'lunch': {
        'balanced': {'name': 'Quinoa bowl with chicken', 'calories': 450, 'protein': 25},
        'vegetarian': {'name': 'Lentil soup with salad', 'calories': 380, 'protein': 18},
        'low-carb': {'name': 'Grilled salmon with vegetables', 'calories': 420, 'protein': 35},
        'vegan': {'name': 'Buddha bowl with tofu', 'calories': 400, 'protein': 20}
    },
    'dinner': {
        'balanced': {'name': 'Grilled chicken with rice', 'calories': 520, 'protein': 32},
        'vegetarian': {'name': 'Vegetable curry with quinoa', 'calories': 450, 'protein': 15},
        'low-carb': {'name': 'Steak with roasted vegetables', 'calories': 480, 'protein': 40},
        'vegan': {'name': 'Chickpea stew with greens', 'calories': 390, 'protein': 18}
    }
}

recommendation = meals.get(meal_type, {}).get(dietary, {
    'name': 'Healthy mixed salad',
    'calories': 200,
    'protein': 8
})

# Return result in expected format
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
    'timestamp': 'executed',
    'agent_type': 'meal_planner',
    'version': '2.0'
}
"""

async def deploy_and_test():
    base_url = "http://localhost:8000"
    auth_headers = {"Authorization": "Bearer test_user_token"}
    
    print("=" * 100)
    print("DEPLOYING TEST AGENT WITH NEW MODEL A API + OPENTELEMETRY")
    print("=" * 100)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Create Model A agent
        print("[STEP 1] CREATE MODEL A AGENT")
        print("-" * 100)
        
        create_payload = {
            "name": "meal-planner-v2",
            "runtime": "python3.11",
            "requirements": [],
            "env": {},
            "resources": {
                "cpu": "500m",
                "mem": "512Mi"
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/v1/agents/modelA",
                headers=auth_headers,
                json=create_payload
            )
            
            if response.status_code == 201:
                data = response.json()
                agent_id = data['agent_id']
                upload_url = data['upload_url']
                deployment_id = data['deployment_id']
                
                print(f"✅ Agent created successfully!")
                print(f"   Agent ID: {agent_id}")
                print(f"   Deployment ID: {deployment_id}")
                print(f"   Upload URL: {upload_url}")
                print(f"   Expires: {data['expires_at']}")
                print()
            else:
                print(f"❌ Failed to create agent: {response.status_code}")
                print(response.text)
                return
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # Step 2: Simulate artifact upload (in production, upload to signed URL)
        print("[STEP 2] UPLOAD ARTIFACT")
        print("-" * 100)
        print("ℹ️  In production: Upload code to signed S3 URL")
        print("ℹ️  For this demo: Using direct database insert")
        
        # For testing, we'll insert the code directly using the old deploy endpoint
        # In production, client would upload to S3, trigger build
        
        legacy_deploy = {
            "agent_id": agent_id,
            "code": AGENT_CODE,
            "requirements": [],
            "environment": {},
            "max_memory": "512m",
            "max_cpu": "0.5"
        }
        
        response = await client.post(
            f"{base_url}/api/v1/agents/deploy",
            headers=auth_headers,
            json=legacy_deploy
        )
        
        if response.status_code == 200:
            print("✅ Code deployed (using legacy endpoint for demo)")
            print()
        else:
            print(f"⚠️  Deploy status: {response.status_code}")
            print()
        
        # Step 3: Get agent details
        print("[STEP 3] GET AGENT DETAILS")
        print("-" * 100)
        
        try:
            response = await client.get(
                f"{base_url}/v1/agents/{agent_id}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                agent = response.json()
                print(f"✅ Agent details retrieved")
                print(f"   Name: {agent['name']}")
                print(f"   Model Type: {agent['model_type']}")
                print(f"   Status: {agent['status']}")
                print(f"   Runtime: {agent.get('runtime', 'N/A')}")
                print(f"   Created: {agent['created_at']}")
                print(f"   Invocations: {agent['invocation_count']}")
                print(f"   Cost to date: ${agent['cost_to_date']}")
                print()
        except Exception as e:
            print(f"⚠️  Could not get agent details: {e}")
            print()
        
        # Step 4: Test invocations
        print("[STEP 4] TEST INVOCATIONS")
        print("-" * 100)
        
        test_cases = [
            {
                "name": "Balanced Breakfast for 2",
                "input_data": {
                    "meal_type": "breakfast",
                    "dietary": "balanced",
                    "servings": 2
                }
            },
            {
                "name": "Vegetarian Lunch for 4",
                "input_data": {
                    "meal_type": "lunch",
                    "dietary": "vegetarian",
                    "servings": 4
                }
            },
            {
                "name": "Low-Carb Dinner for 3",
                "input_data": {
                    "meal_type": "dinner",
                    "dietary": "low-carb",
                    "servings": 3
                }
            },
            {
                "name": "Vegan Breakfast for 1",
                "input_data": {
                    "meal_type": "breakfast",
                    "dietary": "vegan",
                    "servings": 1
                }
            }
        ]
        
        invocation_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}/{len(test_cases)}: {test_case['name']}")
            print(f"   Input: {test_case['input_data']}")
            
            try:
                response = await client.post(
                    f"{base_url}/v1/agents/{agent_id}/invoke",
                    headers=auth_headers,
                    json={"input_data": test_case['input_data']},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    invocation_results.append(result)
                    
                    print(f"   ✅ Status: {result['status']}")
                    print(f"      Invocation ID: {result['invocation_id']}")
                    
                    if result.get('result'):
                        rec = result['result']
                        print(f"      Recommendation: {rec.get('recommendation', 'N/A')}")
                        print(f"      Calories: {rec.get('nutrition', {}).get('total_calories', 'N/A')}")
                    
                    print(f"      Execution: {result['execution_time_ms']}ms")
                    print(f"      Cost: ${result['cost']:.4f}")
                else:
                    print(f"   ❌ Invocation failed: {response.status_code}")
                    print(f"      Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Step 5: Get metrics
        print("\n[STEP 5] GET AGENT METRICS")
        print("-" * 100)
        
        try:
            response = await client.get(
                f"{base_url}/v1/agents/{agent_id}/metrics?range=1h",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                metrics = response.json()
                print(f"✅ Metrics retrieved")
                print(f"   Total Invocations: {metrics['total_invocations']}")
                print(f"   Successful: {metrics['successful_invocations']}")
                print(f"   Failed: {metrics['failed_invocations']}")
                print(f"   Avg Execution Time: {metrics['avg_execution_time_ms']:.2f}ms")
                print(f"   P50 Latency: {metrics['p50_latency_ms']:.2f}ms")
                print(f"   P95 Latency: {metrics['p95_latency_ms']:.2f}ms")
                print(f"   Total Cost: ${metrics['total_cost_usd']:.4f}")
                print(f"   Error Rate: {metrics['error_rate']:.2%}")
                print()
        except Exception as e:
            print(f"⚠️  Could not get metrics: {e}")
            print()
        
        # Step 6: Get costs
        print("[STEP 6] GET COST BREAKDOWN")
        print("-" * 100)
        
        try:
            response = await client.get(
                f"{base_url}/v1/agents/{agent_id}/costs?period=monthly",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                costs = response.json()
                print(f"✅ Cost breakdown retrieved")
                print(f"   Period: {costs['period']}")
                print(f"   Total Cost: ${costs['total_cost_usd']:.4f}")
                print(f"   Invocations: {costs['invocations']}")
                print(f"   Cost per Invocation: ${costs['cost_per_invocation_usd']:.4f}")
                print(f"   Breakdown:")
                for category, amount in costs.get('breakdown', {}).items():
                    print(f"      {category}: ${amount:.4f}")
                print()
        except Exception as e:
            print(f"⚠️  Could not get costs: {e}")
            print()
        
        # Step 7: Performance summary
        print("[STEP 7] PERFORMANCE SUMMARY")
        print("-" * 100)
        
        if invocation_results:
            total_time = sum(r['execution_time_ms'] for r in invocation_results)
            total_cost = sum(r['cost'] for r in invocation_results)
            avg_time = total_time / len(invocation_results)
            success_count = len([r for r in invocation_results if r['status'] == 'SUCCESS'])
            
            print(f"📊 Total Tests: {len(test_cases)}")
            print(f"📊 Successful: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
            print(f"📊 Average Execution Time: {avg_time:.2f}ms")
            print(f"📊 Total Execution Time: {total_time}ms")
            print(f"📊 Total Cost: ${total_cost:.4f}")
        
        print("\n" + "=" * 100)
        print("DEPLOYMENT & TESTING COMPLETE")
        print("=" * 100)
        print("\n📋 Next Steps:")
        print("   1. Check OpenTelemetry traces: http://localhost:16686 (if Jaeger running)")
        print("   2. Query database: docker exec agentos-postgres psql -U postgres -d agentos")
        print("   3. View metrics: curl http://localhost:8000/v1/agents/{agent_id}/metrics")
        print("   4. Monitor: python monitor_agent.py")
        print(f"\n🆔 Agent ID: {agent_id}")
        print()


if __name__ == "__main__":
    print("\n🚀 AgentOS Model A Deployment Test (Enhanced API)\n")
    asyncio.run(deploy_and_test())
