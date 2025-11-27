"""Docker security scanner."""

import re
from pathlib import Path
from typing import List

from ..types import ComplianceFramework, DockerScan, SecurityIssue


class DockerScanner:
    """Scan Dockerfiles for security issues."""

    # Insecure base images
    INSECURE_BASE_IMAGES = ["latest", "alpine:latest", "ubuntu:latest", "debian:latest"]

    # Secrets patterns to detect
    SECRET_PATTERNS = [
        (r"password\s*=\s*['\"]([^'\"]+)['\"]", "Password"),
        (r"api[_-]?key\s*=\s*['\"]([^'\"]+)['\"]", "API Key"),
        (r"secret\s*=\s*['\"]([^'\"]+)['\"]", "Secret"),
        (r"token\s*=\s*['\"]([^'\"]+)['\"]", "Token"),
        (r"aws_access_key_id\s*=\s*['\"]([^'\"]+)['\"]", "AWS Access Key"),
    ]

    @staticmethod
    def scan_file(file_path: Path) -> DockerScan:
        """
        Scan Dockerfile for security issues.

        Args:
            file_path: Path to Dockerfile

        Returns:
            Docker scan results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return DockerScan()

        issues = []
        base_image_issues = []
        run_as_root = []
        exposed_secrets = []

        lines = content.split("\n")

        has_user_directive = False
        base_image = None

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check FROM instruction
            if line_stripped.upper().startswith("FROM"):
                base_image = line_stripped.split()[1] if len(line_stripped.split()) > 1 else None

                # Check for insecure base images
                if base_image:
                    if any(insecure in base_image for insecure in DockerScanner.INSECURE_BASE_IMAGES):
                        base_image_issues.append(base_image)
                        issues.append(
                            SecurityIssue(
                                severity="medium",
                                rule_id="docker_insecure_base_image",
                                rule_name="Insecure Base Image",
                                message=f"Using potentially insecure base image: {base_image}",
                                file_path=str(file_path),
                                line_number=line_num,
                                remediation="Use specific version tags instead of 'latest'",
                                compliance_frameworks=[ComplianceFramework.SOC2],
                            )
                        )

            # Check USER directive
            if line_stripped.upper().startswith("USER"):
                has_user_directive = True
                user = line_stripped.split()[1] if len(line_stripped.split()) > 1 else None
                if user and user.lower() == "root":
                    run_as_root.append(str(file_path))

            # Check for exposed secrets
            for pattern, secret_type in DockerScanner.SECRET_PATTERNS:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    exposed_secrets.append(f"{secret_type} at line {line_num}")
                    issues.append(
                        SecurityIssue(
                            severity="critical",
                            rule_id="docker_exposed_secret",
                            rule_name="Exposed Secret",
                            message=f"Potential {secret_type} exposed in Dockerfile",
                            file_path=str(file_path),
                            line_number=line_num,
                            remediation="Use build arguments or environment variables instead of hardcoding secrets",
                            compliance_frameworks=[
                                ComplianceFramework.SOC2,
                                ComplianceFramework.PCI_DSS,
                                ComplianceFramework.HIPAA,
                            ],
                        )
                    )

            # Check for running package managers as root without cleanup
            if re.search(r"RUN\s+(apt-get|yum|apk)\s+", line_stripped, re.IGNORECASE):
                if "rm -rf" not in line_stripped and "clean" not in line_stripped.lower():
                    issues.append(
                        SecurityIssue(
                            severity="low",
                            rule_id="docker_no_cleanup",
                            rule_name="Missing Package Manager Cleanup",
                            message="Package installation without cleanup increases image size",
                            file_path=str(file_path),
                            line_number=line_num,
                            remediation="Add cleanup commands (e.g., 'rm -rf /var/lib/apt/lists/*')",
                            compliance_frameworks=[],
                        )
                    )

            # Check for COPY with wildcards
            if re.search(r"COPY\s+\*", line_stripped, re.IGNORECASE):
                issues.append(
                    SecurityIssue(
                        severity="low",
                        rule_id="docker_wildcard_copy",
                        rule_name="Wildcard COPY",
                        message="Using wildcard in COPY may include sensitive files",
                        file_path=str(file_path),
                        line_number=line_num,
                        remediation="Explicitly specify files to COPY or use .dockerignore",
                        compliance_frameworks=[ComplianceFramework.SOC2],
                    )
                )

        # Check if USER directive is missing (runs as root)
        if not has_user_directive:
            run_as_root.append(str(file_path))
            issues.append(
                SecurityIssue(
                    severity="high",
                    rule_id="docker_run_as_root",
                    rule_name="Container Runs as Root",
                    message="Dockerfile does not specify USER directive, container will run as root",
                    file_path=str(file_path),
                    remediation="Add USER directive to run container as non-root user",
                    compliance_frameworks=[ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS],
                )
            )

        return DockerScan(
            total_dockerfiles=1,
            security_issues=issues,
            base_image_issues=base_image_issues,
            run_as_root=run_as_root,
            exposed_secrets=exposed_secrets,
        )

    @staticmethod
    def scan_directory(directory: Path) -> DockerScan:
        """
        Scan directory for Dockerfiles.

        Args:
            directory: Directory path

        Returns:
            Combined scan results
        """
        dockerfile_patterns = ["**/Dockerfile", "**/Dockerfile.*", "**/*.dockerfile"]

        dockerfiles = []
        for pattern in dockerfile_patterns:
            dockerfiles.extend(directory.glob(pattern))

        combined = DockerScan()

        for dockerfile in dockerfiles:
            if dockerfile.is_file():
                scan = DockerScanner.scan_file(dockerfile)
                combined.total_dockerfiles += scan.total_dockerfiles
                combined.security_issues.extend(scan.security_issues)
                combined.base_image_issues.extend(scan.base_image_issues)
                combined.run_as_root.extend(scan.run_as_root)
                combined.exposed_secrets.extend(scan.exposed_secrets)

        return combined
