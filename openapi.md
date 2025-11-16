This is a modular OpenAPI 3.1 spec laid out as multiple YAML “files” in a single markdown response so Windsurf / Claude Code can work with it easily.

You can literally create this directory structure and paste each fenced YAML block into the corresponding file.

Directory Layout
openapi/
  openapi.yaml
  paths/
    runtime.yaml
    agents.yaml
    ingest.yaml
    traces.yaml
    spans.yaml
    replay.yaml
    cost.yaml
    alerts.yaml
    tenants.yaml
    policies.yaml
    connectors.yaml
    health.yaml
  components/
    schemas/
      AgentExecution.yaml
      Agent.yaml
      Trace.yaml
      Span.yaml
      Edge.yaml
      ToolCall.yaml
      CostRecord.yaml
      CostSummary.yaml
      PIIFlags.yaml
      PIIConfig.yaml
      PolicyBundle.yaml
      Tenant.yaml
      Connector.yaml
      ConnectorHealth.yaml
      AlertRule.yaml
      AlertEvent.yaml
      ReplayRequest.yaml
      ReplayResult.yaml
      AuditEvent.yaml
      ErrorResponse.yaml
      Pagination.yaml
    security/
      SecuritySchemes.yaml

openapi/openapi.yaml
openapi: 3.1.0
info:
  title: AgentOS / AgentFlow Unified API
  version: 1.0.0
  description: |
    Unified observability and runtime API for multi-platform AI agent systems.
    Supports native runtime, external connectors, traces, cost, PII, governance, alerts, and replay.

servers:
  - url: https://api.agentflow.example.com
    description: Production
  - url: https://staging.api.agentflow.example.com
    description: Staging

tags:
  - name: Runtime
    description: Native agent runtime deployment and invocation
  - name: Agents
    description: Agent registry and metadata
  - name: Ingest
    description: Telemetry ingestion endpoints
  - name: Traces
    description: Trace and span queries
  - name: Replay
    description: Deterministic replay and debugging
  - name: Cost
    description: CostOps APIs
  - name: Alerts
    description: Alert rules and events
  - name: Tenants
    description: Tenant management and onboarding
  - name: Policies
    description: Governance and policy bundles
  - name: Connectors
    description: External platform connectors
  - name: Health
    description: Health and readiness checks

paths:
  # Runtime
  /v1/runtime/deploy:
    $ref: ./paths/runtime.yaml#/paths/~1v1~1runtime~1deploy
  /v1/runtime/rollback:
    $ref: ./paths/runtime.yaml#/paths/~1v1~1runtime~1rollback
  /v1/runtime/invoke/{agentId}:
    $ref: ./paths/runtime.yaml#/paths/~1v1~1runtime~1invoke~1{agentId}

  # Agents
  /v1/agents:
    $ref: ./paths/agents.yaml#/paths/~1v1~1agents
  /v1/agents/{agentId}:
    $ref: ./paths/agents.yaml#/paths/~1v1~1agents~1{agentId}
  /v1/agents/{agentId}/health:
    $ref: ./paths/agents.yaml#/paths/~1v1~1agents~1{agentId}~1health

  # Ingest
  /v1/telemetry/events:
    $ref: ./paths/ingest.yaml#/paths/~1v1~1telemetry~1events

  # Traces & Spans
  /v1/traces/{traceId}:
    $ref: ./paths/traces.yaml#/paths/~1v1~1traces~1{traceId}
  /v1/traces/search:
    $ref: ./paths/traces.yaml#/paths/~1v1~1traces~1search
  /v1/spans/{spanId}:
    $ref: ./paths/spans.yaml#/paths/~1v1~1spans~1{spanId}
  /v1/edges/{edgeId}:
    $ref: ./paths/spans.yaml#/paths/~1v1~1edges~1{edgeId}

  # Replay
  /v1/replay/{spanId}:
    $ref: ./paths/replay.yaml#/paths/~1v1~1replay~1{spanId}

  # Cost
  /v1/cost/records:
    $ref: ./paths/cost.yaml#/paths/~1v1~1cost~1records
  /v1/cost/summary:
    $ref: ./paths/cost.yaml#/paths/~1v1~1cost~1summary

  # Alerts
  /v1/alerts/rules:
    $ref: ./paths/alerts.yaml#/paths/~1v1~1alerts~1rules
  /v1/alerts/rules/{ruleId}:
    $ref: ./paths/alerts.yaml#/paths/~1v1~1alerts~1rules~1{ruleId}
  /v1/alerts/events:
    $ref: ./paths/alerts.yaml#/paths/~1v1~1alerts~1events

  # Tenants
  /v1/tenants:
    $ref: ./paths/tenants.yaml#/paths/~1v1~1tenants
  /v1/tenants/{tenantId}:
    $ref: ./paths/tenants.yaml#/paths/~1v1~1tenants~1{tenantId}

  # Policies
  /v1/policies/bundles:
    $ref: ./paths/policies.yaml#/paths/~1v1~1policies~1bundles
  /v1/policies/enforce:
    $ref: ./paths/policies.yaml#/paths/~1v1~1policies~1enforce

  # Connectors
  /v1/connectors:
    $ref: ./paths/connectors.yaml#/paths/~1v1~1connectors
  /v1/connectors/{connectorId}:
    $ref: ./paths/connectors.yaml#/paths/~1v1~1connectors~1{connectorId}
  /v1/connectors/{connectorId}/health:
    $ref: ./paths/connectors.yaml#/paths/~1v1~1connectors~1{connectorId}~1health

  # Health
  /v1/health:
    $ref: ./paths/health.yaml#/paths/~1v1~1health
  /v1/health/ready:
    $ref: ./paths/health.yaml#/paths/~1v1~1health~1ready

