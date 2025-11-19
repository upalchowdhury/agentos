import React from 'react'
import { useParams } from 'react-router-dom'

export default function AgentDetail() {
    const { agentId } = useParams()
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Agent: {agentId}</h1>
            <p>Details for agent {agentId}</p>
        </div>
    )
}
