"""
Language-specific analyzer implementations.

Supports Python, JavaScript, Go, Java, Ruby, PHP.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import subprocess
import json
import re


class LanguageAnalyzer:
    """Base class for language-specific analysis."""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def analyze(self) -> Dict[str, Any]:
        """Run all analysis methods."""
        return {
            "coverage": self.get_coverage(),
            "complexity": self.get_complexity(),
            "linting": self.get_linting(),
            "lines_of_code": self.count_lines(),
            "dependencies": self.get_dependencies()
        }

    def get_coverage(self) -> Optional[float]:
        """Get test coverage percentage."""
        raise NotImplementedError

    def get_complexity(self) -> Optional[Dict[str, Any]]:
        """Get code complexity metrics."""
        raise NotImplementedError

    def get_linting(self) -> Optional[Dict[str, Any]]:
        """Get linting issues."""
        raise NotImplementedError

    def count_lines(self) -> int:
        """Count lines of code."""
        raise NotImplementedError

    def get_dependencies(self) -> Optional[List[str]]:
        """Get project dependencies."""
        raise NotImplementedError


class GoAnalyzer(LanguageAnalyzer):
    """Analyzer for Go projects."""

    def get_coverage(self) -> Optional[float]:
        """Get Go test coverage."""
        try:
            result = subprocess.run(
                ["go", "test", "-cover", "./..."],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse coverage from output
            # Format: "coverage: 85.2% of statements"
            match = re.search(r'coverage: ([\d.]+)%', result.stdout)
            if match:
                return float(match.group(1))

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def get_complexity(self) -> Optional[Dict[str, Any]]:
        """Get Go complexity using gocyclo."""
        try:
            result = subprocess.run(
                ["gocyclo", "-avg", "."],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return None

            # Parse average complexity
            match = re.search(r'Average: ([\d.]+)', result.stdout)
            if match:
                return {
                    "average": float(match.group(1)),
                    "tool": "gocyclo"
                }

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def get_linting(self) -> Optional[Dict[str, Any]]:
        """Get Go linting issues using golangci-lint."""
        try:
            result = subprocess.run(
                ["golangci-lint", "run", "--out-format=json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if not result.stdout:
                return {"total_issues": 0}

            data = json.loads(result.stdout)
            issues = data.get("Issues", [])

            return {
                "total_issues": len(issues),
                "by_severity": self._count_by_severity(issues),
                "tool": "golangci-lint"
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def count_lines(self) -> int:
        """Count Go lines of code."""
        total = 0
        for file_path in self.project_path.rglob("*.go"):
            if "vendor" in file_path.parts or "test" in file_path.name:
                continue

            try:
                with open(file_path) as f:
                    total += sum(1 for line in f if line.strip() and not line.strip().startswith("//"))
            except (IOError, UnicodeDecodeError):
                continue

        return total

    def get_dependencies(self) -> Optional[List[str]]:
        """Get Go dependencies from go.mod."""
        go_mod = self.project_path / "go.mod"
        if not go_mod.exists():
            return None

        deps = []
        try:
            content = go_mod.read_text()
            in_require = False

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('require'):
                    in_require = True
                    continue
                if in_require:
                    if line == ')':
                        break
                    if line:
                        dep = line.split()[0]
                        deps.append(dep)
        except Exception:
            return None

        return deps

    def _count_by_severity(self, issues: List[Dict]) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {"error": 0, "warning": 0, "info": 0}
        for issue in issues:
            severity = issue.get("severity", "info").lower()
            if severity in counts:
                counts[severity] += 1
        return counts


class JavaAnalyzer(LanguageAnalyzer):
    """Analyzer for Java projects."""

    def get_coverage(self) -> Optional[float]:
        """Get Java test coverage from JaCoCo."""
        jacoco_xml = self.project_path / "target" / "site" / "jacoco" / "jacoco.xml"

        if not jacoco_xml.exists():
            return None

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(jacoco_xml)
            root = tree.getroot()

            covered = 0
            missed = 0

            for counter in root.findall(".//counter[@type='INSTRUCTION']"):
                covered += int(counter.get('covered', 0))
                missed += int(counter.get('missed', 0))

            total = covered + missed
            if total > 0:
                return (covered / total) * 100

            return None

        except Exception:
            return None

    def get_complexity(self) -> Optional[Dict[str, Any]]:
        """Get Java complexity."""
        # Would use tools like PMD or Checkstyle
        return None

    def get_linting(self) -> Optional[Dict[str, Any]]:
        """Get Java linting from Checkstyle."""
        try:
            result = subprocess.run(
                ["mvn", "checkstyle:check"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse violations from output
            violations = len(re.findall(r'\[ERROR\]', result.stdout))

            return {
                "total_issues": violations,
                "tool": "checkstyle"
            }

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def count_lines(self) -> int:
        """Count Java lines of code."""
        total = 0
        for file_path in self.project_path.rglob("*.java"):
            if "target" in file_path.parts or "test" in str(file_path).lower():
                continue

            try:
                with open(file_path) as f:
                    total += sum(1 for line in f if line.strip() and not line.strip().startswith("//"))
            except (IOError, UnicodeDecodeError):
                continue

        return total

    def get_dependencies(self) -> Optional[List[str]]:
        """Get Java dependencies from pom.xml."""
        pom = self.project_path / "pom.xml"
        if not pom.exists():
            return None

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(pom)
            root = tree.getroot()

            # Handle namespaces
            ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}

            deps = []
            for dep in root.findall('.//mvn:dependency', ns):
                group = dep.find('mvn:groupId', ns)
                artifact = dep.find('mvn:artifactId', ns)
                if group is not None and artifact is not None:
                    deps.append(f"{group.text}:{artifact.text}")

            return deps

        except Exception:
            return None


class RubyAnalyzer(LanguageAnalyzer):
    """Analyzer for Ruby projects."""

    def get_coverage(self) -> Optional[float]:
        """Get Ruby test coverage from SimpleCov."""
        coverage_file = self.project_path / "coverage" / ".resultset.json"

        if not coverage_file.exists():
            return None

        try:
            with open(coverage_file) as f:
                data = json.load(f)

            # SimpleCov format varies, try to extract coverage
            for key, value in data.items():
                if 'coverage' in value:
                    return value['coverage']

            return None

        except (json.JSONDecodeError, IOError):
            return None

    def get_complexity(self) -> Optional[Dict[str, Any]]:
        """Get Ruby complexity using flog."""
        try:
            result = subprocess.run(
                ["flog", "-a", "."],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse average complexity
            match = re.search(r'([\d.]+): flog total', result.stdout)
            if match:
                return {
                    "average": float(match.group(1)),
                    "tool": "flog"
                }

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def get_linting(self) -> Optional[Dict[str, Any]]:
        """Get Ruby linting using RuboCop."""
        try:
            result = subprocess.run(
                ["rubocop", "--format", "json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if not result.stdout:
                return None

            data = json.loads(result.stdout)

            total = sum(len(file.get('offenses', [])) for file in data.get('files', []))

            return {
                "total_issues": total,
                "tool": "rubocop"
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def count_lines(self) -> int:
        """Count Ruby lines of code."""
        total = 0
        for file_path in self.project_path.rglob("*.rb"):
            if "vendor" in file_path.parts or "test" in str(file_path):
                continue

            try:
                with open(file_path) as f:
                    total += sum(1 for line in f if line.strip() and not line.strip().startswith("#"))
            except (IOError, UnicodeDecodeError):
                continue

        return total

    def get_dependencies(self) -> Optional[List[str]]:
        """Get Ruby dependencies from Gemfile."""
        gemfile = self.project_path / "Gemfile"
        if not gemfile.exists():
            return None

        deps = []
        try:
            content = gemfile.read_text()
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('gem '):
                    # Extract gem name
                    match = re.search(r"gem ['\"]([\w-]+)['\"]", line)
                    if match:
                        deps.append(match.group(1))
        except Exception:
            return None

        return deps


class PHPAnalyzer(LanguageAnalyzer):
    """Analyzer for PHP projects."""

    def get_coverage(self) -> Optional[float]:
        """Get PHP test coverage from PHPUnit."""
        coverage_file = self.project_path / "coverage" / "clover.xml"

        if not coverage_file.exists():
            return None

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            metrics = root.find('.//metrics')
            if metrics is not None:
                statements = int(metrics.get('statements', 0))
                covered = int(metrics.get('coveredstatements', 0))

                if statements > 0:
                    return (covered / statements) * 100

            return None

        except Exception:
            return None

    def get_complexity(self) -> Optional[Dict[str, Any]]:
        """Get PHP complexity using PHPMD."""
        return None

    def get_linting(self) -> Optional[Dict[str, Any]]:
        """Get PHP linting using PHP_CodeSniffer."""
        try:
            result = subprocess.run(
                ["phpcs", "--report=json", "."],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if not result.stdout:
                return None

            data = json.loads(result.stdout)

            total_errors = data.get('totals', {}).get('errors', 0)
            total_warnings = data.get('totals', {}).get('warnings', 0)

            return {
                "total_issues": total_errors + total_warnings,
                "errors": total_errors,
                "warnings": total_warnings,
                "tool": "phpcs"
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def count_lines(self) -> int:
        """Count PHP lines of code."""
        total = 0
        for file_path in self.project_path.rglob("*.php"):
            if "vendor" in file_path.parts or "test" in str(file_path):
                continue

            try:
                with open(file_path) as f:
                    total += sum(1 for line in f if line.strip() and not line.strip().startswith("//"))
            except (IOError, UnicodeDecodeError):
                continue

        return total

    def get_dependencies(self) -> Optional[List[str]]:
        """Get PHP dependencies from composer.json."""
        composer = self.project_path / "composer.json"
        if not composer.exists():
            return None

        try:
            with open(composer) as f:
                data = json.load(f)

            deps = []
            for key in ['require', 'require-dev']:
                if key in data:
                    deps.extend(data[key].keys())

            return deps

        except (json.JSONDecodeError, IOError):
            return None


# Factory function
def get_analyzer(language: str, project_path: Path) -> Optional[LanguageAnalyzer]:
    """Get appropriate analyzer for language."""
    analyzers = {
        'go': GoAnalyzer,
        'java': JavaAnalyzer,
        'ruby': RubyAnalyzer,
        'php': PHPAnalyzer
    }

    analyzer_class = analyzers.get(language.lower())
    if analyzer_class:
        return analyzer_class(project_path)

    return None
