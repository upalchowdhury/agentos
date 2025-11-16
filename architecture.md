ARCHITECTURE.md

AgentOS/AgentFlow Unified Architecture Blueprint
Version: 1.0
Last Updated: 2025-11-15
Audience: Platform engineers, backend developers, infra leads, observability engineers.

Table of Contents

Overview

System Goals & Principles

High-Level Architecture Diagram

Component Map

Data Flow Overview

Ingestion Architecture

Buffer Layer (Kafka / PubSub)

Stream Processing Layer

Storage Architecture

Runtime Execution Architecture

API & Gateway Layer

Policy, Compliance, PII

Identity, Authentication & Authorization

Observability of the Platform

Tenancy & Data Isolation Model

Scaling, HA, Failover

Deployment Topology

SLOs, SLAs, KPIs

Data Lifecycle & Retention

Appendix: Sequence Diagrams

1. Overview

AgentOS/AgentFlow is a multi-platform observability and runtime system for AI agents. It unifies:

Telemetry ingestion from dozens of external agent platforms

First-class runtime to execute agents natively

Trace/cost/PII governance

Multi-tenant dashboards and querying

Compliance and audit

Replay, debugging, and anomaly detection

This file defines the full production-grade architecture.

2. System Goals & Principles
Functional Goals

Unified trace collection from runtime + external agent frameworks

Real-time analytics (<5 min P99 from event → searchable)

PII-safe ingestion with redaction and compliance audit

CostOps with token-level accounting

Replay & span-level debugging

Non-Functional Goals

99.9% uptime (SaaS)

99.99% pipeline reliability (buffer + replay support)

Multi-tenant isolation

Backpressure resilience

SOC2-ready

Principles

Everything is schema-based

All ingestion → buffer → stream processor → storage

All processing is idempotent

Storage layers are tiered: Hot → Warm → Cold

All endpoints & internal comms instrumented with OTel

3. High-Level Architecture Diagram
                       ┌───────────────────────────────────────────┐
                       │               CLIENT UI                    │
                       │  React / Next.js (Trace Explorer, Cost,   │
                       │  Catalog, Alerts, Settings)               │
                       └───────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             API + GATEWAY LAYER                             │
│   Kong / Envoy → FastAPI/Go services → OPA → AuthN/AuthZ → Rate Limits      │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HOT STORAGE / QUERY LAYER                            │
│   Traces (Tempo/Jaeger) | Logs (OpenSearch/Loki) | Metrics (Prom/Mimir)     │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAM PROCESSING LAYER                            │
│        Flink / Kafka Streams → PII → Normalization → Cost → OTLP            │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 BUFFER LAYER                                │
│                         Kafka / PubSub / Kinesis                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             INGESTION LAYER                                 │
│  LangChain (OTel SDK) | GCP Logging | Salesforce Events | Copilot | Webhooks│
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AgentOS RUNTIME (Native)                            │
│   Deploy → Invoke → ATP Traces → Unified Schema                             │
└─────────────────────────────────────────────────────────────────────────────┘
                       ┌───────────────────────────────────────────┐
                       │               CLIENT UI                    │
                       │  React / Next.js (Trace Explorer, Cost,   │
                       │  Catalog, Alerts, Settings)               │
                       └───────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             API + GATEWAY LAYER                             │
│   Kong / Envoy → FastAPI/Go services → OPA → AuthN/AuthZ → Rate Limits      │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HOT STORAGE / QUERY LAYER                            │
│   Traces (Tempo/Jaeger) | Logs (OpenSearch/Loki) | Metrics (Prom/Mimir)     │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAM PROCESSING LAYER                            │
│        Flink / Kafka Streams → PII → Normalization → Cost → OTLP            │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 BUFFER LAYER                                │
│                         Kafka / PubSub / Kinesis                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             INGESTION LAYER                                 │
│  LangChain (OTel SDK) | GCP Logging | Salesforce Events | Copilot | Webhooks│
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AgentOS RUNTIME (Native)                            │
│   Deploy → Invoke → ATP Traces → Unified Schema                             │
└─────────────────────────────────────────────────────────────────────────────┘

