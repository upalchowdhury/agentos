import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
    startOnLoad: true,
    theme: 'dark',
    securityLevel: 'loose',
});

const SequenceDiagram = ({ traceId }) => {
    const mermaidRef = useRef(null);

    useEffect(() => {
        // In a real app, we would fetch the trace and generate this diagram dynamically
        // For this demo, we hardcode the Salesforce -> GCP flow
        const graphDefinition = `
      sequenceDiagram
          participant User
          participant SF as Salesforce Agent
          participant GCP as GCP Research Agent
          
          User->>SF: Query Refund Status
          activate SF
          Note right of SF: Platform: Salesforce<br/>Trace: ${traceId || 'trace_123'}
          
          SF->>GCP: Check Policy (HTTP)
          activate GCP
          Note right of GCP: Platform: GCP Vertex AI
          
          GCP->>GCP: LLM Call (Gemini Pro)
          
          GCP-->>SF: Refund Approved
          deactivate GCP
          
          SF-->>User: Your refund is approved
          deactivate SF
    `;

        if (mermaidRef.current) {
            mermaidRef.current.innerHTML = '';
            mermaid.render('mermaid-svg', graphDefinition).then((result) => {
                mermaidRef.current.innerHTML = result.svg;
            });
        }
    }, [traceId]);

    return (
        <div className="w-full overflow-x-auto p-4 bg-gray-900 rounded-lg border border-gray-800">
            <div ref={mermaidRef} className="mermaid flex justify-center" />
        </div>
    );
};

export default SequenceDiagram;
