import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout/Layout';
import { Dashboard } from './components/Dashboard';
import { AgentRegistry } from './components/AgentRegistry';
import { RegisterAgent } from './components/RegisterAgent';
import { RegisterModelBAgent } from './components/RegisterModelBAgent';
import { DeployAgent } from './pages/DeployAgent';
import { Agents } from './pages/Agents';
import { Deployments } from './pages/Deployments';
import { Invocations } from './pages/Invocations';
import { Logs } from './pages/Logs';
import { Metrics } from './pages/Metrics';
import { Settings } from './pages/Settings';
import { TraceViewer } from './pages/TraceViewer';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/deployments" element={<Deployments />} />
            <Route path="/invocations" element={<Invocations />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/registry" element={<AgentRegistry />} />
            <Route path="/register-agent" element={<RegisterAgent />} />
            <Route path="/register-external" element={<RegisterModelBAgent />} />
            <Route path="/deploy" element={<DeployAgent />} />
            <Route path="/trace/:invocationId" element={<TraceViewer />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
