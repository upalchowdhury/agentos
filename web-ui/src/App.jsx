import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Traces from './pages/Traces'
import TraceDetail from './pages/TraceDetail'
import Agents from './pages/Agents'
import AgentDetail from './pages/AgentDetail'
import Logs from './pages/Logs'
import Metrics from './pages/Metrics'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/traces" element={<Traces />} />
        <Route path="/traces/:traceId" element={<TraceDetail />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/agents/:agentId" element={<AgentDetail />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/metrics" element={<Metrics />} />
      </Routes>
    </Layout>
  )
}

export default App
