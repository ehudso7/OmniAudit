"""Unit tests for CodeQualityAnalyzer."""

import pytest
from pathlib import Path
from src.omniaudit.analyzers.code_quality import CodeQualityAnalyzer
from src.omniaudit.analyzers.base import AnalyzerError


def test_analyzer_properties():
    """Test analyzer properties."""
    config = {"project_path": "."}
    analyzer = CodeQualityAnalyzer(config)

    assert analyzer.name == "code_quality_analyzer"
    assert analyzer.version == "0.1.0"


def test_analyzer_missing_project_path():
    """Test error when project_path missing."""
    with pytest.raises(AnalyzerError, match="project_path is required"):
        CodeQualityAnalyzer({})


def test_analyzer_nonexistent_path():
    """Test error when project path doesn't exist."""
    with pytest.raises(AnalyzerError, match="does not exist"):
        CodeQualityAnalyzer({"project_path": "/nonexistent"})


def test_analyzer_analyze(tmp_path):
    """Test basic analysis."""
    # Create minimal project structure
    (tmp_path / "test.py").write_text("def test(): pass\n")

    config = {
        "project_path": str(tmp_path),
        "languages": ["python"]
    }

    analyzer = CodeQualityAnalyzer(config)
    result = analyzer.analyze({})

    assert result["analyzer"] == "code_quality_analyzer"
    assert "data" in result
    assert "metrics" in result["data"]


def test_count_lines(tmp_path):
    """Test line counting."""
    py_file = tmp_path / "test.py"
    py_file.write_text("# Comment\nprint('hello')\n\n")

    analyzer = CodeQualityAnalyzer({"project_path": str(tmp_path)})
    count = analyzer._count_lines(tmp_path, ["*.py"])

    assert count == 2  # Non-empty lines only


def test_calculate_score():
    """Test score calculation."""
    analyzer = CodeQualityAnalyzer({"project_path": "."})

    # Test with empty metrics
    assert analyzer._calculate_score({}) == 0.0

    # Test with Python metrics
    metrics = {
        "python": {
            "coverage": 80.0,
            "complexity": {"average": 5.0}
        }
    }
    score = analyzer._calculate_score(metrics)
    assert score > 0
    assert score <= 100
