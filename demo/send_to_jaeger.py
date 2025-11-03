#!/usr/bin/env python3
"""
Send test traces directly to Jaeger
"""
from jaeger_client import Config
from opentracing_instrumentation.client_hooks import install_all_patches
import time

def init_tracer(service_name='demo-agent'):
    config = Config(
        config={
            'sampler': {'type': 'const', 'param': 1},
            'logging': True,
            'local_agent': {
                'reporting_host': 'localhost',
                'reporting_port': 31831,  # Jaeger agent port via NodePort
            },
        },
        service_name=service_name,
    )
    return config.initialize_tracer()

def create_trace():
    tracer = init_tracer('orchestrator-agent')
    
    with tracer.start_span('orchestrator_workflow') as root_span:
        root_span.set_tag('agent.id', 'orchestrator-001')
        root_span.set_tag('model', 'gpt-4o')
        
        time.sleep(0.05)
        
        with tracer.start_span('planning', child_of=root_span) as plan_span:
            plan_span.set_tag('kind', 'prompt')
            plan_span.set_tag('model', 'gpt-4o')
            plan_span.set_tag('temperature', 0.3)
            time.sleep(0.15)
        
        with tracer.start_span('call_research_agent', child_of=root_span) as research_span:
            research_span.set_tag('kind', 'subagent')
            research_span.set_tag('target', 'research-agent-001')
            research_span.set_tag('model', 'claude-sonnet')
            time.sleep(0.12)
        
        with tracer.start_span('call_writer_agent', child_of=root_span) as writer_span:
            writer_span.set_tag('kind', 'subagent')
            writer_span.set_tag('target', 'writer-agent-001')
            writer_span.set_tag('model', 'gpt-4o-mini')
            time.sleep(0.10)
        
        with tracer.start_span('call_reviewer_agent', child_of=root_span) as reviewer_span:
            reviewer_span.set_tag('kind', 'subagent')
            reviewer_span.set_tag('target', 'reviewer-agent-001')
            reviewer_span.set_tag('model', 'gemini-pro')
            time.sleep(0.11)
    
    time.sleep(2)  # Allow tracer to flush
    tracer.close()
    print("✅ Trace sent to Jaeger!")

if __name__ == "__main__":
    try:
        create_trace()
    except Exception as e:
        print(f"Error: {e}")
        print("\nTry using HTTP directly instead:")
        print("curl -X POST http://localhost:31686/api/traces ...")