components:
  securitySchemes:
    $ref: ./components/security/SecuritySchemes.yaml#/securitySchemes
  schemas:
    AgentExecution:
      $ref: ./components/schemas/AgentExecution.yaml
    Agent:
      $ref: ./components/schemas/Agent.yaml
    Trace:
      $ref: ./components/schemas/Trace.yaml
    Span:
      $ref: ./components/schemas/Span.yaml
    Edge:
      $ref: ./components/schemas/Edge.yaml
    ToolCall:
      $ref: ./components/schemas/ToolCall.yaml
    CostRecord:
      $ref: ./components/schemas/CostRecord.yaml
    CostSummary:
      $ref: ./components/schemas/CostSummary.yaml
    PIIFlags:
      $ref: ./components/schemas/PIIFlags.yaml
    PIIConfig:
      $ref: ./components/schemas/PIIConfig.yaml
    PolicyBundle:
      $ref: ./components/schemas/PolicyBundle.yaml
    Tenant:
      $ref: ./components/schemas/Tenant.yaml
    Connector:
      $ref: ./components/schemas/Connector.yaml
    ConnectorHealth:
      $ref: ./components/schemas/ConnectorHealth.yaml
    AlertRule:
      $ref: ./components/schemas/AlertRule.yaml
    AlertEvent:
      $ref: ./components/schemas/AlertEvent.yaml
    ReplayRequest:
      $ref: ./components/schemas/ReplayRequest.yaml
    ReplayResult:
      $ref: ./components/schemas/ReplayResult.yaml
    AuditEvent:
      $ref: ./components/schemas/AuditEvent.yaml
    ErrorResponse:
      $ref: ./components/schemas/ErrorResponse.yaml
    Pagination:
      $ref: ./components/schemas/Pagination.yaml

security:
  - OAuth2: [read, write]
  - ApiKeyAuth: []

openapi/components/security/SecuritySchemes.yaml
securitySchemes:
  OAuth2:
    type: oauth2
    description: OAuth2 / OIDC with tenant-scoped roles.
    flows:
      authorizationCode:
        authorizationUrl: https://auth.agentflow.example.com/oauth2/authorize
        tokenUrl: https://auth.agentflow.example.com/oauth2/token
        scopes:
          read: Read access to resources
          write: Write access to resources
          admin: Tenant administrative operations

  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
    description: Tenant-scoped API key for programmatic access.

  MTLS:
    type: mutualTLS
    description: Optional mTLS for connector-to-platform communication.

