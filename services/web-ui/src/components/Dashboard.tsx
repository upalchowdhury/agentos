import { useQuery } from '@tanstack/react-query';
import { Activity, DollarSign, AlertTriangle, Users } from 'lucide-react';
import { agentAPI } from '../lib/api';

export function Dashboard() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => agentAPI.dashboard.getMetrics(),
    refetchInterval: 5000, // Refresh every 5s
  });

  const { data: agentStats } = useQuery({
    queryKey: ['agentStats'],
    queryFn: () => agentAPI.dashboard.getAgentStats(),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Control Plane Dashboard</h1>
        <div className="text-sm text-gray-500">
          Last Updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          icon={<Users className="w-8 h-8" />}
          label="Active Agents"
          value={metrics?.activeAgents || 0}
          change="+12 from yesterday"
          color="blue"
        />
        <MetricCard
          icon={<Activity className="w-8 h-8" />}
          label="Throughput"
          value={`${metrics?.throughput || 0}/s`}
          change="calls/second"
          color="green"
        />
        <MetricCard
          icon={<DollarSign className="w-8 h-8" />}
          label="Cost (Last Hour)"
          value={`$${metrics?.cost || 0}`}
          change="↑ 23% from avg"
          color="orange"
        />
        <MetricCard
          icon={<AlertTriangle className="w-8 h-8" />}
          label="Active Alerts"
          value={metrics?.alerts || 0}
          change="2 critical, 1 warning"
          color="red"
        />
      </div>

      {/* Agent Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Top Agents by Activity</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Agent Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Calls (1h)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cost (1h)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Avg Latency
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Error Rate
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {agentStats?.map((agent: any) => (
                <tr key={agent.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={agent.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{agent.calls.toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap">${agent.cost}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{agent.latency}ms</td>
                  <td className="px-6 py-4 whitespace-nowrap">{agent.errorRate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, change, color }: any) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
    red: 'from-red-500 to-red-600',
  };

  return (
    <div className={`bg-gradient-to-br ${colors[color as keyof typeof colors]} text-white rounded-lg p-6 shadow-lg`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="text-sm opacity-90">{label}</div>
          <div className="text-3xl font-bold mt-2">{value}</div>
          <div className="text-xs opacity-80 mt-2">{change}</div>
        </div>
        <div className="opacity-80">{icon}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    healthy: 'bg-green-100 text-green-800',
    critical: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    degraded: 'bg-orange-100 text-orange-800',
  };

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${colors[status as keyof typeof colors]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
