"""Type definitions for infrastructure analyzer."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class IaCTool(str, Enum):
    """Infrastructure as Code tools."""

    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    CLOUDFORMATION = "cloudformation"
    ANSIBLE = "ansible"


class ComplianceFramework(str, Enum):
    """Compliance frameworks."""

    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci-dss"
    GDPR = "gdpr"
    ISO27001 = "iso27001"


class SecurityIssue(BaseModel):
    """Infrastructure security issue."""

    severity: str = Field(description="critical, high, medium, low")
    rule_id: str
    rule_name: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    remediation: str
    compliance_frameworks: List[ComplianceFramework] = Field(default_factory=list)


class TerraformScan(BaseModel):
    """Terraform security scan results."""

    total_resources: int = 0
    scanned_files: int = 0
    security_issues: List[SecurityIssue] = Field(default_factory=list)
    resource_tags_missing: List[str] = Field(default_factory=list)
    unencrypted_resources: List[str] = Field(default_factory=list)
    public_access_resources: List[str] = Field(default_factory=list)


class KubernetesScan(BaseModel):
    """Kubernetes security scan results."""

    total_resources: int = 0
    scanned_files: int = 0
    security_issues: List[SecurityIssue] = Field(default_factory=list)
    privileged_containers: List[str] = Field(default_factory=list)
    missing_resource_limits: List[str] = Field(default_factory=list)
    missing_security_context: List[str] = Field(default_factory=list)


class DockerScan(BaseModel):
    """Docker security scan results."""

    total_dockerfiles: int = 0
    security_issues: List[SecurityIssue] = Field(default_factory=list)
    base_image_issues: List[str] = Field(default_factory=list)
    run_as_root: List[str] = Field(default_factory=list)
    exposed_secrets: List[str] = Field(default_factory=list)


class ComplianceMapping(BaseModel):
    """Compliance framework mapping."""

    framework: ComplianceFramework
    total_controls: int = 0
    implemented_controls: int = 0
    compliance_percentage: float = 0.0
    missing_controls: List[str] = Field(default_factory=list)


class InfrastructureMetrics(BaseModel):
    """Overall infrastructure metrics."""

    tools_detected: List[IaCTool] = Field(default_factory=list)
    terraform_scan: Optional[TerraformScan] = None
    kubernetes_scan: Optional[KubernetesScan] = None
    docker_scan: Optional[DockerScan] = None
    compliance_mappings: List[ComplianceMapping] = Field(default_factory=list)
    total_security_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    overall_security_score: float = 0.0
    files_analyzed: int = 0


class InfrastructureFinding(BaseModel):
    """Individual infrastructure finding."""

    severity: str = Field(description="critical, warning, or info")
    category: str = Field(
        description="security, compliance, optimization, or best_practice"
    )
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    affected_frameworks: List[ComplianceFramework] = Field(default_factory=list)