PATH FILES
openapi/paths/runtime.yaml
paths:
  /v1/runtime/deploy:
    post:
      tags: [Runtime]
      summary: Deploy a new agent version to the native runtime.
      operationId: deployRuntimeAgent
      security:
        - OAuth2: [write]
        - ApiKeyAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, sourceUrl]
              properties:
                name:
                  type: string
                  description: Human-friendly agent name.
                sourceUrl:
                  type: string
                  description: URL to git repo or artifact registry.
                runtimeConfig:
                  type: object
                  description: Runtime configuration (env vars, resources).
                timeoutSeconds:
                  type: integer
                  default: 60
                maxConcurrency:
                  type: integer
                  default: 10
      responses:
        '201':
          description: Agent deployed successfully.
          content:
            application/json:
              schema:
                type: object
                required: [agentId, versionId]
                properties:
                  agentId:
                    type: string
                  versionId:
                    type: string
                  status:
                    type: string
                    enum: [deploying, active]
        '400':
          description: Invalid request payload.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml
        '401':
          description: Unauthorized.

  /v1/runtime/rollback:
    post:
      tags: [Runtime]
      summary: Roll back a runtime agent to the previous version.
      operationId: rollbackRuntimeAgent
      security:
        - OAuth2: [write]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [agentId]
              properties:
                agentId:
                  type: string
                targetVersionId:
                  type: string
                  nullable: true
                  description: |
                    Optional explicit version to roll back to.
                    If omitted, roll back one version.
      responses:
        '200':
          description: Rollback completed.
          content:
            application/json:
              schema:
                type: object
                properties:
                  agentId:
                    type: string
                  versionId:
                    type: string
                  status:
                    type: string
                    enum: [active]
        '404':
          description: Agent or version not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

  /v1/runtime/invoke/{agentId}:
    post:
      tags: [Runtime]
      summary: Invoke a native runtime agent and emit traces.
      operationId: invokeRuntimeAgent
      security:
        - OAuth2: [write]
        - ApiKeyAuth: []
      parameters:
        - name: agentId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [input]
              properties:
                input:
                  type: string
                  description: Raw user input.
                context:
                  type: object
                  description: Arbitrary key/value context.
                traceOptions:
                  type: object
                  properties:
                    traceparent:
                      type: string
                      description: OTel traceparent header for propagation.
      responses:
        '200':
          description: Invocation completed.
          content:
            application/json:
              schema:
                type: object
                properties:
                  traceId:
                    type: string
                  output:
                    type: string
                  cost:
                    $ref: ../components/schemas/CostRecord.yaml
        '202':
          description: Invocation accepted for async processing.
        '400':
          description: Invalid invocation request.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/agents.yaml
paths:
  /v1/agents:
    get:
      tags: [Agents]
      summary: List agents for the current tenant.
      operationId: listAgents
      security:
        - OAuth2: [read]
      parameters:
        - name: platform
          in: query
          schema:
            type: string
        - name: environment
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
        - name: cursor
          in: query
          schema:
            type: string
      responses:
        '200':
          description: A paginated list of agents.
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: ../components/schemas/Agent.yaml
                  pagination:
                    $ref: ../components/schemas/Pagination.yaml

    post:
      tags: [Agents]
      summary: Register a new external agent.
      operationId: createAgent
      security:
        - OAuth2: [write]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              allOf:
                - $ref: ../components/schemas/Agent.yaml
              required: [name, platform]
      responses:
        '201':
          description: Agent registered.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Agent.yaml
        '400':
          description: Invalid agent payload.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

  /v1/agents/{agentId}:
    get:
      tags: [Agents]
      summary: Get a single agent by ID.
      operationId: getAgent
      security:
        - OAuth2: [read]
      parameters:
        - name: agentId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Agent details.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Agent.yaml
        '404':
          description: Agent not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

    patch:
      tags: [Agents]
      summary: Update an agent’s metadata.
      operationId: updateAgent
      security:
        - OAuth2: [write]
      parameters:
        - name: agentId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/Agent.yaml
      responses:
        '200':
          description: Updated agent.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Agent.yaml

  /v1/agents/{agentId}/health:
    get:
      tags: [Agents]
      summary: Get health check status of the agent.
      operationId: getAgentHealth
      security:
        - OAuth2: [read]
      parameters:
        - name: agentId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Agent health.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ConnectorHealth.yaml
        '404':
          description: Agent not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/ingest.yaml
