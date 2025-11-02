"""
Alerts System with Slack/Email Integration
US-O3: Threshold alerts with deep links
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import aiohttp
from pydantic import BaseModel

from .database import db

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Alert types"""
    ERROR_RATE = "error_rate"
    LATENCY_P95 = "latency_p95"
    COST_THRESHOLD = "cost_threshold"
    BUDGET_EXCEEDED = "budget_exceeded"
    HEALTH_CHECK_FAILED = "health_check_failed"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertChannel(str, Enum):
    """Notification channels"""
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    alert_type: AlertType
    threshold_value: float
    window_minutes: int
    severity: AlertSeverity
    enabled: bool = True


class AlertConfig(BaseModel):
    """Alert configuration"""
    agent_id: Optional[str] = None
    owner_id: Optional[str] = None
    thresholds: List[Dict[str, Any]]
    channels: List[str]
    slack_webhook_url: Optional[str] = None
    email_recipients: List[str] = []
    webhook_url: Optional[str] = None


class AlertRule:
    """Base alert rule"""
    
    def __init__(self, threshold: AlertThreshold, config: AlertConfig):
        self.threshold = threshold
        self.config = config
    
    async def check(self) -> Optional[Dict]:
        """Check if alert should be triggered"""
        raise NotImplementedError
    
    async def should_notify(self, alert_data: Dict) -> bool:
        """Check if we should send notification (debouncing)"""
        # Check if same alert was sent recently (within 15 minutes)
        alert_key = f"{self.threshold.alert_type}:{alert_data.get('agent_id', 'global')}"
        
        # Query recent alerts
        recent = await db.fetchval(
            """
            SELECT id FROM alerts
            WHERE type = $1 
            AND context->>'agent_id' = $2
            AND created_at > $3
            LIMIT 1
            """,
            self.threshold.alert_type.value,
            alert_data.get("agent_id", ""),
            datetime.utcnow() - timedelta(minutes=15),
        )
        
        return recent is None


