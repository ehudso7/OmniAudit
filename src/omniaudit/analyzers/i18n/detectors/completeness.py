"""Translation completeness checker."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..types import I18nFramework, LocaleSupport, PluralizationCheck, TranslationFile


class CompletenessChecker:
    """Check translation completeness across locales."""

    # Common pluralization forms by language
    PLURAL_FORMS = {
        "en": ["one", "other"],
        "fr": ["one", "other"],
        "de": ["one", "other"],
        "es": ["one", "other"],
        "ru": ["one", "few", "many", "other"],
        "ar": ["zero", "one", "two", "few", "many", "other"],
        "pl": ["one", "few", "many", "other"],
        "cs": ["one", "few", "many", "other"],
    }

    @staticmethod
    def detect_framework(project_path: Path) -> Optional[I18nFramework]:
        """
        Detect i18n framework used in project.

        Args:
            project_path: Root path of the project

        Returns:
            Detected framework or None
        """
        # Check package.json for i18n dependencies
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text(encoding="utf-8"))
                deps = {**content.get("dependencies", {}), **content.get("devDependencies", {})}

                if "react-i18next" in deps or "i18next" in deps:
                    return I18nFramework.REACT_I18NEXT
                elif "vue-i18n" in deps:
                    return I18nFramework.VUE_I18N
                elif "@angular/localize" in deps:
                    return I18nFramework.ANGULAR_I18N
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # Check for gettext files
        if any(project_path.glob("**/*.po")) or any(project_path.glob("**/*.pot")):
            return I18nFramework.GETTEXT

        return None

    @staticmethod
    def find_translation_files(
        project_path: Path, framework: Optional[I18nFramework] = None
    ) -> List[Path]:
        """
        Find translation files in project.

        Args:
            project_path: Root path of the project
            framework: Optional framework to guide search

        Returns:
            List of translation file paths
        """
        patterns = []

        if framework == I18nFramework.REACT_I18NEXT:
            patterns = ["**/locales/**/*.json", "**/translations/**/*.json", "**/i18n/**/*.json"]
        elif framework == I18nFramework.VUE_I18N:
            patterns = ["**/locales/**/*.json", "**/i18n/**/*.json"]
        elif framework == I18nFramework.GETTEXT:
            patterns = ["**/*.po", "**/*.pot"]
        else:
            # Generic search
            patterns = [
                "**/locales/**/*.json",
                "**/translations/**/*.json",
                "**/i18n/**/*.json",
                "**/lang/**/*.json",
                "**/*.po",
            ]

        files = []
        for pattern in patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file() and "node_modules" not in str(file_path):
                    files.append(file_path)

        return files

    @staticmethod
    def load_translation_keys(file_path: Path) -> Dict[str, any]:
        """
        Load translation keys from file.

        Args:
            file_path: Path to translation file

        Returns:
            Dictionary of translation keys
        """
        try:
            if file_path.suffix == ".json":
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                return CompletenessChecker._flatten_dict(data)
            elif file_path.suffix == ".po":
                # Basic .po file parsing
                return CompletenessChecker._parse_po_file(file_path)
        except (IOError, json.JSONDecodeError, UnicodeDecodeError):
            pass

        return {}

    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = "", sep: str = ".") -> Dict[str, any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(CompletenessChecker._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def _parse_po_file(file_path: Path) -> Dict[str, str]:
        """Parse gettext .po file."""
        translations = {}
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            current_msgid = None
            current_msgstr = None

            for line in lines:
                line = line.strip()

                if line.startswith("msgid "):
                    current_msgid = line[6:].strip('"')
                elif line.startswith("msgstr "):
                    current_msgstr = line[7:].strip('"')

                    if current_msgid and current_msgstr:
                        translations[current_msgid] = current_msgstr
                        current_msgid = None
                        current_msgstr = None

        except (IOError, UnicodeDecodeError):
            pass

        return translations

    @staticmethod
    def extract_locale_from_path(file_path: Path) -> Optional[str]:
        """
        Extract locale identifier from file path.

        Args:
            file_path: Path to translation file

        Returns:
            Locale identifier (e.g., 'en', 'fr', 'es-ES')
        """
        # Common locale patterns
        locale_pattern = r"([a-z]{2}(?:[-_][A-Z]{2})?)"

        # Try filename first (e.g., en.json, fr-FR.json)
        match = re.match(locale_pattern, file_path.stem)
        if match:
            return match.group(1).replace("_", "-")

        # Try parent directory (e.g., locales/en/translations.json)
        if file_path.parent.name and re.match(locale_pattern, file_path.parent.name):
            return file_path.parent.name.replace("_", "-")

        return None

    @staticmethod
    def compare_translations(
        base_keys: Set[str], target_keys: Set[str]
    ) -> tuple[List[str], List[str]]:
        """
        Compare translation keys between locales.

        Args:
            base_keys: Base locale keys
            target_keys: Target locale keys

        Returns:
            Tuple of (missing keys, extra keys)
        """
        missing = list(base_keys - target_keys)
        extra = list(target_keys - base_keys)
        return missing, extra

    @staticmethod
    def check_pluralization(
        translations: Dict[str, any], locale: str, file_path: str
    ) -> List[PluralizationCheck]:
        """
        Check pluralization handling.

        Args:
            translations: Translation dictionary
            locale: Locale code
            file_path: Path to translation file

        Returns:
            List of pluralization checks
        """
        checks = []
        locale_base = locale.split("-")[0]  # Get base language (en from en-US)
        expected_forms = CompletenessChecker.PLURAL_FORMS.get(
            locale_base, ["one", "other"]
        )

        for key, value in translations.items():
            # Check if value is a pluralization object
            if isinstance(value, dict):
                has_plural = any(form in value for form in expected_forms)

                if has_plural:
                    missing_forms = [form for form in expected_forms if form not in value]
                    checks.append(
                        PluralizationCheck(
                            key=key,
                            locale=locale,
                            has_plural_forms=True,
                            missing_forms=missing_forms,
                            file_path=file_path,
                        )
                    )

        return checks

    @staticmethod
    def analyze_locale_support(
        translation_files: List[TranslationFile], base_locale: str
    ) -> List[LocaleSupport]:
        """
        Analyze support for each locale.

        Args:
            translation_files: List of translation files
            base_locale: Base locale for comparison

        Returns:
            List of locale support information
        """
        base_file = next((f for f in translation_files if f.locale == base_locale), None)
        if not base_file:
            return []

        locale_support = []

        for trans_file in translation_files:
            if trans_file.locale == base_locale:
                continue

            completeness = (
                (trans_file.translated_keys / base_file.total_keys * 100)
                if base_file.total_keys > 0
                else 0.0
            )

            locale_support.append(
                LocaleSupport(
                    locale=trans_file.locale,
                    completeness=completeness,
                    missing_count=len(trans_file.missing_keys),
                    extra_count=len(trans_file.extra_keys),
                    has_pluralization=False,  # Updated by analyzer
                )
            )

        return locale_support
