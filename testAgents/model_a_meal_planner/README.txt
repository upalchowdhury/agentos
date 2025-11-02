Meal Planner Agent - Model A Version
====================================

Same functionality as model_b_sample.py but deployed as Model A.

SETUP:
------
1. Get Google API key: https://makersuite.google.com/app/apikey
2. Set environment variable:
   export GOOGLE_API_KEY='your-key-here'

DEPLOY:
-------
./register_agent.sh

INVOKE:
-------
./invoke_agent.sh <agent-id>

TEST LOCALLY (optional):
------------------------
pip install google-generativeai
python test_local.py

DIFFERENCE FROM MODEL B:
------------------------
- Model A: Code runs ON AgentOS infrastructure
- Model B: Code runs on YOUR machine

Same Gemini API, same results, different hosting!
