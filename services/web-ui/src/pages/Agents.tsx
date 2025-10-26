import { Link } from 'react-router-dom';

export function Agents() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-black text-gray-900 dark:text-white">Agents</h1>
        <Link
          to="/deploy"
          className="flex items-center justify-center rounded-lg h-10 px-4 bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors"
        >
          Deploy New Agent
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
        <p className="text-gray-500 dark:text-gray-400">
          Agent management interface coming soon. Deploy and manage your AI agents here.
        </p>
      </div>
    </div>
  );
}
