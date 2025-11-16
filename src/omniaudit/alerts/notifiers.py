"""
Alert Notifiers

Send notifications via various channels (email, Slack, webhooks).
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class BaseNotifier(ABC):
    """Base class for notifiers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notifier.

        Args:
            config: Notifier configuration
        """
        self.config = config

    @abstractmethod
    def send(self, alert: Dict[str, Any]) -> bool:
        """
        Send alert notification.

        Args:
            alert: Alert data

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class EmailNotifier(BaseNotifier):
    """
    Email notifier.

    Configuration:
        smtp_host: str - SMTP server host
        smtp_port: int - SMTP server port (default: 587)
        username: str - SMTP username
        password: str - SMTP password
        from_email: str - Sender email address
        to_emails: List[str] - Recipient email addresses
    """

    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_host = self.config.get("smtp_host")
            smtp_port = self.config.get("smtp_port", 587)
            username = self.config.get("username")
            password = self.config.get("password")
            from_email = self.config.get("from_email")
            to_emails = self.config.get("to_emails", [])

            if not all([smtp_host, username, password, from_email, to_emails]):
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"OmniAudit Alert: {alert['rule_name']}"

            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False

    def _format_email_body(self, alert: Dict[str, Any]) -> str:
        """Format email body."""
        return f"""
OmniAudit Alert

Rule: {alert['rule_name']}
Metric: {alert['metric_name']}
Value: {alert['metric_value']}
Threshold: {alert['threshold']}
Condition: {alert['condition']}
Timestamp: {alert['timestamp']}

Message:
{alert['message']}

---
Sent by OmniAudit Alert System
"""


class SlackNotifier(BaseNotifier):
    """
    Slack notifier.

    Configuration:
        webhook_url: str - Slack webhook URL
        channel: str - Optional channel override
        username: str - Optional username override
    """

    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via Slack webhook."""
        if not REQUESTS_AVAILABLE:
            print("requests library required for Slack notifications")
            return False

        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                return False

            payload = {
                "text": f"🚨 *OmniAudit Alert*",
                "attachments": [
                    {
                        "color": self._get_alert_color(alert),
                        "fields": [
                            {
                                "title": "Rule",
                                "value": alert["rule_name"],
                                "short": True
                            },
                            {
                                "title": "Metric",
                                "value": alert["metric_name"],
                                "short": True
                            },
                            {
                                "title": "Value",
                                "value": f"{alert['metric_value']:.2f}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert['threshold']:.2f}",
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert["message"],
                                "short": False
                            }
                        ],
                        "footer": "OmniAudit Alert System",
                        "ts": int(alert.get("timestamp", 0))
                    }
                ]
            }

            # Add channel/username overrides if specified
            if self.config.get("channel"):
                payload["channel"] = self.config["channel"]
            if self.config.get("username"):
                payload["username"] = self.config["username"]

            response = requests.post(webhook_url, json=payload)
            return response.status_code == 200

        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    def _get_alert_color(self, alert: Dict[str, Any]) -> str:
        """Get color based on alert severity."""
        value = alert.get("metric_value", 0)
        threshold = alert.get("threshold", 0)

        # Simple logic: red if exceeds threshold significantly
        if abs(value - threshold) / threshold > 0.5:
            return "danger"
        elif abs(value - threshold) / threshold > 0.2:
            return "warning"
        else:
            return "good"


class WebhookNotifier(BaseNotifier):
    """
    Generic webhook notifier.

    Configuration:
        url: str - Webhook URL
        method: str - HTTP method (default: POST)
        headers: Dict - Optional custom headers
    """

    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via webhook."""
        if not REQUESTS_AVAILABLE:
            print("requests library required for webhook notifications")
            return False

        try:
            url = self.config.get("url")
            if not url:
                return False

            method = self.config.get("method", "POST").upper()
            headers = self.config.get("headers", {})
            headers.setdefault("Content-Type", "application/json")

            payload = {
                "event": "alert_triggered",
                "alert": alert
            }

            if method == "POST":
                response = requests.post(url, json=payload, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=payload, headers=headers)
            else:
                return False

            return 200 <= response.status_code < 300

        except Exception as e:
            print(f"Failed to send webhook notification: {e}")
            return False


def get_notifier(channel: str, config: Dict[str, Any]) -> Optional[BaseNotifier]:
    """
    Get notifier instance for channel.

    Args:
        channel: Notification channel (email, slack, webhook)
        config: Notifier configuration

    Returns:
        Notifier instance or None
    """
    notifiers = {
        "email": EmailNotifier,
        "slack": SlackNotifier,
        "webhook": WebhookNotifier
    }

    notifier_class = notifiers.get(channel.lower())
    if notifier_class:
        # Extract channel-specific config
        channel_config = config.get(channel, {})
        return notifier_class(channel_config)

    return None
