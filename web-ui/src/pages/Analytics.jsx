import React, { useState, useEffect } from 'react'

// Mock data
const MOCK_RISK = {
    piiDetectionRate: 0.05,
    policyViolationRate: 0.02,
    riskScore: 15,
    incidents: 3,
    topRisks: [
        { category: 'PII Leak', count: 12 },
        { category: 'Prompt Injection', count: 5 },
        { category: 'Unauthorized Tool', count: 2 },
    ]
}

const MOCK_ROI = {
    totalCost: 1250.50,
    estimatedValue: 5000.00,
    roiPercentage: 300,
    savings: 3749.50,
    currency: 'USD'
}

const Card = ({ title, children, className = '' }) => (
    <div className={`bg-gray-900 rounded-xl border border-gray-800 p-6 ${className}`}>
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-4">{title}</h3>
        {children}
    </div>
)

const Stat = ({ label, value, subtext, color = 'text-white' }) => (
    <div>
        <div className="text-gray-500 text-xs mb-1">{label}</div>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        {subtext && <div className="text-gray-600 text-xs mt-1">{subtext}</div>}
    </div>
)

export default function Analytics() {
    const [risk, setRisk] = useState(null)
    const [roi, setRoi] = useState(null)

    useEffect(() => {
        // Simulate API fetch
        setTimeout(() => {
            setRisk(MOCK_RISK)
            setRoi(MOCK_ROI)
        }, 500)
    }, [])

    if (!risk || !roi) return <div className="p-6 text-gray-400">Loading analytics...</div>

    return (
        <div className="p-6 bg-gray-950 min-h-screen text-gray-100">
            <h1 className="text-2xl font-bold mb-6">Advanced Analytics</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* ROI Section */}
                <Card title="Return on Investment (ROI)">
                    <div className="grid grid-cols-2 gap-6 mb-6">
                        <Stat
                            label="Total Cost"
                            value={`$${roi.totalCost.toLocaleString()}`}
                            subtext="Last 30 days"
                        />
                        <Stat
                            label="Estimated Value"
                            value={`$${roi.estimatedValue.toLocaleString()}`}
                            color="text-green-400"
                            subtext="Based on task completion"
                        />
                        <Stat
                            label="Net Savings"
                            value={`$${roi.savings.toLocaleString()}`}
                            color="text-blue-400"
                        />
                        <Stat
                            label="ROI"
                            value={`${roi.roiPercentage}%`}
                            color="text-purple-400"
                        />
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden flex">
                        <div style={{ width: '25%' }} className="bg-red-500 h-full" title="Cost"></div>
                        <div style={{ width: '75%' }} className="bg-green-500 h-full" title="Value"></div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>Cost</span>
                        <span>Value Generated</span>
                    </div>
                </Card>

                {/* Risk Section */}
                <Card title="Risk & Compliance">
                    <div className="flex items-center justify-between mb-6">
                        <div className="relative w-24 h-24 flex items-center justify-center">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-gray-800" />
                                <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-yellow-500" strokeDasharray={`${risk.riskScore * 2.51} 251`} />
                            </svg>
                            <div className="absolute text-xl font-bold">{risk.riskScore}</div>
                        </div>
                        <div className="flex-1 ml-8 grid grid-cols-2 gap-4">
                            <Stat label="PII Rate" value={`${(risk.piiDetectionRate * 100).toFixed(1)}%`} />
                            <Stat label="Violations" value={`${(risk.policyViolationRate * 100).toFixed(1)}%`} />
                            <Stat label="Incidents" value={risk.incidents} color="text-red-400" />
                        </div>
                    </div>
                    <div>
                        <h4 className="text-xs text-gray-500 mb-2">Top Risk Categories</h4>
                        <div className="space-y-2">
                            {risk.topRisks.map(r => (
                                <div key={r.category} className="flex justify-between text-sm">
                                    <span className="text-gray-300">{r.category}</span>
                                    <span className="text-gray-500">{r.count} events</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </Card>
            </div>

            {/* Policy Drift Section */}
            <Card title="Policy Drift Detection">
                <div className="overflow-x-auto">
                    <table className="min-w-full text-left text-sm text-gray-300">
                        <thead className="bg-gray-800 text-xs uppercase font-medium text-gray-400">
                            <tr>
                                <th className="px-4 py-3">Agent</th>
                                <th className="px-4 py-3">Policy</th>
                                <th className="px-4 py-3">Trend</th>
                                <th className="px-4 py-3">Current Rate</th>
                                <th className="px-4 py-3">Change</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            <tr className="hover:bg-gray-800/50">
                                <td className="px-4 py-3 font-medium text-white">customer-service-bot</td>
                                <td className="px-4 py-3">No PII (Email)</td>
                                <td className="px-4 py-3 text-red-400">Increasing</td>
                                <td className="px-4 py-3">5.2%</td>
                                <td className="px-4 py-3 text-red-400">+2.1%</td>
                            </tr>
                            <tr className="hover:bg-gray-800/50">
                                <td className="px-4 py-3 font-medium text-white">sales-agent</td>
                                <td className="px-4 py-3">Approved Tools Only</td>
                                <td className="px-4 py-3 text-green-400">Decreasing</td>
                                <td className="px-4 py-3">0.5%</td>
                                <td className="px-4 py-3 text-green-400">-1.2%</td>
                            </tr>
                            <tr className="hover:bg-gray-800/50">
                                <td className="px-4 py-3 font-medium text-white">analyst-agent</td>
                                <td className="px-4 py-3">Max Token Limit</td>
                                <td className="px-4 py-3 text-gray-400">Stable</td>
                                <td className="px-4 py-3">1.0%</td>
                                <td className="px-4 py-3 text-gray-400">0.0%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    )
}