class ErrorRateAlertRule(AlertRule):
    """Alert when error rate exceeds threshold"""
    
    async def check(self) -> Optional[Dict]:
        window_start = datetime.utcnow() - timedelta(minutes=self.threshold.window_minutes)
        
        conditions = ["i.started_at >= $1"]
        params = [window_start]
        param_idx = 2
        
        if self.config.agent_id:
            conditions.append(f"i.agent_id = ${param_idx}")
            params.append(UUID(self.config.agent_id))
            param_idx += 1
        elif self.config.owner_id:
            conditions.append(f"a.owner_id = ${param_idx}")
            params.append(self.config.owner_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            COUNT(*) as total_invocations,
            COUNT(*) FILTER (WHERE i.status = 'ERROR') as error_count,
            CASE 
                WHEN COUNT(*) > 0 
                THEN (COUNT(*) FILTER (WHERE i.status = 'ERROR'))::float / COUNT(*)::float * 100
                ELSE 0
            END as error_rate_pct
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE {where_clause}
        """
        
        row = await db.fetchrow(query, *params)
        
        error_rate = float(row["error_rate_pct"])
        
        if error_rate > self.threshold.threshold_value:
            return {
                "alert_type": self.threshold.alert_type.value,
                "severity": self.threshold.severity.value,
                "message": f"Error rate exceeded threshold: {error_rate:.1f}% (threshold: {self.threshold.threshold_value}%)",
                "error_rate_pct": error_rate,
                "threshold_pct": self.threshold.threshold_value,
                "total_invocations": row["total_invocations"],
                "error_count": row["error_count"],
                "window_minutes": self.threshold.window_minutes,
            }
        
        return None


class LatencyAlertRule(AlertRule):
    """Alert when p95 latency exceeds threshold"""
    
    async def check(self) -> Optional[Dict]:
        window_start = datetime.utcnow() - timedelta(minutes=self.threshold.window_minutes)
        
        conditions = ["i.started_at >= $1", "i.status = 'SUCCESS'"]
        params = [window_start]
        param_idx = 2
        
        if self.config.agent_id:
            conditions.append(f"i.agent_id = ${param_idx}")
            params.append(UUID(self.config.agent_id))
            param_idx += 1
        elif self.config.owner_id:
            conditions.append(f"a.owner_id = ${param_idx}")
            params.append(self.config.owner_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY i.execution_time_ms) as p95_latency_ms,
            COUNT(*) as sample_size
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE {where_clause}
        """
        
        row = await db.fetchrow(query, *params)
        
        if row["sample_size"] == 0:
            return None
        
        p95_latency = float(row["p95_latency_ms"]) if row["p95_latency_ms"] else 0
        
        if p95_latency > self.threshold.threshold_value:
            return {
                "alert_type": self.threshold.alert_type.value,
                "severity": self.threshold.severity.value,
                "message": f"P95 latency exceeded threshold: {p95_latency:.0f}ms (threshold: {self.threshold.threshold_value}ms)",
                "p95_latency_ms": p95_latency,
                "threshold_ms": self.threshold.threshold_value,
                "sample_size": row["sample_size"],
                "window_minutes": self.threshold.window_minutes,
            }
        
        return None


class CostAlertRule(AlertRule):
    """Alert when cost exceeds threshold"""
    
    async def check(self) -> Optional[Dict]:
        window_start = datetime.utcnow() - timedelta(minutes=self.threshold.window_minutes)
        
        conditions = ["i.started_at >= $1"]
        params = [window_start]
        param_idx = 2
        
        if self.config.agent_id:
            conditions.append(f"i.agent_id = ${param_idx}")
            params.append(UUID(self.config.agent_id))
            param_idx += 1
        elif self.config.owner_id:
            conditions.append(f"a.owner_id = ${param_idx}")
            params.append(self.config.owner_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            COALESCE(SUM(i.cost_decimal), 0.0) as total_cost
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE {where_clause}
        """
        
        row = await db.fetchrow(query, *params)
        
        total_cost = float(row["total_cost"])
        
        if total_cost > self.threshold.threshold_value:
            return {
                "alert_type": self.threshold.alert_type.value,
                "severity": self.threshold.severity.value,
                "message": f"Cost exceeded threshold: ${total_cost:.2f} (threshold: ${self.threshold.threshold_value:.2f})",
                "total_cost_usd": total_cost,
                "threshold_usd": self.threshold.threshold_value,
                "window_minutes": self.threshold.window_minutes,
            }
        
        return None


class AlertManager:
    """Manages alert rules and notifications"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.running = False
    
    def register_alert(self, config: AlertConfig):
        """Register alert configuration"""
        for threshold_data in config.thresholds:
            threshold = AlertThreshold(
                alert_type=AlertType(threshold_data["alert_type"]),
                threshold_value=threshold_data["threshold_value"],
                window_minutes=threshold_data.get("window_minutes", 5),
                severity=AlertSeverity(threshold_data.get("severity", "medium")),
                enabled=threshold_data.get("enabled", True),
            )
            
            # Create appropriate rule
            if threshold.alert_type == AlertType.ERROR_RATE:
                rule = ErrorRateAlertRule(threshold, config)
            elif threshold.alert_type == AlertType.LATENCY_P95:
                rule = LatencyAlertRule(threshold, config)
            elif threshold.alert_type == AlertType.COST_THRESHOLD:
                rule = CostAlertRule(threshold, config)
            else:
                continue
            
            self.rules.append(rule)
            logger.info(f"Registered alert rule: {threshold.alert_type.value}")
    
    async def start_monitoring(self, check_interval: int = 60):
        """Start background alert monitoring"""
        self.running = True
        logger.info("Alert monitoring started")
        
        while self.running:
            try:
                await self.check_all_rules()
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
            
            await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        logger.info("Alert monitoring stopped")
    
    async def check_all_rules(self):
        """Check all registered rules"""
        for rule in self.rules:
            if not rule.threshold.enabled:
                continue
            
            try:
                alert_data = await rule.check()
                
                if alert_data:
                    # Check debouncing
                    if await rule.should_notify(alert_data):
                        await self.send_alert(alert_data, rule.config)
                        await self.record_alert(alert_data, rule.config)
            
            except Exception as e:
                logger.error(f"Error checking rule {rule.threshold.alert_type}: {e}")
    
    async def send_alert(self, alert_data: Dict, config: AlertConfig):
        """Send alert to configured channels"""
        for channel in config.channels:
            try:
                if channel == AlertChannel.SLACK.value and config.slack_webhook_url:
                    await self.send_slack_alert(alert_data, config)
                elif channel == AlertChannel.EMAIL.value and config.email_recipients:
                    await self.send_email_alert(alert_data, config)
                elif channel == AlertChannel.WEBHOOK.value and config.webhook_url:
                    await self.send_webhook_alert(alert_data, config)
            
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
    
    async def send_slack_alert(self, alert_data: Dict, config: AlertConfig):
        """Send alert to Slack"""
        # Build deep link to filtered view
        base_url = "http://localhost:3001"  # Configure in production
        deep_link = f"{base_url}/observability"
        
        if config.agent_id:
            deep_link += f"?agent_id={config.agent_id}"
        
        # Build Slack message
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        
        emoji = severity_emoji.get(alert_data["severity"], "⚠️")
        
        message = {
            "text": f"{emoji} *Alert: {alert_data['alert_type']}*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {alert_data['message']}",
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{alert_data['severity']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                        },
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Details"
                            },
                            "url": deep_link,
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.slack_webhook_url,
                json=message,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    logger.error(f"Slack webhook failed: {response.status}")
                else:
                    logger.info("Slack alert sent successfully")
    
    async def send_email_alert(self, alert_data: Dict, config: AlertConfig):
        """Send alert via email (placeholder - integrate with SendGrid/SES)"""
        logger.info(f"Email alert would be sent to: {config.email_recipients}")
        # TODO: Integrate with email service
    
    async def send_webhook_alert(self, alert_data: Dict, config: AlertConfig):
        """Send alert to custom webhook"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.webhook_url,
                json=alert_data,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status >= 400:
                    logger.error(f"Webhook alert failed: {response.status}")
                else:
                    logger.info("Webhook alert sent successfully")
    
    async def record_alert(self, alert_data: Dict, config: AlertConfig):
        """Record alert to database"""
        try:
            await db.execute(
                """
                INSERT INTO alerts (
                    type, severity, agent_id, version_id, context
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                alert_data["alert_type"],
                alert_data["severity"],
                UUID(config.agent_id) if config.agent_id else None,
                None,  # version_id
                json.dumps(alert_data),
            )
        except Exception as e:
            logger.error(f"Failed to record alert: {e}")


# Global alert manager
alert_manager = AlertManager()
