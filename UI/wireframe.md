<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Economy OS - Wireframes</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        .wireframe-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .nav-tabs {
            background: white;
            border-bottom: 2px solid #e0e0e0;
            padding: 0 20px;
            margin-bottom: 30px;
            display: flex;
            gap: 5px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .nav-tab {
            padding: 15px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        
        .nav-tab:hover {
            color: #333;
            background: #f9f9f9;
        }
        
        .nav-tab.active {
            color: #2563eb;
            border-bottom-color: #2563eb;
        }
        
        .screen {
            display: none;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .screen.active {
            display: block;
        }
        
        .screen-header {
            background: #1e293b;
            color: white;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: 600;
        }
        
        .screen-subheader {
            background: #334155;
            color: #94a3b8;
            padding: 10px 20px;
            font-size: 12px;
            border-bottom: 1px solid #475569;
        }
        
        .screen-body {
            padding: 20px;
        }
        
        /* Layout Grid */
        .grid {
            display: grid;
            gap: 20px;
        }
        
        .grid-2 {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .grid-3 {
            grid-template-columns: repeat(3, 1fr);
        }
        
        .grid-4 {
            grid-template-columns: repeat(4, 1fr);
        }
        
        .grid-sidebar {
            grid-template-columns: 250px 1fr;
        }
        
        /* Components */
        .card {
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 16px;
            background: white;
        }
        
        .card-header {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-body {
            font-size: 13px;
            color: #666;
        }
        
        .metric-card {
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .metric-card.green {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }
        
        .metric-card.orange {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }
        
        .metric-card.red {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            margin: 10px 0;
        }
        
        .metric-label {
            font-size: 13px;
            opacity: 0.9;
        }
        
        .metric-change {
            font-size: 12px;
            margin-top: 8px;
            opacity: 0.9;
        }
        
        .button {
            padding: 8px 16px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .button-primary {
            background: #2563eb;
            color: white;
        }
        
        .button-primary:hover {
            background: #1d4ed8;
        }
        
        .button-secondary {
            background: #e5e7eb;
            color: #374151;
        }
        
        .button-secondary:hover {
            background: #d1d5db;
        }
        
        .button-danger {
            background: #ef4444;
            color: white;
        }
        
        .input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            font-size: 13px;
            margin-bottom: 12px;
        }
        
        .select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            font-size: 13px;
            margin-bottom: 12px;
        }
        
        .label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 6px;
            color: #374151;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .badge-success {
            background: #d1fae5;
            color: #065f46;
        }
        
        .badge-warning {
            background: #fef3c7;
            color: #92400e;
        }
        
        .badge-error {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .badge-info {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        .table th {
            text-align: left;
            padding: 12px;
            background: #f9fafb;
            border-bottom: 2px solid #e5e7eb;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6b7280;
        }
        
        .table td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .table tr:hover {
            background: #f9fafb;
        }
        
        .chart-placeholder {
            height: 200px;
            background: linear-gradient(180deg, #f9fafb 0%, #f3f4f6 100%);
            border: 1px dashed #d1d5db;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #9ca3af;
            font-size: 13px;
        }
        
        .graph-placeholder {
            height: 400px;
            background: #1e293b;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }
        
        .node {
            position: absolute;
            width: 80px;
            height: 80px;
            background: #3b82f6;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
            font-weight: 600;
            text-align: center;
            padding: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .node.active {
            background: #10b981;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .connection {
            position: absolute;
            height: 2px;
            background: #475569;
            transform-origin: left center;
        }
        
        .connection.active {
            background: #3b82f6;
            animation: flow 1s infinite;
        }
        
        @keyframes flow {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }
        
        .sidebar {
            background: #f9fafb;
            border-right: 1px solid #e5e7eb;
            padding: 20px;
        }
        
        .sidebar-item {
            padding: 10px 12px;
            border-radius: 4px;
            margin-bottom: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .sidebar-item:hover {
            background: #e5e7eb;
        }
        
        .sidebar-item.active {
            background: #2563eb;
            color: white;
        }
        
        .alert {
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 13px;
        }
        
        .alert-warning {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #92400e;
        }
        
        .alert-error {
            background: #fee2e2;
            border-left: 4px solid #ef4444;
            color: #991b1b;
        }
        
        .alert-success {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            color: #065f46;
        }
        
        .breadcrumb {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 20px;
        }
        
        .breadcrumb a {
            color: #2563eb;
            text-decoration: none;
        }
        
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        
        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 16px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            margin: 12px 0;
        }
        
        .form-section {
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .form-section:last-child {
            border-bottom: none;
        }
        
        .form-section-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #1f2937;
        }
        
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #e5e7eb;
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 24px;
        }
        
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -24px;
            top: 4px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #3b82f6;
            border: 3px solid white;
        }
        
        .timeline-item.success::before {
            background: #10b981;
        }
        
        .timeline-item.error::before {
            background: #ef4444;
        }
        
        .timeline-time {
            font-size: 11px;
            color: #9ca3af;
            margin-bottom: 4px;
        }
        
        .timeline-content {
            font-size: 13px;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 13px;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .stat-label {
            color: #6b7280;
        }
        
        .stat-value {
            font-weight: 600;
        }
        
        .progress-bar {
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: #3b82f6;
            border-radius: 4px;
            transition: width 0.3s;
        }
        
        .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        
        .tag {
            padding: 4px 10px;
            background: #f3f4f6;
            border-radius: 12px;
            font-size: 11px;
            color: #4b5563;
        }
    </style>
</head>
<body>
    <div class="wireframe-container">
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showScreen('dashboard')">Dashboard</button>
            <button class="nav-tab" onclick="showScreen('registry')">Agent Registry</button>
            <button class="nav-tab" onclick="showScreen('call-graph')">Live Call Graph</button>
            <button class="nav-tab" onclick="showScreen('policy')">Policy Studio</button>
            <button class="nav-tab" onclick="showScreen('memory')">Memory Browser</button>
            <button class="nav-tab" onclick="showScreen('tracing')">Distributed Tracing</button>
            <button class="nav-tab" onclick="showScreen('register-agent')">Register Agent</button>
            <button class="nav-tab" onclick="showScreen('security')">Security Audit</button>
        </div>

        <!-- DASHBOARD -->
        <div id="dashboard" class="screen active">
            <div class="screen-header">Control Plane Dashboard</div>
            <div class="screen-subheader">Organization: Acme Corp | Region: us-east-1 | Last Updated: 2s ago</div>
            <div class="screen-body">
                <!-- Key Metrics -->
                <div class="grid grid-4" style="margin-bottom: 30px;">
                    <div class="metric-card">
                        <div class="metric-label">Active Agents</div>
                        <div class="metric-value">127</div>
                        <div class="metric-change">↑ 12 from yesterday</div>
                    </div>
                    <div class="metric-card green">
                        <div class="metric-label">Throughput</div>
                        <div class="metric-value">1.2K</div>
                        <div class="metric-change">calls/second</div>
                    </div>
                    <div class="metric-card orange">
                        <div class="metric-label">Cost (Last Hour)</div>
                        <div class="metric-value">$847</div>
                        <div class="metric-change">↑ 23% from avg</div>
                    </div>
                    <div class="metric-card red">
                        <div class="metric-label">Active Alerts</div>
                        <div class="metric-value">3</div>
                        <div class="metric-change">2 critical, 1 warning</div>
                    </div>
                </div>

                <!-- Alerts -->
                <div style="margin-bottom: 30px;">
                    <div class="alert alert-error">
                        <strong>⚠ Critical:</strong> Agent "fraud-detector-v2" exceeded cost budget by 340% in last 15 min
                        <button class="button button-danger" style="float: right; margin-top: -4px;">Pause Agent</button>
                    </div>
                    <div class="alert alert-warning">
                        <strong>⚡ Warning:</strong> 12 agents attempting unauthorized cross-org calls
                    </div>
                </div>

                <!-- Main Grid -->
                <div class="grid grid-2">
                    <!-- Fleet Health -->
                    <div class="card">
                        <div class="card-header">
                            Fleet Health
                            <select style="font-size: 12px; padding: 4px 8px;">
                                <option>Last Hour</option>
                                <option>Last 24h</option>
                                <option>Last 7d</option>
                            </select>
                        </div>
                        <div class="card-body">
                            <div class="chart-placeholder">
                                📊 Call Volume & Latency Chart<br>
                                <small>(Peak: 2.4K calls/s at 14:23 UTC)</small>
                            </div>
                            <div style="margin-top: 16px;">
                                <div class="stat-row">
                                    <span class="stat-label">Avg Latency (p95)</span>
                                    <span class="stat-value">234ms</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Success Rate</span>
                                    <span class="stat-value">99.2%</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Failed Auth Attempts</span>
                                    <span class="stat-value" style="color: #ef4444;">147</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Cost Breakdown -->
                    <div class="card">
                        <div class="card-header">
                            Cost Breakdown (Last 24h)
                            <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Export Report</button>
                        </div>
                        <div class="card-body">
                            <div class="chart-placeholder">
                                💰 Cost by Agent/Model<br>
                                <small>(Total: $18,432)</small>
                            </div>
                            <div style="margin-top: 16px;">
                                <div class="stat-row">
                                    <span class="stat-label">GPT-4</span>
                                    <span class="stat-value">$12,340 (67%)</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Claude Sonnet</span>
                                    <span class="stat-value">$4,892 (27%)</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Memory Storage</span>
                                    <span class="stat-value">$890 (5%)</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Gateway/Routing</span>
                                    <span class="stat-value">$310 (2%)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Agent Table -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        Top Agents by Activity
                        <input type="text" placeholder="Search agents..." style="font-size: 12px; padding: 6px 10px; width: 200px; border: 1px solid #d1d5db; border-radius: 4px;">
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Agent Name</th>
                                    <th>Status</th>
                                    <th>Calls (1h)</th>
                                    <th>Cost (1h)</th>
                                    <th>Avg Latency</th>
                                    <th>Error Rate</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>fraud-detector-v2</strong></td>
                                    <td><span class="badge badge-error">Critical</span></td>
                                    <td>23,441</td>
                                    <td>$847</td>
                                    <td>156ms</td>
                                    <td>0.3%</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                        <button class="button button-danger" style="font-size: 11px; padding: 4px 8px;">Pause</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>customer-support-orchestrator</strong></td>
                                    <td><span class="badge badge-success">Healthy</span></td>
                                    <td>18,923</td>
                                    <td>$234</td>
                                    <td>289ms</td>
                                    <td>0.1%</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>data-analyst-fleet</strong></td>
                                    <td><span class="badge badge-success">Healthy</span></td>
                                    <td>12,567</td>
                                    <td>$445</td>
                                    <td>412ms</td>
                                    <td>0.8%</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>code-review-assistant</strong></td>
                                    <td><span class="badge badge-warning">Degraded</span></td>
                                    <td>8,234</td>
                                    <td>$156</td>
                                    <td>534ms</td>
                                    <td>2.4%</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>email-classifier</strong></td>
                                    <td><span class="badge badge-success">Healthy</span></td>
                                    <td>6,891</td>
                                    <td>$89</td>
                                    <td>134ms</td>
                                    <td>0.2%</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- AGENT REGISTRY -->
        <div id="registry" class="screen">
            <div class="screen-header">Agent Registry</div>
            <div class="screen-subheader">Browse, search, and manage all registered agents in your organization</div>
            <div class="screen-body">
                <!-- Search & Filters -->
                <div style="margin-bottom: 30px; display: flex; gap: 12px; align-items: center;">
                    <input class="input" placeholder="🔍 Search agents by name, capability, or tag..." style="flex: 1; margin: 0;">
                    <select class="select" style="width: 150px; margin: 0;">
                        <option>All Status</option>
                        <option>Active</option>
                        <option>Paused</option>
                        <option>Error</option>
                    </select>
                    <select class="select" style="width: 150px; margin: 0;">
                        <option>All Models</option>
                        <option>GPT-4</option>
                        <option>Claude Sonnet</option>
                        <option>Gemini Pro</option>
                    </select>
                    <button class="button button-primary">+ Register New Agent</button>
                </div>

                <!-- Agent Cards -->
                <div class="grid grid-3">
                    <!-- Agent Card 1 -->
                    <div class="card" style="cursor: pointer; transition: all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.boxShadow='none'">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                            <div>
                                <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">fraud-detector-v2</div>
                                <div style="font-size: 11px; color: #9ca3af;">DID: did:agent:8d7f...4a2b</div>
                            </div>
                            <span class="badge badge-error">Critical</span>
                        </div>
                        
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                            Real-time fraud detection using multi-agent pattern analysis
                        </div>
                        
                        <div class="tag-list">
                            <span class="tag">GPT-4</span>
                            <span class="tag">Fraud</span>
                            <span class="tag">Finance</span>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6;">
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Calls (24h)</span>
                                <span class="stat-value">234K</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Cost (24h)</span>
                                <span class="stat-value" style="color: #ef4444;">$2,847</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Reputation Score</span>
                                <span class="stat-value">94/100</span>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Details</button>
                            <button class="button button-danger" style="flex: 1; font-size: 11px; padding: 6px;">Pause</button>
                        </div>
                    </div>

                    <!-- Agent Card 2 -->
                    <div class="card" style="cursor: pointer; transition: all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.boxShadow='none'">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                            <div>
                                <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">customer-support-orchestrator</div>
                                <div style="font-size: 11px; color: #9ca3af;">DID: did:agent:3f2e...9c1d</div>
                            </div>
                            <span class="badge badge-success">Healthy</span>
                        </div>
                        
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                            Routes support tickets to specialized sub-agents based on issue type
                        </div>
                        
                        <div class="tag-list">
                            <span class="tag">Claude Sonnet</span>
                            <span class="tag">Support</span>
                            <span class="tag">Orchestrator</span>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6;">
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Calls (24h)</span>
                                <span class="stat-value">189K</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Cost (24h)</span>
                                <span class="stat-value">$1,234</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Reputation Score</span>
                                <span class="stat-value">98/100</span>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Details</button>
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Configure</button>
                        </div>
                    </div>

                    <!-- Agent Card 3 -->
                    <div class="card" style="cursor: pointer; transition: all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.boxShadow='none'">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                            <div>
                                <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">data-analyst-fleet</div>
                                <div style="font-size: 11px; color: #9ca3af;">DID: did:agent:7b4a...2e8f</div>
                            </div>
                            <span class="badge badge-success">Healthy</span>
                        </div>
                        
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                            MapReduce-style parallel data analysis with 50+ worker sub-agents
                        </div>
                        
                        <div class="tag-list">
                            <span class="tag">GPT-4</span>
                            <span class="tag">Analytics</span>
                            <span class="tag">MapReduce</span>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6;">
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Calls (24h)</span>
                                <span class="stat-value">156K</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Cost (24h)</span>
                                <span class="stat-value">$3,445</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Reputation Score</span>
                                <span class="stat-value">96/100</span>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Details</button>
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Scale</button>
                        </div>
                    </div>

                    <!-- Agent Card 4 -->
                    <div class="card" style="cursor: pointer; transition: all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.boxShadow='none'">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                            <div>
                                <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">code-review-assistant</div>
                                <div style="font-size: 11px; color: #9ca3af;">DID: did:agent:1c9f...6d3a</div>
                            </div>
                            <span class="badge badge-warning">Degraded</span>
                        </div>
                        
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                            Automated code review with security, performance, and style analysis
                        </div>
                        
                        <div class="tag-list">
                            <span class="tag">GPT-4</span>
                            <span class="tag">DevOps</span>
                            <span class="tag">Code</span>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6;">
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Calls (24h)</span>
                                <span class="stat-value">67K</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Cost (24h)</span>
                                <span class="stat-value">$892</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Reputation Score</span>
                                <span class="stat-value" style="color: #f59e0b;">87/100</span>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Details</button>
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Debug</button>
                        </div>
                    </div>

                    <!-- Agent Card 5 -->
                    <div class="card" style="cursor: pointer; transition: all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.boxShadow='none'">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                            <div>
                                <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">email-classifier</div>
                                <div style="font-size: 11px; color: #9ca3af;">DID: did:agent:5e3d...8f7c</div>
                            </div>
                            <span class="badge badge-success">Healthy</span>
                        </div>
                        
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                            Intelligent email routing and priority classification
                        </div>
                        
                        <div class="tag-list">
                            <span class="tag">Claude Haiku</span>
                            <span class="tag">Email</span>
                            <span class="tag">Classification</span>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6;">
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Calls (24h)</span>
                                <span class="stat-value">423K</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Cost (24h)</span>
                                <span class="stat-value">$234</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Reputation Score</span>
                                <span class="stat-value">99/100</span>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Details</button>
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Clone</button>
                        </div>
                    </div>

                    <!-- Agent Card 6 -->
                    <div class="card" style="cursor: pointer; transition: all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.boxShadow='none'">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                            <div>
                                <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">sentiment-analyzer</div>
                                <div style="font-size: 11px; color: #9ca3af;">DID: did:agent:9a2c...4b1e</div>
                            </div>
                            <span class="badge badge-success">Healthy</span>
                        </div>
                        
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                            Multi-language sentiment analysis for customer feedback
                        </div>
                        
                        <div class="tag-list">
                            <span class="tag">GPT-4</span>
                            <span class="tag">NLP</span>
                            <span class="tag">Sentiment</span>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6;">
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Calls (24h)</span>
                                <span class="stat-value">92K</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Cost (24h)</span>
                                <span class="stat-value">$567</span>
                            </div>
                            <div class="stat-row" style="padding: 4px 0; border: none;">
                                <span class="stat-label">Reputation Score</span>
                                <span class="stat-value">95/100</span>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px; display: flex; gap: 8px;">
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Details</button>
                            <button class="button button-secondary" style="flex: 1; font-size: 11px; padding: 6px;">Test</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- LIVE CALL GRAPH -->
        <div id="call-graph" class="screen">
            <div class="screen-header">Live Call Graph</div>
            <div class="screen-subheader">Real-time visualization of agent-to-agent communication | Updates every 2s</div>
            <div class="screen-body">
                <!-- Controls -->
                <div style="margin-bottom: 20px; display: flex; gap: 12px; align-items: center;">
                    <select class="select" style="width: 200px; margin: 0;">
                        <option>All Organizations</option>
                        <option>Acme Corp Only</option>
                        <option>Cross-Org Calls</option>
                    </select>
                    <select class="select" style="width: 200px; margin: 0;">
                        <option>Last 5 minutes</option>
                        <option>Last 15 minutes</option>
                        <option>Last Hour</option>
                    </select>
                    <div style="flex: 1;"></div>
                    <label style="font-size: 13px; display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" checked> Show Failed Calls
                    </label>
                    <button class="button button-secondary">Export Graph</button>
                    <button class="button button-primary">Pause Stream</button>
                </div>

                <!-- Graph Visualization -->
                <div class="graph-placeholder">
                    <!-- Central Orchestrator -->
                    <div class="node active" style="top: 180px; left: 640px;">
                        customer-support
                    </div>
                    
                    <!-- Surrounding Nodes -->
                    <div class="node" style="top: 50px; left: 500px;">
                        email-classifier
                    </div>
                    <div class="node" style="top: 50px; left: 780px;">
                        sentiment-analyzer
                    </div>
                    <div class="node active" style="top: 180px; left: 360px;">
                        fraud-detector
                    </div>
                    <div class="node" style="top: 180px; left: 920px;">
                        billing-agent
                    </div>
                    <div class="node" style="top: 310px; left: 500px;">
                        escalation-handler
                    </div>
                    <div class="node active" style="top: 310px; left: 780px;">
                        data-analyst
                    </div>
                    
                    <!-- Connections (simplified - would be dynamically drawn) -->
                    <div class="connection active" style="top: 220px; left: 440px; width: 200px; transform: rotate(0deg);"></div>
                    <div class="connection" style="top: 100px; left: 570px; width: 120px; transform: rotate(45deg);"></div>
                    <div class="connection active" style="top: 220px; left: 720px; width: 200px; transform: rotate(0deg);"></div>
                    
                    <!-- Legend -->
                    <div style="position: absolute; top: 20px; left: 20px; background: rgba(255,255,255,0.1); padding: 16px; border-radius: 6px; font-size: 12px; color: #e2e8f0;">
                        <div style="margin-bottom: 8px; font-weight: 600;">Legend</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background: #10b981;"></div>
                            Active Call
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background: #3b82f6;"></div>
                            Idle Agent
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="width: 12px; height: 2px; background: #3b82f6;"></div>
                            Connection Flow
                        </div>
                    </div>
                    
                    <!-- Stats Overlay -->
                    <div style="position: absolute; bottom: 20px; right: 20px; background: rgba(255,255,255,0.1); padding: 16px; border-radius: 6px; font-size: 12px; color: #e2e8f0;">
                        <div style="margin-bottom: 8px; font-weight: 600;">Live Stats</div>
                        <div style="margin-bottom: 4px;">Active Calls: <strong>47</strong></div>
                        <div style="margin-bottom: 4px;">Throughput: <strong>1,234/s</strong></div>
                        <div style="margin-bottom: 4px;">Avg Latency: <strong>234ms</strong></div>
                        <div>Failed (1m): <strong style="color: #ef4444;">3</strong></div>
                    </div>
                </div>

                <!-- Call Stream -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">Recent Agent-to-Agent Calls</div>
                    <div class="card-body" style="padding: 0;">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Caller Agent</th>
                                    <th>Target Agent</th>
                                    <th>Protocol</th>
                                    <th>Status</th>
                                    <th>Latency</th>
                                    <th>Cost</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>14:23:45</td>
                                    <td>customer-support</td>
                                    <td>fraud-detector</td>
                                    <td><span class="badge badge-info">A2A</span></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>142ms</td>
                                    <td>$0.023</td>
                                    <td><button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">Trace</button></td>
                                </tr>
                                <tr>
                                    <td>14:23:44</td>
                                    <td>data-analyst</td>
                                    <td>memory-service</td>
                                    <td><span class="badge badge-info">MCP</span></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>89ms</td>
                                    <td>$0.001</td>
                                    <td><button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">Trace</button></td>
                                </tr>
                                <tr style="background: #fef2f2;">
                                    <td>14:23:43</td>
                                    <td>billing-agent</td>
                                    <td>external-payment-api</td>
                                    <td><span class="badge badge-info">REST</span></td>
                                    <td><span class="badge badge-error">403</span></td>
                                    <td>234ms</td>
                                    <td>$0.012</td>
                                    <td><button class="button button-danger" style="font-size: 11px; padding: 4px 8px;">Debug</button></td>
                                </tr>
                                <tr>
                                    <td>14:23:42</td>
                                    <td>customer-support</td>
                                    <td>sentiment-analyzer</td>
                                    <td><span class="badge badge-info">A2A</span></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>167ms</td>
                                    <td>$0.034</td>
                                    <td><button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">Trace</button></td>
                                </tr>
                                <tr>
                                    <td>14:23:41</td>
                                    <td>fraud-detector</td>
                                    <td>reputation-service</td>
                                    <td><span class="badge badge-info">MCP</span></td>
                                    <td><span class="badge badge-success">200</span></td>
                                    <td>56ms</td>
                                    <td>$0.002</td>
                                    <td><button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">Trace</button></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- POLICY STUDIO -->
        <div id="policy" class="screen">
            <div class="screen-header">Policy Studio</div>
            <div class="screen-subheader">Create and manage access control, cost limits, and behavioral policies</div>
            <div class="screen-body">
                <div class="grid grid-sidebar">
                    <!-- Sidebar -->
                    <div class="sidebar">
                        <div style="font-weight: 600; margin-bottom: 12px; font-size: 13px;">Policy Categories</div>
                        <div class="sidebar-item active">🔐 Access Control</div>
                        <div class="sidebar-item">💰 Cost Limits</div>
                        <div class="sidebar-item">⚡ Rate Limiting</div>
                        <div class="sidebar-item">🛡️ Security Rules</div>
                        <div class="sidebar-item">📋 Approval Workflows</div>
                        <div class="sidebar-item">🔔 Alerting</div>
                        
                        <div style="margin-top: 30px;">
                            <button class="button button-primary" style="width: 100%;">+ New Policy</button>
                        </div>
                    </div>

                    <!-- Main Content -->
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h2 style="font-size: 18px; font-weight: 600;">Access Control Policies</h2>
                            <div style="display: flex; gap: 8px;">
                                <button class="button button-secondary">Import</button>
                                <button class="button button-primary">+ Create Policy</button>
                            </div>
                        </div>

                        <!-- Policy List -->
                        <div class="card" style="margin-bottom: 20px;">
                            <div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-weight: 600; margin-bottom: 4px;">Prevent Cross-Org Agent Calls</div>
                                    <div style="font-size: 12px; color: #6b7280;">Blocks agents from calling agents in other organizations</div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <span class="badge badge-success">Active</span>
                                    <label style="display: flex; align-items: center; font-size: 13px; cursor: pointer;">
                                        <input type="checkbox" checked style="margin-right: 6px;"> Enabled
                                    </label>
                                    <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Edit</button>
                                </div>
                            </div>
                            <div style="padding: 16px; background: #f9fafb; font-size: 12px; font-family: monospace;">
                                <strong>Rule:</strong> IF caller.org ≠ target.org THEN deny
                            </div>
                        </div>

                        <div class="card" style="margin-bottom: 20px;">
                            <div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-weight: 600; margin-bottom: 4px;">Require Approval for High-Cost Operations</div>
                                    <div style="font-size: 12px; color: #6b7280;">Operations >$100 require manual approval</div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <span class="badge badge-success">Active</span>
                                    <label style="display: flex; align-items: center; font-size: 13px; cursor: pointer;">
                                        <input type="checkbox" checked style="margin-right: 6px;"> Enabled
                                    </label>
                                    <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Edit</button>
                                </div>
                            </div>
                            <div style="padding: 16px; background: #f9fafb; font-size: 12px; font-family: monospace;">
                                <strong>Rule:</strong> IF estimated_cost > $100 THEN require_approval(security_team)
                            </div>
                        </div>

                        <div class="card" style="margin-bottom: 20px;">
                            <div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-weight: 600; margin-bottom: 4px;">Block Low-Reputation Agents</div>
                                    <div style="font-size: 12px; color: #6b7280;">Deny calls from agents with reputation score <50</div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <span class="badge badge-warning">Warning</span>
                                    <label style="display: flex; align-items: center; font-size: 13px; cursor: pointer;">
                                        <input type="checkbox" checked style="margin-right: 6px;"> Enabled
                                    </label>
                                    <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Edit</button>
                                </div>
                            </div>
                            <div style="padding: 16px; background: #f9fafb; font-size: 12px; font-family: monospace;">
                                <strong>Rule:</strong> IF caller.reputation < 50 THEN deny AND alert(security_team)
                            </div>
                        </div>

                        <!-- Policy Builder -->
                        <div class="card">
                            <div class="card-header">Visual Policy Builder</div>
                            <div class="card-body">
                                <div style="background: #f9fafb; padding: 20px; border-radius: 4px; border: 2px dashed #d1d5db;">
                                    <div style="margin-bottom: 16px;">
                                        <label class="label">Policy Name</label>
                                        <input class="input" placeholder="e.g., Limit fraud detector cost">
                                    </div>

                                    <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; align-items: end; margin-bottom: 16px;">
                                        <div>
                                            <label class="label">IF Condition</label>
                                            <select class="select">
                                                <option>Agent Name</option>
                                                <option>Cost Per Call</option>
                                                <option>Reputation Score</option>
                                                <option>Organization</option>
                                                <option>Time of Day</option>
                                            </select>
                                        </div>
                                        <div style="padding-bottom: 12px; font-weight: 600; color: #6b7280;">
                                            is
                                        </div>
                                        <div>
                                            <label class="label">Value</label>
                                            <input class="input" placeholder="Enter value">
                                        </div>
                                    </div>

                                    <div style="margin-bottom: 16px;">
                                        <label class="label">THEN Action</label>
                                        <select class="select">
                                            <option>Allow</option>
                                            <option>Deny</option>
                                            <option>Require Approval</option>
                                            <option>Alert Only</option>
                                            <option>Throttle</option>
                                        </select>
                                    </div>

                                    <div style="display: flex; gap: 8px;">
                                        <button class="button button-secondary">+ Add Condition</button>
                                        <button class="button button-primary">Create Policy</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- MEMORY BROWSER -->
        <div id="memory" class="screen">
            <div class="screen-header">Federated Memory Browser</div>
            <div class="screen-subheader">Explore and manage shared context across agent ecosystems</div>
            <div class="screen-body">
                <!-- Search & Filters -->
                <div style="margin-bottom: 20px; display: flex; gap: 12px;">
                    <input class="input" placeholder="🔍 Search memory by content, agent, or context..." style="flex: 1; margin: 0;">
                    <select class="select" style="width: 150px; margin: 0;">
                        <option>All Agents</option>
                        <option>fraud-detector</option>
                        <option>customer-support</option>
                    </select>
                    <select class="select" style="width: 150px; margin: 0;">
                        <option>Last 24h</option>
                        <option>Last 7d</option>
                        <option>Last 30d</option>
                    </select>
                </div>

                <div class="grid grid-2">
                    <!-- Memory Stats -->
                    <div class="card">
                        <div class="card-header">Memory Statistics</div>
                        <div class="card-body">
                            <div class="stat-row">
                                <span class="stat-label">Total Memory Objects</span>
                                <span class="stat-value">1,247,893</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">Shared Contexts</span>
                                <span class="stat-value">34,567</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">Storage Used</span>
                                <span class="stat-value">847 GB</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">Avg Read Latency</span>
                                <span class="stat-value">12ms</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">Write Throughput</span>
                                <span class="stat-value">2.3K ops/s</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">Monthly Cost</span>
                                <span class="stat-value">$1,234</span>
                            </div>
                        </div>
                    </div>

                    <!-- Memory Access Graph -->
                    <div class="card">
                        <div class="card-header">Memory Access Patterns</div>
                        <div class="card-body">
                            <div class="chart-placeholder">
                                📈 Read/Write Operations Over Time<br>
                                <small>(Peak: 4.2K ops/s at 14:00 UTC)</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Memory Contexts -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        Recent Memory Contexts
                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Prune Old Data</button>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Context ID</th>
                                    <th>Owner Agent</th>
                                    <th>Shared With</th>
                                    <th>Size</th>
                                    <th>Created</th>
                                    <th>Last Access</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code style="font-size: 11px;">ctx_8d7f...4a2b</code></td>
                                    <td>fraud-detector-v2</td>
                                    <td>
                                        <div style="display: flex; gap: 4px;">
                                            <span class="badge badge-info" style="font-size: 10px;">customer-support</span>
                                            <span class="badge badge-info" style="font-size: 10px;">+3 more</span>
                                        </div>
                                    </td>
                                    <td>2.4 MB</td>
                                    <td>2m ago</td>
                                    <td>Just now</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><code style="font-size: 11px;">ctx_3f2e...9c1d</code></td>
                                    <td>customer-support</td>
                                    <td>
                                        <div style="display: flex; gap: 4px;">
                                            <span class="badge badge-info" style="font-size: 10px;">sentiment-analyzer</span>
                                        </div>
                                    </td>
                                    <td>1.8 MB</td>
                                    <td>5m ago</td>
                                    <td>3m ago</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><code style="font-size: 11px;">ctx_7b4a...2e8f</code></td>
                                    <td>data-analyst-fleet</td>
                                    <td>
                                        <div style="display: flex; gap: 4px;">
                                            <span class="badge badge-info" style="font-size: 10px;">worker-01</span>
                                            <span class="badge badge-info" style="font-size: 10px;">worker-02</span>
                                            <span class="badge badge-info" style="font-size: 10px;">+48 more</span>
                                        </div>
                                    </td>
                                    <td>15.6 MB</td>
                                    <td>12m ago</td>
                                    <td>1m ago</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><code style="font-size: 11px;">ctx_1c9f...6d3a</code></td>
                                    <td>code-review-assistant</td>
                                    <td>
                                        <div style="display: flex; gap: 4px;">
                                            <span class="badge badge-info" style="font-size: 10px;">security-analyzer</span>
                                        </div>
                                    </td>
                                    <td>890 KB</td>
                                    <td>18m ago</td>
                                    <td>15m ago</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Memory Detail View -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">Memory Context Detail: ctx_8d7f...4a2b</div>
                    <div class="card-body">
                        <div class="grid grid-2" style="margin-bottom: 20px;">
                            <div>
                                <div class="label">Owner Agent</div>
                                <div style="font-size: 13px; margin-bottom: 12px;">fraud-detector-v2</div>
                                
                                <div class="label">Context Type</div>
                                <div style="font-size: 13px; margin-bottom: 12px;">Transaction History</div>
                                
                                <div class="label">Encryption</div>
                                <div style="font-size: 13px;"><span class="badge badge-success">AES-256 Encrypted</span></div>
                            </div>
                            <div>
                                <div class="label">Created</div>
                                <div style="font-size: 13px; margin-bottom: 12px;">2025-10-25 14:23:41 UTC</div>
                                
                                <div class="label">TTL (Time to Live)</div>
                                <div style="font-size: 13px; margin-bottom: 12px;">24 hours</div>
                                
                                <div class="label">Access Pattern</div>
                                <div style="font-size: 13px;">Read-Heavy (234 reads, 12 writes)</div>
                            </div>
                        </div>

                        <div class="label">Memory Content Preview</div>
                        <div class="code-block">
{
  "transaction_id": "txn_789abc",
  "user_id": "usr_456def",
  "amount": 15000.00,
  "risk_signals": [
    "unusual_amount",
    "new_device",
    "velocity_check_failed"
  ],
  "fraud_score": 0.87,
  "recommended_action": "require_2fa"
}
                        </div>

                        <div style="margin-top: 16px;">
                            <button class="button button-secondary">Download Full Context</button>
                            <button class="button button-danger" style="margin-left: 8px;">Revoke Access</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- DISTRIBUTED TRACING -->
        <div id="tracing" class="screen">
            <div class="screen-header">Distributed Tracing</div>
            <div class="screen-subheader">OpenTelemetry-native tracing across multi-agent workflows</div>
            <div class="screen-body">
                <div class="breadcrumb">
                    <a href="#">Traces</a> / <strong>trace_8d7f4a2b</strong>
                </div>

                <!-- Trace Overview -->
                <div class="grid grid-4" style="margin-bottom: 20px;">
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">TOTAL DURATION</div>
                        <div style="font-size: 24px; font-weight: 700;">2.34s</div>
                    </div>
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">SPANS</div>
                        <div style="font-size: 24px; font-weight: 700;">127</div>
                    </div>
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">AGENTS INVOLVED</div>
                        <div style="font-size: 24px; font-weight: 700;">8</div>
                    </div>
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">TOTAL COST</div>
                        <div style="font-size: 24px; font-weight: 700; color: #ef4444;">$2.84</div>
                    </div>
                </div>

                <!-- Timeline View -->
                <div class="card" style="margin-bottom: 20px;">
                    <div class="card-header">
                        Trace Timeline
                        <div style="display: flex; gap: 8px;">
                            <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Collapse All</button>
                            <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Export JSON</button>
                        </div>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <!-- Timeline would be an interactive component - showing simplified version -->
                        <div style="padding: 20px; background: #1e293b; color: #e2e8f0; font-family: monospace; font-size: 12px;">
                            <div style="margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(59, 130, 246, 0.2); border-left: 3px solid #3b82f6; margin-bottom: 4px;">
                                    <span>▼ customer-support-orchestrator [ROOT]</span>
                                    <span>0ms ──────────────────────────────────── 2,340ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #6366f1; margin-left: 30px; margin-bottom: 4px;">
                                    <span>▼ email-classifier.classify</span>
                                    <span style="margin-left: auto;">45ms ─── 234ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #6366f1; margin-left: 30px; margin-bottom: 4px;">
                                    <span>▼ sentiment-analyzer.analyze</span>
                                    <span style="margin-left: auto;">250ms ───── 456ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(239, 68, 68, 0.2); border-left: 3px solid #ef4444; margin-left: 30px; margin-bottom: 4px;">
                                    <span>▼ fraud-detector-v2.check [SLOW]</span>
                                    <span style="margin-left: auto;">470ms ───────────────────── 1,890ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #8b5cf6; margin-left: 60px; margin-bottom: 4px;">
                                    <span>  → memory.read_context</span>
                                    <span style="margin-left: auto;">490ms ── 512ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #8b5cf6; margin-left: 60px; margin-bottom: 4px;">
                                    <span>  → reputation-service.get_score</span>
                                    <span style="margin-left: auto;">520ms ─ 567ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(239, 68, 68, 0.2); border-left: 3px solid #ef4444; margin-left: 60px; margin-bottom: 4px;">
                                    <span>  → gpt-4.completion [EXPENSIVE]</span>
                                    <span style="margin-left: auto;">580ms ──────────────── 1,850ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #6366f1; margin-left: 30px; margin-bottom: 4px;">
                                    <span>▼ escalation-handler.route</span>
                                    <span style="margin-left: auto;">1,900ms ─── 2,100ms</span>
                                </div>
                                
                                <div style="display: flex; justify-space-between; padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #6366f1; margin-left: 30px;">
                                    <span>▼ response.format</span>
                                    <span style="margin-left: auto;">2,110ms ── 2,340ms</span>
                                </div>
                            </div>
                            
                            <div style="font-size: 11px; color: #94a3b8; padding-top: 12px; border-top: 1px solid #475569;">
                                Legend: <span style="color: #3b82f6;">■</span> Root  <span style="color: #6366f1;">■</span> Agent Call  <span style="color: #8b5cf6;">■</span> Service Call  <span style="color: #ef4444;">■</span> Anomaly
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Span Details -->
                <div class="card">
                    <div class="card-header">Selected Span: fraud-detector-v2.check</div>
                    <div class="card-body">
                        <div class="grid grid-2" style="margin-bottom: 20px;">
                            <div>
                                <div class="stat-row">
                                    <span class="stat-label">Span ID</span>
                                    <span class="stat-value" style="font-family: monospace; font-size: 11px;">span_7b4a2e8f</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Parent Span</span>
                                    <span class="stat-value" style="font-family: monospace; font-size: 11px;">span_8d7f4a2b</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Agent</span>
                                    <span class="stat-value">fraud-detector-v2</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Operation</span>
                                    <span class="stat-value">check_transaction</span>
                                </div>
                            </div>
                            <div>
                                <div class="stat-row">
                                    <span class="stat-label">Duration</span>
                                    <span class="stat-value" style="color: #ef4444;">1,420ms (61% of trace)</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Status</span>
                                    <span class="stat-value"><span class="badge badge-success">OK</span></span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Model Used</span>
                                    <span class="stat-value">GPT-4</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Cost</span>
                                    <span class="stat-value" style="color: #ef4444;">$2.34 (82% of trace)</span>
                                </div>
                            </div>
                        </div>

                        <div class="label">Span Attributes</div>
                        <div class="code-block">
{
  "agent.name": "fraud-detector-v2",
  "agent.did": "did:agent:8d7f...4a2b",
  "operation": "check_transaction",
  "model": "gpt-4",
  "input_tokens": 12450,
  "output_tokens": 890,
  "cost_usd": 2.34,
  "memory_context_used": true,
  "reputation_score_checked": true,
  "fraud_score": 0.87,
  "recommended_action": "require_2fa"
}
                        </div>

                        <div style="margin-top: 16px;">
                            <div class="alert alert-warning">
                                <strong>⚠️ Performance Alert:</strong> This span took 3.2x longer than average (typical: 445ms). High token usage detected.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- REGISTER AGENT -->
        <div id="register-agent" class="screen">
            <div class="screen-header">Register New Agent</div>
            <div class="screen-subheader">Deploy a new autonomous agent to your infrastructure</div>
            <div class="screen-body">
                <div style="max-width: 800px; margin: 0 auto;">
                    <!-- Step 1 -->
                    <div class="form-section">
                        <div class="form-section-title">1. Basic Information</div>
                        
                        <label class="label">Agent Name *</label>
                        <input class="input" placeholder="e.g., fraud-detector-v3" value="">
                        
                        <label class="label">Description</label>
                        <textarea class="input" rows="3" placeholder="Describe what this agent does..."></textarea>
                        
                        <label class="label">Tags</label>
                        <input class="input" placeholder="fraud, finance, security (comma-separated)">
                    </div>

                    <!-- Step 2 -->
                    <div class="form-section">
                        <div class="form-section-title">2. Model Configuration</div>
                        
                        <label class="label">Base Model *</label>
                        <select class="select">
                            <option>GPT-4</option>
                            <option>GPT-4 Turbo</option>
                            <option>Claude Sonnet 4.5</option>
                            <option>Claude Opus 4</option>
                            <option>Gemini Pro 1.5</option>
                        </select>
                        
                        <label class="label">Temperature</label>
                        <input type="range" min="0" max="100" value="70" style="width: 100%; margin-bottom: 12px;">
                        <div style="font-size: 12px; color: #6b7280; margin-top: -8px;">0.70 (Balanced)</div>
                        
                        <label class="label">Max Tokens per Call</label>
                        <input class="input" type="number" placeholder="4096">
                    </div>

                    <!-- Step 3 -->
                    <div class="form-section">
                        <div class="form-section-title">3. Identity & Security</div>
                        
                        <div class="alert alert-success" style="margin-bottom: 16px;">
                            <strong>✓ DID Generated:</strong> did:agent:9f3e2c1b-auto-generated
                        </div>
                        
                        <label class="label">Permission Scopes</label>
                        <div style="margin-bottom: 12px;">
                            <label style="display: flex; align-items: center; font-size: 13px; margin-bottom: 8px;">
                                <input type="checkbox" checked style="margin-right: 8px;">
                                <span>Can call other agents in same organization</span>
                            </label>
                            <label style="display: flex; align-items: center; font-size: 13px; margin-bottom: 8px;">
                                <input type="checkbox" style="margin-right: 8px;">
                                <span>Can call external APIs</span>
                            </label>
                            <label style="display: flex; align-items: center; font-size: 13px; margin-bottom: 8px;">
                                <input type="checkbox" checked style="margin-right: 8px;">
                                <span>Can read from federated memory</span>
                            </label>
                            <label style="display: flex; align-items: center; font-size: 13px; margin-bottom: 8px;">
                                <input type="checkbox" checked style="margin-right: 8px;">
                                <span>Can write to federated memory</span>
                            </label>
                        </div>
                        
                        <label class="label">Verifiable Credentials (Optional)</label>
                        <button class="button button-secondary">+ Request Credential</button>
                    </div>

                    <!-- Step 4 -->
                    <div class="form-section">
                        <div class="form-section-title">4. Memory Configuration</div>
                        
                        <label style="display: flex; align-items: center; font-size: 13px; margin-bottom: 16px;">
                            <input type="checkbox" checked style="margin-right: 8px;">
                            <span>Enable shared memory access</span>
                        </label>
                        
                        <label class="label">Memory Retention Policy</label>
                        <select class="select">
                            <option>24 hours</option>
                            <option>7 days</option>
                            <option>30 days</option>
                            <option>Forever (manual cleanup)</option>
                        </select>
                        
                        <label class="label">Context Window Strategy</label>
                        <select class="select">
                            <option>Automatic (system-managed)</option>
                            <option>Fixed size (8K tokens)</option>
                            <option>Fixed size (32K tokens)</option>
                            <option>Sliding window</option>
                        </select>
                    </div>

                    <!-- Step 5 -->
                    <div class="form-section">
                        <div class="form-section-title">5. Policy & Limits</div>
                        
                        <label class="label">Cost Budget (per hour)</label>
                        <input class="input" type="number" placeholder="100" value="100">
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Agent will be automatically paused if exceeded</div>
                        
                        <label class="label">Rate Limit</label>
                        <input class="input" type="number" placeholder="1000" value="1000">
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Maximum calls per minute</div>
                        
                        <label class="label">Approval Workflow</label>
                        <select class="select">
                            <option>None (fully autonomous)</option>
                            <option>Require approval for operations >$50</option>
                            <option>Require approval for all external calls</option>
                            <option>Require approval for everything (human-in-loop)</option>
                        </select>
                    </div>

                    <!-- Step 6 -->
                    <div class="form-section" style="border-bottom: none;">
                        <div class="form-section-title">6. Deployment</div>
                        
                        <label class="label">Environment</label>
                        <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                            <label style="flex: 1; display: flex; align-items: center; padding: 12px; border: 2px solid #e5e7eb; border-radius: 6px; cursor: pointer;">
                                <input type="radio" name="env" value="staging" style="margin-right: 8px;">
                                <div>
                                    <div style="font-weight: 600; font-size: 13px;">Staging</div>
                                    <div style="font-size: 11px; color: #6b7280;">Test before production</div>
                                </div>
                            </label>
                            <label style="flex: 1; display: flex; align-items: center; padding: 12px; border: 2px solid #2563eb; border-radius: 6px; cursor: pointer; background: #eff6ff;">
                                <input type="radio" name="env" value="production" checked style="margin-right: 8px;">
                                <div>
                                    <div style="font-weight: 600; font-size: 13px;">Production</div>
                                    <div style="font-size: 11px; color: #6b7280;">Deploy immediately</div>
                                </div>
                            </label>
                        </div>
                        
                        <label style="display: flex; align-items: center; font-size: 13px; margin-bottom: 16px;">
                            <input type="checkbox" checked style="margin-right: 8px;">
                            <span>Run validation suite before deployment</span>
                        </label>
                        
                        <div style="display: flex; gap: 12px; margin-top: 24px;">
                            <button class="button button-secondary" style="flex: 1;">Save as Draft</button>
                            <button class="button button-primary" style="flex: 1;">Deploy Agent →</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- SECURITY AUDIT -->
        <div id="security" class="screen">
            <div class="screen-header">Security Audit Dashboard</div>
            <div class="screen-subheader">Monitor trust, detect threats, and enforce compliance</div>
            <div class="screen-body">
                <!-- Security Metrics -->
                <div class="grid grid-4" style="margin-bottom: 30px;">
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">FAILED AUTH ATTEMPTS</div>
                        <div style="font-size: 24px; font-weight: 700; color: #ef4444;">147</div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">↑ 23% from yesterday</div>
                    </div>
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">POLICY VIOLATIONS</div>
                        <div style="font-size: 24px; font-weight: 700; color: #f59e0b;">12</div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Last 24h</div>
                    </div>
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">QUARANTINED AGENTS</div>
                        <div style="font-size: 24px; font-weight: 700;">2</div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Pending review</div>
                    </div>
                    <div class="card">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">AVG REPUTATION</div>
                        <div style="font-size: 24px; font-weight: 700; color: #10b981;">94/100</div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Across all agents</div>
                    </div>
                </div>

                <div class="grid grid-2">
                    <!-- Recent Threats -->
                    <div class="card">
                        <div class="card-header">Recent Security Events</div>
                        <div class="card-body">
                            <div class="timeline">
                                <div class="timeline-item error">
                                    <div class="timeline-time">14:23:45 UTC</div>
                                    <div class="timeline-content">
                                        <strong>Unauthorized cross-org call blocked</strong><br>
                                        <span style="font-size: 12px; color: #6b7280;">
                                            Agent "external-scraper" (did:agent:7f3e...2a1b) attempted to call internal agent
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="timeline-item error">
                                    <div class="timeline-time">14:18:32 UTC</div>
                                    <div class="timeline-content">
                                        <strong>Low reputation agent detected</strong><br>
                                        <span style="font-size: 12px; color: #6b7280;">
                                            Agent "data-collector-beta" reputation dropped to 42/100
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="timeline-item success">
                                    <div class="timeline-time">14:12:15 UTC</div>
                                    <div class="timeline-content">
                                        <strong>Credential successfully issued</strong><br>
                                        <span style="font-size: 12px; color: #6b7280;">
                                            New verifiable credential issued to "fraud-detector-v2"
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="timeline-item">
                                    <div class="timeline-time">14:05:23 UTC</div>
                                    <div class="timeline-content">
                                        <strong>Policy updated</strong><br>
                                        <span style="font-size: 12px; color: #6b7280;">
                                            "Block low-reputation agents" policy enabled
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="timeline-item error">
                                    <div class="timeline-time">13:58:41 UTC</div>
                                    <div class="timeline-content">
                                        <strong>Suspicious activity pattern</strong><br>
                                        <span style="font-size: 12px; color: #6b7280;">
                                            Agent "batch-processor" made 10K+ calls in 2 minutes
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Reputation Graph -->
                    <div class="card">
                        <div class="card-header">Agent Reputation Distribution</div>
                        <div class="card-body">
                            <div class="chart-placeholder">
                                📊 Reputation Score Distribution<br>
                                <small>(Most agents have high trust scores)</small>
                            </div>
                            <div style="margin-top: 16px;">
                                <div class="stat-row">
                                    <span class="stat-label">High Trust (90-100)</span>
                                    <span class="stat-value">89 agents</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Medium Trust (70-89)</span>
                                    <span class="stat-value">32 agents</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Low Trust (50-69)</span>
                                    <span class="stat-value">4 agents</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label" style="color: #ef4444;">Untrusted (<50)</span>
                                    <span class="stat-value" style="color: #ef4444;">2 agents</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Agent Credentials -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        Agent Credentials & Permissions
                        <button class="button button-primary" style="font-size: 11px; padding: 4px 12px;">+ Issue Credential</button>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Agent</th>
                                    <th>DID</th>
                                    <th>Credentials</th>
                                    <th>Permissions</th>
                                    <th>Reputation</th>
                                    <th>Last Verified</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>fraud-detector-v2</strong></td>
                                    <td><code style="font-size: 11px;">did:agent:8d7f...4a2b</code></td>
                                    <td>
                                        <span class="badge badge-success" style="font-size: 10px;">Verified</span>
                                        <span class="badge badge-info" style="font-size: 10px;">PCI-DSS</span>
                                    </td>
                                    <td style="font-size: 12px;">Read, Write, Call</td>
                                    <td><span style="color: #10b981; font-weight: 600;">94/100</span></td>
                                    <td>2h ago</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>customer-support</strong></td>
                                    <td><code style="font-size: 11px;">did:agent:3f2e...9c1d</code></td>
                                    <td>
                                        <span class="badge badge-success" style="font-size: 10px;">Verified</span>
                                    </td>
                                    <td style="font-size: 12px;">Read, Call</td>
                                    <td><span style="color: #10b981; font-weight: 600;">98/100</span></td>
                                    <td>1h ago</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                                <tr style="background: #fef2f2;">
                                    <td><strong>data-collector-beta</strong></td>
                                    <td><code style="font-size: 11px;">did:agent:7f3e...2a1b</code></td>
                                    <td>
                                        <span class="badge badge-error" style="font-size: 10px;">Revoked</span>
                                    </td>
                                    <td style="font-size: 12px;">None</td>
                                    <td><span style="color: #ef4444; font-weight: 600;">42/100</span></td>
                                    <td>12m ago</td>
                                    <td>
                                        <button class="button button-danger" style="font-size: 11px; padding: 4px 8px;">Quarantine</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>email-classifier</strong></td>
                                    <td><code style="font-size: 11px;">did:agent:5e3d...8f7c</code></td>
                                    <td>
                                        <span class="badge badge-success" style="font-size: 10px;">Verified</span>
                                    </td>
                                    <td style="font-size: 12px;">Read, Write</td>
                                    <td><span style="color: #10b981; font-weight: 600;">99/100</span></td>
                                    <td>30m ago</td>
                                    <td>
                                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 8px;">View</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Audit Log -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        Audit Log
                        <button class="button button-secondary" style="font-size: 11px; padding: 4px 12px;">Export CSV</button>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Event Type</th>
                                    <th>Actor</th>
                                    <th>Target</th>
                                    <th>Action</th>
                                    <th>Result</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>14:23:45</td>
                                    <td><span class="badge badge-error">Auth Failure</span></td>
                                    <td>external-scraper</td>
                                    <td>customer-db</td>
                                    <td>Attempted unauthorized access</td>
                                    <td><span style="color: #ef4444;">Blocked</span></td>
                                </tr>
                                <tr>
                                    <td>14:18:32</td>
                                    <td><span class="badge badge-warning">Policy Violation</span></td>
                                    <td>data-collector-beta</td>
                                    <td>N/A</td>
                                    <td>Reputation score dropped below threshold</td>
                                    <td><span style="color: #f59e0b;">Flagged</span></td>
                                </tr>
                                <tr>
                                    <td>14:12:15</td>
                                    <td><span class="badge badge-success">Credential Issued</span></td>
                                    <td>admin@acme.com</td>
                                    <td>fraud-detector-v2</td>
                                    <td>Issued PCI-DSS credential</td>
                                    <td><span style="color: #10b981;">Success</span></td>
                                </tr>
                                <tr>
                                    <td>14:05:23</td>
                                    <td><span class="badge badge-info">Policy Change</span></td>
                                    <td>admin@acme.com</td>
                                    <td>Global Policy</td>
                                    <td>Enabled "Block low-reputation agents"</td>
                                    <td><span style="color: #10b981;">Applied</span></td>
                                </tr>
                                <tr>
                                    <td>13:58:41</td>
                                    <td><span class="badge badge-warning">Anomaly Detected</span></td>
                                    <td>batch-processor</td>
                                    <td>N/A</td>
                                    <td>Unusual call volume spike</td>
                                    <td><span style="color: #f59e0b;">Investigating</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function showScreen(screenId) {
            // Hide all screens
            document.querySelectorAll('.screen').forEach(screen => {
                screen.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected screen
            document.getElementById(screenId).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
    </script>
</body>
</html>