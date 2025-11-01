import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { agentAPI } from '../lib/api';

export function RegisterModelBAgent() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    endpoint_url: '',
    auth_type: 'none',
    auth_value: '',
    auth_header_name: '',
    rps: 10,
    burst: 20,
    health_check_path: '/health',
    timeout_seconds: 30,
    enable_alerts: false,
    error_rate: 0.4,
    latency_ms: 2500,
  });

  const registerAgent = useMutation({
    mutationFn: (data: any) => agentAPI.runtime.registerModelB(data),
    onSuccess: (response) => {
      alert(`Agent registered successfully! Agent ID: ${response.data.agent_id}`);
      navigate('/agents');
    },
    onError: (error: any) => {
      alert(`Failed to register agent: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const payload: any = {
      name: formData.name,
      endpoint_url: formData.endpoint_url,
      auth: {
        type: formData.auth_type,
      },
      rate_limit: {
        rps: formData.rps,
        burst: formData.burst,
      },
      health_check_path: formData.health_check_path,
      timeout_seconds: formData.timeout_seconds,
    };

    if (formData.auth_type === 'bearer') {
      payload.auth.value = formData.auth_value;
    } else if (formData.auth_type === 'header') {
      payload.auth.header_name = formData.auth_header_name;
      payload.auth.value = formData.auth_value;
    }

    if (formData.enable_alerts) {
      payload.alerts = {
        error_rate: formData.error_rate,
        latency_ms: formData.latency_ms,
      };
    }

    registerAgent.mutate(payload);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Register External Agent (Model B)
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Connect an external agent endpoint to AgentOS for unified observability, rate limiting, and policy enforcement.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
        <section>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Agent Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., local-reasoner, openai-assistant"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Minimum 3 characters, maximum 100
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Endpoint URL *
              </label>
              <input
                type="url"
                required
                value={formData.endpoint_url}
                onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
                placeholder="http://localhost:9000/invoke"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                HTTP/HTTPS endpoint where AgentOS will proxy invocation requests
              </p>
            </div>
          </div>
        </section>

        <section className="border-t border-gray-200 dark:border-gray-700 pt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Authentication</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Authentication Type
              </label>
              <select
                value={formData.auth_type}
                onChange={(e) => setFormData({ ...formData, auth_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              >
                <option value="none">None</option>
                <option value="bearer">Bearer Token</option>
                <option value="header">Custom Header</option>
              </select>
            </div>

            {formData.auth_type === 'bearer' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Bearer Token *
                </label>
                <input
                  type="password"
                  required
                  value={formData.auth_value}
                  onChange={(e) => setFormData({ ...formData, auth_value: e.target.value })}
                  placeholder="your-secret-token"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>
            )}

            {formData.auth_type === 'header' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Header Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.auth_header_name}
                    onChange={(e) => setFormData({ ...formData, auth_header_name: e.target.value })}
                    placeholder="X-API-Key"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Header Value *
                  </label>
                  <input
                    type="password"
                    required
                    value={formData.auth_value}
                    onChange={(e) => setFormData({ ...formData, auth_value: e.target.value })}
                    placeholder="your-api-key"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  />
                </div>
              </>
            )}
          </div>
        </section>

        <section className="border-t border-gray-200 dark:border-gray-700 pt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Rate Limiting & Timeouts</h2>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Requests Per Second
                </label>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={formData.rps}
                  onChange={(e) => setFormData({ ...formData, rps: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Burst Capacity
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.burst}
                  onChange={(e) => setFormData({ ...formData, burst: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Request Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="1"
                  max="300"
                  value={formData.timeout_seconds}
                  onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Health Check Path
                </label>
                <input
                  type="text"
                  value={formData.health_check_path}
                  onChange={(e) => setFormData({ ...formData, health_check_path: e.target.value })}
                  placeholder="/health"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>
        </section>

        <section className="border-t border-gray-200 dark:border-gray-700 pt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Alert Thresholds (Optional)</h2>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enable_alerts"
                checked={formData.enable_alerts}
                onChange={(e) => setFormData({ ...formData, enable_alerts: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="enable_alerts" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Enable alert thresholds for this agent
              </label>
            </div>

            {formData.enable_alerts && (
              <div className="grid grid-cols-2 gap-4 pl-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Error Rate Threshold (0-1)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={formData.error_rate}
                    onChange={(e) => setFormData({ ...formData, error_rate: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Alert if error rate exceeds this value (e.g., 0.4 = 40%)
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Latency Threshold (ms)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.latency_ms}
                    onChange={(e) => setFormData({ ...formData, latency_ms: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Alert if latency exceeds this value in milliseconds
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>

        <div className="flex gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={() => navigate('/agents')}
            className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={registerAgent.isPending}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {registerAgent.isPending ? 'Registering...' : 'Register Agent →'}
          </button>
        </div>
      </form>

      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
          What happens after registration?
        </h3>
        <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
          <li>AgentOS performs a health check on your endpoint</li>
          <li>Agent appears in Dashboard with "Partial Telemetry" badge initially</li>
          <li>Integrate the AgentOS SDK to upgrade to "Verified Telemetry"</li>
          <li>Invoke via <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">POST /v1/agents/[agent_id]/invoke</code></li>
        </ul>
      </div>
    </div>
  );
}
