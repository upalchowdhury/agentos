# Sentiment Analyzer Agent for AgentOS

A production-ready agent that demonstrates AgentOS runtime capabilities with comprehensive logging and monitoring.

## Features

- **Sentiment Analysis**: Analyzes text sentiment (positive/negative/neutral)
- **Entity Extraction**: Identifies key terms in the text
- **Detailed Metrics**: Logs processing time, word count, and other metrics
- **Error Handling**: Graceful error handling with detailed logging
- **Monitoring Ready**: Logs structured events for observability

## Agent Capabilities

The agent logs the following data points:

1. **Invocation Metrics**:
   - Processing time (ms)
   - Input length
   - Word count
   - Character count

2. **Analysis Results**:
   - Sentiment score (-1 to 1)
   - Sentiment label (positive/negative/neutral)
   - Confidence level
   - Key entities/terms

3. **Events Logged**:
   - `invocation_started`: When agent execution begins
   - `invocation_completed`: When agent completes successfully
   - `invocation_failed`: When agent encounters an error

## Deployment

### Prerequisites

- AgentOS runtime running on Kubernetes
- Port forwarding enabled: `kubectl port-forward -n agentos svc/runtime 8000:8000`

### Deploy the Agent

```bash
cd /Users/upalc/AgentOS/agentos/testAgents/runtime_agent
chmod +x deploy_agent.sh invoke_agent.sh
./deploy_agent.sh
```

### Invoke the Agent

```bash
./invoke_agent.sh
```

## Monitoring Usage

### View Agent Logs

```bash
# Real-time logs
kubectl logs -n agentos deployment/runtime -f | grep AGENT_LOG

# Last 100 lines
kubectl logs -n agentos deployment/runtime --tail=100 | grep AGENT_LOG
```

### Check Agent Status

```bash
curl http://localhost:8000/api/v1/agents/sentiment-analyzer-001/status | jq .
```

### View Metrics in Dashboard

The agent logs structured JSON events that can be:
- Collected by the observability stack
- Displayed in dashboards
- Used for alerting and monitoring

## Example Usage

### API Call

```bash
curl -X POST http://localhost:8000/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "sentiment-analyzer-001",
    "input": {
      "text": "This is an amazing product! I absolutely love it!"
    }
  }'
```

### Expected Response

```json
{
  "invocation_id": "uuid-here",
  "status": "completed",
  "output": {
    "agent_id": "sentiment-analyzer-v1",
    "sentiment": {
      "score": 0.667,
      "label": "positive",
      "confidence": 0.667
    },
    "entities": {
      "product": 1,
      "love": 1,
      "amazing": 1
    },
    "metrics": {
      "processing_time_ms": 1.23,
      "word_count": 8,
      "character_count": 48,
      "timestamp": "2025-10-29T20:00:00.000Z"
    },
    "status": "success"
  }
}
```

## Monitoring in Production

This agent is designed to integrate with:

- **Prometheus**: Metrics collection
- **Grafana**: Dashboard visualization
- **OpenTelemetry**: Distributed tracing
- **ClickHouse**: Event storage and analytics

Each invocation generates structured logs that include:
- Timestamp
- Processing time
- Input/output sizes
- Sentiment analysis results
- Error information (if applicable)

## Customization

To customize the agent:

1. Edit `sentiment_analyzer.py`
2. Modify the `analyze_sentiment()` function for better accuracy
3. Add more sophisticated NLP libraries (textblob, vaderSentiment, etc.)
4. Extend logging to include custom metrics
5. Redeploy using `./deploy_agent.sh`

## Troubleshooting

### Agent Won't Deploy

- Check runtime is accessible: `curl http://localhost:8000/health`
- Verify database tables exist
- Check runtime logs: `kubectl logs -n agentos deployment/runtime`

### Agent Fails to Invoke

- Verify agent was deployed: `curl http://localhost:8000/api/v1/agents/sentiment-analyzer-001/status`
- Check input format is correct (must include `text` key)
- Review runtime logs for errors

### No Logs Appearing

- Ensure you're looking at the correct pod
- Check log level configuration
- Verify the agent is actually being invoked
