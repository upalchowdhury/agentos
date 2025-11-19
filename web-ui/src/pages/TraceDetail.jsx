import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Flamegraph from '../components/Flamegraph'
import SpanTable from '../components/SpanTable'

// Mock data generator
const generateMockTrace = (traceId) => {
    const now = Date.now()
    return {
        traceId,
        spans: [
            { spanId: '1', parentSpanId: null, name: 'agent_execution', kind: 'root', startTime: now, endTime: now + 1500, status: 'ok' },
            { spanId: '2', parentSpanId: '1', name: 'retrieve_context', kind: 'tool', startTime: now + 100, endTime: now + 300, status: 'ok' },
            { spanId: '3', parentSpanId: '1', name: 'llm_generation', kind: 'llm', startTime: now + 350, endTime: now + 1200, status: 'ok' },
            { spanId: '4', parentSpanId: '3', name: 'embedding_lookup', kind: 'tool', startTime: now + 400, endTime: now + 500, status: 'ok' },
            { spanId: '5', parentSpanId: '1', name: 'post_process', kind: 'internal', startTime: now + 1250, endTime: now + 1450, status: 'ok' },
        ]
    }
}

export default function TraceDetail() {
    const { traceId } = useParams()
    const [trace, setTrace] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Simulate API fetch
        setTimeout(() => {
            setTrace(generateMockTrace(traceId))
            setLoading(false)
        }, 500)
    }, [traceId])

    if (loading) return <div className="p-6 text-gray-400">Loading trace...</div>
    if (!trace) return <div className="p-6 text-red-400">Trace not found</div>

    return (
        <div className="p-6 space-y-6 bg-gray-950 min-h-screen text-gray-100">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">Trace: <span className="font-mono text-blue-400">{traceId}</span></h1>
                <div className="text-sm text-gray-400">
                    Duration: <span className="text-white font-medium">1500ms</span>
                </div>
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h2 className="text-lg font-semibold mb-4">Timeline</h2>
                <Flamegraph trace={trace} />
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h2 className="text-lg font-semibold mb-4">Spans</h2>
                <SpanTable spans={trace.spans} />
            </div>
        </div>
    )
}
