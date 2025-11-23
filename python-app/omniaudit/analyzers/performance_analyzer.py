"""
Performance Analyzer

Analyzes application performance from logs and metrics.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import re
from datetime import datetime

from .base import BaseAnalyzer, AnalyzerError


class PerformanceAnalyzer(BaseAnalyzer):
    """
    Analyzes application performance metrics.

    Parses log files to extract:
    - Response times
    - Error rates
    - Request throughput
    - Resource usage

    Configuration:
        log_path: str - Path to log file or directory (required)
        log_format: str - Log format type (default: "json")

    Example:
        >>> analyzer = PerformanceAnalyzer({
        ...     "log_path": "/var/log/app/access.log",
        ...     "log_format": "common"
        ... })
        >>> result = analyzer.analyze({})
    """

    @property
    def name(self) -> str:
        return "performance_analyzer"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "log_path" not in self.config:
            raise AnalyzerError("log_path is required")

        path = Path(self.config["log_path"])
        if not path.exists():
            raise AnalyzerError(f"Log path does not exist: {path}")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze performance metrics.

        Args:
            data: Optional input data

        Returns:
            Performance metrics
        """
        log_path = Path(self.config["log_path"])
        log_format = self.config.get("log_format", "json")

        results = {
            "log_path": str(log_path),
            "log_format": log_format,
            "metrics": {}
        }

        if log_path.is_file():
            results["metrics"] = self._analyze_log_file(log_path, log_format)
        elif log_path.is_dir():
            # Analyze all log files in directory
            all_metrics = []
            for log_file in log_path.glob("*.log"):
                metrics = self._analyze_log_file(log_file, log_format)
                all_metrics.append(metrics)

            # Aggregate metrics
            results["metrics"] = self._aggregate_metrics(all_metrics)

        return self._create_response(results)

    def _analyze_log_file(self, log_path: Path, log_format: str) -> Dict[str, Any]:
        """Analyze a single log file."""
        metrics = {
            "total_requests": 0,
            "errors": 0,
            "response_times": [],
            "status_codes": {},
            "endpoints": {}
        }

        try:
            with open(log_path, 'r') as f:
                for line in f:
                    self._parse_log_line(line, log_format, metrics)
        except Exception as e:
            raise AnalyzerError(f"Failed to parse log file: {e}")

        # Calculate statistics
        return self._calculate_statistics(metrics)

    def _parse_log_line(self, line: str, log_format: str, metrics: Dict[str, Any]) -> None:
        """Parse a single log line."""
        if log_format == "json":
            self._parse_json_log(line, metrics)
        elif log_format == "common":
            self._parse_common_log(line, metrics)
        elif log_format == "combined":
            self._parse_combined_log(line, metrics)

    def _parse_json_log(self, line: str, metrics: Dict[str, Any]) -> None:
        """Parse JSON format log line."""
        try:
            import json
            data = json.loads(line)

            metrics["total_requests"] += 1

            # Extract status code
            status = data.get("status", 200)
            metrics["status_codes"][status] = metrics["status_codes"].get(status, 0) + 1

            if status >= 400:
                metrics["errors"] += 1

            # Extract response time
            if "response_time" in data:
                metrics["response_times"].append(float(data["response_time"]))

            # Track endpoint
            if "path" in data:
                path = data["path"]
                if path not in metrics["endpoints"]:
                    metrics["endpoints"][path] = {"count": 0, "errors": 0}
                metrics["endpoints"][path]["count"] += 1
                if status >= 400:
                    metrics["endpoints"][path]["errors"] += 1

        except json.JSONDecodeError:
            pass

    def _parse_common_log(self, line: str, metrics: Dict[str, Any]) -> None:
        """Parse Common Log Format."""
        # Pattern: 127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
        pattern = r'(\S+) \S+ \S+ \[([^\]]+)\] "([A-Z]+) ([^\s]+) HTTP/[^"]+" (\d{3}) (\d+)'
        match = re.match(pattern, line)

        if match:
            metrics["total_requests"] += 1
            status = int(match.group(5))
            path = match.group(4)

            metrics["status_codes"][status] = metrics["status_codes"].get(status, 0) + 1

            if status >= 400:
                metrics["errors"] += 1

            if path not in metrics["endpoints"]:
                metrics["endpoints"][path] = {"count": 0, "errors": 0}
            metrics["endpoints"][path]["count"] += 1
            if status >= 400:
                metrics["endpoints"][path]["errors"] += 1

    def _parse_combined_log(self, line: str, metrics: Dict[str, Any]) -> None:
        """Parse Combined Log Format (extends Common format)."""
        self._parse_common_log(line, metrics)

    def _calculate_statistics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from raw metrics."""
        response_times = metrics.get("response_times", [])

        stats = {
            "total_requests": metrics["total_requests"],
            "total_errors": metrics["errors"],
            "error_rate": (metrics["errors"] / metrics["total_requests"] * 100)
                         if metrics["total_requests"] > 0 else 0,
            "status_codes": metrics["status_codes"]
        }

        if response_times:
            sorted_times = sorted(response_times)
            stats["response_time"] = {
                "mean": sum(response_times) / len(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "p50": sorted_times[len(sorted_times) // 2],
                "p95": sorted_times[int(len(sorted_times) * 0.95)],
                "p99": sorted_times[int(len(sorted_times) * 0.99)]
            }

        # Top endpoints by requests
        endpoints = metrics.get("endpoints", {})
        if endpoints:
            top_endpoints = sorted(
                endpoints.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10]

            stats["top_endpoints"] = [
                {
                    "path": path,
                    "requests": data["count"],
                    "errors": data["errors"],
                    "error_rate": (data["errors"] / data["count"] * 100)
                                 if data["count"] > 0 else 0
                }
                for path, data in top_endpoints
            ]

        return stats

    def _aggregate_metrics(self, all_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics from multiple log files."""
        if not all_metrics:
            return {}

        # Simple aggregation - sum totals, average response times
        aggregated = {
            "total_requests": sum(m.get("total_requests", 0) for m in all_metrics),
            "total_errors": sum(m.get("total_errors", 0) for m in all_metrics),
            "status_codes": {},
            "files_analyzed": len(all_metrics)
        }

        # Aggregate status codes
        for metrics in all_metrics:
            for code, count in metrics.get("status_codes", {}).items():
                aggregated["status_codes"][code] = aggregated["status_codes"].get(code, 0) + count

        # Calculate aggregate error rate
        if aggregated["total_requests"] > 0:
            aggregated["error_rate"] = (aggregated["total_errors"] /
                                       aggregated["total_requests"] * 100)

        return aggregated
