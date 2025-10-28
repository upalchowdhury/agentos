"""
OpenTelemetry Integration for Agent Economy OS
Provides distributed tracing, metrics, and logs across all agent invocations
"""

import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, SERVICE_INSTANCE_ID
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

# Context variable for current trace
current_trace_context: ContextVar[Optional[dict]] = ContextVar('current_trace_context', default=None)


class TelemetryConfig:
    """OpenTelemetry configuration"""
    
    def __init__(
        self,
        service_name: str = "runtime-service",
        service_version: str = "0.2.0",
        service_instance_id: Optional[str] = None,
        otlp_endpoint: Optional[str] = None,  # e.g., "http://localhost:4317"
        jaeger_endpoint: Optional[str] = None,  # e.g., "http://localhost:14268/api/traces"
        enable_console_export: bool = False
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.service_instance_id = service_instance_id or "runtime-1"
        self.otlp_endpoint = otlp_endpoint
        self.jaeger_endpoint = jaeger_endpoint
        self.enable_console_export = enable_console_export


def setup_telemetry(config: TelemetryConfig) -> tuple:
    """
    Setup OpenTelemetry tracing and metrics
    
    Returns:
        (tracer, meter) tuple
    """
    
    # Create resource
    resource = Resource.create({
        SERVICE_NAME: config.service_name,
        SERVICE_VERSION: config.service_version,
        SERVICE_INSTANCE_ID: config.service_instance_id,
        "deployment.environment": "production",
        "service.namespace": "agentos"
    })
    
    # Setup tracing
    tracer_provider = TracerProvider(resource=resource)
    
    # Add exporters
    if config.otlp_endpoint:
        # OTLP exporter (for Grafana Tempo, Honeycomb, etc.)
        otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OpenTelemetry: OTLP exporter configured to {config.otlp_endpoint}")
    
    if config.jaeger_endpoint:
        # Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        logger.info(f"OpenTelemetry: Jaeger exporter configured")
    
    if config.enable_console_export:
        # Console exporter (for debugging)
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("OpenTelemetry: Console exporter enabled")
    
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(__name__)
    
    # Setup metrics
    if config.otlp_endpoint:
        metric_exporter = OTLPMetricExporter(endpoint=config.otlp_endpoint, insecure=True)
    elif config.enable_console_export:
        metric_exporter = ConsoleMetricExporter()
    else:
        metric_exporter = None
    
    if metric_exporter:
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        meter = metrics.get_meter(__name__)
        logger.info("OpenTelemetry: Metrics configured")
    else:
        meter = None
    
    # Auto-instrument libraries
    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    
    logger.info(f"OpenTelemetry initialized for {config.service_name}")
    
    return tracer, meter


class AgentTracer:
    """
    Agent-specific tracing utilities
    Provides convenience methods for tracing agent operations
    """
    
    def __init__(self, tracer: trace.Tracer, meter: Optional[metrics.Meter] = None):
        self.tracer = tracer
        self.meter = meter
        
        # Create metrics
        if self.meter:
            self.invocation_counter = self.meter.create_counter(
                "agent.invocations.total",
                description="Total agent invocations",
                unit="1"
            )
            
            self.invocation_duration = self.meter.create_histogram(
                "agent.invocation.duration",
                description="Agent invocation duration",
                unit="ms"
            )
            
            self.invocation_cost = self.meter.create_histogram(
                "agent.invocation.cost",
                description="Agent invocation cost",
                unit="USD"
            )
            
            self.error_counter = self.meter.create_counter(
                "agent.errors.total",
                description="Total agent errors",
                unit="1"
            )
    
    def trace_agent_deployment(self, agent_id: str, model_type: str):
        """
        Trace agent deployment
        
        Usage:
            with tracer.trace_agent_deployment(agent_id, "A"):
                # deployment logic
        """
        return self.tracer.start_as_current_span(
            "agent.deploy",
            attributes={
                "agent.id": agent_id,
                "agent.model_type": model_type,
                "operation": "deploy"
            }
        )
    
    def trace_agent_build(self, agent_id: str, version_id: str):
        """Trace agent build process"""
        return self.tracer.start_as_current_span(
            "agent.build",
            attributes={
                "agent.id": agent_id,
                "agent.version_id": version_id,
                "operation": "build"
            }
        )
    
    def trace_agent_invocation(
        self,
        agent_id: str,
        model_type: str,
        caller_type: str = "user",
        caller_id: Optional[str] = None
    ):
        """
        Trace agent invocation
        
        Usage:
            with tracer.trace_agent_invocation(agent_id, "A", "user", user_id) as span:
                # invocation logic
                span.set_attribute("result.status", "success")
        """
        return self.tracer.start_as_current_span(
            "agent.invoke",
            attributes={
                "agent.id": agent_id,
                "agent.model_type": model_type,
                "caller.type": caller_type,
                "caller.id": caller_id or "unknown",
                "operation": "invoke"
            }
        )
    
    def trace_external_call(
        self,
        provider: str,
        endpoint: str,
        agent_id: str
    ):
        """
        Trace external API call (Model B)
        
        Usage:
            with tracer.trace_external_call("salesforce", endpoint, agent_id):
                # call external API
        """
        return self.tracer.start_as_current_span(
            "agent.external_call",
            attributes={
                "provider": provider,
                "endpoint": endpoint,
                "agent.id": agent_id,
                "operation": "external_call"
            }
        )
    
    def trace_a2a_invocation(
        self,
        caller_agent_id: str,
        target_agent_id: str
    ):
        """
        Trace agent-to-agent invocation
        
        Usage:
            with tracer.trace_a2a_invocation(caller_id, target_id):
                # A2A invocation
        """
        return self.tracer.start_as_current_span(
            "agent.a2a_invoke",
            attributes={
                "caller.agent_id": caller_agent_id,
                "target.agent_id": target_agent_id,
                "operation": "a2a"
            }
        )
    
    def trace_opa_decision(self, agent_id: str, subject_id: str):
        """Trace OPA policy decision"""
        return self.tracer.start_as_current_span(
            "opa.check_permission",
            attributes={
                "agent.id": agent_id,
                "subject.id": subject_id,
                "operation": "authz"
            }
        )
    
    def record_invocation_metrics(
        self,
        agent_id: str,
        model_type: str,
        status: str,
        duration_ms: float,
        cost_usd: float,
        provider: Optional[str] = None
    ):
        """
        Record invocation metrics
        
        Args:
            agent_id: Agent identifier
            model_type: 'A' or 'B'
            status: 'SUCCESS', 'ERROR', 'TIMEOUT', 'DENIED'
            duration_ms: Execution time in milliseconds
            cost_usd: Cost in USD
            provider: Provider name for Model B (e.g., 'salesforce')
        """
        
        if not self.meter:
            return
        
        attributes = {
            "agent.id": agent_id,
            "agent.model_type": model_type,
            "status": status
        }
        
        if provider:
            attributes["provider"] = provider
        
        # Increment counter
        self.invocation_counter.add(1, attributes)
        
        # Record duration
        self.invocation_duration.record(duration_ms, attributes)
        
        # Record cost
        self.invocation_cost.record(cost_usd, attributes)
        
        # Track errors
        if status in ['ERROR', 'TIMEOUT', 'DENIED']:
            self.error_counter.add(1, attributes)
    
    def add_event(self, name: str, attributes: Dict[str, Any]):
        """Add event to current span"""
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes)
    
    def set_error(self, exception: Exception):
        """Mark current span as error"""
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))