paths:
  /v1/telemetry/events:
    post:
      tags: [Ingest]
      summary: Ingest one or more telemetry events into the unified pipeline.
      operationId: ingestTelemetryEvents
      security:
        - ApiKeyAuth: []
        - MTLS: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [events]
              properties:
                events:
                  type: array
                  items:
                    $ref: ../components/schemas/AgentExecution.yaml
      responses:
        '202':
          description: Events accepted for processing.
          content:
            application/json:
              schema:
                type: object
                properties:
                  accepted:
                    type: integer
                  rejected:
                    type: integer
        '400':
          description: Invalid payload.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/traces.yaml
paths:
  /v1/traces/{traceId}:
    get:
      tags: [Traces]
      summary: Get a full trace by ID.
      operationId: getTrace
      security:
        - OAuth2: [read]
      parameters:
        - name: traceId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Trace details.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Trace.yaml
        '404':
          description: Trace not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

  /v1/traces/search:
    post:
      tags: [Traces]
      summary: Search traces by filters and full-text.
      operationId: searchTraces
      security:
        - OAuth2: [read]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                  description: Full-text query.
                filters:
                  type: object
                  properties:
                    platform:
                      type: string
                    agentId:
                      type: string
                    status:
                      type: string
                    piiDetected:
                      type: boolean
                    minCostUsd:
                      type: number
                    maxCostUsd:
                      type: number
                    from:
                      type: string
                      format: date-time
                    to:
                      type: string
                      format: date-time
                limit:
                  type: integer
                  default: 50
                cursor:
                  type: string
      responses:
        '200':
          description: Search results.
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: ../components/schemas/Trace.yaml
                  pagination:
                    $ref: ../components/schemas/Pagination.yaml

openapi/paths/spans.yaml
paths:
  /v1/spans/{spanId}:
    get:
      tags: [Traces]
      summary: Get a single span by ID.
      operationId: getSpan
      security:
        - OAuth2: [read]
      parameters:
        - name: spanId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Span details.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Span.yaml
        '404':
          description: Span not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

  /v1/edges/{edgeId}:
    get:
      tags: [Traces]
      summary: Get an inter-span edge by ID.
      operationId: getEdge
      security:
        - OAuth2: [read]
      parameters:
        - name: edgeId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edge details.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Edge.yaml
        '404':
          description: Edge not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/replay.yaml
paths:
  /v1/replay/{spanId}:
    post:
      tags: [Replay]
      summary: Replay a span deterministically.
      operationId: replaySpan
      security:
        - OAuth2: [write]
      parameters:
        - name: spanId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: false
        content:
          application/json:
            schema:
              $ref: ../components/schemas/ReplayRequest.yaml
      responses:
        '200':
          description: Replay result and parity stats.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ReplayResult.yaml
        '404':
          description: Span not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/cost.yaml
paths:
  /v1/cost/records:
    get:
      tags: [Cost]
      summary: List raw cost records.
      operationId: listCostRecords
      security:
        - OAuth2: [read]
      parameters:
        - name: from
          in: query
          schema:
            type: string
            format: date-time
        - name: to
          in: query
          schema:
            type: string
            format: date-time
        - name: agentId
          in: query
          schema:
            type: string
        - name: team
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
        - name: cursor
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Cost records.
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: ../components/schemas/CostRecord.yaml
                  pagination:
                    $ref: ../components/schemas/Pagination.yaml

  /v1/cost/summary:
    get:
      tags: [Cost]
      summary: Get aggregated cost summary.
      operationId: getCostSummary
      security:
        - OAuth2: [read]
      parameters:
        - name: groupBy
          in: query
          schema:
            type: string
            enum: [agent, team, platform, environment, customer]
        - name: from
          in: query
          schema:
            type: string
            format: date-time
        - name: to
          in: query
          schema:
            type: string
            format: date-time
      responses:
        '200':
          description: Cost summary.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/CostSummary.yaml

