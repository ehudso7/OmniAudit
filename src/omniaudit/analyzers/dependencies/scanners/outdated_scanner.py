"""
Outdated Package Scanner Module

Detects outdated dependencies and potential typosquatting attacks.
"""

import asyncio
import difflib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
from packaging import version as pkg_version

from ..types import Dependency, OutdatedPackage, TyposquattingMatch


class OutdatedScanner:
    """
    Scans for outdated packages and typosquatting.

    Features:
    - Check for newer versions
    - Identify breaking changes (semver)
    - Detect typosquatting attempts
    - Calculate package age
    """

    def __init__(self):
        """Initialize outdated scanner."""
        self.registry_urls = {
            "npm": "https://registry.npmjs.org",
            "pypi": "https://pypi.org/pypi",
            "cargo": "https://crates.io/api/v1",
            "go": "https://proxy.golang.org",
        }

        # Known popular packages for typosquatting detection
        self.popular_packages: Dict[str, List[str]] = {
            "npm": [
                "react",
                "vue",
                "angular",
                "express",
                "lodash",
                "webpack",
                "babel",
                "eslint",
                "typescript",
                "axios",
            ],
            "pip": [
                "django",
                "flask",
                "requests",
                "numpy",
                "pandas",
                "pytest",
                "setuptools",
                "pip",
                "boto3",
                "sqlalchemy",
            ],
        }

    async def scan_dependencies(
        self, dependencies: List[Dependency]
    ) -> tuple[List[OutdatedPackage], List[TyposquattingMatch]]:
        """
        Scan dependencies for outdated versions and typosquatting.

        Args:
            dependencies: List of dependencies to scan

        Returns:
            Tuple of (outdated_packages, typosquatting_matches)
        """
        outdated: List[OutdatedPackage] = []
        typosquatting: List[TyposquattingMatch] = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for dep in dependencies:
                task = self._check_dependency(session, dep)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for dep, result in zip(dependencies, results):
                if isinstance(result, Exception):
                    continue

                if result:
                    outdated_pkg, typo_matches = result
                    if outdated_pkg:
                        outdated.append(outdated_pkg)
                    typosquatting.extend(typo_matches)

        return outdated, typosquatting

    async def _check_dependency(
        self, session: aiohttp.ClientSession, dependency: Dependency
    ) -> tuple[Optional[OutdatedPackage], List[TyposquattingMatch]]:
        """
        Check a single dependency for updates and typosquatting.

        Args:
            session: aiohttp session
            dependency: Dependency to check

        Returns:
            Tuple of (outdated_package, typosquatting_matches)
        """
        outdated_pkg = None
        typo_matches = []

        # Check for outdated version
        latest_version = await self._get_latest_version(session, dependency)
        if latest_version and latest_version != dependency.version:
            try:
                current = pkg_version.parse(dependency.version)
                latest = pkg_version.parse(latest_version)

                if latest > current:
                    # Check for breaking changes (major version bump)
                    breaking = (
                        hasattr(latest, "major")
                        and hasattr(current, "major")
                        and latest.major > current.major
                    )

                    # Estimate age (simplified)
                    age_days = 30  # Default estimate

                    outdated_pkg = OutdatedPackage(
                        dependency=dependency,
                        current_version=dependency.version,
                        latest_version=latest_version,
                        latest_stable_version=latest_version,
                        age_days=age_days,
                        breaking_changes=breaking,
                    )
            except Exception:
                pass

        # Check for typosquatting
        typo_matches = self._check_typosquatting(dependency)

        return outdated_pkg, typo_matches

    async def _get_latest_version(
        self, session: aiohttp.ClientSession, dependency: Dependency
    ) -> Optional[str]:
        """
        Get latest version of a package from registry.

        Args:
            session: aiohttp session
            dependency: Dependency to check

        Returns:
            Latest version string or None
        """
        pkg_mgr = dependency.package_manager.value

        if pkg_mgr in ["npm", "yarn", "pnpm"]:
            return await self._get_npm_latest(session, dependency.name)
        elif pkg_mgr in ["pip", "poetry"]:
            return await self._get_pypi_latest(session, dependency.name)
        elif pkg_mgr == "cargo":
            return await self._get_cargo_latest(session, dependency.name)

        return None

    async def _get_npm_latest(
        self, session: aiohttp.ClientSession, package_name: str
    ) -> Optional[str]:
        """Get latest version from npm registry."""
        url = f"{self.registry_urls['npm']}/{package_name}"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                return data.get("dist-tags", {}).get("latest")

        except Exception:
            return None

    async def _get_pypi_latest(
        self, session: aiohttp.ClientSession, package_name: str
    ) -> Optional[str]:
        """Get latest version from PyPI."""
        url = f"{self.registry_urls['pypi']}/{package_name}/json"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                return data.get("info", {}).get("version")

        except Exception:
            return None

    async def _get_cargo_latest(
        self, session: aiohttp.ClientSession, package_name: str
    ) -> Optional[str]:
        """Get latest version from crates.io."""
        url = f"{self.registry_urls['cargo']}/crates/{package_name}"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                crate = data.get("crate", {})
                return crate.get("max_version")

        except Exception:
            return None

    def _check_typosquatting(self, dependency: Dependency) -> List[TyposquattingMatch]:
        """
        Check if package name might be typosquatting.

        Uses string similarity and common substitution patterns.

        Args:
            dependency: Dependency to check

        Returns:
            List of potential typosquatting matches
        """
        matches: List[TyposquattingMatch] = []

        pkg_mgr = dependency.package_manager.value
        if pkg_mgr in ["npm", "yarn", "pnpm"]:
            ecosystem = "npm"
        elif pkg_mgr in ["pip", "poetry"]:
            ecosystem = "pip"
        else:
            return matches

        popular = self.popular_packages.get(ecosystem, [])

        for legit_pkg in popular:
            similarity = self._calculate_similarity(dependency.name, legit_pkg)

            # Flag if similarity is high but not exact match
            if 0.7 <= similarity < 1.0:
                risk_level = "high" if similarity >= 0.9 else "medium"

                reasoning = self._analyze_typosquatting_pattern(dependency.name, legit_pkg)

                match = TyposquattingMatch(
                    package_name=dependency.name,
                    legitimate_package=legit_pkg,
                    similarity_score=similarity,
                    risk_level=risk_level,
                    reasoning=reasoning,
                )
                matches.append(match)

        return matches

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate string similarity between two package names.

        Args:
            name1: First package name
            name2: Second package name

        Returns:
            Similarity score (0.0-1.0)
        """
        # Use difflib for sequence matching
        return difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

    def _analyze_typosquatting_pattern(self, suspect: str, legit: str) -> str:
        """
        Analyze what typosquatting pattern might be used.

        Args:
            suspect: Suspicious package name
            legit: Legitimate package name

        Returns:
            Description of the pattern
        """
        suspect_lower = suspect.lower()
        legit_lower = legit.lower()

        # Check for common patterns
        if suspect_lower.replace("-", "") == legit_lower.replace("-", ""):
            return "Hyphen substitution (e.g., 'my-package' vs 'mypackage')"

        if suspect_lower.replace("_", "") == legit_lower.replace("_", ""):
            return "Underscore substitution"

        # Character substitution
        substitutions = {
            "0": "o",
            "1": "l",
            "l": "1",
            "o": "0",
            "rn": "m",
            "vv": "w",
        }

        for old, new in substitutions.items():
            if suspect_lower.replace(old, new) == legit_lower:
                return f"Character substitution: '{old}' -> '{new}'"

        # Missing/extra character
        if len(suspect) == len(legit) + 1 or len(suspect) == len(legit) - 1:
            return "Missing or extra character"

        # Swapped characters
        if sorted(suspect_lower) == sorted(legit_lower):
            return "Character transposition (swapped letters)"

        return "High similarity to popular package"

    def scan_dependencies_sync(
        self, dependencies: List[Dependency]
    ) -> tuple[List[OutdatedPackage], List[TyposquattingMatch]]:
        """
        Synchronous wrapper for scan_dependencies.

        Args:
            dependencies: List of dependencies to scan

        Returns:
            Tuple of (outdated_packages, typosquatting_matches)
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.scan_dependencies(dependencies))
