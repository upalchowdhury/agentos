import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Plus } from 'lucide-react';
import { agentAPI } from '../lib/api';
import { useNavigate } from 'react-router-dom';

export function AgentRegistry() {
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentAPI.identity.listDIDs(),
  });

  const filteredAgents = agents?.data?.documents?.filter((agent: any) =>
    agent.id.toLowerCase().includes(search.toLowerCase()) ||
    agent.metadata?.name?.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Agent Registry</h1>
        <button
          onClick={() => navigate('/register-agent')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Register New Agent
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search agents by name, DID, or capability..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Agent Grid */}
      {isLoading ? (
        <div>Loading agents...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent: any) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );
}

function AgentCard({ agent }: { agent: any }) {
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 cursor-pointer">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-lg">{agent.metadata?.name || agent.id}</h3>
          <p className="text-xs text-gray-500 truncate">{agent.id}</p>
        </div>
        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
          Active
        </span>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        {agent.metadata?.description || 'No description provided'}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {agent.metadata?.tags?.map((tag: string) => (
          <span key={tag} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
            {tag}
          </span>
        ))}
      </div>

      <div className="border-t pt-4 space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Created</span>
          <span className="font-medium">
            {new Date(agent.metadata?.created).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button className="flex-1 bg-gray-100 text-gray-700 py-2 rounded hover:bg-gray-200">
          Details
        </button>
        <button className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
          Configure
        </button>
      </div>
    </div>
  );
}