4. Component Map
Component	Description
Connectors	Platform-specific ingestion endpoints and log exporters
Ingestion API	Accepts webhooks and OTel pipeline events
Kafka/PubSub	Buffer + replay
Stream Processor	Normalization, PII, cost enrichment
OTel Gateway	Converts internal events into OTLP for Tempo/Mimir
Storage Layer	Traces/logs/metrics + cold storage
API Layer	Query, replay, cost, governance, agents
UI	Multi-pane dashboards
Policy Engine (OPA)	RBAC, ABAC, obligations
Runtime	Sandbox to execute agents with first-class traces
5. Data Flow Overview
Native runtime
Deploy → Invoke → ATP Steps → Unified Schema → Kafka → Processor → Tempo/OpenSearch/UI

External platforms

Examples:

LangChain:
OTel SDK → Collector → Ingestion API → Kafka → Processor → Storage

GCP Agent Engine:
Cloud Logging → PubSub → Cloud Function → Ingestion API → Kafka → Processor

Salesforce Agentforce:
Event Monitoring API → Poller → Kafka → Processor

6. Ingestion Architecture
Ingestion methods supported:
Platform	Method
LangChain, LlamaIndex	OTel SDK → OTel Collector
GCP Agent Engine	Cloud Logging → Pub/Sub → Cloud Function
Salesforce Agentforce	Event Monitoring API polling
Microsoft Copilot Studio	EventHub → Azure Function
REST/Generic Agents	Webhook receiver
Native runtime	Direct internal publish
Key ingestion services:

ingest-api

