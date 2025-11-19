import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

// Mock data
const MOCK_PROMPTS = [
    { id: '1', name: 'customer-service-greeting', description: 'Initial greeting for support bot', updatedAt: '2025-11-18T10:00:00Z' },
    { id: '2', name: 'sql-generator', description: 'Text to SQL conversion prompt', updatedAt: '2025-11-17T15:30:00Z' },
    { id: '3', name: 'summary-helper', description: 'Summarize long documents', updatedAt: '2025-11-16T09:15:00Z' },
]

export default function Prompts() {
    const [prompts, setPrompts] = useState([])

    useEffect(() => {
        // Simulate API fetch
        setPrompts(MOCK_PROMPTS)
    }, [])

    return (
        <div className="p-6 bg-gray-950 min-h-screen text-gray-100">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Prompts</h1>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                    New Prompt
                </button>
            </div>

            <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-800">
                    <thead className="bg-gray-950">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Description</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Last Updated</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                        {prompts.map((prompt) => (
                            <tr key={prompt.id} className="hover:bg-gray-800/50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <Link to={`/prompts/${prompt.id}`} className="text-blue-400 hover:text-blue-300 font-medium">
                                        {prompt.name}
                                    </Link>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-300">{prompt.description}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(prompt.updatedAt).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <Link to={`/prompts/${prompt.id}`} className="text-gray-400 hover:text-white">
                                        View
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
