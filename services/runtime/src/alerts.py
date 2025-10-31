import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from .config import settings
from .database import db

logger = logging.getLogger(__name__)


@dataclass
class AlertThresholds:
    error_rate: float = 0.3
    latency_ms: int = 5000
    sample_window: int = 20

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AlertThresholds":
        data = {}
        if payload.get("error_rate") is not None:
            data["error_rate"] = float(payload["error_rate"])
        if payload.get("latency_ms") is not None:
            data["latency_ms"] = int(payload["latency_ms"])
        if payload.get("sample_window") is not None:
            data["sample_window"] = int(payload["sample_window"])
        return cls(**data)


class AlertManager:
    """
    Evaluates agent health and emits Slack notifications when error
    rates or latency breach thresholds.
    """

    def __init__(self, webhook_url: Optional[str], thresholds: Optional[AlertThresholds] = None) -> None:
        self.webhook_url = webhook_url
        self.thresholds = thresholds or AlertThresholds()

    async def evaluate(
        self,
        *,
        agent_id: str,
        agent_name: str,
        telemetry_quality: Optional[str],
    ) -> None:
        if not self.webhook_url:
            return

        recent = await db.fetch(
            """
            SELECT status, execution_time_ms
            FROM invocations
            WHERE agent_id = $1
            ORDER BY started_at DESC
            LIMIT $2
            """,
            agent_id,
            self.thresholds.sample_window,
        )

        if not recent:
            return

        total = len(recent)
        error_count = sum(1 for row in recent if row["status"] == "ERROR")
        avg_error_rate = error_count / total

        latency_samples = [row["execution_time_ms"] for row in recent if row.get("execution_time_ms") is not None]
        max_latency = max(latency_samples) if latency_samples else 0

        triggers: List[str] = []
        if avg_error_rate >= self.thresholds.error_rate:
            triggers.append(f"error rate {avg_error_rate:.0%} (>{self.thresholds.error_rate:.0%})")
        if max_latency and max_latency >= self.thresholds.latency_ms:
            triggers.append(f"max latency {max_latency} ms (>={self.thresholds.latency_ms} ms)")

        if not triggers:
            return

        payload = self._build_payload(
            agent_id=agent_id,
            agent_name=agent_name,
            telemetry_quality=telemetry_quality,
            triggers=triggers,
            total=total,
            error_count=error_count,
            max_latency=max_latency,
        )

        await self._send(payload)

    def _build_payload(
        self,
        *,
        agent_id: str,
        agent_name: str,
        telemetry_quality: Optional[str],
        triggers: List[str],
        total: int,
        error_count: int,
        max_latency: int,
    ) -> Dict[str, Any]:
        title = f":rotating_light: Agent Alert — {agent_name}"
        description = "\n".join(f"• {item}" for item in triggers)
        quality = telemetry_quality or "unknown"

        link_url = None
        if settings.WEB_APP_URL:
            link_url = (
                f"{settings.WEB_APP_URL.rstrip('/')}/logs"
                f"?agent_id={agent_id}"
                f"&subject_type=user"
                f"&level=ERROR"
            )

        payload = {
            "text": title,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{title}*\n{description}"},
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"*Agent ID:* `{agent_id}`"},
                        {"type": "mrkdwn", "text": f"*Telemetry:* {quality}"},
                        {"type": "mrkdwn", "text": f"*Window:* {total} invocations"},
                        {"type": "mrkdwn", "text": f"*Errors:* {error_count}"},
                        {"type": "mrkdwn", "text": f"*Max latency:* {max_latency} ms"},
                    ],
                },
            ],
        }

        if link_url:
            payload["blocks"].append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Open Logs"},
                            "url": link_url,
                        }
                    ],
                }
            )
        return payload

    async def _send(self, payload: Dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self.webhook_url, json=payload)
            if response.status_code >= 400:
                logger.warning("Failed to send Slack alert (%s): %s", response.status_code, response.text)
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Slack alert failed: %s", exc)


alert_manager = AlertManager(settings.SLACK_WEBHOOK_URL)
