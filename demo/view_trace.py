#!/usr/bin/env python3
"""
Trace Visualizer - Shows hierarchical span tree for a trace
"""
import sys
import psycopg2
from collections import defaultdict

DB_HOST = "localhost"
DB_PORT = 30432  # K8s NodePort for postgres
DB_USER = "postgres"
DB_PASS = "postgres"
DB_NAME = "agentos"

def build_tree(spans):
    """Build hierarchical tree from spans"""
    children = defaultdict(list)
    root = None
    
    for span in spans:
        if span['parent_span_id'] is None:
            root = span
        else:
            children[span['parent_span_id']].append(span)
    
    return root, children

def print_tree(span, children, indent=0):
    """Recursively print span tree"""
    prefix = "  " * indent
    arrow = "└─ " if indent > 0 else ""
    
    # Format span info
    name = span['name']
    kind = span['kind']
    duration = span['duration_ms'] or 0
    agent = span['agent_id'] or 'unknown'
    model = span['model_name'] or '-'
    
    # Color codes
    if kind == 'system':
        color = '\033[94m'  # Blue
    elif kind == 'prompt':
        color = '\033[92m'  # Green
    elif kind == 'tool':
        color = '\033[93m'  # Yellow
    elif kind == 'subagent':
        color = '\033[95m'  # Magenta
    else:
        color = '\033[0m'   # Default
    
    reset = '\033[0m'
    
    print(f"{prefix}{arrow}{color}{name}{reset} [{kind}]")
    print(f"{prefix}  ├─ Agent: {agent[:20]}...")
    if model != '-':
        print(f"{prefix}  ├─ Model: {model}")
    print(f"{prefix}  └─ Duration: {duration}ms")
    
    # Print children
    for child in children.get(span['span_id'], []):
        print_tree(child, children, indent + 1)

def get_latest_trace():
    """Get the most recent trace ID"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASS, database=DB_NAME
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT trace_id, COUNT(*) as spans
        FROM telemetry_spans 
        GROUP BY trace_id 
        ORDER BY MAX(created_at) DESC 
        LIMIT 5
    """)
    
    traces = cur.fetchall()
    
    if not traces:
        print("❌ No traces found in database")
        return None
    
    print("\n📊 Recent Traces:")
    for i, (trace_id, span_count) in enumerate(traces, 1):
        print(f"  {i}. {trace_id} ({span_count} spans)")
    
    return traces[0][0]  # Return most recent

def view_trace(trace_id=None):
    """View hierarchical trace"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASS, database=DB_NAME
    )
    cur = conn.cursor()
    
    if not trace_id:
        trace_id = get_latest_trace()
        if not trace_id:
            return
    
    print(f"\n🔍 Trace: {trace_id}\n")
    
    # Get all spans for this trace
    cur.execute("""
        SELECT 
            span_id,
            parent_span_id,
            name,
            kind,
            start_ts,
            end_ts,
            duration_ms,
            agent_id,
            model_name,
            tokens_in,
            tokens_out
        FROM telemetry_spans
        WHERE trace_id = %s
        ORDER BY start_ts
    """, (trace_id,))
    
    rows = cur.fetchall()
    
    if not rows:
        print(f"❌ No spans found for trace {trace_id}")
        return
    
    # Convert to dicts
    spans = []
    for row in rows:
        spans.append({
            'span_id': row[0],
            'parent_span_id': row[1],
            'name': row[2],
            'kind': row[3],
            'start_ts': row[4],
            'end_ts': row[5],
            'duration_ms': row[6],
            'agent_id': row[7],
            'model_name': row[8],
            'tokens_in': row[9],
            'tokens_out': row[10]
        })
    
    # Build and print tree
    root, children = build_tree(spans)
    
    if root:
        print("🌳 Span Tree:\n")
        print_tree(root, children)
    else:
        print("⚠️  No root span found")
    
    # Print summary
    total_duration = sum(s['duration_ms'] or 0 for s in spans)
    total_tokens_in = sum(s['tokens_in'] or 0 for s in spans)
    total_tokens_out = sum(s['tokens_out'] or 0 for s in spans)
    
    print(f"\n📈 Summary:")
    print(f"  • Total Spans: {len(spans)}")
    print(f"  • Total Duration: {total_duration}ms")
    print(f"  • Tokens In: {total_tokens_in}")
    print(f"  • Tokens Out: {total_tokens_out}")
    
    # Print edges
    cur.execute("""
        SELECT from_agent_id, to_agent_id, channel, instruction_type
        FROM telemetry_edges
        WHERE from_span_id IN (
            SELECT span_id FROM telemetry_spans WHERE trace_id = %s
        )
    """, (trace_id,))
    
    edges = cur.fetchall()
    
    if edges:
        print(f"\n🔗 Inter-Agent Edges:")
        for from_agent, to_agent, channel, inst_type in edges:
            print(f"  • {from_agent[:20]}... → {to_agent[:20]}... [{inst_type}]")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    trace_id = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        view_trace(trace_id)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure postgres is exposed:")
        print("   kubectl port-forward svc/postgres 30432:5432 -n agentos")
