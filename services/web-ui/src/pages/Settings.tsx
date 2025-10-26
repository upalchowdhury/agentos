export function Settings() {
  return (
    <div>
      <h1 className="text-3xl font-black text-gray-900 dark:text-white mb-6">Settings</h1>

      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Account Settings</h2>
          <p className="text-gray-500 dark:text-gray-400">
            Manage your account preferences, profile information, and authentication settings.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">System Configuration</h2>
          <p className="text-gray-500 dark:text-gray-400">
            Configure system-wide settings, resource limits, and default deployment parameters.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Integrations</h2>
          <p className="text-gray-500 dark:text-gray-400">
            Connect external services and configure API keys for third-party integrations.
          </p>
        </div>
      </div>
    </div>
  );
}
