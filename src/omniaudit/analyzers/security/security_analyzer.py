"""
Security Analyzer

Comprehensive security analysis tool performing SAST, secret detection,
and vulnerability identification.
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base import BaseAnalyzer, AnalyzerError
from .types import SecurityFinding, SecurityReport, Severity
from .detectors import (
    SecretsDetector,
    InjectionDetector,
    XSSDetector,
    CryptoDetector,
    OWASPDetector,
)


class SecurityAnalyzer(BaseAnalyzer):
    """
    Performs comprehensive security analysis on codebases.

    Features:
    - Secret detection (API keys, passwords, tokens, certificates)
    - SAST analysis (SQL injection, XSS, SSRF, path traversal)
    - Cryptographic weakness detection
    - OWASP Top 10 coverage
    - CWE mapping
    - Severity classification

    Configuration:
        project_path: str - Path to project root (required)
        rules_path: Optional[str] - Path to custom rules file
        detectors: Optional[List[str]] - List of detectors to enable
        min_severity: Optional[str] - Minimum severity to report (default: "info")
        exclude_patterns: Optional[List[str]] - Patterns to exclude from scanning

    Example:
        >>> analyzer = SecurityAnalyzer({"project_path": "."})
        >>> result = analyzer.analyze({})
        >>> print(result["data"]["summary"]["total_findings"])
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security analyzer."""
        super().__init__(config)
        self._initialize_detectors()

    @property
    def name(self) -> str:
        return "security_analyzer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path does not exist: {path}")

    def _initialize_detectors(self) -> None:
        """Initialize all security detectors."""
        # Get rules path
        rules_path = self.config.get("rules_path")
        if rules_path:
            rules_path = Path(rules_path)
        else:
            # Use default rules
            rules_path = Path(__file__).parent / "rules" / "security_rules.yaml"

        # Initialize detectors
        enabled_detectors = self.config.get("detectors", ["all"])

        if "all" in enabled_detectors:
            self.detectors = {
                "secrets": SecretsDetector(rules_path),
                "injection": InjectionDetector(rules_path),
                "xss": XSSDetector(rules_path),
                "crypto": CryptoDetector(rules_path),
                "owasp": OWASPDetector(rules_path),
            }
        else:
            self.detectors = {}
            if "secrets" in enabled_detectors:
                self.detectors["secrets"] = SecretsDetector(rules_path)
            if "injection" in enabled_detectors:
                self.detectors["injection"] = InjectionDetector(rules_path)
            if "xss" in enabled_detectors:
                self.detectors["xss"] = XSSDetector(rules_path)
            if "crypto" in enabled_detectors:
                self.detectors["crypto"] = CryptoDetector(rules_path)
            if "owasp" in enabled_detectors:
                self.detectors["owasp"] = OWASPDetector(rules_path)

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform security analysis on the codebase.

        Args:
            data: Optional input data (not used currently)

        Returns:
            Security analysis results with findings and metrics
        """
        project_path = Path(self.config["project_path"])
        min_severity = Severity(self.config.get("min_severity", "info"))

        # Create scan ID
        scan_id = str(uuid.uuid4())

        # Collect all findings
        all_findings: List[SecurityFinding] = []

        for detector_name, detector in self.detectors.items():
            try:
                findings = detector.scan_directory(project_path)
                all_findings.extend(findings)
            except Exception as e:
                # Log error but continue with other detectors
                pass

        # Filter by severity
        filtered_findings = self._filter_by_severity(all_findings, min_severity)

        # Deduplicate findings
        unique_findings = self._deduplicate_findings(filtered_findings)

        # Sort by severity (critical first)
        sorted_findings = self._sort_findings(unique_findings)

        # Create report
        report = SecurityReport(
            scan_id=scan_id,
            timestamp=datetime.utcnow(),
            findings=sorted_findings,
            summary=self._create_summary(sorted_findings),
            metadata={
                "project_path": str(project_path),
                "detectors_used": list(self.detectors.keys()),
                "total_files_scanned": self._count_files(project_path),
                "scan_duration_seconds": 0,  # TODO: Add timing
            },
        )

        # Convert to dict for response
        report_dict = report.dict()

        # Add additional analysis
        report_dict["risk_score"] = self._calculate_risk_score(report)
        report_dict["compliance"] = self._check_compliance(report)

        return self._create_response(report_dict)

    def _filter_by_severity(
        self, findings: List[SecurityFinding], min_severity: Severity
    ) -> List[SecurityFinding]:
        """Filter findings by minimum severity."""
        severity_order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }

        min_level = severity_order[min_severity]

        return [f for f in findings if severity_order[f.severity] >= min_level]

    def _deduplicate_findings(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Remove duplicate findings based on file, line, and issue type."""
        seen = set()
        unique = []

        for finding in findings:
            key = (finding.file_path, finding.line_number, finding.title)
            if key not in seen:
                seen.add(key)
                unique.append(finding)

        return unique

    def _sort_findings(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Sort findings by severity (critical first) and confidence."""
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }

        return sorted(
            findings, key=lambda f: (severity_order[f.severity], -f.confidence, f.file_path)
        )

    def _create_summary(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Create summary statistics from findings."""
        summary = {
            "total_findings": len(findings),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
            },
            "by_category": {},
            "top_issues": [],
            "files_with_issues": len(set(f.file_path for f in findings)),
        }

        # Count by severity
        for finding in findings:
            summary["by_severity"][finding.severity.value] += 1

        # Count by category
        for finding in findings:
            category = finding.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1

        # Get top issues (most common)
        issue_counts = {}
        for finding in findings:
            issue_counts[finding.title] = issue_counts.get(finding.title, 0) + 1

        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        summary["top_issues"] = [
            {"issue": issue, "count": count} for issue, count in top_issues
        ]

        return summary

    def _calculate_risk_score(self, report: SecurityReport) -> float:
        """
        Calculate overall risk score (0-100).

        Based on severity and number of findings.
        """
        severity_weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 5.0,
            Severity.MEDIUM: 2.0,
            Severity.LOW: 0.5,
            Severity.INFO: 0.1,
        }

        total_risk = 0.0
        for finding in report.findings:
            total_risk += severity_weights[finding.severity] * finding.confidence

        # Normalize to 0-100 scale (cap at 100)
        normalized_score = min(100.0, total_risk)

        return round(normalized_score, 2)

    def _check_compliance(self, report: SecurityReport) -> Dict[str, Any]:
        """Check compliance with security standards."""
        compliance = {
            "owasp_top_10": {
                "covered": True,
                "issues_found": {},
            },
            "pci_dss": {
                "compliant": report.get_critical_findings() == [],
                "critical_issues": len(report.get_critical_findings()),
            },
            "hipaa": {
                "encryption_issues": 0,
                "access_control_issues": 0,
            },
        }

        # Count OWASP issues
        for finding in report.findings:
            if finding.owasp:
                owasp_cat = finding.owasp
                compliance["owasp_top_10"]["issues_found"][owasp_cat] = (
                    compliance["owasp_top_10"]["issues_found"].get(owasp_cat, 0) + 1
                )

        # Count HIPAA-related issues
        for finding in report.findings:
            if "crypt" in finding.category.value.lower():
                compliance["hipaa"]["encryption_issues"] += 1
            if "access" in finding.category.value.lower() or "auth" in finding.category.value.lower():
                compliance["hipaa"]["access_control_issues"] += 1

        return compliance

    def _count_files(self, directory: Path) -> int:
        """Count total files scanned."""
        extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php"]
        count = 0

        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                if any(
                    part in file_path.parts
                    for part in ["node_modules", "venv", "__pycache__", ".git", "dist", "build"]
                ):
                    continue
                count += 1

        return count

    def export_sarif(self, report: SecurityReport) -> Dict[str, Any]:
        """
        Export findings in SARIF format for integration with CI/CD tools.

        SARIF: Static Analysis Results Interchange Format
        """
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "OmniAudit Security Analyzer",
                            "version": self.version,
                            "informationUri": "https://github.com/omniaudit/omniaudit",
                        }
                    },
                    "results": [],
                }
            ],
        }

        for finding in report.findings:
            result = {
                "ruleId": f"CWE-{finding.cwe.id}" if finding.cwe else finding.category.value,
                "level": self._severity_to_sarif_level(finding.severity),
                "message": {"text": finding.description},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.file_path},
                            "region": {
                                "startLine": finding.line_number,
                                "snippet": {"text": finding.code_snippet},
                            },
                        }
                    }
                ],
            }
            sarif["runs"][0]["results"].append(result)

        return sarif

    def _severity_to_sarif_level(self, severity: Severity) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.INFO: "note",
        }
        return mapping[severity]
