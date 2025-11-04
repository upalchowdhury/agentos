"""
Span-level anomaly detectors for security and quality monitoring.

Detectors:
- Prompt Injection: Detect jailbreak attempts and prompt manipulation
- Tool Abuse: Detect unusual tool calling patterns
- Context Tampering: Detect hash mismatches and signature failures
- Cost Outliers: Statistical outlier detection
- Latency Outliers: Performance anomaly detection
"""

import hashlib
import json
import re
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_type: str
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    detector_name: str
    detector_version: str
    evidence: Dict[str, Any]
    message: str


class PromptInjectionDetector:
    """
    Detects prompt injection attempts using regex patterns and heuristics.

    Flags suspicious patterns like:
    - "Ignore previous instructions"
    - Role-switching attempts
    - System prompt overrides
    - Jailbreak templates
    """

    VERSION = "1.0.0"

    # Jailbreak patterns
    PATTERNS = [
        # Direct instruction overrides
        (r"ignore\s+(previous|all|above|prior)\s+instructions?", "instruction_override", 0.9),
        (r"disregard\s+(previous|all|above)\s+(instructions?|rules?)", "instruction_override", 0.9),
        (r"forget\s+(everything|all|what)", "forget_directive", 0.85),

        # Role switching
        (r"you\s+are\s+now\s+(a|an)\s+\w+", "role_switch", 0.8),
        (r"act\s+as\s+(if\s+)?(you|a|an)\s+(are|were)", "role_switch", 0.75),
        (r"pretend\s+(to\s+be|you\s+are)", "role_switch", 0.75),

        # System prompt access
        (r"(show|display|reveal|print)\s+(your|the)\s+system\s+prompt", "system_access", 0.95),
        (r"what\s+(are|were|is)\s+your\s+(initial|original)\s+instructions", "system_access", 0.9),

        # DAN (Do Anything Now) variants
        (r"\bDAN\b.*\bmode\b", "dan_jailbreak", 0.9),
        (r"do\s+anything\s+now", "dan_jailbreak", 0.85),

        # Encoding tricks
        (r"(base64|hex|rot13|unicode)\s*(encode|decode|convert)", "encoding_trick", 0.7),

        # Boundary manipulation
        (r"(\[INST\]|\[/INST\]|\<\|.*?\|\>)", "boundary_manipulation", 0.85),
    ]

    def detect(self, span: Dict[str, Any]) -> Optional[Anomaly]:
        """Detect prompt injection in span"""
        if span["kind"] != "prompt":
            return None

        input_text = span.get("input_excerpt", "")
        if not input_text:
            return None

        # Check patterns
        matches = []
        for pattern, category, confidence in self.PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                matches.append((category, confidence))

        if not matches:
            return None

        # Aggregate confidence
        max_confidence = max(c for _, c in matches)
        categories = [cat for cat, _ in matches]

        # Determine severity
        if max_confidence >= 0.9:
            severity = "critical"
        elif max_confidence >= 0.8:
            severity = "high"
        elif max_confidence >= 0.7:
            severity = "medium"
        else:
            severity = "low"

        return Anomaly(
            anomaly_type="prompt_injection",
            severity=severity,
            confidence=max_confidence,
            detector_name="regex_injection",
            detector_version=self.VERSION,
            evidence={
                "categories": categories,
                "input_excerpt": input_text[:200],
                "pattern_matches": len(matches)
            },
            message=f"Potential prompt injection detected: {', '.join(set(categories))}"
        )


