"""
License Scanner Module

Scans dependencies for license compliance issues and compatibility.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import yaml

from ..types import Dependency, LicenseIssue, LicenseCompatibility


class LicenseScanner:
    """
    Scans dependencies for license compliance and compatibility.

    Features:
    - License identification
    - License compatibility checking
    - GPL/LGPL/AGPL detection
    - Proprietary license detection
    - License policy enforcement
    """

    def __init__(self, project_license: Optional[str] = None):
        """
        Initialize license scanner.

        Args:
            project_license: Your project's license (e.g., "MIT", "Apache-2.0")
        """
        self.project_license = project_license
        self.compatibility_data = self._load_compatibility_data()

    def _load_compatibility_data(self) -> Dict[str, Any]:
        """Load license compatibility rules."""
        # Try to load from data file
        data_path = Path(__file__).parent.parent / "data" / "license_compatibility.yaml"

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            # Return minimal compatibility data
            return self._get_default_compatibility()

    def _get_default_compatibility(self) -> Dict[str, Any]:
        """Get default license compatibility rules."""
        return {
            "permissive_licenses": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"],
            "weak_copyleft_licenses": ["LGPL-2.1", "LGPL-3.0", "MPL-2.0"],
            "strong_copyleft_licenses": ["GPL-2.0", "GPL-3.0", "AGPL-3.0"],
            "compatibility": {
                "MIT": {
                    "allowed": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"],
                    "restricted": ["GPL-2.0", "GPL-3.0", "AGPL-3.0"],
                }
            },
        }

    def scan_dependencies(self, dependencies: List[Dependency]) -> List[LicenseIssue]:
        """
        Scan dependencies for license issues.

        Args:
            dependencies: List of dependencies to scan

        Returns:
            List of license compliance issues
        """
        issues: List[LicenseIssue] = []

        for dep in dependencies:
            # Check for missing license
            if not dep.license or dep.license.lower() in ["unknown", "unlicensed", "none"]:
                issues.append(
                    LicenseIssue(
                        dependency=dep,
                        issue_type="missing_license",
                        severity="medium",
                        description=f"Package '{dep.name}' has no license information",
                        recommendation="Contact package maintainer or find alternative package",
                    )
                )
                continue

            # Normalize license name
            normalized_license = self._normalize_license(dep.license)

            # Check compatibility with project license
            if self.project_license:
                compat_issue = self._check_compatibility(dep, normalized_license)
                if compat_issue:
                    issues.append(compat_issue)

            # Check for restrictive licenses
            restrictive_issue = self._check_restrictive_license(dep, normalized_license)
            if restrictive_issue:
                issues.append(restrictive_issue)

            # Check for proprietary licenses
            if self._is_proprietary(normalized_license):
                issues.append(
                    LicenseIssue(
                        dependency=dep,
                        issue_type="proprietary_license",
                        severity="high",
                        description=f"Package '{dep.name}' uses proprietary license: {dep.license}",
                        recommendation="Review license terms carefully. Consider alternatives.",
                    )
                )

        return issues

    def _normalize_license(self, license_str: str) -> str:
        """
        Normalize license string to standard identifier.

        Args:
            license_str: Raw license string

        Returns:
            Normalized SPDX identifier
        """
        # Check aliases
        aliases = self.compatibility_data.get("aliases", {})
        if license_str in aliases:
            return aliases[license_str]

        # Basic normalization
        normalized = license_str.strip()

        # Remove common prefixes/suffixes
        normalized = normalized.replace("License", "").strip()
        normalized = normalized.replace("The ", "").strip()

        return normalized

    def _check_compatibility(
        self, dependency: Dependency, dep_license: str
    ) -> Optional[LicenseIssue]:
        """
        Check if dependency license is compatible with project license.

        Args:
            dependency: Dependency to check
            dep_license: Normalized dependency license

        Returns:
            LicenseIssue if incompatible, None otherwise
        """
        if not self.project_license:
            return None

        project_compat = self.compatibility_data.get("compatibility", {}).get(
            self.project_license, {}
        )

        allowed = project_compat.get("allowed", [])
        restricted = project_compat.get("restricted", [])

        if dep_license in restricted:
            return LicenseIssue(
                dependency=dependency,
                issue_type="incompatible_license",
                severity="high",
                description=f"License '{dep_license}' is incompatible with project license '{self.project_license}'",
                recommendation=f"Remove this dependency or change project license",
            )

        # Warn about copyleft in permissive projects
        if self._is_permissive(self.project_license) and self._is_copyleft(dep_license):
            return LicenseIssue(
                dependency=dependency,
                issue_type="copyleft_in_permissive",
                severity="medium",
                description=f"Copyleft license '{dep_license}' used in permissive project",
                recommendation="Review if this is intentional. May affect distribution.",
            )

        return None

    def _check_restrictive_license(
        self, dependency: Dependency, dep_license: str
    ) -> Optional[LicenseIssue]:
        """
        Check for restrictive licenses (GPL, AGPL).

        Args:
            dependency: Dependency to check
            dep_license: Normalized dependency license

        Returns:
            LicenseIssue if restrictive, None otherwise
        """
        strong_copyleft = self.compatibility_data.get("strong_copyleft_licenses", [])

        if dep_license in strong_copyleft:
            warnings = self.compatibility_data.get("warnings", {}).get(dep_license, [])
            warning_text = "\n".join(warnings) if warnings else ""

            return LicenseIssue(
                dependency=dependency,
                issue_type="restrictive_license",
                severity="medium",
                description=f"Package '{dependency.name}' uses restrictive license: {dep_license}\n{warning_text}",
                recommendation="Understand copyleft obligations before using in production",
            )

        return None

    def _is_permissive(self, license_str: str) -> bool:
        """Check if license is permissive."""
        permissive = self.compatibility_data.get("permissive_licenses", [])
        return license_str in permissive

    def _is_copyleft(self, license_str: str) -> bool:
        """Check if license is copyleft."""
        weak = self.compatibility_data.get("weak_copyleft_licenses", [])
        strong = self.compatibility_data.get("strong_copyleft_licenses", [])
        return license_str in weak or license_str in strong

    def _is_proprietary(self, license_str: str) -> bool:
        """Check if license is proprietary."""
        proprietary_keywords = [
            "proprietary",
            "commercial",
            "custom",
            "private",
            "closed",
            "unlicensed",
        ]
        return any(keyword in license_str.lower() for keyword in proprietary_keywords)

    def get_license_summary(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """
        Get summary of licenses used in dependencies.

        Args:
            dependencies: List of dependencies

        Returns:
            Summary statistics
        """
        license_counts: Dict[str, int] = {}
        categories: Dict[str, int] = {"permissive": 0, "copyleft": 0, "proprietary": 0, "unknown": 0}

        for dep in dependencies:
            if not dep.license:
                categories["unknown"] += 1
                continue

            normalized = self._normalize_license(dep.license)
            license_counts[normalized] = license_counts.get(normalized, 0) + 1

            if self._is_permissive(normalized):
                categories["permissive"] += 1
            elif self._is_copyleft(normalized):
                categories["copyleft"] += 1
            elif self._is_proprietary(normalized):
                categories["proprietary"] += 1
            else:
                categories["unknown"] += 1

        return {
            "total_dependencies": len(dependencies),
            "license_counts": license_counts,
            "categories": categories,
            "unique_licenses": len(license_counts),
        }
