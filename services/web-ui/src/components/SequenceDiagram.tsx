/**
 * Inter-Agent Sequence Diagram Component
 *
 * Visualizes agent-to-agent communication flows:
 * - Vertical agent lanes
 * - Horizontal arrows for messages/calls
 * - Protocol badges (A2A, MCP, HTTP)
 * - Signature verification status
 * - Policy enforcement indicators
 */

import React, { useState, useMemo } from 'react';
import './SequenceDiagram.css';

export interface Edge {
  edge_id: string;
  trace_id: string;
  timestamp: string;
  channel: 'a2a' | 'mcp' | 'http' | 'grpc' | 'queue';
  instruction_type: 'prompt' | 'tool_request' | 'system_directive' | 'callback' | 'response';
  from_agent_name: string;
  from_agent_id: string;
  from_span_name?: string;
  to_agent_name: string;
  to_agent_id: string;
  to_span_name?: string;
  latency_ms?: number;
  size_bytes?: number;
  signature_verified: boolean;
  redaction_applied: boolean;
  policy_enforced?: string[];
  obligations?: string[];
}

interface Props {
  edges: Edge[];
  traceId: string;
  onEdgeClick?: (edge: Edge) => void;
}

interface Agent {
  id: string;
  name: string;
  color: string;
}

const SequenceDiagram: React.FC<Props> = ({ edges, traceId, onEdgeClick }) => {
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<Edge | null>(null);

  // Extract unique agents
  const agents = useMemo(() => extractAgents(edges), [edges]);

  // Sort edges by timestamp
  const sortedEdges = useMemo(
    () => [...edges].sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    ),
    [edges]
  );

  const handleEdgeClick = (edge: Edge) => {
    setSelectedEdge(edge);
    if (onEdgeClick) {
      onEdgeClick(edge);
    }
  };

  if (edges.length === 0) {
    return (
      <div className="sequence-diagram-empty">
        <p>No inter-agent communication detected</p>
      </div>
    );
  }

  return (
    <div className="sequence-diagram">
      <div className="diagram-header">
        <h3>Inter-Agent Sequence Diagram</h3>
        <div className="diagram-legend">
          <span className="legend-item"><span className="protocol-badge a2a">A2A</span> Agent-to-Agent</span>
          <span className="legend-item"><span className="protocol-badge mcp">MCP</span> Model Context Protocol</span>
          <span className="legend-item"><span className="status-icon verified">✓</span> Signature Verified</span>
          <span className="legend-item"><span className="status-icon unverified">✗</span> Unverified</span>
        </div>
      </div>

      <div className="diagram-canvas">
        {/* Agent lanes (vertical) */}
        <div className="agent-lanes">
          {agents.map((agent, index) => (
            <AgentLane
              key={agent.id}
              agent={agent}
              index={index}
              totalAgents={agents.length}
            />
          ))}
        </div>

        {/* Messages (arrows) */}
        <div className="message-flows">
          {sortedEdges.map((edge, index) => {
            const fromIndex = agents.findIndex(a => a.id === edge.from_agent_id);
            const toIndex = agents.findIndex(a => a.id === edge.to_agent_id);

            if (fromIndex === -1 || toIndex === -1) return null;

            return (
              <MessageArrow
                key={edge.edge_id}
                edge={edge}
                fromIndex={fromIndex}
                toIndex={toIndex}
                totalAgents={agents.length}
                sequenceIndex={index}
                onClick={handleEdgeClick}
                onHover={setHoveredEdge}
                isSelected={selectedEdge?.edge_id === edge.edge_id}
                isHovered={hoveredEdge?.edge_id === edge.edge_id}
              />
            );
          })}
        </div>
      </div>

      {selectedEdge && (
        <EdgeDetailPanel edge={selectedEdge} onClose={() => setSelectedEdge(null)} />
      )}
    </div>
  );
};

// ============================================================================
// AgentLane Component
// ============================================================================

interface AgentLaneProps {
  agent: Agent;
  index: number;
  totalAgents: number;
}

const AgentLane: React.FC<AgentLaneProps> = ({ agent, index, totalAgents }) => {
  const leftPercent = ((index + 0.5) / totalAgents) * 100;

  return (
    <div
      className="agent-lane"
      style={{ left: `${leftPercent}%` }}
    >
      <div className="agent-header" style={{ backgroundColor: agent.color }}>
        <div className="agent-name">{agent.name}</div>
        <div className="agent-id">{agent.id.substring(0, 8)}</div>
      </div>
      <div className="agent-lifeline"></div>
    </div>
  );
};

// ============================================================================
// MessageArrow Component
// ============================================================================

interface MessageArrowProps {
  edge: Edge;
  fromIndex: number;
  toIndex: number;
  totalAgents: number;
  sequenceIndex: number;
  onClick: (edge: Edge) => void;
  onHover: (edge: Edge | null) => void;
  isSelected: boolean;
  isHovered: boolean;
}