# Trace context propagation utilities
class TraceContextPropagator:
    """
    Utilities for propagating trace context across services
    Used for A2A invocations and external calls
    """
    
    @staticmethod
    def inject_context() -> Dict[str, str]:
        """
        Extract current trace context as HTTP headers
        
        Returns:
            Headers dict with trace context (traceparent, tracestate)
        """
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        return carrier
    
    @staticmethod
    def extract_context(headers: Dict[str, str]):
        """
        Extract trace context from HTTP headers
        
        Args:
            headers: Request headers
        """
        ctx = TraceContextTextMapPropagator().extract(carrier=headers)
        return ctx


# Singleton instances
_tracer: Optional[AgentTracer] = None
_config: Optional[TelemetryConfig] = None


def init_telemetry(config: TelemetryConfig):
    """Initialize telemetry (call once at startup)"""
    global _tracer, _config
    
    tracer, meter = setup_telemetry(config)
    _tracer = AgentTracer(tracer, meter)
    _config = config
    
    logger.info("Telemetry initialized successfully")


def get_tracer() -> AgentTracer:
    """Get the global tracer instance"""
    if _tracer is None:
        # Initialize with defaults if not already done
        init_telemetry(TelemetryConfig(enable_console_export=True))
    return _tracer


def get_config() -> TelemetryConfig:
    """Get the current telemetry config"""
    return _config or TelemetryConfig()
