"""
Prometheus Metrics

Application metrics for monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps

# Request metrics
request_count = Counter(
    'omniaudit_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'omniaudit_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Audit metrics
audit_count = Counter(
    'omniaudit_audits_total',
    'Total audit count',
    ['status']
)

audit_duration = Histogram(
    'omniaudit_audit_duration_seconds',
    'Audit execution duration',
    ['collector', 'analyzer']
)

# Database metrics
db_query_duration = Histogram(
    'omniaudit_db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

db_connection_pool = Gauge(
    'omniaudit_db_connections',
    'Database connection pool size',
    ['state']
)

# Collector metrics
collector_success = Counter(
    'omniaudit_collector_success_total',
    'Successful collector runs',
    ['collector']
)

collector_failure = Counter(
    'omniaudit_collector_failure_total',
    'Failed collector runs',
    ['collector', 'error_type']
)


def track_time(metric: Histogram, labels: dict = None):
    """
    Decorator to track execution time.

    Example:
        >>> @track_time(audit_duration, {'collector': 'git'})
        >>> def run_audit():
        >>>     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        return wrapper
    return decorator
