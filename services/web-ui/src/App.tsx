import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './components/Dashboard';
import { AgentRegistry } from './components/AgentRegistry';
import { RegisterAgent } from './components/RegisterAgent';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4">
              <div className="flex space-x-8">
                <Link to="/" className="px-3 py-4 text-sm font-medium hover:text-blue-600">
                  Dashboard
                </Link>
                <Link to="/registry" className="px-3 py-4 text-sm font-medium hover:text-blue-600">
                  Agent Registry
                </Link>
                <Link to="/register-agent" className="px-3 py-4 text-sm font-medium hover:text-blue-600">
                  Register Agent
                </Link>
              </div>
            </div>
          </nav>

          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/registry" element={<AgentRegistry />} />
            <Route path="/register-agent" element={<RegisterAgent />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
