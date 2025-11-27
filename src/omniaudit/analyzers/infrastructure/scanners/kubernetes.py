"""Kubernetes manifest scanner."""

import re
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None

from ..types import ComplianceFramework, KubernetesScan, SecurityIssue


class KubernetesScanner:
    """Scan Kubernetes manifests for security issues."""

    @staticmethod
    def scan_file(file_path: Path) -> KubernetesScan:
        """
        Scan Kubernetes manifest file.

        Args:
            file_path: Path to manifest file

        Returns:
            Kubernetes scan results
        """
        if yaml is None:
            return KubernetesScan()

        try:
            content = file_path.read_text(encoding="utf-8")
            manifests = list(yaml.safe_load_all(content))
        except (IOError, yaml.YAMLError, UnicodeDecodeError):
            return KubernetesScan()

        issues = []
        privileged_containers = []
        missing_limits = []
        missing_security_context = []
        total_resources = 0

        for manifest in manifests:
            if not manifest or not isinstance(manifest, dict):
                continue

            total_resources += 1
            kind = manifest.get("kind", "Unknown")
            name = manifest.get("metadata", {}).get("name", "unnamed")

            # Check Pods and Deployments
            if kind in ["Pod", "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"]:
                spec = manifest.get("spec", {})

                # For Deployments, get the pod template spec
                if kind in ["Deployment", "StatefulSet", "DaemonSet"]:
                    spec = spec.get("template", {}).get("spec", {})
                elif kind in ["Job", "CronJob"]:
                    if kind == "CronJob":
                        spec = spec.get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
                    else:
                        spec = spec.get("template", {}).get("spec", {})

                containers = spec.get("containers", [])

                for container in containers:
                    container_name = container.get("name", "unnamed")

                    # Check for privileged containers
                    security_context = container.get("securityContext", {})
                    if security_context.get("privileged", False):
                        privileged_containers.append(f"{kind}/{name}/{container_name}")
                        issues.append(
                            SecurityIssue(
                                severity="critical",
                                rule_id="k8s_privileged_container",
                                rule_name="Privileged Container",
                                message=f"Container '{container_name}' runs in privileged mode",
                                file_path=str(file_path),
                                resource_type=kind,
                                resource_name=name,
                                remediation="Remove privileged: true unless absolutely necessary",
                                compliance_frameworks=[
                                    ComplianceFramework.SOC2,
                                    ComplianceFramework.PCI_DSS,
                                ],
                            )
                        )

                    # Check for missing resource limits
                    resources = container.get("resources", {})
                    if not resources.get("limits"):
                        missing_limits.append(f"{kind}/{name}/{container_name}")
                        issues.append(
                            SecurityIssue(
                                severity="medium",
                                rule_id="k8s_missing_limits",
                                rule_name="Missing Resource Limits",
                                message=f"Container '{container_name}' missing resource limits",
                                file_path=str(file_path),
                                resource_type=kind,
                                resource_name=name,
                                remediation="Add resources.limits for CPU and memory",
                                compliance_frameworks=[ComplianceFramework.SOC2],
                            )
                        )

                    # Check for running as root
                    if not security_context:
                        missing_security_context.append(f"{kind}/{name}/{container_name}")
                        issues.append(
                            SecurityIssue(
                                severity="high",
                                rule_id="k8s_missing_security_context",
                                rule_name="Missing Security Context",
                                message=f"Container '{container_name}' missing security context",
                                file_path=str(file_path),
                                resource_type=kind,
                                resource_name=name,
                                remediation="Add securityContext with runAsNonRoot: true and runAsUser",
                                compliance_frameworks=[
                                    ComplianceFramework.SOC2,
                                    ComplianceFramework.PCI_DSS,
                                ],
                            )
                        )

            # Check Services for type LoadBalancer without annotations
            if kind == "Service":
                spec = manifest.get("spec", {})
                if spec.get("type") == "LoadBalancer":
                    annotations = manifest.get("metadata", {}).get("annotations", {})
                    if not annotations:
                        issues.append(
                            SecurityIssue(
                                severity="medium",
                                rule_id="k8s_loadbalancer_no_annotations",
                                rule_name="LoadBalancer Without Annotations",
                                message=f"LoadBalancer Service '{name}' without security annotations",
                                file_path=str(file_path),
                                resource_type=kind,
                                resource_name=name,
                                remediation="Add appropriate cloud provider annotations for security",
                                compliance_frameworks=[ComplianceFramework.SOC2],
                            )
                        )

        return KubernetesScan(
            total_resources=total_resources,
            scanned_files=1,
            security_issues=issues,
            privileged_containers=privileged_containers,
            missing_resource_limits=missing_limits,
            missing_security_context=missing_security_context,
        )

    @staticmethod
    def scan_directory(directory: Path) -> KubernetesScan:
        """
        Scan directory for Kubernetes manifests.

        Args:
            directory: Directory path

        Returns:
            Combined scan results
        """
        manifest_files = list(directory.glob("**/*.yaml")) + list(directory.glob("**/*.yml"))

        # Filter for K8s manifests
        k8s_files = []
        for file in manifest_files:
            if "k8s" in str(file).lower() or "kubernetes" in str(file).lower():
                k8s_files.append(file)
            else:
                # Check if file contains K8s resources
                try:
                    content = file.read_text(encoding="utf-8")
                    if "kind:" in content and "apiVersion:" in content:
                        k8s_files.append(file)
                except (IOError, UnicodeDecodeError):
                    pass

        combined = KubernetesScan()

        for k8s_file in k8s_files:
            scan = KubernetesScanner.scan_file(k8s_file)
            combined.total_resources += scan.total_resources
            combined.scanned_files += scan.scanned_files
            combined.security_issues.extend(scan.security_issues)
            combined.privileged_containers.extend(scan.privileged_containers)
            combined.missing_resource_limits.extend(scan.missing_resource_limits)
            combined.missing_security_context.extend(scan.missing_security_context)

        return combined
