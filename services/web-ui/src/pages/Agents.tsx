import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentAPI } from '../lib/api';

const numberFormatter = new Intl.NumberFormat('en-US');
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 4,
});

export function Agents() {
  const [showRegistrationMenu, setShowRegistrationMenu] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['agents-list'],
    queryFn: async () => {
      const response = await agentAPI.runtime.getObservabilityAgents('30d');
      return response.data ?? [];
    },
  });

  const agents = data ?? [];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-black text-gray-900 dark:text-white">Agents</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Manage your deployed and external agents
          </p>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowRegistrationMenu(!showRegistrationMenu)}
            className="flex items-center justify-center rounded-lg h-10 px-4 bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors"
          >
            Register New Agent
          </button>
          {showRegistrationMenu && (
            <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
              <Link
                to="/deploy"
                onClick={() => setShowRegistrationMenu(false)}
                className="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-900 border-b border-gray-200 dark:border-gray-700"
              >
                <div className="font-semibold text-gray-900 dark:text-white">Model A (Deploy Code)</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Deploy agent code on AgentOS</div>
              </Link>
              <Link
                to="/register-external"
                onClick={() => setShowRegistrationMenu(false)}
                className="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-900"
              >
                <div className="font-semibold text-gray-900 dark:text-white">Model B (External Endpoint)</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Connect external agent via HTTP</div>
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            All Agents ({agents.length})
          </h2>
        </div>
        {isLoading ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">Loading agents...</div>
        ) : agents.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No agents registered yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              Get started by registering your first agent
            </p>
            <div className="flex gap-4 justify-center">
              <Link
                to="/deploy"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700"
              >
                Deploy Code (Model A)
              </Link>
              <Link
                to="/register-external"
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-lg text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                Register External (Model B)
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Agent Name</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Type</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Status</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Telemetry</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Invocations</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Success Rate</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Cost</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {agents.map((agent: any) => (
                  <tr key={agent.agent_id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                    <td className="p-4 text-sm font-medium text-gray-900 dark:text-white">
                      {agent.name || agent.agent_id}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                        {agent.model_type || 'Unknown'}
                      </span>
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        agent.status === 'RUNNING' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300'
                      }`}>
                        {agent.status || 'Unknown'}
                      </span>
                    </td>
                    <td className="p-4 text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        agent.telemetry_quality === 'verified'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
                      }`}>
                        {agent.telemetry_quality === 'verified' ? 'Verified' : 'Partial'}
                      </span>
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {numberFormatter.format(agent.total_invocations ?? 0)}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {((agent.success_rate ?? 0) * 100).toFixed(1)}%
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {currencyFormatter.format(agent.cost_usd ?? 0)}
                    </td>
                    <td className="p-4 text-sm">
                      <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium">
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
