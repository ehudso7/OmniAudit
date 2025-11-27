"""
Clean Architecture Pattern Validation Module.

Validates adherence to Clean Architecture principles.
"""

from pathlib import Path
from typing import List

from ..types import ArchitecturePattern, ArchitectureValidation, LayerType


class CleanArchitectureValidator:
    """Validates Clean Architecture pattern."""

    def validate(
        self,
        project_path: Path,
        layer_violations: List,
        module_metrics: List,
    ) -> ArchitectureValidation:
        """Validate Clean Architecture compliance.

        Args:
            project_path: Project root
            layer_violations: Layer violations
            module_metrics: Module metrics

        Returns:
            Architecture validation result
        """
        # Detect if Clean Architecture is intended
        has_clean_structure = self._detect_clean_structure(project_path)

        if not has_clean_structure:
            return ArchitectureValidation(
                detected_pattern=ArchitecturePattern.UNKNOWN,
                confidence=0.3,
                compliance_score=50.0,
                violations=[],
                recommendations=["Consider adopting Clean Architecture for better maintainability"],
            )

        # Calculate compliance score
        compliance_score = self._calculate_compliance(layer_violations, module_metrics)

        # Collect violations
        violations = [
            f"{v.from_layer.value} -> {v.to_layer.value}: {v.description}"
            for v in layer_violations[:5]
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(layer_violations, compliance_score)

        return ArchitectureValidation(
            detected_pattern=ArchitecturePattern.CLEAN,
            confidence=0.8,
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations,
        )

    def _detect_clean_structure(self, project_path: Path) -> bool:
        """Detect if project follows Clean Architecture structure.

        Args:
            project_path: Project root

        Returns:
            True if Clean Architecture detected
        """
        # Look for typical Clean Architecture directories
        indicators = ["domain", "application", "infrastructure", "presentation"]

        found_count = 0
        for indicator in indicators:
            if list(project_path.rglob(f"*{indicator}*")):
                found_count += 1

        return found_count >= 2

    def _calculate_compliance(self, layer_violations: List, module_metrics: List) -> float:
        """Calculate Clean Architecture compliance score.

        Args:
            layer_violations: Layer violations
            module_metrics: Module metrics

        Returns:
            Compliance score (0-100)
        """
        score = 100.0

        # Penalty for layer violations
        score -= min(50, len(layer_violations) * 5)

        # Penalty for high coupling
        if module_metrics:
            avg_coupling = sum(
                m.coupling.efferent_coupling for m in module_metrics
            ) / len(module_metrics)
            if avg_coupling > 10:
                score -= min(25, (avg_coupling - 10) * 2.5)

        return max(0.0, round(score, 2))

    def _generate_recommendations(
        self, layer_violations: List, compliance_score: float
    ) -> List[str]:
        """Generate recommendations.

        Args:
            layer_violations: Layer violations
            compliance_score: Compliance score

        Returns:
            List of recommendations
        """
        recommendations = []

        if compliance_score < 70:
            recommendations.append(
                "Review and enforce Clean Architecture layer dependencies"
            )

        if layer_violations:
            domain_violations = [
                v for v in layer_violations if v.from_layer == LayerType.DOMAIN
            ]
            if domain_violations:
                recommendations.append(
                    "Keep domain layer independent - use dependency inversion"
                )

        if len(recommendations) == 0:
            recommendations.append(
                "Continue maintaining Clean Architecture principles"
            )

        return recommendations[:5]
