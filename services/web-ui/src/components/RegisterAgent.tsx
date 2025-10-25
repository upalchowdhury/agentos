import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { agentAPI } from '../lib/api';

export function RegisterAgent() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    agentType: '',
    name: '',
    description: '',
    tags: '',
    model: 'GPT-4',
    temperature: 0.7,
    maxTokens: 4096,
    costBudget: 100,
    rateLimit: 1000,
  });

  const createDID = useMutation({
    mutationFn: (data: any) => agentAPI.identity.createDID(data),
    onSuccess: (response) => {
      const did = response.data.did.id;
      issueCredential.mutate({
        subjectDID: did,
        claims: {
          model: formData.model,
          permissions: ['call_agents', 'read_memory', 'write_memory'],
        },
        expiresIn: '30d',
      });
    },
  });

  const issueCredential = useMutation({
    mutationFn: (data: any) => agentAPI.identity.issueCredential(data),
    onSuccess: () => {
      alert('Agent registered successfully!');
      navigate('/registry');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    createDID.mutate({
      agentType: formData.agentType,
      metadata: {
        name: formData.name,
        description: formData.description,
        tags: formData.tags.split(',').map(t => t.trim()),
        model: formData.model,
        temperature: formData.temperature,
        maxTokens: formData.maxTokens,
        costBudget: formData.costBudget,
        rateLimit: formData.rateLimit,
      },
    });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Register New Agent</h1>

      <form onSubmit={handleSubmit} className="space-y-8 bg-white rounded-lg shadow p-6">
        <section>
          <h2 className="text-xl font-semibold mb-4">1. Basic Information</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agent Type *
              </label>
              <input
                type="text"
                required
                value={formData.agentType}
                onChange={(e) => setFormData({ ...formData, agentType: e.target.value })}
                placeholder="e.g., assistant, classifier, analyzer"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agent Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., fraud-detector-v3"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                placeholder="Describe what this agent does..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="fraud, finance, security"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </section>

        <section className="border-t pt-8">
          <h2 className="text-xl font-semibold mb-4">2. Model Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base Model *
              </label>
              <select
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option>GPT-4</option>
                <option>GPT-4 Turbo</option>
                <option>Claude Sonnet 4.5</option>
                <option>Claude Opus 4</option>
                <option>Gemini Pro 1.5</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: {formData.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={formData.temperature}
                onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Tokens per Call
              </label>
              <input
                type="number"
                value={formData.maxTokens}
                onChange={(e) => setFormData({ ...formData, maxTokens: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </section>

        <section className="border-t pt-8">
          <h2 className="text-xl font-semibold mb-4">3. Policy & Limits</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cost Budget (per hour, USD)
              </label>
              <input
                type="number"
                value={formData.costBudget}
                onChange={(e) => setFormData({ ...formData, costBudget: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Agent will be automatically paused if exceeded
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rate Limit (calls per minute)
              </label>
              <input
                type="number"
                value={formData.rateLimit}
                onChange={(e) => setFormData({ ...formData, rateLimit: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </section>

        <div className="flex gap-4 pt-4">
          <button
            type="button"
            onClick={() => navigate('/registry')}
            className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createDID.isPending}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {createDID.isPending ? 'Deploying...' : 'Deploy Agent →'}
          </button>
        </div>
      </form>
    </div>
  );
}
