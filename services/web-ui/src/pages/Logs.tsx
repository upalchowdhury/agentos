import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentAPI } from '../lib/api';

export function Logs() {
  const [traceId, setTraceId] = useState('');
  const [agentId, setAgentId] = useState('');
  const [limit, setLimit] = useState(200);
  const [level, setLevel] = useState('');
  const [subjectType, setSubjectType] = useState('');
  const [requester, setRequester] = useState('');
  const [callerAgent, setCallerAgent] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['observability-logs', traceId, agentId, limit, level, subjectType, requester, callerAgent],
    queryFn: async () => {
      const response = await agentAPI.runtime.getLogs({
        trace_id: traceId || undefined,
        agent_id: agentId || undefined,
        limit,
        level: level || undefined,
        subject_type: subjectType || undefined,
        requester_id: requester || undefined,
        caller_agent_id: callerAgent || undefined,
      });
      return response.data ?? [];
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 dark:text-white">Logs</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Filter logs by trace ID to correlate events with specific invocations.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={traceId}
            onChange={(event) => setTraceId(event.target.value)}
            placeholder="Filter by trace ID"
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          />
          <input
            value={agentId}
            onChange={(event) => setAgentId(event.target.value)}
            placeholder="Filter by agent ID"
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          />
          <select
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          >
            {[50, 100, 200, 300, 500].map((option) => (
              <option key={option} value={option}>
                {option} rows
              </option>
            ))}
          </select>
          <select
            value={level}
            onChange={(event) => setLevel(event.target.value)}
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          >
            {['', 'INFO', 'WARNING', 'ERROR'].map((option) => (
              <option key={option || 'all'} value={option}>
                {option ? `${option} only` : 'All levels'}
              </option>
            ))}
          </select>
          <select
            value={subjectType}
            onChange={(event) => setSubjectType(event.target.value)}
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          >
            {['', 'user', 'agent'].map((option) => (
              <option key={option || 'any'} value={option}>
                {option ? `Subject: ${option.toUpperCase()}` : 'All subjects'}
              </option>
            ))}
          </select>
          <input
            value={requester}
            onChange={(event) => setRequester(event.target.value)}
            placeholder="Requester contains…"
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          />
          <input
            value={callerAgent}
            onChange={(event) => setCallerAgent(event.target.value)}
            placeholder="Caller agent contains…"
            className="h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          />
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">Loading logs…</div>
        ) : data.length === 0 ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">
            No logs found for the selected filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <HeaderCell>Timestamp</HeaderCell>
                  <HeaderCell>Level</HeaderCell>
                  <HeaderCell>Agent</HeaderCell>
                  <HeaderCell>Trace ID</HeaderCell>
                  <HeaderCell>Subject</HeaderCell>
                  <HeaderCell>Requester</HeaderCell>
                  <HeaderCell>Caller Agent</HeaderCell>
                  <HeaderCell>Message</HeaderCell>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {data.map((log: any, index: number) => (
                  <tr key={`${log.trace_id}-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                    <Cell>{formatTimestamp(log.timestamp)}</Cell>
                    <Cell>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          log.level === 'ERROR'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/60 dark:text-red-300'
                            : log.level === 'WARNING'
                            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/60 dark:text-yellow-300'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-200'
                        }`}
                      >
                        {log.level || 'INFO'}
                      </span>
                    </Cell>
                    <Cell>{log.agent_name}</Cell>
                    <Cell className="font-mono text-xs">{log.trace_id ?? '—'}</Cell>
                    <Cell>{log.subject_type ? log.subject_type.toUpperCase() : '—'}</Cell>
                    <Cell className="font-mono text-xs">{log.requester_id ?? '—'}</Cell>
                    <Cell className="font-mono text-xs">{log.caller_agent_id ?? '—'}</Cell>
                    <td className="p-4 text-sm text-gray-700 dark:text-gray-200">
                      <div>{log.message}</div>
                      {renderPolicyAlerts(log.policy_alerts)}
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

function HeaderCell({ children }: { children: React.ReactNode }) {
  return (
    <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase">
      {children}
    </th>
  );
}

function Cell({ children }: { children: React.ReactNode }) {
  return <td className="p-4 text-sm text-gray-600 dark:text-gray-300">{children}</td>;
}

function renderPolicyAlerts(alerts?: Record<string, any> | null): JSX.Element | null {
  if (!alerts || typeof alerts !== 'object') {
    return null;
  }
  const entries = Object.entries(alerts);
  if (!entries.length) {
    return null;
  }
  return (
    <div className="mt-2 space-y-1 text-xs text-amber-600 dark:text-amber-400">
      {entries.map(([name, value]) => {
        const flaggedCount = Array.isArray((value as any)?.flagged)
          ? (value as any).flagged.length
          : undefined;
        return (
          <div key={name} className="flex items-center gap-1">
            <span className="font-semibold">Policy Alert · {name}</span>
            {flaggedCount != null && flaggedCount > 0 && (
              <span>({flaggedCount} flagged)</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function formatTimestamp(value?: string) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
}
