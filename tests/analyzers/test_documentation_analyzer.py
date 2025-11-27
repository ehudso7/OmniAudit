"""Tests for DocumentationAnalyzer."""

import pytest
from pathlib import Path
from omniaudit.analyzers.documentation import DocumentationAnalyzer
from omniaudit.analyzers.documentation.parsers import DocstringParser, JSDocParser, MarkdownParser
from omniaudit.analyzers.base import AnalyzerError


class TestDocumentationAnalyzer:
    """Test DocumentationAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = DocumentationAnalyzer(config)

        assert analyzer.name == "documentation_analyzer"
        assert analyzer.version == "1.0.0"

    def test_missing_project_path(self):
        """Test error when project_path missing."""
        with pytest.raises(AnalyzerError, match="project_path is required"):
            DocumentationAnalyzer({})

    def test_nonexistent_path(self):
        """Test error when project path doesn't exist."""
        with pytest.raises(AnalyzerError, match="does not exist"):
            DocumentationAnalyzer({"project_path": "/nonexistent/path"})

    def test_analyze_empty_project(self, tmp_path):
        """Test analysis of empty project."""
        config = {"project_path": str(tmp_path)}
        analyzer = DocumentationAnalyzer(config)

        result = analyzer.analyze({})

        assert result["analyzer"] == "documentation_analyzer"
        assert "data" in result
        assert "metrics" in result["data"]

        metrics = result["data"]["metrics"]
        assert metrics["function_coverage"]["total_items"] == 0
        assert metrics["class_coverage"]["total_items"] == 0

    def test_analyze_python_file_with_docstrings(self, tmp_path):
        """Test analysis of Python file with docstrings."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''
def documented_function():
    """This function has a docstring."""
    pass

def undocumented_function():
    pass

class DocumentedClass:
    """This class has a docstring."""
    pass
''')

        config = {"project_path": str(tmp_path)}
        analyzer = DocumentationAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        # Should find 2 functions, 1 documented
        assert metrics["function_coverage"]["total_items"] == 2
        assert metrics["function_coverage"]["documented_items"] == 1
        assert metrics["function_coverage"]["coverage_percentage"] == 50.0

        # Should find 1 class, 1 documented
        assert metrics["class_coverage"]["total_items"] == 1
        assert metrics["class_coverage"]["documented_items"] == 1

    def test_analyze_with_readme(self, tmp_path):
        """Test analysis with README file."""
        readme = tmp_path / "README.md"
        readme.write_text('''
# Project Title

## Description
This is a test project.

## Installation
pip install test

## Usage
Run the test.

## Examples
Example code here.
''')

        config = {"project_path": str(tmp_path)}
        analyzer = DocumentationAnalyzer(config)

        result = analyzer.analyze({})
        readme_analysis = result["data"]["metrics"]["readme_analysis"]

        assert readme_analysis["exists"] is True
        assert readme_analysis["has_title"] is True
        assert readme_analysis["has_description"] is True
        assert readme_analysis["has_installation"] is True
        assert readme_analysis["has_usage"] is True
        assert readme_analysis["has_examples"] is True
        assert readme_analysis["completeness_score"] > 50


class TestDocstringParser:
    """Test DocstringParser class."""

    def test_parse_function_with_docstring(self, tmp_path):
        """Test parsing function with docstring."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''
def my_function(arg1, arg2):
    """
    Function description.

    Args:
        arg1: First argument
        arg2: Second argument

    Returns:
        Result value

    Examples:
        >>> my_function(1, 2)
        3
    """
    return arg1 + arg2
''')

        functions, _ = DocstringParser.parse_file(py_file)

        assert len(functions) == 1
        func = functions[0]
        assert func.name == "my_function"
        assert func.has_description is True
        assert func.has_params is True
        assert func.has_returns is True
        assert func.has_examples is True

    def test_parse_class_with_docstring(self, tmp_path):
        """Test parsing class with docstring."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''
class MyClass:
    """
    Class description.

    Attributes:
        attr1: First attribute
        attr2: Second attribute
    """
    pass
''')

        _, classes = DocstringParser.parse_file(py_file)

        assert len(classes) == 1
        cls = classes[0]
        assert cls.name == "MyClass"
        assert cls.has_description is True
        assert cls.has_attributes is True


class TestJSDocParser:
    """Test JSDocParser class."""

    def test_parse_jsdoc_function(self, tmp_path):
        """Test parsing JSDoc function."""
        js_file = tmp_path / "test.js"
        js_file.write_text('''
/**
 * Add two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum of a and b
 * @example
 * add(1, 2) // 3
 */
function add(a, b) {
    return a + b;
}
''')

        functions = JSDocParser.parse_file(js_file)

        assert len(functions) == 1
        func = functions[0]
        assert func.name == "add"
        assert func.has_description is True
        assert func.has_params is True
        assert func.has_returns is True
        assert func.has_examples is True

    def test_find_undocumented_functions(self, tmp_path):
        """Test finding undocumented functions."""
        js_file = tmp_path / "test.js"
        js_file.write_text('''
function documented() {}

/**
 * This is documented
 */
function alsoDocumented() {}

function undocumented() {}
''')

        undocumented = JSDocParser.find_undocumented_functions(js_file)

        assert "undocumented" in undocumented
        assert "documented" in undocumented
        assert "alsoDocumented" not in undocumented


class TestMarkdownParser:
    """Test MarkdownParser class."""

    def test_find_readme(self, tmp_path):
        """Test finding README file."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test")

        found = MarkdownParser.find_readme(tmp_path)

        assert found == readme

    def test_analyze_readme_completeness(self, tmp_path):
        """Test analyzing README completeness."""
        readme = tmp_path / "README.md"
        readme.write_text('''
# Project Title

## Description
Project description here.

## Installation
Installation instructions.

## Usage
Usage instructions.

## License
MIT License
''')

        analysis = MarkdownParser.analyze_readme(readme)

        assert analysis.exists is True
        assert analysis.has_title is True
        assert analysis.has_description is True
        assert analysis.has_installation is True
        assert analysis.has_usage is True
        assert analysis.has_license is True
        assert analysis.word_count > 0
        assert analysis.completeness_score > 0

    def test_extract_code_examples(self):
        """Test extracting code examples."""
        content = '''
# Example

```python
print("Hello")
```

Some text

```javascript
console.log("World");
```
'''

        examples = MarkdownParser.extract_code_examples(content)

        assert len(examples) == 2
        assert 'print("Hello")' in examples[0]
        assert 'console.log("World")' in examples[1]
