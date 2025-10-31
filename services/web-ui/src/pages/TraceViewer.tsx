import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { agentAPI } from '../lib/api';

const numberFormatter = new Intl.NumberFormat('en-US');

export function TraceViewer() {
  const { invocationId } = useParams<{ invocationId: string }>();
  const navigate = useNavigate();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['trace-details', invocationId],
    enabled: Boolean(invocationId),
    queryFn: async () => {
      const response = await agentAPI.runtime.getTraceDetails(invocationId!);
      return response.data;
    },
  });

  const steps = useMemo(() => data?.steps ?? [], [data]);
  const logs = useMemo(() => data?.logs ?? [], [data]);
  const actor = data?.actor ?? null;
  const policy = data?.policy ?? null;
  const policyAlerts = data?.policy_alerts ?? null;

  const obligations = useMemo(() => {
    if (!policy || !policy.obligations) return [] as Array<[string, any]>;
    return Object.entries(policy.obligations);
  }, [policy]);

  const enforcement = useMemo(() => {
    if (!policy || !policy.enforcement) return [] as Array<[string, any]>;
    return Object.entries(policy.enforcement);
  }, [policy]);

  const policyAlertEntries = useMemo(() => {
    if (!policyAlerts) return [] as Array<[string, any]>;
    return Object.entries(policyAlerts);
  }, [policyAlerts]);

  const hasPolicyDetails =
    obligations.length > 0 ||
    enforcement.length > 0 ||
    policyAlertEntries.length > 0;

  const obligationSummary = obligations.length
    ? obligations
        .map(([name, value]) =>
          typeof value === 'boolean'
            ? `${name}:${value ? 'on' : 'off'}`
            : `${name}`
        )
        .join(', ')
    : 'None';

  const policyAlertSummary = policyAlertEntries.length
    ? policyAlertEntries.map(([name]) => name).join(', ')
    : 'None';

  const formatEnforcementValue = (name: string, value: any) => {
    if (value == null) return '—';
    if (name === 'pii_redaction') {
      const matches = value.total_matches ?? value.matches?.length ?? 0;
      return matches
        ? `${matches} match${matches === 1 ? '' : 'es'} redacted`
        : 'No matches redacted';
    }
    if (name === 'content_filter') {
      const flagged = Array.isArray(value.flagged) ? value.flagged.length : 0;
      return flagged
        ? `${flagged} flagged term${flagged === 1 ? '' : 's'}`
        : 'No flags';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '—';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Back
          </button>
          <h1 className="text-3xl font-bold mt-2">
            Trace Details
          </h1>
          {data && (
            <p className="text-gray-500 dark:text-gray-400">
              Invocation <span className="font-mono">{data.invocation_id}</span>
            </p>
          )}
        </div>
        {data && (
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
              data.telemetry_quality === 'verified'
                ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
            }`}
          >
            {data.telemetry_quality === 'verified' ? 'Verified Telemetry' : 'Partial Telemetry'}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="text-sm text-gray-500 dark:text-gray-400">Loading trace…</div>
      ) : isError || !data ? (
        <div className="text-sm text-red-500">
          Unable to load trace details. Please try again later.
        </div>
      ) : (
        <div className="space-y-6">
          <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-300">
              <SummaryItem label="Agent" value={data.agent_name} />
              <SummaryItem label="Status" value={data.status} />
              <SummaryItem label="Start" value={formatTimestamp(data.start_ts)} />
              <SummaryItem label="End" value={formatTimestamp(data.end_ts)} />
              <SummaryItem
                label="Execution Time"
                value={
                  data.execution_time_ms != null
                    ? `${numberFormatter.format(data.execution_time_ms)} ms`
                    : '—'
                }
              />
              <SummaryItem
                label="Cost"
                value={`$${numberFormatter.format(data.cost_usd ?? 0)}`}
              />
              <SummaryItem label="Trace ID" value={data.trace_id} />
              <SummaryItem
                label="Subject"
                value={actor?.subject_type ? actor.subject_type.toUpperCase() : '—'}
              />
              <SummaryItem label="Requester" value={data.requester_id ?? '—'} />
              <SummaryItem label="Caller Agent" value={data.caller_agent_id ?? '—'} />
              <SummaryItem label="Policy Obligations" value={obligationSummary || 'None'} />
              <SummaryItem label="Policy Alerts" value={policyAlertSummary || 'None'} />
            </div>
          </section>

          {hasPolicyDetails && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <h2 className="text-lg font-semibold p-6 pb-0">Policy Enforcement</h2>
              <div className="p-6 space-y-4 text-sm text-gray-600 dark:text-gray-300">
                {obligations.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-xs uppercase tracking-wide">
                      Obligations
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {obligations.map(([name, value]) => (
                        <span
                          key={name}
                          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                            value
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
                              : 'bg-gray-100 text-gray-700 dark:bg-gray-900/50 dark:text-gray-300'
                          }`}
                        >
                          {name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {enforcement.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-xs uppercase tracking-wide">
                      Enforcement Summary
                    </h3>
                    <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
                      {enforcement.map(([name, value]) => (
                        <li key={name} className="flex items-start gap-2">
                          <span className="font-medium text-gray-700 dark:text-gray-200">{name}</span>
                          <span className="text-gray-500 dark:text-gray-400">{formatEnforcementValue(name, value)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {policyAlertEntries.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-xs uppercase tracking-wide">
                      Alerts
                    </h3>
                    <ul className="space-y-1 text-sm text-amber-600 dark:text-amber-400">
                      {policyAlertEntries.map(([name, value]) => (
                        <li key={name}>
                          {name}: {Array.isArray(value?.flagged) ? `${value.flagged.length} flag${value.flagged.length === 1 ? '' : 's'}` : JSON.stringify(value)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </section>
          )}

          <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <h2 className="text-lg font-semibold p-6 pb-0">Trace Steps</h2>
            {steps.length === 0 ? (
              <div className="p-6 text-sm text-gray-500 dark:text-gray-400">
                No detailed steps were captured for this invocation.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-gray-50 dark:bg-gray-900/50">
                    <tr>
                      <HeaderCell>Step</HeaderCell>
                      <HeaderCell>Type</HeaderCell>
                      <HeaderCell>Status</HeaderCell>
                      <HeaderCell>Latency</HeaderCell>
                      <HeaderCell>Input</HeaderCell>
                      <HeaderCell>Output</HeaderCell>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {steps.map((step) => (
                      <tr key={step.step_id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                        <Cell>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {step.name}
                          </div>
                          {step.parent_step_id && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Parent: {step.parent_step_id}
                            </div>
                          )}
                        </Cell>
                        <Cell>{step.kind}</Cell>
                        <Cell>{step.status}</Cell>
                        <Cell>
                          {step.latency_ms != null
                            ? `${numberFormatter.format(step.latency_ms)} ms`
                            : '—'}
                        </Cell>
                        <Cell>
                          <CodeBlock>{step.input_excerpt ?? '—'}</CodeBlock>
                        </Cell>
                        <Cell>
                          <CodeBlock>{step.output_excerpt ?? '—'}</CodeBlock>
                        </Cell>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <h2 className="text-lg font-semibold p-6 pb-0">Logs</h2>
            {logs.length === 0 ? (
              <div className="p-6 text-sm text-gray-500 dark:text-gray-400">
                No logs were captured for this trace.
              </div>
            ) : (
              <ul className="p-6 space-y-4 text-sm text-gray-700 dark:text-gray-200">
                {logs.map((log, index) => (
                  <li key={index} className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                        {formatTimestamp(log.timestamp)}
                      </div>
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
                    </div>
                    <pre className="bg-white dark:bg-gray-900/60 rounded-md px-3 py-2 text-xs text-gray-800 dark:text-gray-100 whitespace-pre-wrap break-words">
                      {log.message || '—'}
                    </pre>
                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-gray-500 dark:text-gray-400">
                      <span className="font-mono">Trace: {log.trace_id ?? '—'}</span>
                      <span className="font-mono">Requester: {log.requester_id ?? '—'}</span>
                      <span className="font-mono">Caller: {log.caller_agent_id ?? '—'}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase text-gray-400 dark:text-gray-500">{label}</p>
      <p className="text-sm text-gray-900 dark:text-white font-medium break-all">{value}</p>
    </div>
  );
}

function HeaderCell({ children }: { children: React.ReactNode }) {
  return (
    <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">
      {children}
    </th>
  );
}

function Cell({ children }: { children: React.ReactNode }) {
  return (
    <td className="p-4 text-sm text-gray-600 dark:text-gray-300 align-top">
      {children}
    </td>
  );
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <pre className="bg-gray-100 dark:bg-gray-900/60 rounded-md px-3 py-2 text-xs text-gray-700 dark:text-gray-200 overflow-x-auto max-w-xs">
      {children}
    </pre>
  );
}
