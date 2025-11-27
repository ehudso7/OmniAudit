"""Tests for AccessibilityAnalyzer."""

import pytest
from pathlib import Path
from omniaudit.analyzers.accessibility import AccessibilityAnalyzer
from omniaudit.analyzers.accessibility.checkers import WCAGChecker, ARIAChecker, ContrastChecker
from omniaudit.analyzers.accessibility.types import WCAGLevel
from omniaudit.analyzers.base import AnalyzerError


class TestAccessibilityAnalyzer:
    """Test AccessibilityAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = AccessibilityAnalyzer(config)

        assert analyzer.name == "accessibility_analyzer"
        assert analyzer.version == "1.0.0"
        assert analyzer.wcag_level == WCAGLevel.AA

    def test_custom_wcag_level(self, tmp_path):
        """Test custom WCAG level."""
        config = {"project_path": str(tmp_path), "wcag_level": "AAA"}
        analyzer = AccessibilityAnalyzer(config)

        assert analyzer.wcag_level == WCAGLevel.AAA

    def test_analyze_empty_project(self, tmp_path):
        """Test analysis of project without HTML files."""
        config = {"project_path": str(tmp_path)}
        analyzer = AccessibilityAnalyzer(config)

        result = analyzer.analyze({})

        assert result["analyzer"] == "accessibility_analyzer"
        metrics = result["data"]["metrics"]
        assert metrics["files_analyzed"] == 0

    def test_analyze_html_file(self, tmp_path):
        """Test analysis of HTML file."""
        html_file = tmp_path / "index.html"
        html_file.write_text('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test Page</title>
</head>
<body>
    <main>
        <h1>Welcome</h1>
        <img src="test.jpg" alt="Test image">
        <button aria-label="Submit">Submit</button>
    </main>
</body>
</html>
''')

        config = {"project_path": str(tmp_path)}
        analyzer = AccessibilityAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        assert metrics["files_analyzed"] == 1
        assert metrics["overall_score"] > 0


class TestWCAGChecker:
    """Test WCAGChecker class."""

    def test_check_missing_alt_text(self, tmp_path):
        """Test checking for missing alt text."""
        html_file = tmp_path / "test.html"
        html_file.write_text('''
<html>
<body>
    <img src="image.jpg">
</body>
</html>
''')

        result = WCAGChecker.check_file(html_file)

        assert result.failed_checks > 0
        assert any("alt" in issue.message.lower() for issue in result.issues)

    def test_check_missing_lang(self, tmp_path):
        """Test checking for missing lang attribute."""
        html_file = tmp_path / "test.html"
        html_file.write_text('''
<html>
<body>
    <h1>Test</h1>
</body>
</html>
''')

        result = WCAGChecker.check_file(html_file)

        assert any("lang" in issue.message.lower() for issue in result.issues)

    def test_heading_hierarchy(self, tmp_path):
        """Test heading hierarchy checking."""
        html_file = tmp_path / "test.html"
        html_file.write_text('''
<html lang="en">
<body>
    <h2>Second heading first (bad)</h2>
    <h1>First heading</h1>
    <h4>Skipped h3 (bad)</h4>
</body>
</html>
''')

        result = WCAGChecker.check_file(html_file)

        # Should find heading hierarchy issues
        hierarchy_issues = [i for i in result.issues if "heading" in i.message.lower()]
        assert len(hierarchy_issues) > 0


class TestARIAChecker:
    """Test ARIAChecker class."""

    def test_valid_aria_role(self, tmp_path):
        """Test valid ARIA role."""
        html_file = tmp_path / "test.html"
        html_file.write_text('''
<html>
<body>
    <div role="navigation">
        <button>Click me</button>
    </div>
</body>
</html>
''')

        result = ARIAChecker.validate_file(html_file)

        assert result.total_aria_elements > 0
        assert result.valid_aria_usage > 0

    def test_invalid_aria_role(self, tmp_path):
        """Test invalid ARIA role."""
        html_file = tmp_path / "test.html"
        html_file.write_text('''
<html>
<body>
    <div role="invalidrole">
        <button>Click me</button>
    </div>
</body>
</html>
''')

        result = ARIAChecker.validate_file(html_file)

        assert result.invalid_aria_usage > 0
        assert any("invalid" in issue.message.lower() for issue in result.issues)

    def test_missing_required_attrs(self, tmp_path):
        """Test missing required ARIA attributes."""
        html_file = tmp_path / "test.html"
        html_file.write_text('''
<html>
<body>
    <div role="checkbox">Checkbox without aria-checked</div>
</body>
</html>
''')

        result = ARIAChecker.validate_file(html_file)

        assert result.missing_required_attrs > 0


class TestContrastChecker:
    """Test ContrastChecker class."""

    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        assert ContrastChecker.hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert ContrastChecker.hex_to_rgb("#000000") == (0, 0, 0)
        assert ContrastChecker.hex_to_rgb("FFF") == (255, 255, 255)

    def test_contrast_ratio_calculation(self):
        """Test contrast ratio calculation."""
        # Black on white should have high contrast (21:1)
        ratio = ContrastChecker.calculate_contrast_ratio("#000000", "#FFFFFF")
        assert ratio == 21.0

        # White on white should have low contrast (1:1)
        ratio = ContrastChecker.calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
        assert ratio == 1.0

    def test_wcag_compliance(self):
        """Test WCAG contrast compliance checking."""
        # Black on white passes all levels
        result = ContrastChecker.check_contrast("#000000", "#FFFFFF")

        assert result.wcag_aa_normal is True
        assert result.wcag_aa_large is True
        assert result.wcag_aaa_normal is True
        assert result.wcag_aaa_large is True

        # Light gray on white fails most levels
        result = ContrastChecker.check_contrast("#CCCCCC", "#FFFFFF")

        assert result.wcag_aa_normal is False

    def test_extract_colors_from_css(self, tmp_path):
        """Test extracting colors from CSS."""
        css_file = tmp_path / "test.css"
        css_file.write_text('''
.button {
    color: #000000;
    background-color: #FFFFFF;
}

.warning {
    color: #FFFF00;
    background: #FFFFFF;
}
''')

        results = ContrastChecker.extract_colors_from_css(css_file)

        assert len(results) > 0
        # First color combo should pass
        assert results[0].wcag_aa_normal is True
