/**
 * Span Flamegraph Component
 *
 * Visualizes span hierarchy as a flamegraph with:
 * - Hierarchical spans (parent-child relationships)
 * - Color-coded by status (success, error, timeout)
 * - Width proportional to duration
 * - Click to drill down into span details
 * - Hover for quick info
 */

import React, { useState, useMemo } from 'react';
import './SpanFlamegraph.css';

export interface Span {
  span_id: string;
  parent_span_id: string | null;
  name: string;
  kind: 'prompt' | 'tool' | 'subagent' | 'system' | 'network';
  start_ts: string;
  duration_ms: number;
  status: 'success' | 'error' | 'timeout' | 'cancelled';
  depth: number;

  // Optional fields for detail view
  model_provider?: string;
  model_name?: string;
  tokens_in?: number;
  tokens_out?: number;
  cost_cents?: number;
  error_message?: string;
  tool_name?: string;
  protocol?: string;
  remote_agent_id?: string;
}

interface SpanNode extends Span {
  children: SpanNode[];
  startOffset: number;  // Relative to parent start
}

interface Props {
  spans: Span[];
  traceId: string;
  onSpanClick?: (span: Span) => void;
}

const SpanFlamegraph: React.FC<Props> = ({ spans, traceId, onSpanClick }) => {
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);
  const [hoveredSpan, setHoveredSpan] = useState<Span | null>(null);

  // Build span tree
  const spanTree = useMemo(() => buildSpanTree(spans), [spans]);

  // Calculate total duration from root span
  const totalDuration = useMemo(() => {
    if (spanTree.length === 0) return 1;
    return Math.max(...spanTree.map(s => s.duration_ms));
  }, [spanTree]);

  const handleSpanClick = (span: Span) => {
    setSelectedSpan(span);
    if (onSpanClick) {
      onSpanClick(span);
    }
  };

  if (spans.length === 0) {
    return (
      <div className="span-flamegraph-empty">
        <p>No spans to display</p>
      </div>
    );
  }

  return (
    <div className="span-flamegraph">
      <div className="flamegraph-header">
        <h3>Span Flamegraph</h3>
        <div className="flamegraph-legend">
          <span className="legend-item"><span className="color-box status-success"></span> Success</span>
          <span className="legend-item"><span className="color-box status-error"></span> Error</span>
          <span className="legend-item"><span className="color-box status-timeout"></span> Timeout</span>
        </div>
      </div>

      <div className="flamegraph-chart">
        {spanTree.map((node) => (
          <SpanRow
            key={node.span_id}
            node={node}
            totalDuration={totalDuration}
            depth={0}
            onSpanClick={handleSpanClick}
            onSpanHover={setHoveredSpan}
            selectedSpan={selectedSpan}
            hoveredSpan={hoveredSpan}
          />
        ))}
      </div>

      {selectedSpan && (
        <SpanDetailPanel
          span={selectedSpan}
          onClose={() => setSelectedSpan(null)}
        />
      )}

      {hoveredSpan && !selectedSpan && (
        <SpanTooltip span={hoveredSpan} />
      )}
    </div>
  );
};

// ============================================================================
// SpanRow Component (Recursive)
// ============================================================================

interface SpanRowProps {
  node: SpanNode;
  totalDuration: number;
  depth: number;
  onSpanClick: (span: Span) => void;
  onSpanHover: (span: Span | null) => void;
  selectedSpan: Span | null;
  hoveredSpan: Span | null;
}