openapi/paths/alerts.yaml
paths:
  /v1/alerts/rules:
    get:
      tags: [Alerts]
      summary: List alert rules.
      operationId: listAlertRules
      security:
        - OAuth2: [read]
      responses:
        '200':
          description: Alert rules.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: ../components/schemas/AlertRule.yaml

    post:
      tags: [Alerts]
      summary: Create an alert rule.
      operationId: createAlertRule
      security:
        - OAuth2: [write]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/AlertRule.yaml
      responses:
        '201':
          description: Created alert rule.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/AlertRule.yaml

  /v1/alerts/rules/{ruleId}:
    patch:
      tags: [Alerts]
      summary: Update an alert rule.
      operationId: updateAlertRule
      security:
        - OAuth2: [write]
      parameters:
        - name: ruleId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/AlertRule.yaml
      responses:
        '200':
          description: Updated alert rule.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/AlertRule.yaml

    delete:
      tags: [Alerts]
      summary: Delete an alert rule.
      operationId: deleteAlertRule
      security:
        - OAuth2: [write]
      parameters:
        - name: ruleId
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Deleted.

  /v1/alerts/events:
    get:
      tags: [Alerts]
      summary: List alert events.
      operationId: listAlertEvents
      security:
        - OAuth2: [read]
      parameters:
        - name: from
          in: query
          schema:
            type: string
            format: date-time
        - name: to
          in: query
          schema:
            type: string
            format: date-time
        - name: ruleId
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Alert events.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: ../components/schemas/AlertEvent.yaml

openapi/paths/tenants.yaml
paths:
  /v1/tenants:
    get:
      tags: [Tenants]
      summary: List tenants (admin only).
      operationId: listTenants
      security:
        - OAuth2: [admin]
      responses:
        '200':
          description: Tenants.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: ../components/schemas/Tenant.yaml

    post:
      tags: [Tenants]
      summary: Create a new tenant (admin only).
      operationId: createTenant
      security:
        - OAuth2: [admin]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/Tenant.yaml
      responses:
        '201':
          description: Tenant created.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Tenant.yaml

  /v1/tenants/{tenantId}:
    get:
      tags: [Tenants]
      summary: Get tenant details.
      operationId: getTenant
      security:
        - OAuth2: [admin]
      parameters:
        - name: tenantId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Tenant details.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Tenant.yaml
        '404':
          description: Tenant not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/policies.yaml
paths:
  /v1/policies/bundles:
    get:
      tags: [Policies]
      summary: List policy bundles for the tenant.
      operationId: listPolicyBundles
      security:
        - OAuth2: [read]
      responses:
        '200':
          description: Policy bundles.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: ../components/schemas/PolicyBundle.yaml

    post:
      tags: [Policies]
      summary: Upload or update a policy bundle.
      operationId: upsertPolicyBundle
      security:
        - OAuth2: [write]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/PolicyBundle.yaml
      responses:
        '201':
          description: Policy bundle created or updated.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/PolicyBundle.yaml

  /v1/policies/enforce:
    post:
      tags: [Policies]
      summary: Evaluate a policy decision for a hypothetical or real request.
      operationId: enforcePolicy
      security:
        - OAuth2: [read]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [input]
              properties:
                input:
                  type: object
                  description: OPA-style input document.
      responses:
        '200':
          description: Policy decision.
          content:
            application/json:
              schema:
                type: object
                properties:
                  allow:
                    type: boolean
                  obligations:
                    type: array
                    items:
                      type: string

