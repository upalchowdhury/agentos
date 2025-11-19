import React from 'react'

export default function SpanTable({ spans }) {
    if (!spans) return null

    return (
        <div className="overflow-x-auto bg-gray-800 rounded-lg shadow">
            <table className="min-w-full text-left text-sm text-gray-300">
                <thead className="bg-gray-900 text-gray-400 uppercase text-xs font-medium">
                    <tr>
                        <th className="px-4 py-3">Span Name</th>
                        <th className="px-4 py-3">Kind</th>
                        <th className="px-4 py-3">Duration</th>
                        <th className="px-4 py-3">Start Time</th>
                        <th className="px-4 py-3">Status</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                    {spans.map((span) => (
                        <tr key={span.spanId} className="hover:bg-gray-700/50 transition-colors">
                            <td className="px-4 py-3 font-medium text-white">{span.name}</td>
                            <td className="px-4 py-3">
                                <span className={`px-2 py-0.5 rounded text-xs ${span.kind === 'llm' ? 'bg-purple-900 text-purple-200' :
                                        span.kind === 'tool' ? 'bg-blue-900 text-blue-200' :
                                            'bg-gray-700 text-gray-300'
                                    }`}>
                                    {span.kind}
                                </span>
                            </td>
                            <td className="px-4 py-3">{span.endTime - span.startTime}ms</td>
                            <td className="px-4 py-3 text-gray-500">{new Date(span.startTime).toLocaleTimeString()}</td>
                            <td className="px-4 py-3">
                                <span className={`px-2 py-0.5 rounded text-xs ${span.status === 'error' ? 'bg-red-900 text-red-200' : 'bg-green-900 text-green-200'
                                    }`}>
                                    {span.status || 'ok'}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
