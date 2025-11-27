"""Terraform security scanner."""

import re
from pathlib import Path
from typing import List

from ..types import ComplianceFramework, SecurityIssue, TerraformScan


class TerraformScanner:
    """Scan Terraform files for security issues."""

    SECURITY_RULES = {
        "unencrypted_s3": {
            "resource": "aws_s3_bucket",
            "check": lambda content: "server_side_encryption_configuration" not in content,
            "severity": "high",
            "message": "S3 bucket does not have server-side encryption enabled",
            "remediation": "Add server_side_encryption_configuration block to enable encryption",
            "frameworks": [ComplianceFramework.SOC2, ComplianceFramework.HIPAA, ComplianceFramework.GDPR],
        },
        "public_s3": {
            "resource": "aws_s3_bucket",
            "check": lambda content: '"public-read"' in content or '"public-read-write"' in content,
            "severity": "critical",
            "message": "S3 bucket has public access enabled",
            "remediation": "Remove public ACLs and use bucket policies for access control",
            "frameworks": [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS],
        },
        "unencrypted_rds": {
            "resource": "aws_db_instance",
            "check": lambda content: 'storage_encrypted = false' in content or (
                'storage_encrypted' not in content
            ),
            "severity": "high",
            "message": "RDS instance does not have encryption enabled",
            "remediation": "Set storage_encrypted = true",
            "frameworks": [ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS],
        },
        "missing_vpc_flow_logs": {
            "resource": "aws_vpc",
            "check": lambda content, resources: not any(
                "aws_flow_log" in r for r in resources
            ),
            "severity": "medium",
            "message": "VPC does not have flow logs enabled",
            "remediation": "Create aws_flow_log resource for the VPC",
            "frameworks": [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS],
        },
        "public_security_group": {
            "resource": "aws_security_group",
            "check": lambda content: '0.0.0.0/0' in content and (
                'ingress' in content or 'from_port' in content
            ),
            "severity": "high",
            "message": "Security group allows ingress from 0.0.0.0/0",
            "remediation": "Restrict ingress to specific IP ranges",
            "frameworks": [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS],
        },
    }

    @staticmethod
    def scan_file(file_path: Path) -> TerraformScan:
        """
        Scan Terraform file for security issues.

        Args:
            file_path: Path to Terraform file

        Returns:
            Terraform scan results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return TerraformScan()

        issues = []
        resource_tags_missing = []
        unencrypted_resources = []
        public_access_resources = []

        # Extract all resource blocks
        resources = TerraformScanner._extract_resources(content)

        for resource in resources:
            resource_type = resource["type"]
            resource_name = resource["name"]
            resource_content = resource["content"]
            line_number = resource["line_number"]

            # Check for missing tags
            if not re.search(r'tags\s*=\s*\{', resource_content):
                resource_tags_missing.append(f"{resource_type}.{resource_name}")

            # Apply security rules
            for rule_id, rule in TerraformScanner.SECURITY_RULES.items():
                if resource_type == rule["resource"]:
                    # Check if rule applies
                    is_vulnerable = False

                    if "resources" in rule["check"].__code__.co_varnames:
                        is_vulnerable = rule["check"](resource_content, [r["type"] for r in resources])
                    else:
                        is_vulnerable = rule["check"](resource_content)

                    if is_vulnerable:
                        issue = SecurityIssue(
                            severity=rule["severity"],
                            rule_id=rule_id,
                            rule_name=rule_id.replace("_", " ").title(),
                            message=rule["message"],
                            file_path=str(file_path),
                            line_number=line_number,
                            resource_type=resource_type,
                            resource_name=resource_name,
                            remediation=rule["remediation"],
                            compliance_frameworks=rule["frameworks"],
                        )
                        issues.append(issue)

                        # Track specific issue types
                        if "unencrypted" in rule_id:
                            unencrypted_resources.append(f"{resource_type}.{resource_name}")
                        if "public" in rule_id:
                            public_access_resources.append(f"{resource_type}.{resource_name}")

        return TerraformScan(
            total_resources=len(resources),
            scanned_files=1,
            security_issues=issues,
            resource_tags_missing=resource_tags_missing,
            unencrypted_resources=unencrypted_resources,
            public_access_resources=public_access_resources,
        )

    @staticmethod
    def _extract_resources(content: str) -> List[dict]:
        """Extract resource blocks from Terraform content."""
        resources = []

        # Match resource blocks: resource "type" "name" {
        pattern = re.compile(
            r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
            re.DOTALL,
        )

        lines = content.split("\n")
        for match in pattern.finditer(content):
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_content = match.group(3)

            # Calculate line number
            line_number = content[: match.start()].count("\n") + 1

            resources.append(
                {
                    "type": resource_type,
                    "name": resource_name,
                    "content": resource_content,
                    "line_number": line_number,
                }
            )

        return resources

    @staticmethod
    def scan_directory(directory: Path) -> TerraformScan:
        """
        Scan directory for Terraform files.

        Args:
            directory: Directory path

        Returns:
            Combined scan results
        """
        tf_files = list(directory.glob("**/*.tf"))

        combined = TerraformScan()

        for tf_file in tf_files:
            scan = TerraformScanner.scan_file(tf_file)
            combined.total_resources += scan.total_resources
            combined.scanned_files += scan.scanned_files
            combined.security_issues.extend(scan.security_issues)
            combined.resource_tags_missing.extend(scan.resource_tags_missing)
            combined.unencrypted_resources.extend(scan.unencrypted_resources)
            combined.public_access_resources.extend(scan.public_access_resources)

        return combined