class ToolAbuseDetector:
    """
    Detects tool abuse patterns:
    - Excessive retry attempts
    - Schema mismatches
    - Unusual call sequences
    - High latency deltas
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.call_history: Dict[str, List[Dict]] = {}  # agent_id -> calls

    def detect(self, span: Dict[str, Any]) -> Optional[Anomaly]:
        """Detect tool abuse in span"""
        if span["kind"] != "tool":
            return None

        tool_name = span.get("tool_name")
        agent_id = span["agent_id"]
        latency_ms = span.get("duration_ms", 0)
        status = span["status"]

        if not tool_name:
            return None

        # Track call history
        if agent_id not in self.call_history:
            self.call_history[agent_id] = []

        self.call_history[agent_id].append({
            "tool": tool_name,
            "latency": latency_ms,
            "status": status,
            "timestamp": span["start_ts"]
        })

        # Keep last 100 calls
        self.call_history[agent_id] = self.call_history[agent_id][-100:]

        # Check for excessive retries (same tool, multiple errors)
        recent_calls = self.call_history[agent_id][-10:]
        same_tool_errors = sum(
            1 for call in recent_calls
            if call["tool"] == tool_name and call["status"] == "error"
        )

        if same_tool_errors >= 5:
            return Anomaly(
                anomaly_type="tool_abuse",
                severity="high",
                confidence=0.9,
                detector_name="retry_abuse",
                detector_version=self.VERSION,
                evidence={
                    "tool_name": tool_name,
                    "error_count": same_tool_errors,
                    "recent_calls": len(recent_calls)
                },
                message=f"Excessive tool failures: {tool_name} failed {same_tool_errors} times"
            )

        # Check for latency outliers
        tool_latencies = [
            call["latency"] for call in self.call_history[agent_id]
            if call["tool"] == tool_name and call["latency"] > 0
        ]

        if len(tool_latencies) >= 5:
            avg_latency = sum(tool_latencies) / len(tool_latencies)
            if latency_ms > avg_latency * 5:  # 5x slower
                return Anomaly(
                    anomaly_type="tool_abuse",
                    severity="medium",
                    confidence=0.7,
                    detector_name="latency_outlier",
                    detector_version=self.VERSION,
                    evidence={
                        "tool_name": tool_name,
                        "current_latency_ms": latency_ms,
                        "avg_latency_ms": avg_latency,
                        "deviation": latency_ms / avg_latency
                    },
                    message=f"Tool latency anomaly: {tool_name} took {latency_ms}ms (avg: {avg_latency:.0f}ms)"
                )

        return None


class ContextTamperingDetector:
    """
    Detects context tampering:
    - Content hash mismatches
    - Signature verification failures
    - Unexpected parent span changes
    """

    VERSION = "1.0.0"

    def detect(self, span: Dict[str, Any], parent_span: Optional[Dict[str, Any]] = None) -> Optional[Anomaly]:
        """Detect context tampering"""

        # Check signature verification
        if span.get("signature_verified") is False:
            protocol = span.get("protocol")
            if protocol in ["a2a", "mcp"]:  # Protocols that require signatures
                return Anomaly(
                    anomaly_type="context_tampering",
                    severity="critical",
                    confidence=0.95,
                    detector_name="signature_mismatch",
                    detector_version=self.VERSION,
                    evidence={
                        "protocol": protocol,
                        "remote_agent_id": span.get("remote_agent_id")
                    },
                    message=f"Signature verification failed for {protocol} call"
                )

        # Check content hash consistency
        content_hash_in = span.get("content_hash_in")
        if content_hash_in and parent_span:
            parent_hash_out = parent_span.get("content_hash_out")
            if parent_hash_out and parent_hash_out != content_hash_in:
                # Hash mismatch between parent output and child input
                return Anomaly(
                    anomaly_type="context_tampering",
                    severity="high",
                    confidence=0.85,
                    detector_name="hash_mismatch",
                    detector_version=self.VERSION,
                    evidence={
                        "parent_hash": parent_hash_out,
                        "child_hash": content_hash_in,
                        "parent_span_id": parent_span["span_id"]
                    },
                    message="Content hash mismatch between parent and child spans"
                )

        return None


class CostOutlierDetector:
    """Detect cost anomalies using statistical methods"""

    VERSION = "1.0.0"

    def detect(self, span: Dict[str, Any], agent_stats: List[Dict[str, Any]]) -> Optional[Anomaly]:
        """Detect cost outliers"""
        cost_cents = span.get("cost_cents", 0)
        if cost_cents == 0:
            return None

        # Calculate stats from agent history
        costs = [s["cost_cents"] for s in agent_stats if s.get("cost_cents", 0) > 0]
        if len(costs) < 5:
            return None  # Not enough data

        mean = sum(costs) / len(costs)
        variance = sum((x - mean) ** 2 for x in costs) / len(costs)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return None

        z_score = (cost_cents - mean) / std_dev

        if abs(z_score) > 3.0:  # 3 standard deviations
            severity = "critical" if abs(z_score) > 5.0 else "high"

            return Anomaly(
                anomaly_type="cost_outlier",
                severity=severity,
                confidence=min(0.95, abs(z_score) / 10.0),
                detector_name="statistical_outlier",
                detector_version=self.VERSION,
                evidence={
                    "cost_cents": cost_cents,
                    "mean_cost": mean,
                    "std_dev": std_dev,
                    "z_score": z_score
                },
                message=f"Cost outlier: {cost_cents}¢ (mean: {mean:.1f}¢, z-score: {z_score:.2f})"
            )

        return None


class AnomalyDetectionEngine:
    """
    Orchestrates multiple anomaly detectors.

    Usage:
        engine = AnomalyDetectionEngine()
        anomalies = engine.analyze_span(span, parent_span, agent_stats)
    """

    def __init__(self):
        self.prompt_injection_detector = PromptInjectionDetector()
        self.tool_abuse_detector = ToolAbuseDetector()
        self.context_tampering_detector = ContextTamperingDetector()
        self.cost_outlier_detector = CostOutlierDetector()

    def analyze_span(
        self,
        span: Dict[str, Any],
        parent_span: Optional[Dict[str, Any]] = None,
        agent_stats: Optional[List[Dict[str, Any]]] = None
    ) -> List[Anomaly]:
        """
        Run all detectors on a span.

        Returns list of detected anomalies.
        """
        anomalies = []

        # Prompt injection
        if span["kind"] == "prompt":
            anomaly = self.prompt_injection_detector.detect(span)
            if anomaly:
                anomalies.append(anomaly)

        # Tool abuse
        if span["kind"] == "tool":
            anomaly = self.tool_abuse_detector.detect(span)
            if anomaly:
                anomalies.append(anomaly)

        # Context tampering
        anomaly = self.context_tampering_detector.detect(span, parent_span)
        if anomaly:
            anomalies.append(anomaly)

        # Cost outliers
        if agent_stats:
            anomaly = self.cost_outlier_detector.detect(span, agent_stats)
            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    async def store_anomalies(self, span_id: str, trace_id: str, agent_id: str, anomalies: List[Anomaly], db):
        """Store detected anomalies in database"""
        for anomaly in anomalies:
            try:
                await db.execute(
                    """
                    INSERT INTO span_anomalies (
                        span_id, trace_id, agent_id, anomaly_type, severity,
                        confidence, detector_name, detector_version, evidence, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    span_id,
                    trace_id,
                    agent_id,
                    anomaly.anomaly_type,
                    anomaly.severity,
                    anomaly.confidence,
                    anomaly.detector_name,
                    anomaly.detector_version,
                    json.dumps(anomaly.evidence),
                    "open"
                )
                logger.info(
                    f"Stored anomaly: {anomaly.anomaly_type} for span {span_id} "
                    f"(severity: {anomaly.severity}, confidence: {anomaly.confidence:.2f})"
                )
            except Exception as e:
                logger.error(f"Failed to store anomaly: {e}")