connectors/*

gcp-function

salesforce-poller

azure-function

Validation

JSON schema validation on receipt

Trace correlation (trace_id/span_id)

Initial PII pre-filter

Rate limiting

Per-tenant

Per-IP

Per-platform

Deduplication

Based on:

event_id

timestamp

hash(payload)

7. Buffer Layer

Kafka (preferred) or Cloud Pub/Sub.

Requirements:

7-day retention

3x replication

6–12 partitions per tenant (configurable)

Exactly-once semantics (Flink + Kafka)

Topics:
raw.langchain
raw.gcp
raw.salesforce
raw.azure
raw.runtime
raw.webhooks
normalized.events

8. Stream Processing Layer
Technologies:

Apache Flink (primary)

Kafka Streams fallback for smaller deployments

Processor Responsibilities:
1. Schema Validation

Errors → Dead-letter queue (dlq.invalid_schema).

2. PII Detection & Redaction

Regex: email, phone, SSN, credit card

NER: person, org, address, custom

Redaction modes: mask, hash, remove

3. Normalization

Transform into unified schema:

agent_execution root

llm block

tools_called

context

4. Enrichment

Cost calculation (input_tokens * price)

GeoIP lookup

Team + tenant assignment

5. Sampling

Tail sampling

Error-always

6. Transformation to OTLP

For traces/logs/metrics export.

9. Storage Architecture
Hot Storage (7–30 days)
Purpose	Technology
Traces	Tempo or Jaeger
Logs	OpenSearch or Loki
Metrics	Prometheus + Mimir
Rationale:

Tempo is cheap and horizontally scalable

OpenSearch supports full-text queries

Mimir provides multi-tenant metrics

Warm/Cold Storage

BigQuery, Snowflake, or S3 + Athena

Retention: 12–365 days

Partitioning: tenant_id/date/platform

10. Runtime Execution Architecture
Components:

runtime-controller

runtime-worker

invoke-service

deploy-service

Flow:
POST /runtime/deploy → Build container → Push → Register version  
POST /runtime/invoke → New container → Execution → Emit ATP events → Kafka

Requirements:

Sandboxed (Firecracker or containerd)

Model/tool config hashing for replay

Concurrency & timeout settings

Deterministic replay capability

11. API & Gateway Layer
Gateway

Kong/Envoy

OPA decision-point integration

Rate limiting

mTLS optional for enterprise

API Servers (FastAPI or Go)

Services:

api-runtime

api-traces

api-cost

api-agents

api-alerts

api-tenants

api-governance

api-connectors

All APIs exposed via a unified API:

/v1/runtime
/v1/traces
/v1/spans
/v1/agents
/v1/replay
/v1/cost
/v1/alerts
/v1/policies
/v1/tenants
/v1/connectors


(Full OpenAPI provided in Part 3.)

12. Policy, Compliance & PII
Policy Engine

OPA (Open Policy Agent)

Policies defined as Rego bundles

Deployed at gateway

Covers:

Deploy permissions

Invocation permissions

Query data permissions

Redaction obligations

Cost-budget enforcement

PII Pipeline

Multi-stage (regex + ML)

Real-time + retroactive

Redaction modes configurable per tenant

GDPR Features

Right-to-be-forgotten

Retention expiry

Access audit logs

13. Identity, Authentication & Authorization
Authentication

OAuth2 / OIDC (SAML for enterprise)

API keys

mTLS for agents

Authorization

RBAC (tenant → team → role)

ABAC (tags: platform, environment, sensitivity)

OPA enforced

14. Observability of the Platform
What we monitor:

Kafka lag

Stream processor throughput

Flink checkpoint failures

Error rates

Ingestion queue depth

API latency p95

PII detection hit-rate

Cost anomalies (self-monitoring)

Where it's stored:

Prometheus/Mimir for metrics

Tempo for traces

Grafana dashboards

15. Tenancy & Data Isolation Model
Enforcement Points:

Ingestion

Kafka topic routing

Stream processor context tagging

Storage partitioning

API query filters via OPA

Isolation Strategies:

Row-level filtering (tenant_id field required)

Index per tenant (OpenSearch)

Trace partitioning (Tempo namespaces)

Metrics labels (tenant="foo")

16. Scaling, HA, Failover
Scaling rules:

Kafka partitions scaled per throughput

Flink autoscaling based on lag & CPU

API servers autoscaled on RPS

Frontend static assets via CDN

HA:

3+ replicas for all stateless components

3-node Kafka cluster per region

Tempo/Mimir multi-ingester setup

Multi-region active/active optional

17. Deployment Topology
Baseline (Prod)

Kubernetes (GKE or EKS)

3 availability zones

Connected to cloud-native services where appropriate

Structure:
k8s/
  - ingress (envoy)
  - gateway
  - api-services
  - runtime-controller
  - stream-processor
  - opensearch
  - tempo
  - mimir
  - grafana
  - kafka (or external)

18. SLOs, SLAs, KPIs
SLOs

Ingest API: p95 < 200ms

Query traces: <1s for 100-step trace

UI load time: <2s

Processing end-to-end: <5 minutes P99

SLA

Uptime: 99.9%

Data durability (buffer): 99.99%

KPIs

Span coverage ≥95%

Edge fidelity ≥99%

Cost accuracy ±2%

19. Data Lifecycle & Retention
Tier	Data	Retention	Storage
Hot	Traces, logs	7–30 days	Tempo/OpenSearch
Warm	Aggregates	90 days	Mimir
Cold	Full history	1–365 days	BigQuery/Snowflake
Deleted	PII or tenant closure	Immediate	Verified via audit
20. Appendix: Sequence Diagrams
Runtime → Trace
Client → Runtime API → Worker → ATP Events → Kafka → Processor → Tempo → UI

External Platform (GCP)
Cloud Logging → Pub/Sub → Cloud Function → Ingest API → Kafka → Processor → Tempo → UI

Replay
UI → Replay API → Runtime Worker → Deterministic Run → Results → Storage → UI

END OF ARCHITECTURE.md