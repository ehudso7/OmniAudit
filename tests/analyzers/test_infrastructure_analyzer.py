"""Tests for InfrastructureAnalyzer."""

import pytest
from pathlib import Path
from src.omniaudit.analyzers.infrastructure import InfrastructureAnalyzer, IaCTool
from src.omniaudit.analyzers.infrastructure.scanners import TerraformScanner, KubernetesScanner, DockerScanner
from src.omniaudit.analyzers.base import AnalyzerError


class TestInfrastructureAnalyzer:
    """Test InfrastructureAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = InfrastructureAnalyzer(config)

        assert analyzer.name == "infrastructure_analyzer"
        assert analyzer.version == "1.0.0"

    def test_analyze_empty_project(self, tmp_path):
        """Test analysis of project without IaC."""
        config = {"project_path": str(tmp_path)}
        analyzer = InfrastructureAnalyzer(config)

        result = analyzer.analyze({})

        assert result["analyzer"] == "infrastructure_analyzer"
        metrics = result["data"]["metrics"]
        assert len(metrics["tools_detected"]) == 0

    def test_detect_terraform(self, tmp_path):
        """Test Terraform detection."""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text('''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}
''')

        config = {"project_path": str(tmp_path)}
        analyzer = InfrastructureAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        assert IaCTool.TERRAFORM in metrics["tools_detected"]

    def test_detect_docker(self, tmp_path):
        """Test Docker detection."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text('''
FROM node:14
WORKDIR /app
COPY . .
CMD ["node", "server.js"]
''')

        config = {"project_path": str(tmp_path)}
        analyzer = InfrastructureAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        assert IaCTool.DOCKER in metrics["tools_detected"]


class TestTerraformScanner:
    """Test TerraformScanner class."""

    def test_scan_unencrypted_s3(self, tmp_path):
        """Test scanning for unencrypted S3 buckets."""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text('''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  acl    = "private"
}
''')

        scan = TerraformScanner.scan_file(tf_file)

        assert scan.total_resources == 1
        assert len(scan.security_issues) > 0
        # Should find unencrypted bucket
        assert any("encrypt" in issue.message.lower() for issue in scan.security_issues)

    def test_scan_public_s3(self, tmp_path):
        """Test scanning for public S3 buckets."""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text('''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  acl    = "public-read"
}
''')

        scan = TerraformScanner.scan_file(tf_file)

        # Should find public access issue
        public_issues = [i for i in scan.security_issues if "public" in i.message.lower()]
        assert len(public_issues) > 0
        assert any(i.severity == "critical" for i in public_issues)

    def test_scan_missing_tags(self, tmp_path):
        """Test scanning for missing resource tags."""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text('''
resource "aws_instance" "example" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
}
''')

        scan = TerraformScanner.scan_file(tf_file)

        assert len(scan.resource_tags_missing) > 0

    def test_extract_resources(self):
        """Test resource extraction from Terraform."""
        content = '''
resource "aws_instance" "web" {
  ami = "ami-12345"
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data"
}
'''

        resources = TerraformScanner._extract_resources(content)

        assert len(resources) == 2
        assert resources[0]["type"] == "aws_instance"
        assert resources[0]["name"] == "web"
        assert resources[1]["type"] == "aws_s3_bucket"
        assert resources[1]["name"] == "data"


class TestKubernetesScanner:
    """Test KubernetesScanner class."""

    def test_scan_privileged_container(self, tmp_path):
        """Test scanning for privileged containers."""
        k8s_file = tmp_path / "deployment.yaml"
        k8s_file.write_text('''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  template:
    spec:
      containers:
      - name: test
        image: nginx
        securityContext:
          privileged: true
''')

        scan = KubernetesScanner.scan_file(k8s_file)

        assert scan.total_resources > 0
        assert len(scan.privileged_containers) > 0
        assert any("privileged" in issue.message.lower() for issue in scan.security_issues)

    def test_scan_missing_resource_limits(self, tmp_path):
        """Test scanning for missing resource limits."""
        k8s_file = tmp_path / "deployment.yaml"
        k8s_file.write_text('''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  template:
    spec:
      containers:
      - name: test
        image: nginx
''')

        scan = KubernetesScanner.scan_file(k8s_file)

        assert len(scan.missing_resource_limits) > 0

    def test_scan_missing_security_context(self, tmp_path):
        """Test scanning for missing security context."""
        k8s_file = tmp_path / "pod.yaml"
        k8s_file.write_text('''
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx
''')

        scan = KubernetesScanner.scan_file(k8s_file)

        assert len(scan.missing_security_context) > 0


class TestDockerScanner:
    """Test DockerScanner class."""

    def test_scan_insecure_base_image(self, tmp_path):
        """Test scanning for insecure base images."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text('''
FROM ubuntu:latest
RUN apt-get update
''')

        scan = DockerScanner.scan_file(dockerfile)

        assert len(scan.base_image_issues) > 0
        assert any("latest" in issue for issue in scan.base_image_issues)

    def test_scan_run_as_root(self, tmp_path):
        """Test scanning for containers running as root."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text('''
FROM node:14
WORKDIR /app
COPY . .
CMD ["node", "server.js"]
''')

        scan = DockerScanner.scan_file(dockerfile)

        # Should detect missing USER directive
        assert len(scan.run_as_root) > 0

    def test_scan_with_user_directive(self, tmp_path):
        """Test scanning Dockerfile with USER directive."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text('''
FROM node:14
RUN useradd -m appuser
USER appuser
WORKDIR /app
COPY . .
CMD ["node", "server.js"]
''')

        scan = DockerScanner.scan_file(dockerfile)

        # Should not flag as running as root
        root_issues = [i for i in scan.security_issues if "root" in i.message.lower()]
        assert len(root_issues) == 0

    def test_scan_exposed_secret(self, tmp_path):
        """Test scanning for exposed secrets."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text('''
FROM node:14
ENV API_KEY="secret-key-12345"
ENV PASSWORD="mypassword"
''')

        scan = DockerScanner.scan_file(dockerfile)

        assert len(scan.exposed_secrets) > 0
        critical_issues = [i for i in scan.security_issues if i.severity == "critical"]
        assert len(critical_issues) > 0