openapi/paths/connectors.yaml
paths:
  /v1/connectors:
    get:
      tags: [Connectors]
      summary: List available connectors for the tenant.
      operationId: listConnectors
      security:
        - OAuth2: [read]
      responses:
        '200':
          description: Connectors.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: ../components/schemas/Connector.yaml

    post:
      tags: [Connectors]
      summary: Register a new connector instance (e.g., GCP Agent Engine, Salesforce).
      operationId: createConnector
      security:
        - OAuth2: [write]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/Connector.yaml
      responses:
        '201':
          description: Connector created.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Connector.yaml

  /v1/connectors/{connectorId}:
    get:
      tags: [Connectors]
      summary: Get connector details.
      operationId: getConnector
      security:
        - OAuth2: [read]
      parameters:
        - name: connectorId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Connector details.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Connector.yaml
        '404':
          description: Connector not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

    patch:
      tags: [Connectors]
      summary: Update connector configuration.
      operationId: updateConnector
      security:
        - OAuth2: [write]
      parameters:
        - name: connectorId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: ../components/schemas/Connector.yaml
      responses:
        '200':
          description: Updated connector.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/Connector.yaml

  /v1/connectors/{connectorId}/health:
    get:
      tags: [Connectors]
      summary: Get the runtime health of a connector instance.
      operationId: getConnectorHealth
      security:
        - OAuth2: [read]
      parameters:
        - name: connectorId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Connector health.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ConnectorHealth.yaml
        '404':
          description: Connector not found.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

openapi/paths/health.yaml
paths:
  /v1/health:
    get:
      tags: [Health]
      summary: Liveness probe.
      operationId: health
      responses:
        '200':
          description: Service is alive.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [ok]

  /v1/health/ready:
    get:
      tags: [Health]
      summary: Readiness probe.
      operationId: readiness
      responses:
        '200':
          description: Service is ready to receive traffic.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [ready]
        '503':
          description: Service is not ready.
          content:
            application/json:
              schema:
                $ref: ../components/schemas/ErrorResponse.yaml

SCHEMA FILES

I’ll keep these concise but expressive; you can extend fields as needed.

openapi/components/schemas/AgentExecution.yaml
type: object
description: Unified schema for a single agent execution event.
required:
  - id
  - platform
  - timestamp
  - agent
  - execution
  - context
properties:
  id:
    type: string
    description: Unique event ID.
  platform:
    type: string
    description: Source platform identifier.
    example: salesforce_agentforce
  tenantId:
    type: string
  timestamp:
    type: string
    format: date-time
  agent:
    type: object
    required: [id, name, version, type]
    properties:
      id:
        type: string
      name:
        type: string
      version:
        type: string
      type:
        type: string
        enum: [conversational, workflow, analytical]
  execution:
    type: object
    required: [traceId, spanId, durationMs, status]
    properties:
      traceId:
        type: string
      spanId:
        type: string
      parentSpanId:
        type: string
        nullable: true
      durationMs:
        type: integer
      status:
        type: string
        enum: [success, failure, timeout]
  llm:
    type: object
    nullable: true
    properties:
      provider:
        type: string
      model:
        type: string
      inputTokens:
        type: integer
      outputTokens:
        type: integer
      totalCostUsd:
        type: number
        format: float
  io:
    type: object
    properties:
      input:
        type: string
        description: Sanitized input.
      output:
        type: string
        description: Sanitized output.
      piiDetected:
        type: boolean
      piiTypes:
        type: array
        items:
          type: string
  context:
    type: object
    properties:
      userId:
        type: string
      sessionId:
        type: string
      environment:
        type: string
        enum: [production, staging, development]
      team:
        type: string
      tags:
        type: object
        additionalProperties:
          type: string
  toolsCalled:
    type: array
    items:
      $ref: ./ToolCall.yaml

openapi/components/schemas/Agent.yaml
type: object
description: Logical agent metadata.
required: [id, name, platform]
properties:
  id:
    type: string
  name:
    type: string
  description:
    type: string
  platform:
    type: string
    description: |
      Platform where this agent runs (e.g., runtime, salesforce_agentforce, gcp_agent_engine).
  environment:
    type: string
    enum: [production, staging, development]
  team:
    type: string
  version:
    type: string
  runtimeType:
    type: string
    enum: [native, external]
  telemetryBadge:
    type: string
    enum: [verified, partial, external]
  createdAt:
    type: string
    format: date-time
  updatedAt:
    type: string
    format: date-time

