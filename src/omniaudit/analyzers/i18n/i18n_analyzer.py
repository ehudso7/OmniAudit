"""Internationalization (i18n) analyzer."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseAnalyzer, AnalyzerError
from .detectors import CompletenessChecker, HardcodedStringDetector
from .types import I18nFinding, I18nMetrics, TranslationFile


class I18nAnalyzer(BaseAnalyzer):
    """
    Analyze internationalization implementation.

    Supports:
    - Hardcoded string detection
    - Translation completeness checking
    - Pluralization handling validation
    - Locale support analysis
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize i18n analyzer."""
        super().__init__(config)
        self.project_path = Path(self.config["project_path"])
        self.base_locale = self.config.get("base_locale", "en")

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "i18n_analyzer"

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
        Analyze i18n implementation.

        Args:
            data: Input data (file patterns, exclusions, etc.)

        Returns:
            Analysis results with metrics and findings
        """
        exclude_patterns = data.get(
            "exclude_patterns",
            ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/build/**", "**/test/**", "**/tests/**"],
        )

        # Detect i18n framework
        framework = CompletenessChecker.detect_framework(self.project_path)

        # Find translation files
        translation_file_paths = CompletenessChecker.find_translation_files(
            self.project_path, framework
        )

        # Analyze translation completeness
        translation_files = self._analyze_translation_files(translation_file_paths)

        # Check pluralization
        pluralization_checks = self._check_pluralization(translation_files)

        # Analyze locale support
        locale_support = CompletenessChecker.analyze_locale_support(
            translation_files, self.base_locale
        )

        # Detect hardcoded strings
        hardcoded_strings = self._detect_hardcoded_strings(exclude_patterns)

        # Calculate metrics
        total_keys = sum(tf.total_keys for tf in translation_files)
        avg_completeness = (
            sum(ls.completeness for ls in locale_support) / len(locale_support)
            if locale_support
            else 0.0
        )

        overall_score = self._calculate_overall_score(
            hardcoded_strings, translation_files, locale_support
        )

        metrics = I18nMetrics(
            framework_detected=framework,
            hardcoded_strings=hardcoded_strings[:100],  # Limit to first 100
            translation_files=translation_files,
            locale_support=locale_support,
            pluralization_checks=pluralization_checks,
            base_locale=self.base_locale,
            total_translation_keys=total_keys,
            average_completeness=avg_completeness,
            overall_score=overall_score,
            files_analyzed=len(translation_file_paths),
        )

        findings = self._generate_findings(metrics)

        return self._create_response(
            {
                "metrics": metrics.model_dump(),
                "findings": [f.model_dump() for f in findings],
                "summary": self._generate_summary(metrics),
            }
        )

    def _analyze_translation_files(
        self, file_paths: List[Path]
    ) -> List[TranslationFile]:
        """Analyze translation files."""
        translation_files = []
        base_keys = None

        # Group files by locale
        locale_files: Dict[str, Path] = {}
        for file_path in file_paths:
            locale = CompletenessChecker.extract_locale_from_path(file_path)
            if locale:
                locale_files[locale] = file_path

        # Load base locale first
        if self.base_locale in locale_files:
            base_path = locale_files[self.base_locale]
            base_keys = set(CompletenessChecker.load_translation_keys(base_path).keys())

            translation_files.append(
                TranslationFile(
                    locale=self.base_locale,
                    file_path=str(base_path),
                    total_keys=len(base_keys),
                    translated_keys=len(base_keys),
                    missing_keys=[],
                    extra_keys=[],
                )
            )

        # Analyze other locales
        for locale, file_path in locale_files.items():
            if locale == self.base_locale:
                continue

            keys = set(CompletenessChecker.load_translation_keys(file_path).keys())

            if base_keys:
                missing, extra = CompletenessChecker.compare_translations(base_keys, keys)
            else:
                missing, extra = [], []

            translation_files.append(
                TranslationFile(
                    locale=locale,
                    file_path=str(file_path),
                    total_keys=len(keys),
                    translated_keys=len(keys) - len(missing),
                    missing_keys=missing[:50],  # Limit to first 50
                    extra_keys=extra[:50],
                )
            )

        return translation_files

    def _check_pluralization(self, translation_files: List[TranslationFile]) -> List:
        """Check pluralization handling."""
        all_checks = []

        for trans_file in translation_files:
            file_path = Path(trans_file.file_path)
            translations = CompletenessChecker.load_translation_keys(file_path)

            checks = CompletenessChecker.check_pluralization(
                translations, trans_file.locale, str(file_path)
            )
            all_checks.extend(checks)

        return all_checks

    def _detect_hardcoded_strings(self, exclude_patterns: List[str]) -> List:
        """Detect hardcoded strings in source files."""
        hardcoded = []

        # Python files
        python_files = self._find_files(["**/*.py"], exclude_patterns)
        for file_path in python_files[:50]:  # Limit to 50 files for performance
            strings = HardcodedStringDetector.detect_in_python(file_path)
            hardcoded.extend(strings)

        # JavaScript/TypeScript files
        js_files = self._find_files(
            ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"], exclude_patterns
        )
        for file_path in js_files[:50]:  # Limit to 50 files for performance
            strings = HardcodedStringDetector.detect_in_javascript(file_path)
            hardcoded.extend(strings)

        # Sort by confidence (highest first)
        hardcoded.sort(key=lambda x: x.confidence, reverse=True)

        return hardcoded

    def _calculate_overall_score(
        self, hardcoded_strings, translation_files, locale_support
    ) -> float:
        """Calculate overall i18n score."""
        # Penalize for hardcoded strings
        hardcoded_penalty = min(50, len(hardcoded_strings) * 2)

        # Reward for translation completeness
        completeness_score = (
            sum(ls.completeness for ls in locale_support) / len(locale_support)
            if locale_support
            else 0
        )

        # Reward for having translations
        has_translations = 20 if len(translation_files) > 1 else 0

        score = max(0, completeness_score + has_translations - hardcoded_penalty)
        return round(score, 2)

    def _generate_findings(self, metrics: I18nMetrics) -> List[I18nFinding]:
        """Generate findings from metrics."""
        findings = []

        # Hardcoded strings
        high_confidence_strings = [
            s for s in metrics.hardcoded_strings if s.confidence > 0.7
        ]
        if len(high_confidence_strings) > 10:
            findings.append(
                I18nFinding(
                    severity="critical",
                    category="hardcoded_strings",
                    message=f"Found {len(high_confidence_strings)} hardcoded user-facing strings",
                    suggestion="Extract strings to translation files for internationalization",
                )
            )
        elif len(high_confidence_strings) > 0:
            findings.append(
                I18nFinding(
                    severity="warning",
                    category="hardcoded_strings",
                    message=f"Found {len(high_confidence_strings)} potential hardcoded strings",
                    suggestion="Review and extract user-facing strings to translation files",
                )
            )

        # Translation completeness
        incomplete_locales = [ls for ls in metrics.locale_support if ls.completeness < 80]
        if incomplete_locales:
            for locale in incomplete_locales[:5]:  # Limit to first 5
                findings.append(
                    I18nFinding(
                        severity="warning",
                        category="missing_translations",
                        message=f"Locale '{locale.locale}' is only {locale.completeness:.1f}% complete ({locale.missing_count} missing keys)",
                        suggestion=f"Add missing translations for {locale.locale}",
                    )
                )

        # No translations found
        if not metrics.translation_files:
            findings.append(
                I18nFinding(
                    severity="critical",
                    category="missing_translations",
                    message="No translation files found",
                    suggestion="Set up i18n framework and create translation files",
                )
            )

        # Framework detection
        if not metrics.framework_detected and metrics.translation_files:
            findings.append(
                I18nFinding(
                    severity="info",
                    category="locale_support",
                    message="i18n framework not detected",
                    suggestion="Consider using a standard i18n framework (react-i18next, vue-i18n, etc.)",
                )
            )

        # Pluralization
        missing_plural_forms = [
            p for p in metrics.pluralization_checks if p.missing_forms
        ]
        if missing_plural_forms:
            findings.append(
                I18nFinding(
                    severity="warning",
                    category="pluralization",
                    message=f"{len(missing_plural_forms)} translation keys missing plural forms",
                    suggestion="Add all required plural forms for proper pluralization",
                )
            )

        return findings

    def _generate_summary(self, metrics: I18nMetrics) -> str:
        """Generate summary text."""
        if not metrics.translation_files:
            return "No i18n implementation detected. Consider adding internationalization support."

        locales = len(set(tf.locale for tf in metrics.translation_files))
        return (
            f"i18n Score: {metrics.overall_score:.1f}/100. "
            f"Supporting {locales} locale(s) with {metrics.average_completeness:.1f}% average completeness. "
            f"Found {len(metrics.hardcoded_strings)} potential hardcoded strings."
        )

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
