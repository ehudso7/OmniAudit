"""
Business Metrics Collector

Executes custom SQL queries to fetch business KPIs.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text

from .base import BaseCollector, ConfigurationError, DataCollectionError


class BusinessMetricsCollector(BaseCollector):
    """
    Collects business metrics from databases.

    Configuration:
        database_url: str - Database connection string (required)
        queries: Dict[str, str] - Named SQL queries (required)

    Example:
        >>> config = {
        ...     "database_url": "postgresql://user:pass@host/db",
        ...     "queries": {
        ...         "daily_revenue": "SELECT SUM(amount) FROM orders WHERE date = CURRENT_DATE",
        ...         "active_users": "SELECT COUNT(DISTINCT user_id) FROM sessions WHERE date >= CURRENT_DATE - 7"
        ...     }
        ... }
        >>> collector = BusinessMetricsCollector(config)
        >>> result = collector.collect()
    """

    @property
    def name(self) -> str:
        return "business_metrics_collector"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
        if "database_url" not in self.config:
            raise ConfigurationError("database_url required")

        if "queries" not in self.config or not self.config["queries"]:
            raise ConfigurationError("queries required")

    def collect(self) -> Dict[str, Any]:
        """Execute queries and collect results."""
        database_url = self.config["database_url"]
        queries = self.config["queries"]

        try:
            engine = create_engine(database_url)

            results = {}
            with engine.connect() as conn:
                for name, query in queries.items():
                    try:
                        result = conn.execute(text(query))
                        row = result.fetchone()

                        if row:
                            # Get first column value
                            results[name] = row[0]
                        else:
                            results[name] = None

                    except Exception as e:
                        results[name] = {"error": str(e)}

            data = {
                "metrics": results,
                "query_count": len(queries)
            }

            return self._create_response(data)

        except Exception as e:
            raise DataCollectionError(f"Database query failed: {e}")