openapi/components/schemas/Trace.yaml
type: object
description: A distributed trace across one or more agents/platforms.
required: [traceId, spans]
properties:
  traceId:
    type: string
  rootSpanId:
    type: string
  spans:
    type: array
    items:
      $ref: ./Span.yaml
  edges:
    type: array
    items:
      $ref: ./Edge.yaml
  cost:
    $ref: ./CostRecord.yaml
  piiFlags:
    $ref: ./PIIFlags.yaml
  createdAt:
    type: string
    format: date-time

openapi/components/schemas/Span.yaml
type: object
description: A single span within a trace.
required:
  - spanId
  - traceId
  - name
  - startTime
  - endTime
properties:
  spanId:
    type: string
  traceId:
    type: string
  parentSpanId:
    type: string
    nullable: true
  name:
    type: string
  serviceName:
    type: string
  kind:
    type: string
    enum: [internal, server, client, producer, consumer]
  attributes:
    type: object
    additionalProperties:
      type: string
  startTime:
    type: string
    format: date-time
  endTime:
    type: string
    format: date-time
  status:
    type: string
    enum: [ok, error]
  statusMessage:
    type: string
    nullable: true
  toolCalls:
    type: array
    items:
      $ref: ./ToolCall.yaml
  piiFlags:
    $ref: ./PIIFlags.yaml

openapi/components/schemas/Edge.yaml
type: object
description: Directed edge between spans (for inter-agent flows).
required: [id, fromSpanId, toSpanId]
properties:
  id:
    type: string
  fromSpanId:
    type: string
  toSpanId:
    type: string
  type:
    type: string
    enum: [message, tool_call, dependency]
  metadata:
    type: object
    additionalProperties:
      type: string

openapi/components/schemas/ToolCall.yaml
type: object
description: Tool call performed by an agent or span.
required: [name, durationMs, status]
properties:
  name:
    type: string
  durationMs:
    type: integer
  status:
    type: string
    enum: [success, failure, timeout]
  request:
    type: string
    nullable: true
  response:
    type: string
    nullable: true

openapi/components/schemas/CostRecord.yaml
type: object
description: Cost record for a specific execution or span.
required:
  - traceId
  - amountUsd
properties:
  traceId:
    type: string
  spanId:
    type: string
    nullable: true
  agentId:
    type: string
    nullable: true
  team:
    type: string
    nullable: true
  platform:
    type: string
    nullable: true
  provider:
    type: string
    nullable: true
  model:
    type: string
    nullable: true
  inputTokens:
    type: integer
    nullable: true
  outputTokens:
    type: integer
    nullable: true
  amountUsd:
    type: number
    format: float
  currency:
    type: string
    default: USD
  timestamp:
    type: string
    format: date-time

openapi/components/schemas/CostSummary.yaml
type: object
description: Aggregated cost summary.
properties:
  groupBy:
    type: string
  from:
    type: string
    format: date-time
  to:
    type: string
    format: date-time
  totals:
    type: array
    items:
      type: object
      properties:
        key:
          type: string
          description: Group key (agentId, team name, platform etc.).
        amountUsd:
          type: number
          format: float
        executions:
          type: integer

openapi/components/schemas/PIIFlags.yaml
type: object
description: PII detection flags attached to an event/span/trace.
properties:
  piiDetected:
    type: boolean
  piiTypes:
    type: array
    items:
      type: string
  redactionApplied:
    type: boolean
  redactionStrategy:
    type: string
    enum: [mask, hash, remove, encrypt]

openapi/components/schemas/PIIConfig.yaml
type: object
description: Tenant-level PII configuration.
properties:
  enabled:
    type: boolean
  regexPatterns:
    type: array
    items:
      type: string
  nerModels:
    type: array
    items:
      type: string
  defaultStrategy:
    type: string
    enum: [mask, hash, remove, encrypt]

openapi/components/schemas/PolicyBundle.yaml
type: object
description: Policy bundle for OPA.
required: [id, name, rules]
properties:
  id:
    type: string
  name:
    type: string
  description:
    type: string
  rules:
    type: string
    description: Raw Rego or JSON bundle, base64-encoded or inlined.
  version:
    type: string
  createdAt:
    type: string
    format: date-time
  updatedAt:
    type: string
    format: date-time

