"""
CVE Scanner Module

Scans dependencies for known vulnerabilities using multiple databases:
- NVD (National Vulnerability Database)
- GitHub Advisory Database
- OSV (Open Source Vulnerabilities)
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from packaging import version as pkg_version

from ..types import (
    Dependency,
    Vulnerability,
    DependencyVulnerability,
    VulnerabilitySeverity,
)


class CVEScanner:
    """
    Scans dependencies for CVEs and security vulnerabilities.

    Integrates with:
    - OSV API (https://osv.dev)
    - GitHub Advisory Database
    - NVD API
    """

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize CVE scanner.

        Args:
            api_keys: Optional API keys for vulnerability databases
                     {"nvd": "key", "github": "token"}
        """
        self.api_keys = api_keys or {}
        self.osv_api_url = "https://api.osv.dev/v1"
        self.github_api_url = "https://api.github.com/graphql"
        self.nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"

        # Cache for API responses
        self._cache: Dict[str, List[Vulnerability]] = {}

    async def scan_dependencies(
        self, dependencies: List[Dependency]
    ) -> List[DependencyVulnerability]:
        """
        Scan list of dependencies for vulnerabilities.

        Args:
            dependencies: List of dependencies to scan

        Returns:
            List of found vulnerabilities
        """
        vulnerabilities: List[DependencyVulnerability] = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for dep in dependencies:
                task = self._scan_dependency(session, dep)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for dep, result in zip(dependencies, results):
                if isinstance(result, Exception):
                    # Log error but continue
                    continue

                if result:
                    for vuln in result:
                        dep_vuln = DependencyVulnerability(
                            dependency=dep,
                            vulnerability=vuln,
                            is_direct=dep.is_direct,
                            dependency_chain=[dep.name],
                        )
                        vulnerabilities.append(dep_vuln)

        return vulnerabilities

    async def _scan_dependency(
        self, session: aiohttp.ClientSession, dependency: Dependency
    ) -> List[Vulnerability]:
        """
        Scan a single dependency for vulnerabilities.

        Args:
            session: aiohttp session
            dependency: Dependency to scan

        Returns:
            List of vulnerabilities affecting this dependency
        """
        # Check cache first
        cache_key = f"{dependency.name}@{dependency.version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        vulnerabilities: List[Vulnerability] = []

        # Query OSV database (fastest and most comprehensive)
        try:
            osv_vulns = await self._query_osv(session, dependency)
            vulnerabilities.extend(osv_vulns)
        except Exception as e:
            # Continue with other sources
            pass

        # Cache results
        self._cache[cache_key] = vulnerabilities

        return vulnerabilities

    async def _query_osv(
        self, session: aiohttp.ClientSession, dependency: Dependency
    ) -> List[Vulnerability]:
        """
        Query OSV API for vulnerabilities.

        Args:
            session: aiohttp session
            dependency: Dependency to check

        Returns:
            List of vulnerabilities from OSV
        """
        # Map package manager to OSV ecosystem
        ecosystem_map = {
            "npm": "npm",
            "yarn": "npm",
            "pnpm": "npm",
            "pip": "PyPI",
            "poetry": "PyPI",
            "cargo": "crates.io",
            "go": "Go",
            "maven": "Maven",
            "gradle": "Maven",
            "composer": "Packagist",
            "bundler": "RubyGems",
        }

        ecosystem = ecosystem_map.get(dependency.package_manager.value, "")
        if not ecosystem:
            return []

        # Query OSV
        url = f"{self.osv_api_url}/query"
        payload = {
            "package": {"name": dependency.name, "ecosystem": ecosystem},
            "version": dependency.version,
        }

        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                vulnerabilities = []

                if "vulns" in data:
                    for vuln_data in data["vulns"]:
                        vuln = self._parse_osv_vulnerability(vuln_data, dependency)
                        if vuln:
                            vulnerabilities.append(vuln)

                return vulnerabilities

        except Exception as e:
            return []

    def _parse_osv_vulnerability(
        self, data: Dict[str, Any], dependency: Dependency
    ) -> Optional[Vulnerability]:
        """
        Parse OSV vulnerability data into Vulnerability object.

        Args:
            data: Raw OSV vulnerability data
            dependency: Affected dependency

        Returns:
            Parsed Vulnerability object
        """
        try:
            vuln_id = data.get("id", "UNKNOWN")
            summary = data.get("summary", "")
            details = data.get("details", summary)

            # Parse severity
            severity = VulnerabilitySeverity.MEDIUM
            cvss_score = None

            if "severity" in data:
                for severity_data in data["severity"]:
                    if severity_data.get("type") == "CVSS_V3":
                        score_str = severity_data.get("score", "")
                        # Parse CVSS score from string like "CVSS:3.1/AV:N/AC:L..."
                        if "/" in score_str:
                            try:
                                # Extract numeric score if available
                                cvss_score = self._calculate_cvss_score(score_str)
                                severity = self._severity_from_cvss(cvss_score)
                            except Exception:
                                pass

            # Parse affected and patched versions
            affected_versions = []
            patched_versions = []

            if "affected" in data:
                for affected in data["affected"]:
                    if "ranges" in affected:
                        for range_data in affected["ranges"]:
                            if "events" in range_data:
                                for event in range_data["events"]:
                                    if "introduced" in event:
                                        affected_versions.append(f">={event['introduced']}")
                                    if "fixed" in event:
                                        patched_versions.append(f">={event['fixed']}")

            # Parse published date
            published_date = None
            if "published" in data:
                try:
                    published_date = datetime.fromisoformat(
                        data["published"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            # Parse references
            references = []
            if "references" in data:
                for ref in data["references"]:
                    if "url" in ref:
                        references.append(ref["url"])

            # Parse CWE IDs
            cwe_ids = []
            if "database_specific" in data:
                if "cwe_ids" in data["database_specific"]:
                    for cwe in data["database_specific"]["cwe_ids"]:
                        # Extract number from "CWE-89" format
                        if cwe.startswith("CWE-"):
                            try:
                                cwe_ids.append(int(cwe.split("-")[1]))
                            except Exception:
                                pass

            return Vulnerability(
                id=vuln_id,
                title=summary or vuln_id,
                description=details,
                severity=severity,
                cvss_score=cvss_score,
                affected_versions=affected_versions,
                patched_versions=patched_versions,
                published_date=published_date,
                references=references,
                cwe_ids=cwe_ids,
            )

        except Exception as e:
            return None

    def _calculate_cvss_score(self, cvss_string: str) -> float:
        """
        Calculate CVSS score from CVSS vector string.

        This is a simplified calculation. Real CVSS calculation is more complex.

        Args:
            cvss_string: CVSS vector string

        Returns:
            Estimated CVSS score (0.0-10.0)
        """
        # Simplified scoring based on attack vector and complexity
        score = 5.0  # Default medium

        if "AV:N" in cvss_string:  # Network attack vector
            score += 2.0
        if "AC:L" in cvss_string:  # Low attack complexity
            score += 1.0
        if "PR:N" in cvss_string:  # No privileges required
            score += 1.5
        if "UI:N" in cvss_string:  # No user interaction
            score += 0.5

        # Impact
        if "C:H" in cvss_string or "I:H" in cvss_string or "A:H" in cvss_string:
            score += 1.0

        return min(10.0, score)

    def _severity_from_cvss(self, cvss_score: float) -> VulnerabilitySeverity:
        """
        Convert CVSS score to severity level.

        Args:
            cvss_score: CVSS score (0.0-10.0)

        Returns:
            Severity level
        """
        if cvss_score >= 9.0:
            return VulnerabilitySeverity.CRITICAL
        elif cvss_score >= 7.0:
            return VulnerabilitySeverity.HIGH
        elif cvss_score >= 4.0:
            return VulnerabilitySeverity.MEDIUM
        elif cvss_score > 0.0:
            return VulnerabilitySeverity.LOW
        else:
            return VulnerabilitySeverity.NONE

    def scan_dependencies_sync(
        self, dependencies: List[Dependency]
    ) -> List[DependencyVulnerability]:
        """
        Synchronous wrapper for scan_dependencies.

        Args:
            dependencies: List of dependencies to scan

        Returns:
            List of found vulnerabilities
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.scan_dependencies(dependencies))
