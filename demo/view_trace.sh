#!/bin/bash
# View trace-level mapping with hierarchical spans

echo "🔍 Trace Viewer"
echo "==============="
echo ""

# Get recent traces
echo "📊 Recent Traces:"
kubectl exec postgres-0 -n agentos -- psql -U postgres -d agentos -t -c "
SELECT trace_id, COUNT(*) as spans 
FROM telemetry_spans 
GROUP BY trace_id 
ORDER BY MAX(created_at) DESC 
LIMIT 5;
" 2>/dev/null | head -5

echo ""
echo "Getting latest trace details..."
echo ""

# Get the latest trace ID
TRACE_ID=$(kubectl exec postgres-0 -n agentos -- psql -U postgres -d agentos -t -c "
SELECT trace_id FROM telemetry_spans ORDER BY created_at DESC LIMIT 1;
" 2>/dev/null | xargs)

if [ -z "$TRACE_ID" ]; then
    echo "❌ No traces found. Run the demo first:"
    echo "   cd demo && ./run_demo.sh"
    exit 1
fi

echo "🆔 Trace ID: $TRACE_ID"
echo ""

# Get all spans for this trace
echo "🌳 Span Tree:"
echo ""

kubectl exec postgres-0 -n agentos -- psql -U postgres -d agentos -c "
SELECT 
    CASE 
        WHEN parent_span_id IS NULL THEN '📦 ROOT'
        ELSE '  └─ CHILD'
    END as level,
    LEFT(name, 30) as span_name,
    kind,
    duration_ms || 'ms' as duration,
    LEFT(COALESCE(model_name, '-'), 20) as model,
    LEFT(agent_id, 25) as agent
FROM telemetry_spans
WHERE trace_id = '$TRACE_ID'
ORDER BY start_ts;
" 2>/dev/null

echo ""
echo "📈 Summary:"
kubectl exec postgres-0 -n agentos -- psql -U postgres -d agentos -t -c "
SELECT 
    'Total Spans: ' || COUNT(*) || E'\n' ||
    'Total Duration: ' || SUM(duration_ms) || 'ms' || E'\n' ||
    'Tokens In: ' || SUM(COALESCE(tokens_in, 0)) || E'\n' ||
    'Tokens Out: ' || SUM(COALESCE(tokens_out, 0))
FROM telemetry_spans
WHERE trace_id = '$TRACE_ID';
" 2>/dev/null

echo ""
echo "🔗 Inter-Agent Edges:"
kubectl exec postgres-0 -n agentos -- psql -U postgres -d agentos -c "
SELECT 
    LEFT(from_agent_id, 20) as from_agent,
    ' → ' as arrow,
    LEFT(to_agent_id, 20) as to_agent,
    instruction_type
FROM telemetry_edges
WHERE from_span_id IN (
    SELECT span_id FROM telemetry_spans WHERE trace_id = '$TRACE_ID'
)
ORDER BY time;
" 2>/dev/null

echo ""
echo "💡 View in Jaeger: http://localhost:31686"
echo "   Search for trace: $TRACE_ID"
