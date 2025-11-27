"""Infrastructure as Code security analyzer."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseAnalyzer, AnalyzerError
from .scanners import ComplianceMapper, DockerScanner, KubernetesScanner, TerraformScanner
from .types import IaCTool, InfrastructureFinding, InfrastructureMetrics


class InfrastructureAnalyzer(BaseAnalyzer):
    """
    Analyze Infrastructure as Code for security and compliance.

    Supports:
    - Terraform security scanning
    - Kubernetes manifest validation
    - Dockerfile optimization
    - Compliance framework mapping (SOC2, HIPAA, PCI-DSS, GDPR)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize infrastructure analyzer."""
        super().__init__(config)
        self.project_path = Path(self.config["project_path"])

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "infrastructure_analyzer"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required in configuration")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path {path} does not exist")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze infrastructure security and compliance.

        Args:
            data: Input data (file patterns, exclusions, etc.)

        Returns:
            Analysis results with metrics and findings
        """
        # Detect IaC tools
        tools_detected = self._detect_iac_tools()

        # Scan Terraform
        terraform_scan = None
        if IaCTool.TERRAFORM in tools_detected:
            terraform_scan = TerraformScanner.scan_directory(self.project_path)

        # Scan Kubernetes
        kubernetes_scan = None
        if IaCTool.KUBERNETES in tools_detected:
            kubernetes_scan = KubernetesScanner.scan_directory(self.project_path)

        # Scan Docker
        docker_scan = None
        if IaCTool.DOCKER in tools_detected:
            docker_scan = DockerScanner.scan_directory(self.project_path)

        # Collect all security issues
        all_issues = []
        if terraform_scan:
            all_issues.extend(terraform_scan.security_issues)
        if kubernetes_scan:
            all_issues.extend(kubernetes_scan.security_issues)
        if docker_scan:
            all_issues.extend(docker_scan.security_issues)

        # Map to compliance frameworks
        compliance_mappings = ComplianceMapper.map_issues_to_compliance(all_issues)

        # Count issues by severity
        critical = sum(1 for i in all_issues if i.severity == "critical")
        high = sum(1 for i in all_issues if i.severity == "high")
        medium = sum(1 for i in all_issues if i.severity == "medium")
        low = sum(1 for i in all_issues if i.severity == "low")

        # Calculate security score
        security_score = self._calculate_security_score(critical, high, medium, low)

        # Count files analyzed
        files_analyzed = 0
        if terraform_scan:
            files_analyzed += terraform_scan.scanned_files
        if kubernetes_scan:
            files_analyzed += kubernetes_scan.scanned_files
        if docker_scan:
            files_analyzed += docker_scan.total_dockerfiles

        metrics = InfrastructureMetrics(
            tools_detected=tools_detected,
            terraform_scan=terraform_scan,
            kubernetes_scan=kubernetes_scan,
            docker_scan=docker_scan,
            compliance_mappings=compliance_mappings,
            total_security_issues=len(all_issues),
            critical_issues=critical,
            high_issues=high,
            medium_issues=medium,
            low_issues=low,
            overall_security_score=security_score,
            files_analyzed=files_analyzed,
        )

        findings = self._generate_findings(metrics)

        return self._create_response(
            {
                "metrics": metrics.model_dump(),
                "findings": [f.model_dump() for f in findings],
                "summary": self._generate_summary(metrics),
                "compliance_summary": ComplianceMapper.generate_compliance_summary(
                    compliance_mappings
                ),
            }
        )

    def _detect_iac_tools(self) -> List[IaCTool]:
        """Detect IaC tools used in project."""
        tools = []

        # Check for Terraform
        if list(self.project_path.glob("**/*.tf")):
            tools.append(IaCTool.TERRAFORM)

        # Check for Kubernetes
        k8s_indicators = ["k8s", "kubernetes", "manifests"]
        yaml_files = list(self.project_path.glob("**/*.yaml")) + list(
            self.project_path.glob("**/*.yml")
        )

        for yaml_file in yaml_files:
            if any(indicator in str(yaml_file).lower() for indicator in k8s_indicators):
                tools.append(IaCTool.KUBERNETES)
                break
            else:
                # Check file content for K8s resources
                try:
                    content = yaml_file.read_text(encoding="utf-8")
                    if "kind:" in content and "apiVersion:" in content:
                        tools.append(IaCTool.KUBERNETES)
                        break
                except (IOError, UnicodeDecodeError):
                    pass

        # Check for Docker
        if list(self.project_path.glob("**/Dockerfile*")) or list(
            self.project_path.glob("**/*.dockerfile")
        ):
            tools.append(IaCTool.DOCKER)

        # Check for CloudFormation
        if list(self.project_path.glob("**/*cloudformation*.yaml")) or list(
            self.project_path.glob("**/*cloudformation*.json")
        ):
            tools.append(IaCTool.CLOUDFORMATION)

        # Check for Ansible
        if list(self.project_path.glob("**/*playbook*.yaml")) or list(
            self.project_path.glob("**/ansible.cfg")
        ):
            tools.append(IaCTool.ANSIBLE)

        return tools

    def _calculate_security_score(
        self, critical: int, high: int, medium: int, low: int
    ) -> float:
        """Calculate overall security score (0-100)."""
        # Start with perfect score
        score = 100.0

        # Deduct points based on severity
        score -= critical * 15  # -15 points per critical issue
        score -= high * 10  # -10 points per high issue
        score -= medium * 5  # -5 points per medium issue
        score -= low * 1  # -1 point per low issue

        return max(0.0, round(score, 2))

    def _generate_findings(self, metrics: InfrastructureMetrics) -> List[InfrastructureFinding]:
        """Generate findings from metrics."""
        findings = []

        # Critical issues
        if metrics.critical_issues > 0:
            findings.append(
                InfrastructureFinding(
                    severity="critical",
                    category="security",
                    message=f"Found {metrics.critical_issues} critical security issues that must be addressed immediately",
                    suggestion="Review and remediate all critical issues before deployment",
                )
            )

        # Terraform-specific findings
        if metrics.terraform_scan:
            if metrics.terraform_scan.unencrypted_resources:
                findings.append(
                    InfrastructureFinding(
                        severity="warning",
                        category="security",
                        message=f"{len(metrics.terraform_scan.unencrypted_resources)} resources without encryption",
                        suggestion="Enable encryption for all data storage resources",
                        affected_frameworks=[fm for fm in metrics.compliance_mappings if fm.compliance_percentage < 100],
                    )
                )

            if metrics.terraform_scan.public_access_resources:
                findings.append(
                    InfrastructureFinding(
                        severity="critical",
                        category="security",
                        message=f"{len(metrics.terraform_scan.public_access_resources)} resources with public access",
                        suggestion="Restrict access to private networks and use security groups",
                    )
                )

        # Kubernetes-specific findings
        if metrics.kubernetes_scan:
            if metrics.kubernetes_scan.privileged_containers:
                findings.append(
                    InfrastructureFinding(
                        severity="critical",
                        category="security",
                        message=f"{len(metrics.kubernetes_scan.privileged_containers)} containers running in privileged mode",
                        suggestion="Remove privileged mode unless absolutely necessary",
                    )
                )

            if metrics.kubernetes_scan.missing_resource_limits:
                findings.append(
                    InfrastructureFinding(
                        severity="warning",
                        category="optimization",
                        message=f"{len(metrics.kubernetes_scan.missing_resource_limits)} containers missing resource limits",
                        suggestion="Add CPU and memory limits to prevent resource exhaustion",
                    )
                )

        # Docker-specific findings
        if metrics.docker_scan:
            if metrics.docker_scan.run_as_root:
                findings.append(
                    InfrastructureFinding(
                        severity="warning",
                        category="security",
                        message=f"{len(metrics.docker_scan.run_as_root)} Dockerfiles run containers as root",
                        suggestion="Add USER directive to run as non-root user",
                    )
                )

            if metrics.docker_scan.exposed_secrets:
                findings.append(
                    InfrastructureFinding(
                        severity="critical",
                        category="security",
                        message=f"{len(metrics.docker_scan.exposed_secrets)} potential secrets exposed in Dockerfiles",
                        suggestion="Use environment variables or secrets management instead",
                    )
                )

        # Compliance findings
        non_compliant = [m for m in metrics.compliance_mappings if m.compliance_percentage < 100]
        if non_compliant:
            for mapping in non_compliant[:3]:  # Limit to first 3
                findings.append(
                    InfrastructureFinding(
                        severity="warning",
                        category="compliance",
                        message=f"{mapping.framework.value.upper()} compliance at {mapping.compliance_percentage:.1f}%",
                        suggestion=f"Address {len(mapping.missing_controls)} missing controls",
                        affected_frameworks=[mapping.framework],
                    )
                )

        # No IaC found
        if not metrics.tools_detected:
            findings.append(
                InfrastructureFinding(
                    severity="info",
                    category="best_practice",
                    message="No Infrastructure as Code detected",
                    suggestion="Consider using IaC tools (Terraform, Kubernetes) for infrastructure management",
                )
            )

        return findings

    def _generate_summary(self, metrics: InfrastructureMetrics) -> str:
        """Generate summary text."""
        if not metrics.tools_detected:
            return "No Infrastructure as Code detected in project."

        tools = ", ".join([t.value for t in metrics.tools_detected])
        return (
            f"Infrastructure Security Score: {metrics.overall_security_score}/100. "
            f"Detected tools: {tools}. "
            f"Found {metrics.total_security_issues} security issues "
            f"({metrics.critical_issues} critical, {metrics.high_issues} high). "
            f"Analyzed {metrics.files_analyzed} files."
        )
