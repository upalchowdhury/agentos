import React from 'react'
import { Link } from 'react-router-dom'

export default function Traces() {
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Traces</h1>
            <p>List of recent traces...</p>
            <ul className="list-disc pl-5 mt-4">
                <li><Link to="/traces/123" className="text-blue-500 hover:underline">Trace 123 (Mock)</Link></li>
            </ul>
        </div>
    )
}
