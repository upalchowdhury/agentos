interface Invocation {
  agent: string;
  deployment: string;
  timestamp: string;
  status: 'Success' | 'Failed' | 'Timeout';
}

const mockInvocations: Invocation[] = [
  {
    agent: 'Auto-Responder',
    deployment: 'dep_1a2b3c4d',
    timestamp: '2023-10-27 10:30 AM',
    status: 'Success',
  },
  {
    agent: 'Data-Analyzer',
    deployment: 'dep_5e6f7g8h',
    timestamp: '2023-10-27 10:28 AM',
    status: 'Failed',
  },
  {
    agent: 'Content-Generator',
    deployment: 'dep_9i0j1k2l',
    timestamp: '2023-10-27 10:25 AM',
    status: 'Success',
  },
];

export function InvocationsTable() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Success':
        return 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300';
      case 'Failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300';
      case 'Timeout':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <h3 className="text-gray-900 dark:text-white text-lg font-bold p-6">Recent Invocations</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Agent</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">
                Deployment
              </th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">
                Timestamp
              </th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Status</th>
              <th className="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {mockInvocations.map((invocation, index) => (
              <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                <td className="p-4 text-sm text-gray-900 dark:text-white font-medium">
                  {invocation.agent}
                </td>
                <td className="p-4 text-sm text-gray-500 dark:text-gray-400">
                  {invocation.deployment}
                </td>
                <td className="p-4 text-sm text-gray-500 dark:text-gray-400">
                  {invocation.timestamp}
                </td>
                <td className="p-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      invocation.status
                    )}`}
                  >
                    {invocation.status}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <a className="text-blue-600 dark:text-blue-400 font-medium text-sm hover:underline">
                    Details
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
