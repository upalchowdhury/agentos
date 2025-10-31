import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentAPI } from '../../lib/api';
import { Search } from 'lucide-react';
import { Link } from 'react-router-dom';

interface InvocationRow {
  invocation_id: string;
  agent_id: string;
  agent_name: string;
  status: string;
  started_at: string;
  execution_time_ms?: number;
  telemetry_quality?: string;
  trace_id?: string;
  requester_id?: string;
  caller_agent_id?: string | null;
  subject_type?: string;
}

export function InvocationsTable() {
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['observability-invocations', search],
    queryFn: async () => {
      const response = await agentAPI.runtime.getRecentInvocations({
        query: search.length ? search : undefined,
      });
      return response.data ?? [];
    },
  });

  const rows: InvocationRow[] = data ?? [];

  const getStatusColor = (status: string) => {
    const normalized = status.toUpperCase();
    switch (normalized) {
      case 'SUCCESS':
        return 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300';
      case 'ERROR':
      case 'FAILED':
        return 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300';
      case 'TIMEOUT':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300';
      case 'DENIED':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300';
    }
  };

  const prettyStatus = (status: string) =>
    status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch (error) {
      return timestamp;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <div className="flex justify-between p-6 pb-0 items-center">
        <h3 className="text-gray-900 dark:text-white text-lg font-bold">Recent Invocations</h3>
        <div className="relative w-full max-w-xs">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by agent, ID, or trace…"
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      <div className="overflow-x-auto">
        {isLoading ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">Loading invocations…</div>
        ) : rows.length === 0 ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">
            No recent invocations recorded.
          </div>
        ) : (
        <table className="w-full text-left">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Agent</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">
                Timestamp
              </th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Status</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Latency</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Telemetry</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Subject</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Requester</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Caller Agent</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {rows.map((invocation) => (
              <tr key={invocation.invocation_id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                <td className="p-4 text-sm text-gray-900 dark:text-white font-medium">
                  {invocation.agent_name}
                </td>
                <td className="p-4 text-sm text-gray-500 dark:text-gray-400">
                  {formatTime(invocation.started_at)}
                </td>
                <td className="p-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      invocation.status
                    )}`}
                  >
                    {prettyStatus(invocation.status)}
                  </span>
                </td>
                <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                  {invocation.execution_time_ms != null
                    ? `${invocation.execution_time_ms} ms`
                    : '—'}
                </td>
                <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      invocation.telemetry_quality === 'verified'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
                    }`}
                  >
                    {invocation.telemetry_quality === 'verified' ? 'Verified' : 'Partial'}
                  </span>
                </td>
                <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                  {invocation.subject_type ? invocation.subject_type.toUpperCase() : '—'}
                </td>
                <td className="p-4 text-xs text-gray-600 dark:text-gray-300 font-mono">
                  {invocation.requester_id ?? '—'}
                </td>
                <td className="p-4 text-xs text-gray-600 dark:text-gray-300 font-mono">
                  {invocation.caller_agent_id ?? '—'}
                </td>
                <td className="p-4 text-right">
                  {invocation.trace_id ? (
                    <Link
                      to={`/trace/${invocation.invocation_id}`}
                      className="text-blue-600 dark:text-blue-400 font-medium text-sm hover:underline"
                    >
                      View Trace
                    </Link>
                  ) : (
                    <span className="text-sm text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
      </div>
    </div>
  );
}
