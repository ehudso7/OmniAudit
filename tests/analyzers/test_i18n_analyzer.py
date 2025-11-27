"""Tests for I18nAnalyzer."""

import pytest
import json
from pathlib import Path
from src.omniaudit.analyzers.i18n import I18nAnalyzer, I18nFramework
from src.omniaudit.analyzers.i18n.detectors import HardcodedStringDetector, CompletenessChecker
from src.omniaudit.analyzers.base import AnalyzerError


class TestI18nAnalyzer:
    """Test I18nAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = I18nAnalyzer(config)

        assert analyzer.name == "i18n_analyzer"
        assert analyzer.version == "1.0.0"
        assert analyzer.base_locale == "en"

    def test_custom_base_locale(self, tmp_path):
        """Test custom base locale."""
        config = {"project_path": str(tmp_path), "base_locale": "fr"}
        analyzer = I18nAnalyzer(config)

        assert analyzer.base_locale == "fr"

    def test_analyze_empty_project(self, tmp_path):
        """Test analysis of project without i18n."""
        config = {"project_path": str(tmp_path)}
        analyzer = I18nAnalyzer(config)

        result = analyzer.analyze({})

        assert result["analyzer"] == "i18n_analyzer"
        metrics = result["data"]["metrics"]
        assert metrics["files_analyzed"] == 0

    def test_analyze_with_translation_files(self, tmp_path):
        """Test analysis with translation files."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        # Create English translations
        en_file = locales_dir / "en.json"
        en_file.write_text(json.dumps({
            "greeting": "Hello",
            "farewell": "Goodbye"
        }))

        # Create French translations (incomplete)
        fr_file = locales_dir / "fr.json"
        fr_file.write_text(json.dumps({
            "greeting": "Bonjour"
        }))

        config = {"project_path": str(tmp_path), "base_locale": "en"}
        analyzer = I18nAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        assert metrics["files_analyzed"] >= 2
        assert len(metrics["translation_files"]) >= 2
        assert metrics["average_completeness"] < 100


class TestHardcodedStringDetector:
    """Test HardcodedStringDetector class."""

    def test_detect_in_python(self, tmp_path):
        """Test detecting hardcoded strings in Python."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''
def greet_user():
    print("Hello, welcome to our application!")
    return "Success"

def process_data():
    status = "processing"
    return status
''')

        strings = HardcodedStringDetector.detect_in_python(py_file)

        # Should find "Hello, welcome to our application!" with high confidence
        assert len(strings) > 0
        high_confidence = [s for s in strings if s.confidence > 0.7]
        assert len(high_confidence) > 0

    def test_detect_in_javascript(self, tmp_path):
        """Test detecting hardcoded strings in JavaScript."""
        js_file = tmp_path / "test.js"
        js_file.write_text('''
function showMessage() {
    alert("Welcome to the application");
    console.log("User logged in successfully");
}

const API_URL = "https://api.example.com";
''')

        strings = HardcodedStringDetector.detect_in_javascript(js_file)

        # Should find user-facing strings
        assert len(strings) > 0
        messages = [s for s in strings if "welcome" in s.text.lower() or "logged" in s.text.lower()]
        assert len(messages) > 0

    def test_is_user_facing_string(self):
        """Test user-facing string detection."""
        assert HardcodedStringDetector._is_user_facing_string("Hello, World!") is True
        assert HardcodedStringDetector._is_user_facing_string("User logged in successfully") is True
        assert HardcodedStringDetector._is_user_facing_string("Welcome") is True

        # Technical strings
        assert HardcodedStringDetector._is_user_facing_string("api_key") is False
        assert HardcodedStringDetector._is_user_facing_string("localhost") is False
        assert HardcodedStringDetector._is_user_facing_string("GET") is False
        assert HardcodedStringDetector._is_user_facing_string("123") is False


class TestCompletenessChecker:
    """Test CompletenessChecker class."""

    def test_detect_framework(self, tmp_path):
        """Test i18n framework detection."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "dependencies": {
                "react-i18next": "^11.0.0"
            }
        }))

        framework = CompletenessChecker.detect_framework(tmp_path)

        assert framework == I18nFramework.REACT_I18NEXT

    def test_load_translation_keys(self, tmp_path):
        """Test loading translation keys."""
        trans_file = tmp_path / "en.json"
        trans_file.write_text(json.dumps({
            "greeting": "Hello",
            "nested": {
                "message": "Test"
            }
        }))

        keys = CompletenessChecker.load_translation_keys(trans_file)

        assert "greeting" in keys
        assert "nested.message" in keys

    def test_compare_translations(self):
        """Test comparing translation keys."""
        base_keys = {"greeting", "farewell", "help"}
        target_keys = {"greeting", "help", "extra"}

        missing, extra = CompletenessChecker.compare_translations(base_keys, target_keys)

        assert "farewell" in missing
        assert "extra" in extra

    def test_extract_locale_from_path(self):
        """Test locale extraction from path."""
        # Filename patterns
        assert CompletenessChecker.extract_locale_from_path(Path("en.json")) == "en"
        assert CompletenessChecker.extract_locale_from_path(Path("fr-FR.json")) == "fr-FR"

        # Directory patterns
        assert CompletenessChecker.extract_locale_from_path(Path("locales/es/messages.json")) == "es"

    def test_check_pluralization(self):
        """Test pluralization checking."""
        translations = {
            "items": {
                "one": "1 item",
                "other": "{count} items"
            },
            "missing_plural": {
                "other": "items"
            }
        }

        checks = CompletenessChecker.check_pluralization(translations, "en", "test.json")

        assert len(checks) > 0
        # First should have plural forms
        assert checks[0].has_plural_forms is True
