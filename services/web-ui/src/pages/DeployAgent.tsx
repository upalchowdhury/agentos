import { useState } from 'react';
import { agentAPI } from '../lib/api';

export function DeployAgent() {
  const [formData, setFormData] = useState({
    agentId: '',
    code: '',
    maxMemory: '512m',
    maxCpu: '0.5',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await agentAPI.runtime.deploy({
        agent_id: formData.agentId,
        code: formData.code,
        requirements: [],
        environment: null,
        max_memory: formData.maxMemory,
        max_cpu: formData.maxCpu,
      });

      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Deployment failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold mb-6 text-gray-900">Deploy Agent</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="agentId" className="block text-sm font-medium text-gray-700 mb-2">
              Agent ID
            </label>
            <input
              type="text"
              id="agentId"
              name="agentId"
              value={formData.agentId}
              onChange={handleChange}
              required
              placeholder="e.g., my-math-agent"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
              Agent Code
            </label>
            <textarea
              id="code"
              name="code"
              value={formData.code}
              onChange={handleChange}
              required
              rows={12}
              placeholder="# Your agent code here&#10;# Must set 'result' variable&#10;result = input_data['x'] + input_data['y']"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              Your code must set a <code className="bg-gray-100 px-1 rounded">result</code> variable. Use <code className="bg-gray-100 px-1 rounded">input_data</code> to access input.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="maxMemory" className="block text-sm font-medium text-gray-700 mb-2">
                Max Memory
              </label>
              <select
                id="maxMemory"
                name="maxMemory"
                value={formData.maxMemory}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="256m">256 MB</option>
                <option value="512m">512 MB</option>
                <option value="1g">1 GB</option>
                <option value="2g">2 GB</option>
              </select>
            </div>

            <div>
              <label htmlFor="maxCpu" className="block text-sm font-medium text-gray-700 mb-2">
                Max CPU
              </label>
              <select
                id="maxCpu"
                name="maxCpu"
                value={formData.maxCpu}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="0.25">0.25 cores</option>
                <option value="0.5">0.5 cores</option>
                <option value="1">1 core</option>
                <option value="2">2 cores</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Deploying...' : 'Deploy Agent'}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="text-sm font-medium text-red-800 mb-1">Deployment Failed</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-sm font-medium text-green-800 mb-3">Deployment Successful</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Deployment ID:</span>
                <code className="text-green-700 bg-green-100 px-2 py-1 rounded">{result.deployment_id}</code>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Agent ID:</span>
                <span className="text-gray-900">{result.agent_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Status:</span>
                <span className="px-2 py-1 bg-green-600 text-white rounded text-xs font-medium">
                  {result.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Deployed At:</span>
                <span className="text-gray-900">{new Date(result.deployed_at).toLocaleString()}</span>
              </div>
              {result.message && (
                <div className="mt-2 pt-2 border-t border-green-200">
                  <p className="text-green-700">{result.message}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
