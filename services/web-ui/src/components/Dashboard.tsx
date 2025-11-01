import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { StatCard } from './Dashboard/StatCard';
import { ChartCard } from './Dashboard/ChartCard';
import { InvocationsTable } from './Dashboard/InvocationsTable';
import { agentAPI } from '../lib/api';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  style: 'percent',
  maximumFractionDigits: 1,
});
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
});

const rangeOptions: { label: string; value: string }[] = [
  { label: 'Last 1h', value: '1h' },
  { label: 'Last 6h', value: '6h' },
  { label: 'Last 12h', value: '12h' },
  { label: 'Last 24h', value: '1d' },
  { label: 'Last 7d', value: '7d' },
  { label: 'Last 30d', value: '30d' },
];

export function Dashboard() {
  const [range, setRange] = useState('1d');
  const [isExporting, setIsExporting] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['observability-agents', range],
    queryFn: async () => {
      const response = await agentAPI.runtime.getObservabilityAgents(range);
      return response.data ?? [];
    },
  });

  const handleExportAudit = async () => {
    try {
      setIsExporting(true);
      const response = await agentAPI.runtime.exportAudit();
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `audit_export_${timestamp}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export audit logs:', error);
      alert('Failed to export audit logs. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const summaries = data ?? [];

  const totalAgents = summaries.length;
  const totalInvocations = summaries.reduce((sum: number, item: any) => sum + (item.total_invocations ?? 0), 0);
  const totalCost = summaries.reduce((sum: number, item: any) => sum + (item.cost_usd ?? 0), 0);
  const verifiedCount = summaries.filter((item: any) => item.telemetry_quality === 'verified').length;
  const totalDenied = summaries.reduce((sum: number, item: any) => sum + (item.denied_invocations ?? 0), 0);
  const totalPolicyAlerts = summaries.reduce((sum: number, item: any) => sum + (item.policy_alerts_count ?? 0), 0);
  const avgSuccessRate = totalAgents
    ? summaries.reduce((sum: number, item: any) => sum + (item.success_rate ?? 0), 0) / totalAgents
    : 0;

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <p className="text-gray-900 dark:text-white text-3xl font-black leading-tight">
          Dashboard
        </p>
        <div className="flex items-center gap-4">
          <select
            value={range}
            onChange={(event) => setRange(event.target.value)}
            className="h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm px-3"
          >
            {rangeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleExportAudit}
            disabled={isExporting}
            className="flex min-w-[84px] items-center justify-center rounded-lg h-10 px-4 bg-green-600 text-white text-sm font-bold hover:bg-green-700 disabled:bg-gray-400 transition-colors"
          >
            <span className="truncate">{isExporting ? 'Exporting...' : 'Export Audit'}</span>
          </button>
          <Link
            to="/agents"
            className="flex min-w-[84px] items-center justify-center rounded-lg h-10 px-4 bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-white text-sm font-bold hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            <span className="truncate">View All Agents</span>
          </Link>
          <Link
            to="/deploy"
            className="flex min-w-[84px] items-center justify-center rounded-lg h-10 px-4 bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors"
          >
            <span className="truncate">Deploy Agent</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          title="Total Agents"
          value={numberFormatter.format(totalAgents)}
          change="—"
        />
        <StatCard
          title="Verified Telemetry"
          value={`${verifiedCount}/${totalAgents || 1}`}
          change="—"
          isPositive={verifiedCount === totalAgents}
        />
        <StatCard
          title="Total Invocations"
          value={numberFormatter.format(totalInvocations)}
          change="—"
        />
        <StatCard
          title="Total Cost"
          value={currencyFormatter.format(totalCost)}
          change="—"
        />
        <StatCard
          title="Denied Invocations"
          value={numberFormatter.format(totalDenied)}
          change="—"
          isPositive={totalDenied === 0}
        />
        <StatCard
          title="Policy Alerts"
          value={numberFormatter.format(totalPolicyAlerts)}
          change="—"
          isPositive={totalPolicyAlerts === 0}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ChartCard
          title="Invocations"
          value={numberFormatter.format(totalInvocations)}
          timeRange={rangeOptions.find((option) => option.value === range)?.label ?? 'Selected range'}
          change="—"
        />
        <ChartCard
          title="Average Success Rate"
          value={percentFormatter.format(avgSuccessRate || 0)}
          timeRange={rangeOptions.find((option) => option.value === range)?.label ?? 'Selected range'}
          change="—"
        />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm mb-6">
        <h3 className="text-gray-900 dark:text-white text-lg font-bold p-6">Agent Telemetry</h3>
        {isLoading ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">Loading telemetry…</div>
        ) : summaries.length === 0 ? (
          <div className="p-6 text-sm text-gray-500 dark:text-gray-400">
            No agent activity recorded for the selected range.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Agent</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Telemetry</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Invocations</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Success Rate</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Error Rate</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Denied</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Policy Alerts</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">P95 Latency</th>
                  <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {summaries.map((summary: any) => (
                  <tr key={summary.agent_id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                    <td className="p-4 text-sm text-gray-900 dark:text-white font-medium">
                      {summary.name}
                    </td>
                    <td className="p-4 text-sm">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          summary.telemetry_quality === 'verified'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
                        }`}
                      >
                        {summary.telemetry_quality === 'verified' ? 'Verified' : 'Partial'}
                      </span>
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {numberFormatter.format(summary.total_invocations ?? 0)}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {percentFormatter.format(summary.success_rate ?? 0)}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {percentFormatter.format(summary.error_rate ?? 0)}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {numberFormatter.format(summary.denied_invocations ?? 0)}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {numberFormatter.format(summary.policy_alerts_count ?? 0)}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {summary.p95_latency_ms != null
                        ? `${numberFormatter.format(summary.p95_latency_ms)} ms`
                        : '—'}
                    </td>
                    <td className="p-4 text-sm text-gray-600 dark:text-gray-300">
                      {currencyFormatter.format(summary.cost_usd ?? 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <InvocationsTable />
    </div>
  );
}
