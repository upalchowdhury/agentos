# Quick Start Guide - Sentiment Analyzer Agent

## 🚀 Deploy and Test in 3 Steps

### Step 1: Deploy the Agent

```bash
cd /Users/upalc/AgentOS/agentos/testAgents/runtime_agent
./deploy_agent.sh
```

Expected output:
```json
{
  "deployment_id": "uuid-here",
  "agent_id": "sentiment-analyzer-001",
  "status": "deployed",
  "created_at": "2025-10-29T..."
}
```

### Step 2: Invoke the Agent

```bash
./invoke_agent.sh
```

This will run 4 test cases and show results for each.

### Step 3: Monitor the Agent

#### View Real-Time Logs
```bash
kubectl logs -n agentos deployment/runtime -f | grep AGENT_LOG
```

#### Check Agent Status
```bash
curl http://localhost:8000/api/v1/agents/sentiment-analyzer-001/status | jq .
```

## 📊 What Gets Logged

Each agent invocation logs:

### 1. Invocation Started Event
```json
{
  "event_type": "invocation_started",
  "timestamp": "2025-10-29T21:01:11.812951",
  "data": {
    "agent_id": "sentiment-analyzer-v1",
    "input_length": 59
  }
}
```

### 2. Invocation Completed Event  
```json
{
  "event_type": "invocation_completed",
  "timestamp": "2025-10-29T21:01:11.813095",
  "data": {
    "agent_id": "sentiment-analyzer-v1",
    "sentiment": "positive",
    "processing_time_ms": 8.89,
    "word_count": 10,
    "status": "success"
  }
}
```

### 3. Response with Detailed Metrics
```json
{
  "agent_id": "sentiment-analyzer-v1",
  "sentiment": {
    "score": 1.0,
    "label": "positive",
    "confidence": 1.0
  },
  "entities": {
    "great": 1,
    "amazing": 1,
    "product": 1
  },
  "metrics": {
    "processing_time_ms": 8.89,
    "word_count": 10,
    "character_count": 47,
    "timestamp": "2025-10-29T21:01:11.813087"
  },
  "status": "success"
}
```

## 🎯 Custom Invocations

### Single Invocation
```bash
curl -X POST http://localhost:8000/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "sentiment-analyzer-001",
    "input": {
      "text": "Your text to analyze here!"
    }
  }' | jq .
```

### Batch Testing
Create a file `test_inputs.txt`:
```
This product exceeded my expectations!
Very disappointed with the service.
It works as described, nothing special.
```

Then run:
```bash
while IFS= read -r line; do
  curl -s -X POST http://localhost:8000/api/v1/agents/invoke \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\":\"sentiment-analyzer-001\",\"input\":{\"text\":\"$line\"}}" | jq .
  sleep 1
done < test_inputs.txt
```

## 📈 Monitoring Dashboard Data

The agent provides metrics perfect for dashboards:

### Key Performance Indicators (KPIs)
- **Invocation Count**: Total number of executions
- **Success Rate**: Percentage of successful invocations
- **Average Processing Time**: Mean latency in milliseconds
- **Sentiment Distribution**: Breakdown of positive/negative/neutral results

### Metrics to Track
- `processing_time_ms` - Agent latency
- `word_count` - Input size
- `sentiment.score` - Sentiment score (-1 to 1)
- `sentiment.label` - Classification result
- `status` - success/error

### Sample Prometheus Queries (if integrated)
```promql
# Average processing time
avg(agent_processing_time_ms{agent_id="sentiment-analyzer-v1"})

# Invocation rate
rate(agent_invocations_total{agent_id="sentiment-analyzer-v1"}[5m])

# Error rate
rate(agent_errors_total{agent_id="sentiment-analyzer-v1"}[5m])
```

## 🔧 Troubleshooting

### Problem: Deployment Fails

**Check runtime is accessible:**
```bash
curl http://localhost:8000/health
```

**Check database tables:**
```bash
kubectl exec -i -n agentos postgres-xxx -- psql agentos -c "\\dt"
```

### Problem: No Logs Appearing

**Check pod is running:**
```bash
kubectl get pods -n agentos | grep runtime
```

**View all logs:**
```bash
kubectl logs -n agentos deployment/runtime --tail=100
```

### Problem: Agent Returns Errors

**Check the error message in the response**
**Common issues:**
- Missing "text" field in input
- Empty text string
- Malformed JSON

## 🎓 Next Steps

1. **Extend the Agent**: Add more sophisticated NLP
2. **Add More Metrics**: Track custom business metrics
3. **Integrate with Grafana**: Create visualization dashboards
4. **Set Up Alerts**: Configure alerts on error rates or latency
5. **Scale Testing**: Run load tests to see performance at scale

## 📝 Notes

- The agent uses simple keyword-based sentiment analysis
- For production, consider using libraries like `textblob` or `vaderSentiment`
- Logs are captured by the runtime and can be shipped to any logging system
- All timestamps are in UTC
- Processing time includes the entire execution cycle
