import { InvocationsTable } from '../components/Dashboard/InvocationsTable';

export function Invocations() {
  return (
    <div>
      <h1 className="text-3xl font-black text-gray-900 dark:text-white mb-6">Invocations</h1>

      <div className="mb-6">
        <p className="text-gray-600 dark:text-gray-400">
          Monitor all agent invocations. View execution history, success rates, error logs, and performance analytics.
        </p>
      </div>

      <InvocationsTable />
    </div>
  );
}
