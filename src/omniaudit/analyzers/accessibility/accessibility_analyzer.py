"""Accessibility compliance analyzer."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from html.parser import HTMLParser

from ..base import BaseAnalyzer, AnalyzerError
from .checkers import ARIAChecker, ContrastChecker, WCAGChecker
from .types import (
    AccessibilityIssue,
    AccessibilityMetrics,
    AccessibilitySummary,
    ColorContrastResult,
    SemanticHTMLMetrics,
    Severity,
    WCAGLevel,
)


class SemanticHTMLParser(HTMLParser):
    """Parser for semantic HTML analysis."""

    SEMANTIC_ELEMENTS = {
        "header",
        "nav",
        "main",
        "article",
        "section",
        "aside",
        "footer",
        "figure",
        "figcaption",
        "time",
        "mark",
    }

    LANDMARK_ROLES = {"banner", "navigation", "main", "complementary", "contentinfo"}

    def __init__(self):
        super().__init__()
        self.total_elements = 0
        self.semantic_elements = 0
        self.non_semantic_elements = 0
        self.div_count = 0
        self.div_nesting_depth = 0
        self.max_div_nesting = 0
        self.heading_levels = []
        self.landmark_roles_present = False

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        """Handle start tags."""
        self.total_elements += 1
        attrs_dict = dict(attrs)

        if tag in self.SEMANTIC_ELEMENTS:
            self.semantic_elements += 1
        elif tag in ["div", "span"]:
            self.non_semantic_elements += 1
            if tag == "div":
                self.div_nesting_depth += 1
                self.max_div_nesting = max(self.max_div_nesting, self.div_nesting_depth)
        else:
            # Other elements are neutral
            pass

        # Check for landmark roles
        role = attrs_dict.get("role")
        if role in self.LANDMARK_ROLES:
            self.landmark_roles_present = True

        # Track heading hierarchy
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.heading_levels.append(int(tag[1]))

    def handle_endtag(self, tag: str) -> None:
        """Handle end tags."""
        if tag == "div":
            self.div_nesting_depth = max(0, self.div_nesting_depth - 1)


class AccessibilityAnalyzer(BaseAnalyzer):
    """
    Analyze accessibility compliance.

    Supports:
    - WCAG 2.1 AA compliance checking
    - ARIA attribute validation
    - Color contrast analysis
    - Semantic HTML enforcement
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize accessibility analyzer."""
        super().__init__(config)
        self.project_path = Path(self.config["project_path"])
        self.wcag_level = WCAGLevel(self.config.get("wcag_level", "AA"))

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "accessibility_analyzer"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required in configuration")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path {path} does not exist")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze accessibility compliance.

        Args:
            data: Input data (file patterns, exclusions, etc.)

        Returns:
            Analysis results with metrics and findings
        """
        exclude_patterns = data.get(
            "exclude_patterns", ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/build/**"]
        )

        # Find HTML and CSS files
        html_files = self._find_files(["**/*.html", "**/*.htm"], exclude_patterns)
        css_files = self._find_files(["**/*.css"], exclude_patterns)

        # Run WCAG compliance checks
        wcag_compliance = self._check_wcag_compliance(html_files)

        # Validate ARIA attributes
        aria_validation = self._validate_aria(html_files)

        # Check color contrast
        color_contrast_issues = self._check_color_contrast(html_files, css_files)

        # Analyze semantic HTML
        semantic_html = self._analyze_semantic_html(html_files)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            wcag_compliance, aria_validation, semantic_html, color_contrast_issues
        )

        metrics = AccessibilityMetrics(
            wcag_compliance=wcag_compliance,
            aria_validation=aria_validation,
            semantic_html=semantic_html,
            color_contrast_issues=color_contrast_issues,
            overall_score=overall_score,
            files_analyzed=len(html_files) + len(css_files),
            total_issues=len(wcag_compliance.issues)
            + len(aria_validation.issues)
            + len(semantic_html.issues),
        )

        summary = self._generate_summary(metrics)

        return self._create_response(
            {
                "metrics": metrics.model_dump(),
                "summary": summary.model_dump(),
                "recommendations": self._generate_recommendations(metrics),
            }
        )

    def _check_wcag_compliance(self, html_files: List[Path]):
        """Check WCAG compliance across HTML files."""
        from .types import WCAGCompliance

        all_issues = []
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        warnings = 0

        for file_path in html_files:
            result = WCAGChecker.check_file(file_path, self.wcag_level)
            all_issues.extend(result.issues)
            total_checks += result.total_checks
            passed_checks += result.passed_checks
            failed_checks += result.failed_checks
            warnings += result.warnings

        compliance_percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 100.0

        return WCAGCompliance(
            level=self.wcag_level,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            compliance_percentage=compliance_percentage,
            issues=all_issues,
        )

    def _validate_aria(self, html_files: List[Path]):
        """Validate ARIA attributes across HTML files."""
        from .types import ARIAValidation

        all_issues = []
        total_aria = 0
        valid_aria = 0
        invalid_aria = 0
        missing_required = 0
        deprecated = 0

        for file_path in html_files:
            result = ARIAChecker.validate_file(file_path)
            all_issues.extend(result.issues)
            total_aria += result.total_aria_elements
            valid_aria += result.valid_aria_usage
            invalid_aria += result.invalid_aria_usage
            missing_required += result.missing_required_attrs
            deprecated += result.deprecated_attrs

        return ARIAValidation(
            total_aria_elements=total_aria,
            valid_aria_usage=valid_aria,
            invalid_aria_usage=invalid_aria,
            missing_required_attrs=missing_required,
            deprecated_attrs=deprecated,
            issues=all_issues,
        )

    def _check_color_contrast(
        self, html_files: List[Path], css_files: List[Path]
    ) -> List[ColorContrastResult]:
        """Check color contrast in HTML and CSS files."""
        results = []

        # Check CSS files
        for file_path in css_files:
            css_results = ContrastChecker.extract_colors_from_css(file_path)
            results.extend(css_results)

        # Check inline styles in HTML
        for file_path in html_files:
            html_results = ContrastChecker.extract_colors_from_html(file_path)
            results.extend(html_results)

        # Filter to only failing contrasts
        return [r for r in results if not r.wcag_aa_normal]

    def _analyze_semantic_html(self, html_files: List[Path]) -> SemanticHTMLMetrics:
        """Analyze semantic HTML usage."""
        total_elements = 0
        semantic_elements = 0
        non_semantic_elements = 0
        div_soup_count = 0
        heading_structure_valid = True
        landmark_roles_present = False
        issues = []

        for file_path in html_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                parser = SemanticHTMLParser()
                parser.feed(content)

                total_elements += parser.total_elements
                semantic_elements += parser.semantic_elements
                non_semantic_elements += parser.non_semantic_elements

                if parser.max_div_nesting > 5:
                    div_soup_count += 1
                    issues.append(
                        AccessibilityIssue(
                            severity=Severity.WARNING,
                            rule="SEMANTIC-HTML",
                            message=f"Excessive div nesting (depth: {parser.max_div_nesting})",
                            file_path=str(file_path),
                            line_number=None,
                            element="<div>",
                            suggestion="Use semantic HTML elements instead of deeply nested divs",
                            wcag_criterion="1.3.1 Info and Relationships (Level A)",
                        )
                    )

                if parser.landmark_roles_present:
                    landmark_roles_present = True

                # Check heading structure
                if parser.heading_levels and parser.heading_levels[0] != 1:
                    heading_structure_valid = False

            except Exception:
                continue

        semantic_percentage = (
            (semantic_elements / total_elements * 100) if total_elements > 0 else 0.0
        )

        return SemanticHTMLMetrics(
            total_elements=total_elements,
            semantic_elements=semantic_elements,
            non_semantic_elements=non_semantic_elements,
            semantic_percentage=semantic_percentage,
            div_soup_count=div_soup_count,
            heading_structure_valid=heading_structure_valid,
            landmark_roles_present=landmark_roles_present,
            issues=issues,
        )

    def _calculate_overall_score(self, wcag, aria, semantic, contrast_issues) -> float:
        """Calculate overall accessibility score."""
        weights = {"wcag": 0.4, "aria": 0.2, "semantic": 0.2, "contrast": 0.2}

        aria_score = (
            (aria.valid_aria_usage / aria.total_aria_elements * 100)
            if aria.total_aria_elements > 0
            else 100.0
        )

        contrast_score = max(0, 100 - len(contrast_issues) * 5)  # -5 points per issue

        score = (
            wcag.compliance_percentage * weights["wcag"]
            + aria_score * weights["aria"]
            + semantic.semantic_percentage * weights["semantic"]
            + contrast_score * weights["contrast"]
        )

        return round(score, 2)

    def _generate_summary(self, metrics: AccessibilityMetrics) -> AccessibilitySummary:
        """Generate summary of accessibility analysis."""
        critical = sum(
            1
            for i in metrics.wcag_compliance.issues + metrics.aria_validation.issues
            if i.severity == Severity.CRITICAL
        )
        errors = sum(
            1
            for i in metrics.wcag_compliance.issues + metrics.aria_validation.issues
            if i.severity == Severity.ERROR
        )
        warnings = sum(
            1
            for i in metrics.wcag_compliance.issues + metrics.aria_validation.issues
            if i.severity == Severity.WARNING
        )

        if metrics.overall_score >= 90:
            recommendation = "Excellent accessibility! Minor improvements needed."
        elif metrics.overall_score >= 70:
            recommendation = "Good accessibility foundation. Address remaining issues."
        elif metrics.overall_score >= 50:
            recommendation = "Moderate accessibility. Significant improvements needed."
        else:
            recommendation = "Poor accessibility. Critical issues must be addressed."

        return AccessibilitySummary(
            total_critical_issues=critical,
            total_errors=errors,
            total_warnings=warnings,
            wcag_aa_compliance=metrics.wcag_compliance.compliance_percentage,
            recommendation=recommendation,
        )

    def _generate_recommendations(self, metrics: AccessibilityMetrics) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if metrics.wcag_compliance.compliance_percentage < 80:
            recommendations.append(
                "Address WCAG compliance issues: add alt text, labels, and proper heading structure"
            )

        if metrics.aria_validation.invalid_aria_usage > 0:
            recommendations.append("Fix invalid ARIA attributes and use valid roles")

        if metrics.semantic_html.semantic_percentage < 50:
            recommendations.append(
                "Use more semantic HTML elements (header, nav, main, article, etc.)"
            )

        if len(metrics.color_contrast_issues) > 0:
            recommendations.append(
                f"Fix {len(metrics.color_contrast_issues)} color contrast issues for better readability"
            )

        if not metrics.semantic_html.landmark_roles_present:
            recommendations.append("Add ARIA landmark roles to improve navigation")

        return recommendations

    def _find_files(self, patterns: List[str], exclude_patterns: List[str]) -> List[Path]:
        """Find files matching patterns."""
        files = []
        for pattern in patterns:
            for file_path in self.project_path.glob(pattern):
                if any(file_path.match(ex) for ex in exclude_patterns):
                    continue
                if file_path.is_file():
                    files.append(file_path)
        return files
