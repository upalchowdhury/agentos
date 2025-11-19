import React from 'react'
import SequenceDiagram from '../components/SequenceDiagram'

export default function Sequence() {
    return (
        <div className="p-6 bg-gray-950 min-h-screen text-gray-100">
            <div className="mb-8">
                <h1 className="text-2xl font-bold mb-2">Cross-Platform Sequence Analysis</h1>
                <p className="text-gray-400">
                    Visualizing inter-agent communication across different platforms (Salesforce, GCP, Native).
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
                        <h2 className="text-lg font-semibold mb-4">Live Interaction Flow</h2>
                        <SequenceDiagram traceId="trace_demo_cross_platform" />
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                        <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Participating Agents</h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                <div>
                                    <div className="font-medium text-blue-400">Salesforce Service Bot</div>
                                    <div className="text-xs text-gray-500">Platform: Salesforce Agentforce</div>
                                </div>
                                <span className="px-2 py-1 text-xs bg-blue-900/30 text-blue-400 rounded border border-blue-800">External</span>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                <div>
                                    <div className="font-medium text-green-400">GCP Research Assistant</div>
                                    <div className="text-xs text-gray-500">Platform: GCP Agent Engine</div>
                                </div>
                                <span className="px-2 py-1 text-xs bg-green-900/30 text-green-400 rounded border border-green-800">External</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                        <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Governance Checks</h3>
                        <div className="space-y-3">
                            <div className="flex items-center text-sm">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                                <span className="text-gray-300">Authentication (mTLS)</span>
                                <span className="ml-auto text-green-500 text-xs">PASS</span>
                            </div>
                            <div className="flex items-center text-sm">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                                <span className="text-gray-300">Budget Cap ($5.00)</span>
                                <span className="ml-auto text-green-500 text-xs">PASS</span>
                            </div>
                            <div className="flex items-center text-sm">
                                <span className="w-2 h-2 bg-red-500 rounded-full mr-3"></span>
                                <span className="text-gray-300">PII Check (Credit Card)</span>
                                <span className="ml-auto text-red-500 text-xs">BLOCKED</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