const SpanRow: React.FC<SpanRowProps> = ({
  node,
  totalDuration,
  depth,
  onSpanClick,
  onSpanHover,
  selectedSpan,
  hoveredSpan
}) => {
  const widthPercent = (node.duration_ms / totalDuration) * 100;
  const isSelected = selectedSpan?.span_id === node.span_id;
  const isHovered = hoveredSpan?.span_id === node.span_id;

  return (
    <>
      <div
        className={`span-row depth-${depth} status-${node.status} ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
        style={{
          marginLeft: `${depth * 20}px`,
          width: `calc(${widthPercent}% - ${depth * 20}px)`
        }}
        onClick={() => onSpanClick(node)}
        onMouseEnter={() => onSpanHover(node)}
        onMouseLeave={() => onSpanHover(null)}
      >
        <div className="span-content">
          <span className="span-kind-icon">{getKindIcon(node.kind)}</span>
          <span className="span-name">{node.name}</span>
          <span className="span-duration">{node.duration_ms}ms</span>
          {node.cost_cents > 0 && (
            <span className="span-cost">${(node.cost_cents / 100).toFixed(3)}</span>
          )}
        </div>
      </div>

      {/* Render children */}
      {node.children.map((child) => (
        <SpanRow
          key={child.span_id}
          node={child}
          totalDuration={totalDuration}
          depth={depth + 1}
          onSpanClick={onSpanClick}
          onSpanHover={onSpanHover}
          selectedSpan={selectedSpan}
          hoveredSpan={hoveredSpan}
        />
      ))}
    </>
  );
};

// ============================================================================
// SpanDetailPanel Component
// ============================================================================

interface SpanDetailPanelProps {
  span: Span;
  onClose: () => void;
}

const SpanDetailPanel: React.FC<SpanDetailPanelProps> = ({ span, onClose }) => {
  return (
    <div className="span-detail-panel">
      <div className="panel-header">
        <h4>Span Details</h4>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      <div className="panel-content">
        <div className="detail-section">
          <h5>Basic Info</h5>
          <table>
            <tbody>
              <tr>
                <td>ID:</td>
                <td><code>{span.span_id}</code></td>
              </tr>
              <tr>
                <td>Name:</td>
                <td>{span.name}</td>
              </tr>
              <tr>
                <td>Kind:</td>
                <td><span className={`badge kind-${span.kind}`}>{span.kind}</span></td>
              </tr>
              <tr>
                <td>Status:</td>
                <td><span className={`badge status-${span.status}`}>{span.status}</span></td>
              </tr>
              <tr>
                <td>Duration:</td>
                <td>{span.duration_ms} ms</td>
              </tr>
              <tr>
                <td>Started:</td>
                <td>{new Date(span.start_ts).toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {span.kind === 'prompt' && span.model_provider && (
          <div className="detail-section">
            <h5>Model Info</h5>
            <table>
              <tbody>
                <tr>
                  <td>Provider:</td>
                  <td>{span.model_provider}</td>
                </tr>
                <tr>
                  <td>Model:</td>
                  <td>{span.model_name}</td>
                </tr>
                {span.tokens_in && (
                  <tr>
                    <td>Tokens In:</td>
                    <td>{span.tokens_in.toLocaleString()}</td>
                  </tr>
                )}
                {span.tokens_out && (
                  <tr>
                    <td>Tokens Out:</td>
                    <td>{span.tokens_out.toLocaleString()}</td>
                  </tr>
                )}
                {span.cost_cents > 0 && (
                  <tr>
                    <td>Cost:</td>
                    <td>${(span.cost_cents / 100).toFixed(4)}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {span.kind === 'tool' && span.tool_name && (
          <div className="detail-section">
            <h5>Tool Info</h5>
            <table>
              <tbody>
                <tr>
                  <td>Tool:</td>
                  <td>{span.tool_name}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {span.kind === 'network' && span.protocol && (
          <div className="detail-section">
            <h5>Network Info</h5>
            <table>
              <tbody>
                <tr>
                  <td>Protocol:</td>
                  <td>{span.protocol}</td>
                </tr>
                {span.remote_agent_id && (
                  <tr>
                    <td>Remote Agent:</td>
                    <td><code>{span.remote_agent_id}</code></td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {span.status === 'error' && span.error_message && (
          <div className="detail-section error-section">
            <h5>Error</h5>
            <pre className="error-message">{span.error_message}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// SpanTooltip Component
// ============================================================================

interface SpanTooltipProps {
  span: Span;
}

const SpanTooltip: React.FC<SpanTooltipProps> = ({ span }) => {
  return (
    <div className="span-tooltip">
      <div className="tooltip-row">
        <strong>{span.name}</strong>
      </div>
      <div className="tooltip-row">
        <span>Duration: {span.duration_ms}ms</span>
      </div>
      {span.cost_cents > 0 && (
        <div className="tooltip-row">
          <span>Cost: ${(span.cost_cents / 100).toFixed(4)}</span>
        </div>
      )}
      <div className="tooltip-row">
        <span className={`badge kind-${span.kind}`}>{span.kind}</span>
        <span className={`badge status-${span.status}`}>{span.status}</span>
      </div>
    </div>
  );
};

// ============================================================================
// Helper Functions
// ============================================================================

function buildSpanTree(spans: Span[]): SpanNode[] {
  // Create map of span_id -> node
  const nodeMap = new Map<string, SpanNode>();

  spans.forEach(span => {
    nodeMap.set(span.span_id, {
      ...span,
      children: [],
      startOffset: 0
    });
  });

  // Build parent-child relationships
  const rootNodes: SpanNode[] = [];

  spans.forEach(span => {
    const node = nodeMap.get(span.span_id)!;

    if (span.parent_span_id) {
      const parent = nodeMap.get(span.parent_span_id);
      if (parent) {
        parent.children.push(node);
      } else {
        // Parent not found, treat as root
        rootNodes.push(node);
      }
    } else {
      // Root span
      rootNodes.push(node);
    }
  });

  // Sort children by start time
  const sortChildren = (node: SpanNode) => {
    node.children.sort((a, b) =>
      new Date(a.start_ts).getTime() - new Date(b.start_ts).getTime()
    );
    node.children.forEach(sortChildren);
  };

  rootNodes.forEach(sortChildren);

  return rootNodes;
}

function getKindIcon(kind: string): string {
  switch (kind) {
    case 'prompt': return '🤖';
    case 'tool': return '🔧';
    case 'subagent': return '🔗';
    case 'network': return '🌐';
    case 'system': return '⚙️';
    default: return '📦';
  }
}

export default SpanFlamegraph;
