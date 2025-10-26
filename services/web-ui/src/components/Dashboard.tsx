import { Link } from 'react-router-dom';
import { StatCard } from './Dashboard/StatCard';
import { ChartCard } from './Dashboard/ChartCard';
import { InvocationsTable } from './Dashboard/InvocationsTable';

export function Dashboard() {
  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <p className="text-gray-900 dark:text-white text-3xl font-black leading-tight">
          Dashboard
        </p>
        <div className="flex items-center gap-4">
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
        <StatCard title="Total Agents" value="12" change="+10%" />
        <StatCard title="Active Deployments" value="5" change="+5%" />
        <StatCard title="Total Invocations" value="1,234" change="+20%" />
        <StatCard title="Total Cost" value="$5,678.90" change="+15%" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ChartCard
          title="Invocations (Last 30 Days)"
          value="1,234"
          timeRange="Last 30 Days"
          change="+20%"
        />
        <ChartCard title="Cost (Last 30 Days)" value="$5,678.90" timeRange="Last 30 Days" change="+15%" />
      </div>

      <InvocationsTable />
    </div>
  );
}