const MessageArrow: React.FC<MessageArrowProps> = ({
  edge,
  fromIndex,
  toIndex,
  totalAgents,
  sequenceIndex,
  onClick,
  onHover,
  isSelected,
  isHovered
}) => {
  const fromPercent = ((fromIndex + 0.5) / totalAgents) * 100;
  const toPercent = ((toIndex + 0.5) / totalAgents) * 100;
  const topPosition = 100 + (sequenceIndex * 60);

  const isRightward = toIndex > fromIndex;
  const leftPercent = Math.min(fromPercent, toPercent);
  const widthPercent = Math.abs(toPercent - fromPercent);

  return (
    <div
      className={`message-arrow ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
      style={{
        top: `${topPosition}px`,
        left: `${leftPercent}%`,
        width: `${widthPercent}%`
      }}
      onClick={() => onClick(edge)}
      onMouseEnter={() => onHover(edge)}
      onMouseLeave={() => onHover(null)}
    >
      <div className={`arrow-line ${isRightward ? 'rightward' : 'leftward'}`}>
        <div className="arrow-head"></div>
      </div>

      <div className="arrow-label">
        <span className={`protocol-badge ${edge.channel}`}>{edge.channel.toUpperCase()}</span>
        <span className="instruction-type">{edge.instruction_type}</span>
        {edge.latency_ms && (
          <span className="latency">{edge.latency_ms}ms</span>
        )}
        {edge.signature_verified ? (
          <span className="status-icon verified" title="Signature Verified">✓</span>
        ) : (
          <span className="status-icon unverified" title="Not Verified">✗</span>
        )}
        {edge.redaction_applied && (
          <span className="status-icon redacted" title="Redaction Applied">🔒</span>
        )}
        {edge.policy_enforced && edge.policy_enforced.length > 0 && (
          <span className="status-icon policy" title="Policy Enforced">🛡️</span>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// EdgeDetailPanel Component
// ============================================================================

interface EdgeDetailPanelProps {
  edge: Edge;
  onClose: () => void;
}

const EdgeDetailPanel: React.FC<EdgeDetailPanelProps> = ({ edge, onClose }) => {
  return (
    <div className="edge-detail-panel">
      <div className="panel-header">
        <h4>Edge Details</h4>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      <div className="panel-content">
        <div className="detail-section">
          <h5>Communication</h5>
          <table>
            <tbody>
              <tr>
                <td>From:</td>
                <td>
                  <strong>{edge.from_agent_name}</strong>
                  <br />
                  <code>{edge.from_agent_id}</code>
                </td>
              </tr>
              <tr>
                <td>To:</td>
                <td>
                  <strong>{edge.to_agent_name}</strong>
                  <br />
                  <code>{edge.to_agent_id}</code>
                </td>
              </tr>
              <tr>
                <td>Protocol:</td>
                <td><span className={`protocol-badge ${edge.channel}`}>{edge.channel.toUpperCase()}</span></td>
              </tr>
              <tr>
                <td>Type:</td>
                <td>{edge.instruction_type}</td>
              </tr>
              <tr>
                <td>Timestamp:</td>
                <td>{new Date(edge.timestamp).toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="detail-section">
          <h5>Performance</h5>
          <table>
            <tbody>
              {edge.latency_ms && (
                <tr>
                  <td>Latency:</td>
                  <td>{edge.latency_ms} ms</td>
                </tr>
              )}
              {edge.size_bytes && (
                <tr>
                  <td>Size:</td>
                  <td>{formatBytes(edge.size_bytes)}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="detail-section">
          <h5>Security</h5>
          <table>
            <tbody>
              <tr>
                <td>Signature:</td>
                <td>
                  {edge.signature_verified ? (
                    <span className="status-badge verified">✓ Verified</span>
                  ) : (
                    <span className="status-badge unverified">✗ Not Verified</span>
                  )}
                </td>
              </tr>
              <tr>
                <td>Redaction:</td>
                <td>
                  {edge.redaction_applied ? (
                    <span className="status-badge applied">Applied</span>
                  ) : (
                    <span>Not Applied</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {edge.policy_enforced && edge.policy_enforced.length > 0 && (
          <div className="detail-section">
            <h5>Policies Enforced</h5>
            <ul className="policy-list">
              {edge.policy_enforced.map((policy, index) => (
                <li key={index}><code>{policy}</code></li>
              ))}
            </ul>
          </div>
        )}

        {edge.obligations && edge.obligations.length > 0 && (
          <div className="detail-section">
            <h5>Obligations</h5>
            <ul className="obligation-list">
              {edge.obligations.map((obligation, index) => (
                <li key={index}>{obligation}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Helper Functions
// ============================================================================

function extractAgents(edges: Edge[]): Agent[] {
  const agentMap = new Map<string, Agent>();
  const colors = ['#0366d6', '#28a745', '#6f42c1', '#f66a0a', '#d73a49', '#17a2b8'];

  edges.forEach(edge => {
    if (!agentMap.has(edge.from_agent_id)) {
      agentMap.set(edge.from_agent_id, {
        id: edge.from_agent_id,
        name: edge.from_agent_name,
        color: colors[agentMap.size % colors.length]
      });
    }

    if (!agentMap.has(edge.to_agent_id)) {
      agentMap.set(edge.to_agent_id, {
        id: edge.to_agent_id,
        name: edge.to_agent_name,
        color: colors[agentMap.size % colors.length]
      });
    }
  });

  return Array.from(agentMap.values());
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default SequenceDiagram;
