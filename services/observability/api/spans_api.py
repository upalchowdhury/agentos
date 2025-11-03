"""
Span-level API endpoints for ATP v0.1
Provides access to spans and edges for flamegraph and sequence diagrams
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import psycopg2
import os

router = APIRouter(prefix="/v1/spans", tags=["spans"])

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres.agentos.svc.cluster.local"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "agentos")
    )

@router.get("/{span_id}")
async def get_span(span_id: str):
    """Get detailed span information by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                span_id, trace_id, parent_span_id, invocation_id, name, kind,
                start_ts, end_ts, duration_ms, status,
                agent_id, version_id,
                model_provider, model_name, model_temperature, model_top_p, model_seed, model_max_tokens,
                tokens_in, tokens_out, input_excerpt, output_excerpt,
                content_hash_in, content_hash_out, signature_verified,
                tool_call_id, tool_name, tool_args_excerpt, tool_return_excerpt,
                policy_enforced, policy_obligations, redaction_mask_ids, budget_enforced_cents, policy_allow,
                network_protocol, remote_agent_id, remote_version_id, request_id, edge_id,
                error_type, error_message, created_at
            FROM telemetry_spans
            WHERE span_id = %s
        """, (span_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Span not found")
        
        return {
            "span_id": row[0],
            "trace_id": row[1],
            "parent_span_id": row[2],
            "invocation_id": row[3],
            "name": row[4],
            "kind": row[5],
            "start_ts": row[6].isoformat() if row[6] else None,
            "end_ts": row[7].isoformat() if row[7] else None,
            "duration_ms": row[8],
            "status": row[9],
            "agent": {
                "agent_id": row[10],
                "version_id": row[11]
            },
            "model": {
                "provider": row[12],
                "name": row[13],
                "parameters": {
                    "temperature": row[14],
                    "top_p": row[15],
                    "seed": row[16],
                    "max_tokens": row[17]
                }
            } if row[12] else None,
            "io": {
                "tokens_in": row[18],
                "tokens_out": row[19],
                "input_excerpt": row[20],
                "output_excerpt": row[21],
                "content_hash_in": row[22],
                "content_hash_out": row[23],
                "signature_verified": row[24]
            },
            "tool": {
                "call_id": row[25],
                "name": row[26],
                "args_excerpt": row[27],
                "return_excerpt": row[28]
            } if row[25] else None,
            "policy": {
                "policy_enforced": row[29] or [],
                "obligations": row[30] or [],
                "redaction_mask_ids": row[31] or [],
                "budget_enforced_cents": row[32],
                "allow": row[33]
            },
            "network": {
                "protocol": row[34],
                "remote_agent_id": row[35],
                "remote_version_id": row[36],
                "request_id": row[37],
                "edge_id": row[38]
            } if row[34] else None,
            "error_type": row[39],
            "error_message": row[40],
            "created_at": row[41].isoformat() if row[41] else None
        }
    finally:
        cur.close()
        conn.close()

@router.get("")
async def get_spans(
    trace_id: Optional[str] = Query(None),
    invocation_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get spans with filtering"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        where_clauses = []
        params = []
        
        if trace_id:
            where_clauses.append("trace_id = %s")
            params.append(trace_id)
        if invocation_id:
            where_clauses.append("invocation_id = %s")
            params.append(invocation_id)
        if agent_id:
            where_clauses.append("agent_id = %s")
            params.append(agent_id)
        if kind:
            where_clauses.append("kind = %s")
            params.append(kind)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
        params.append(limit)
        
        cur.execute(f"""
            SELECT 
                span_id, trace_id, parent_span_id, name, kind, start_ts, end_ts,
                duration_ms, status, agent_id, version_id, model_provider, model_name,
                tokens_in, tokens_out, tool_name, error_type, error_message
            FROM telemetry_spans
            WHERE {where_sql}
            ORDER BY start_ts DESC
            LIMIT %s
        """, params)
        
        spans = []
        for row in cur.fetchall():
            spans.append({
                "span_id": row[0],
                "trace_id": row[1],
                "parent_span_id": row[2],
                "name": row[3],
                "kind": row[4],
                "start_ts": row[5].isoformat() if row[5] else None,
                "end_ts": row[6].isoformat() if row[6] else None,
                "duration_ms": row[7],
                "status": row[8],
                "agent_id": row[9],
                "version_id": row[10],
                "model_provider": row[11],
                "model_name": row[12],
                "tokens_in": row[13],
                "tokens_out": row[14],
                "tool_name": row[15],
                "error_type": row[16],
                "error_message": row[17]
            })
        
        return spans
    finally:
        cur.close()
        conn.close()

@router.get("/edges")
async def get_edges(
    trace_id: Optional[str] = Query(None),
    from_agent_id: Optional[str] = Query(None),
    to_agent_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get inter-agent edges"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        where_clauses = []
        params = []
        
        if from_agent_id:
            where_clauses.append("from_agent_id = %s")
            params.append(from_agent_id)
        if to_agent_id:
            where_clauses.append("to_agent_id = %s")
            params.append(to_agent_id)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
        params.append(limit)
        
        cur.execute(f"""
            SELECT 
                edge_id, time, from_agent_id, from_version_id, from_span_id,
                to_agent_id, to_version_id, to_span_id, channel, instruction_type,
                size_bytes, redaction_applied, signature_verified, content_hash
            FROM telemetry_edges
            WHERE {where_sql}
            ORDER BY time DESC
            LIMIT %s
        """, params)
        
        edges = []
        for row in cur.fetchall():
            edges.append({
                "edge_id": row[0],
                "time": row[1].isoformat() if row[1] else None,
                "from_agent_id": row[2],
                "from_version_id": row[3],
                "from_span_id": row[4],
                "to_agent_id": row[5],
                "to_version_id": row[6],
                "to_span_id": row[7],
                "channel": row[8],
                "instruction_type": row[9],
                "size_bytes": row[10],
                "redaction_applied": row[11],
                "signature_verified": row[12],
                "content_hash": row[13]
            })
        
        return edges
    finally:
        cur.close()
        conn.close()

@router.get("/{edge_id}")
async def get_edge(edge_id: str):
    """Get detailed edge information by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                edge_id, time, from_agent_id, from_version_id, from_span_id,
                to_agent_id, to_version_id, to_span_id, channel, instruction_type,
                size_bytes, redaction_applied, signature_verified, content_hash, created_at
            FROM telemetry_edges
            WHERE edge_id = %s
        """, (edge_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Edge not found")
        
        return {
            "edge_id": row[0],
            "time": row[1].isoformat() if row[1] else None,
            "from_agent_id": row[2],
            "from_version_id": row[3],
            "from_span_id": row[4],
            "to_agent_id": row[5],
            "to_version_id": row[6],
            "to_span_id": row[7],
            "channel": row[8],
            "instruction_type": row[9],
            "size_bytes": row[10],
            "redaction_applied": row[11],
            "signature_verified": row[12],
            "content_hash": row[13],
            "created_at": row[14].isoformat() if row[14] else None
        }
    finally:
        cur.close()
        conn.close()
