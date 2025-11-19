import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

// Mock data
const MOCK_VERSIONS = [
    { id: 'v2', version: 'v1.1', content: 'You are a helpful assistant. Answer concisely.', author: 'alice@example.com', createdAt: '2025-11-18T10:00:00Z' },
    { id: 'v1', version: 'v1.0', content: 'You are a helpful assistant.', author: 'bob@example.com', createdAt: '2025-11-17T09:00:00Z' },
]

export default function PromptDetail() {
    const { promptId } = useParams()
    const [versions, setVersions] = useState([])
    const [selectedVersion, setSelectedVersion] = useState(null)

    useEffect(() => {
        // Simulate API fetch
        setVersions(MOCK_VERSIONS)
        setSelectedVersion(MOCK_VERSIONS[0])
    }, [promptId])

    if (!selectedVersion) return <div className="p-6 text-gray-400">Loading...</div>

    return (
        <div className="p-6 bg-gray-950 min-h-screen text-gray-100">
            <div className="mb-6">
                <h1 className="text-2xl font-bold mb-1">Prompt: <span className="text-blue-400">customer-service-greeting</span></h1>
                <p className="text-gray-400 text-sm">ID: {promptId}</p>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Version List */}
                <div className="col-span-3 bg-gray-900 rounded-lg border border-gray-800 p-4">
                    <h2 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">Versions</h2>
                    <div className="space-y-2">
                        {versions.map((v) => (
                            <div
                                key={v.id}
                                onClick={() => setSelectedVersion(v)}
                                className={`p-3 rounded cursor-pointer transition-colors ${selectedVersion.id === v.id
                                        ? 'bg-blue-900/30 border border-blue-700/50'
                                        : 'bg-gray-800/50 hover:bg-gray-800 border border-transparent'
                                    }`}
                            >
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-mono text-sm font-bold text-blue-300">{v.version}</span>
                                    <span className="text-xs text-gray-500">{new Date(v.createdAt).toLocaleDateString()}</span>
                                </div>
                                <div className="text-xs text-gray-400 truncate">by {v.author}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Content / Diff */}
                <div className="col-span-9 space-y-6">
                    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold">Content</h2>
                            <div className="flex space-x-2">
                                <button className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium transition-colors">
                                    Copy
                                </button>
                                <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition-colors">
                                    Use in Playground
                                </button>
                            </div>
                        </div>
                        <div className="bg-gray-950 p-4 rounded border border-gray-800 font-mono text-sm text-gray-300 whitespace-pre-wrap">
                            {selectedVersion.content}
                        </div>
                    </div>

                    {/* Variables */}
                    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                        <h2 className="text-lg font-semibold mb-4">Variables</h2>
                        <div className="flex flex-wrap gap-2">
                            <span className="px-2 py-1 bg-gray-800 rounded text-xs font-mono text-yellow-400">None detected</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
