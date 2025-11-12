"""
Code Quality Analyzer

Analyzes code quality metrics including test coverage,
complexity, linting, and code style.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import subprocess
import json
import re

from .base import BaseAnalyzer, AnalyzerError


class CodeQualityAnalyzer(BaseAnalyzer):
    """
    Analyzes code quality for Python and JavaScript projects.

    Metrics:
    - Test coverage percentage
    - Cyclomatic complexity
    - Linting issues
    - Code style violations
    - Lines of code

    Configuration:
        project_path: str - Path to project root (required)
        languages: List[str] - Languages to analyze (default: ["python", "javascript"])

    Example:
        >>> analyzer = CodeQualityAnalyzer({"project_path": "."})
        >>> result = analyzer.analyze({})
    """

    @property
    def name(self) -> str:
        return "code_quality_analyzer"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path does not exist: {path}")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code quality.

        Args:
            data: Optional input data (not used currently)

        Returns:
            Code quality metrics
        """
        project_path = Path(self.config["project_path"])
        languages = self.config.get("languages", ["python", "javascript"])

        results = {
            "project_path": str(project_path),
            "languages_analyzed": languages,
            "metrics": {}
        }

        if "python" in languages:
            results["metrics"]["python"] = self._analyze_python(project_path)

        if "javascript" in languages:
            results["metrics"]["javascript"] = self._analyze_javascript(project_path)

        # Calculate overall score
        results["overall_score"] = self._calculate_score(results["metrics"])

        return self._create_response(results)

    def _analyze_python(self, path: Path) -> Dict[str, Any]:
        """Analyze Python code quality."""
        metrics = {
            "coverage": self._get_python_coverage(path),
            "complexity": self._get_python_complexity(path),
            "linting": self._get_python_linting(path),
            "lines_of_code": self._count_lines(path, ["*.py"])
        }
        return metrics

    def _analyze_javascript(self, path: Path) -> Dict[str, Any]:
        """Analyze JavaScript code quality."""
        metrics = {
            "coverage": self._get_js_coverage(path),
            "linting": self._get_js_linting(path),
            "lines_of_code": self._count_lines(path, ["*.js", "*.jsx", "*.ts", "*.tsx"])
        }
        return metrics

    def _get_python_coverage(self, path: Path) -> Optional[float]:
        """Get Python test coverage percentage."""
        try:
            # Look for coverage report
            coverage_file = path / ".coverage"
            if not coverage_file.exists():
                return None

            # Run coverage report
            result = subprocess.run(
                ["coverage", "report", "--precision=2"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return None

            # Parse coverage percentage from output
            # Look for "TOTAL" line
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line:
                    match = re.search(r'(\d+)%', line)
                    if match:
                        return float(match.group(1))

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _get_python_complexity(self, path: Path) -> Optional[Dict[str, Any]]:
        """Calculate Python code complexity."""
        try:
            # Use radon for complexity analysis
            result = subprocess.run(
                ["radon", "cc", str(path), "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return None

            complexity_data = json.loads(result.stdout)

            # Calculate average complexity
            total_complexity = 0
            function_count = 0

            for file_data in complexity_data.values():
                for item in file_data:
                    total_complexity += item.get("complexity", 0)
                    function_count += 1

            avg_complexity = (
                total_complexity / function_count if function_count > 0 else 0
            )

            return {
                "average": round(avg_complexity, 2),
                "function_count": function_count
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def _get_python_linting(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get Python linting issues."""
        try:
            # Use pylint
            result = subprocess.run(
                ["pylint", str(path), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if not result.stdout:
                return None

            issues = json.loads(result.stdout)

            # Count by severity
            severity_counts = {
                "error": 0,
                "warning": 0,
                "refactor": 0,
                "convention": 0
            }

            for issue in issues:
                issue_type = issue.get("type", "").lower()
                if issue_type in severity_counts:
                    severity_counts[issue_type] += 1

            return {
                "total_issues": len(issues),
                "by_severity": severity_counts
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def _get_js_coverage(self, path: Path) -> Optional[float]:
        """Get JavaScript test coverage."""
        # Look for jest coverage report
        coverage_file = path / "coverage" / "coverage-summary.json"

        if not coverage_file.exists():
            return None

        try:
            with open(coverage_file) as f:
                data = json.load(f)
                total = data.get("total", {})
                lines = total.get("lines", {})
                return lines.get("pct")
        except (json.JSONDecodeError, KeyError):
            return None

    def _get_js_linting(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get JavaScript linting issues."""
        try:
            result = subprocess.run(
                ["eslint", ".", "--format=json"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if not result.stdout:
                return None

            data = json.loads(result.stdout)

            total_errors = sum(file.get("errorCount", 0) for file in data)
            total_warnings = sum(file.get("warningCount", 0) for file in data)

            return {
                "total_issues": total_errors + total_warnings,
                "errors": total_errors,
                "warnings": total_warnings
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def _count_lines(self, path: Path, patterns: List[str]) -> int:
        """Count lines of code."""
        total = 0

        for pattern in patterns:
            for file_path in path.rglob(pattern):
                # Skip common directories
                if any(part in file_path.parts for part in [
                    "node_modules", "venv", "__pycache__", ".git", "dist", "build"
                ]):
                    continue

                try:
                    with open(file_path) as f:
                        total += sum(1 for line in f if line.strip())
                except (IOError, UnicodeDecodeError):
                    continue

        return total

    def _calculate_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)."""
        scores = []

        # Python score
        if "python" in metrics:
            py = metrics["python"]
            if py.get("coverage") is not None:
                scores.append(py["coverage"])

            complexity = py.get("complexity", {}).get("average", 0) if py.get("complexity") else 0
            if complexity > 0:
                # Lower complexity is better (cap at 10)
                complexity_score = max(0, 100 - (complexity - 5) * 10)
                scores.append(complexity_score)

        # JavaScript score
        if "javascript" in metrics:
            js = metrics["javascript"]
            if js.get("coverage") is not None:
                scores.append(js["coverage"])

        return round(sum(scores) / len(scores), 2) if scores else 0.0
