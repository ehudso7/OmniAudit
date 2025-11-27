"""Compliance framework mapper."""

from typing import Dict, List

from ..types import ComplianceFramework, ComplianceMapping, SecurityIssue


class ComplianceMapper:
    """Map security findings to compliance frameworks."""

    # Compliance framework control mappings
    FRAMEWORK_CONTROLS = {
        ComplianceFramework.SOC2: {
            "total_controls": 64,
            "control_categories": {
                "encryption": ["Encryption at rest", "Encryption in transit"],
                "access_control": ["Access controls", "Least privilege", "Network segmentation"],
                "monitoring": ["Logging and monitoring", "Audit trails"],
                "incident_response": ["Incident detection", "Response procedures"],
                "change_management": ["Change control", "Configuration management"],
            },
        },
        ComplianceFramework.HIPAA: {
            "total_controls": 45,
            "control_categories": {
                "encryption": ["PHI encryption at rest", "PHI encryption in transit"],
                "access_control": ["Unique user identification", "Emergency access", "Automatic logoff"],
                "audit": ["Audit controls", "Audit logs"],
                "integrity": ["Data integrity controls"],
                "transmission": ["Transmission security"],
            },
        },
        ComplianceFramework.PCI_DSS: {
            "total_controls": 12,
            "control_categories": {
                "network_security": ["Firewall configuration", "Network segmentation"],
                "encryption": ["Cardholder data encryption"],
                "access_control": ["Access control measures", "Unique IDs"],
                "monitoring": ["Track and monitor access", "Log management"],
                "security_testing": ["Security testing procedures"],
            },
        },
        ComplianceFramework.GDPR: {
            "total_controls": 99,
            "control_categories": {
                "data_protection": ["Personal data encryption", "Pseudonymization"],
                "access": ["Data subject access rights", "Right to erasure"],
                "security": ["Security of processing", "Data breach notification"],
                "privacy": ["Privacy by design", "Data protection impact assessment"],
            },
        },
    }

    @staticmethod
    def map_issues_to_compliance(
        security_issues: List[SecurityIssue],
    ) -> List[ComplianceMapping]:
        """
        Map security issues to compliance frameworks.

        Args:
            security_issues: List of security issues

        Returns:
            List of compliance mappings
        """
        mappings = []

        for framework in ComplianceFramework:
            if framework not in ComplianceMapper.FRAMEWORK_CONTROLS:
                continue

            framework_info = ComplianceMapper.FRAMEWORK_CONTROLS[framework]
            total_controls = framework_info["total_controls"]

            # Count issues affecting this framework
            framework_issues = [
                issue
                for issue in security_issues
                if framework in issue.compliance_frameworks
            ]

            # Map issues to control categories
            affected_categories = set()
            for issue in framework_issues:
                category = ComplianceMapper._map_issue_to_category(issue, framework)
                if category:
                    affected_categories.add(category)

            # Calculate implemented controls (simplified)
            # In reality, this would be more sophisticated
            num_categories = len(framework_info["control_categories"])
            affected_count = len(affected_categories)

            # Estimate controls not implemented based on critical/high issues
            critical_high_issues = [
                i for i in framework_issues if i.severity in ["critical", "high"]
            ]

            # Rough estimate: each critical/high issue = 1-2 missing controls
            missing_controls_estimate = min(len(critical_high_issues) * 2, total_controls)

            implemented = max(0, total_controls - missing_controls_estimate)
            compliance_percentage = (implemented / total_controls * 100) if total_controls > 0 else 100.0

            # Generate missing control descriptions
            missing_controls = []
            for category in affected_categories:
                controls = framework_info["control_categories"].get(category, [])
                missing_controls.extend(controls[:2])  # Add first 2 from each category

            mappings.append(
                ComplianceMapping(
                    framework=framework,
                    total_controls=total_controls,
                    implemented_controls=implemented,
                    compliance_percentage=compliance_percentage,
                    missing_controls=missing_controls[:10],  # Limit to 10
                )
            )

        return mappings

    @staticmethod
    def _map_issue_to_category(issue: SecurityIssue, framework: ComplianceFramework) -> str:
        """Map security issue to control category."""
        rule_id = issue.rule_id.lower()
        message = issue.message.lower()

        # Encryption-related
        if any(word in rule_id or word in message for word in ["encrypt", "unencrypted"]):
            return "encryption"

        # Access control-related
        if any(
            word in rule_id or word in message
            for word in ["public", "access", "privileged", "root", "security_group"]
        ):
            return "access_control"

        # Monitoring-related
        if any(word in rule_id or word in message for word in ["log", "audit", "monitoring"]):
            return "monitoring"

        # Network security
        if any(word in rule_id or word in message for word in ["network", "vpc", "firewall"]):
            return "network_security"

        # Data protection
        if any(word in rule_id or word in message for word in ["data", "secret", "sensitive"]):
            return "data_protection"

        return "security"

    @staticmethod
    def generate_compliance_summary(mappings: List[ComplianceMapping]) -> Dict[str, any]:
        """
        Generate summary of compliance status.

        Args:
            mappings: List of compliance mappings

        Returns:
            Summary dictionary
        """
        summary = {
            "frameworks_analyzed": len(mappings),
            "average_compliance": (
                sum(m.compliance_percentage for m in mappings) / len(mappings)
                if mappings
                else 0.0
            ),
            "fully_compliant": [m.framework.value for m in mappings if m.compliance_percentage == 100],
            "needs_improvement": [
                m.framework.value for m in mappings if m.compliance_percentage < 80
            ],
        }

        return summary
