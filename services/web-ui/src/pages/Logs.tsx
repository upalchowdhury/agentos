export function Logs() {
  return (
    <div>
      <h1 className="text-3xl font-black text-gray-900 dark:text-white mb-6">Logs</h1>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
        <p className="text-gray-500 dark:text-gray-400">
          Access detailed system logs. Filter by agent, deployment, timestamp, and log level for debugging and monitoring.
        </p>
      </div>
    </div>
  );
}