openapi/components/schemas/Tenant.yaml
type: object
description: Tenant (organization) configuration.
required: [id, name]
properties:
  id:
    type: string
  name:
    type: string
  slug:
    type: string
  createdAt:
    type: string
    format: date-time
  piiConfig:
    $ref: ./PIIConfig.yaml
  retentionDays:
    type: integer
    description: Days to retain hot data.
  status:
    type: string
    enum: [active, suspended, deleted]

openapi/components/schemas/Connector.yaml
type: object
description: Connector configuration (e.g., GCP, Salesforce, LangChain).
required: [id, type, name]
properties:
  id:
    type: string
  type:
    type: string
    enum:
      - langchain
      - gcp_agent_engine
      - salesforce_agentforce
      - azure_copilot
      - generic_webhook
  name:
    type: string
  description:
    type: string
  config:
    type: object
    description: Provider-specific configuration.
  status:
    type: string
    enum: [active, inactive, error]
  createdAt:
    type: string
    format: date-time
  updatedAt:
    type: string
    format: date-time

openapi/components/schemas/ConnectorHealth.yaml
type: object
description: Connector or agent health status.
properties:
  status:
    type: string
    enum: [healthy, degraded, unhealthy]
  lastCheckAt:
    type: string
    format: date-time
  details:
    type: object
    additionalProperties:
      type: string

openapi/components/schemas/AlertRule.yaml
type: object
description: Alert rule configuration.
required: [id, name, type, expression, channels]
properties:
  id:
    type: string
  name:
    type: string
  description:
    type: string
  type:
    type: string
    enum: [threshold, anomaly, compliance, availability]
  expression:
    type: string
    description: |
      Query or threshold expression, e.g. "error_rate > 0.05 for 5m".
  enabled:
    type: boolean
    default: true
  channels:
    type: array
    items:
      type: string
      enum: [email, slack, pagerduty, webhook]
  createdAt:
    type: string
    format: date-time
  updatedAt:
    type: string
    format: date-time

openapi/components/schemas/AlertEvent.yaml
type: object
description: Fired alert event.
required: [id, ruleId, status, triggeredAt]
properties:
  id:
    type: string
  ruleId:
    type: string
  status:
    type: string
    enum: [open, acknowledged, resolved]
  message:
    type: string
  triggeredAt:
    type: string
    format: date-time
  resolvedAt:
    type: string
    format: date-time
    nullable: true
  context:
    type: object
    additionalProperties:
      type: string

openapi/components/schemas/ReplayRequest.yaml
type: object
description: Options for replaying a span.
properties:
  forceModelVersion:
    type: string
    nullable: true
  overrideParameters:
    type: object
    description: Optional override of model parameters (temperature etc.).
  dryRun:
    type: boolean
    default: false

openapi/components/schemas/ReplayResult.yaml
type: object
description: Replay results and parity stats.
required: [spanId, originalOutput, replayedOutput, parity]
properties:
  spanId:
    type: string
  originalOutput:
    type: string
  replayedOutput:
    type: string
  parity:
    type: string
    enum: [identical, similar, divergent]
  score:
    type: number
    format: float
    description: Similarity score between 0 and 1.
  diff:
    type: string
    description: Human-readable diff representation.

openapi/components/schemas/AuditEvent.yaml
type: object
description: Audit log event (access, config, policy).
required: [id, actor, action, timestamp]
properties:
  id:
    type: string
  actor:
    type: string
  actorType:
    type: string
    enum: [user, api_key, system]
  action:
    type: string
  resource:
    type: string
  tenantId:
    type: string
  timestamp:
    type: string
    format: date-time
  details:
    type: object
    additionalProperties:
      type: string

openapi/components/schemas/ErrorResponse.yaml
type: object
description: Standard error response object.
required: [code, message]
properties:
  code:
    type: string
  message:
    type: string
  requestId:
    type: string
    description: Correlation ID for troubleshooting.
  details:
    type: object
    additionalProperties:
      type: string

openapi/components/schemas/Pagination.yaml
type: object
description: Cursor-based pagination metadata.
properties:
  nextCursor:
    type: string
    nullable: true
  previousCursor:
    type: string
    nullable: true
  limit:
    type: integer
  hasMore:
    type: boolean