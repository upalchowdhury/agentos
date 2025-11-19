import React from 'react'

const SpanBar = ({ span, startTime, totalDuration, depth = 0 }) => {
    const offset = span.startTime - startTime
    const duration = span.endTime - span.startTime
    const leftPct = (offset / totalDuration) * 100
    const widthPct = Math.max((duration / totalDuration) * 100, 0.5) // Min width for visibility

    // Color based on status or kind
    const bgColor = span.status === 'error' ? 'bg-red-500' :
        span.kind === 'llm' ? 'bg-purple-500' :
            span.kind === 'tool' ? 'bg-blue-500' : 'bg-green-500'

    return (
        <div className="relative h-8 mb-1 group">
            <div
                className={`absolute h-full rounded ${bgColor} opacity-80 hover:opacity-100 transition-all cursor-pointer border border-white/10`}
                style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                title={`${span.name} (${duration}ms)`}
            >
                <div className="px-2 py-1 text-xs text-white truncate overflow-hidden whitespace-nowrap">
                    {span.name} <span className="opacity-75">({duration}ms)</span>
                </div>
            </div>
        </div>
    )
}

export default function Flamegraph({ trace }) {
    if (!trace || !trace.spans) return <div>No trace data</div>

    const rootSpan = trace.spans.find(s => !s.parentSpanId) || trace.spans[0]
    const startTime = rootSpan.startTime
    const endTime = Math.max(...trace.spans.map(s => s.endTime))
    const totalDuration = endTime - startTime

    // Sort spans by start time
    const sortedSpans = [...trace.spans].sort((a, b) => a.startTime - b.startTime)

    return (
        <div className="w-full bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <div className="min-w-[800px]">
                <div className="flex justify-between text-xs text-gray-400 mb-2 border-b border-gray-700 pb-1">
                    <span>0ms</span>
                    <span>{totalDuration}ms</span>
                </div>
                <div className="space-y-1">
                    {sortedSpans.map(span => (
                        <SpanBar
                            key={span.spanId}
                            span={span}
                            startTime={startTime}
                            totalDuration={totalDuration}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}
