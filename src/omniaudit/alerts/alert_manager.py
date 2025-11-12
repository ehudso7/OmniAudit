"""
Alert Manager

Manages alert rules and triggers notifications.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from .notifiers import get_notifier


class AlertManager:
    """
    Manages alert rules and triggers notifications.

    Example:
        >>> manager = AlertManager()
        >>> manager.check_metrics(metrics, alert_rules)
    """

    def __init__(self):
        """Initialize alert manager."""
        self.triggered_alerts = []

    def check_metrics(
        self,
        metrics: Dict[str, float],
        alert_rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check metrics against alert rules.

        Args:
            metrics: Dictionary of metric name -> value
            alert_rules: List of alert rule configurations

        Returns:
            List of triggered alerts
        """
        triggered = []

        for rule in alert_rules:
            if not rule.get("enabled", True):
                continue

            metric_name = rule["metric_name"]
            if metric_name not in metrics:
                continue

            metric_value = metrics[metric_name]
            condition = rule["condition"]
            threshold = rule["threshold"]

            if self._evaluate_condition(metric_value, condition, threshold):
                alert = {
                    "rule_id": rule.get("id"),
                    "rule_name": rule["name"],
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "threshold": threshold,
                    "condition": condition,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": self._format_alert_message(
                        rule["name"],
                        metric_name,
                        metric_value,
                        condition,
                        threshold
                    )
                }

                triggered.append(alert)
                self.triggered_alerts.append(alert)

                # Send notifications
                self._send_notifications(alert, rule)

        return triggered

    def _evaluate_condition(
        self,
        value: float,
        condition: str,
        threshold: float
    ) -> bool:
        """Evaluate if condition is met."""
        conditions = {
            "gt": lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "lt": lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
            "ne": lambda v, t: v != t
        }

        condition_func = conditions.get(condition)
        if condition_func:
            return condition_func(value, threshold)

        return False

    def _format_alert_message(
        self,
        rule_name: str,
        metric_name: str,
        value: float,
        condition: str,
        threshold: float
    ) -> str:
        """Format alert message."""
        condition_text = {
            "gt": "greater than",
            "gte": "greater than or equal to",
            "lt": "less than",
            "lte": "less than or equal to",
            "eq": "equal to",
            "ne": "not equal to"
        }

        return (
            f"Alert: {rule_name}\n"
            f"Metric '{metric_name}' is {value:.2f}, "
            f"which is {condition_text.get(condition, condition)} "
            f"threshold of {threshold:.2f}"
        )

    def _send_notifications(
        self,
        alert: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> None:
        """Send alert notifications."""
        channels = rule.get("notification_channels", [])
        config = rule.get("notification_config", {})

        for channel in channels:
            try:
                notifier = get_notifier(channel, config)
                if notifier:
                    notifier.send(alert)
            except Exception as e:
                print(f"Failed to send notification via {channel}: {e}")

    def get_triggered_alerts(
        self,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get triggered alerts.

        Args:
            since: Optional datetime to filter alerts

        Returns:
            List of triggered alerts
        """
        if since is None:
            return self.triggered_alerts

        return [
            alert for alert in self.triggered_alerts
            if datetime.fromisoformat(alert["timestamp"]) >= since
        ]

    def clear_alerts(self) -> None:
        """Clear triggered alerts history."""
        self.triggered_alerts = []
