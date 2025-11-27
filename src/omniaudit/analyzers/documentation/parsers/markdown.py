"""Markdown documentation parser."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from ..types import READMEAnalysis


class MarkdownParser:
    """Parse and analyze Markdown documentation files."""

    README_PATTERNS = {
        "title": re.compile(r"^#\s+(.+)", re.MULTILINE),
        "description": re.compile(
            r"^#+\s*(?:Description|About|Overview)\s*$", re.MULTILINE | re.IGNORECASE
        ),
        "installation": re.compile(
            r"^#+\s*Install(?:ation)?\s*$", re.MULTILINE | re.IGNORECASE
        ),
        "usage": re.compile(
            r"^#+\s*(?:Usage|Getting Started|Quick Start)\s*$",
            re.MULTILINE | re.IGNORECASE,
        ),
        "examples": re.compile(
            r"^#+\s*Examples?\s*$", re.MULTILINE | re.IGNORECASE
        ),
        "api_docs": re.compile(
            r"^#+\s*(?:API|API Documentation|API Reference)\s*$",
            re.MULTILINE | re.IGNORECASE,
        ),
        "contributing": re.compile(
            r"^#+\s*Contribut(?:ing|ion)\s*$", re.MULTILINE | re.IGNORECASE
        ),
        "license": re.compile(
            r"^#+\s*Licen[sc]e\s*$", re.MULTILINE | re.IGNORECASE
        ),
    }

    @staticmethod
    def find_readme(project_path: Path) -> Optional[Path]:
        """
        Find README file in project.

        Args:
            project_path: Root path of the project

        Returns:
            Path to README file if found
        """
        readme_names = [
            "README.md",
            "readme.md",
            "ReadMe.md",
            "README",
            "README.rst",
            "README.txt",
        ]

        for name in readme_names:
            readme_path = project_path / name
            if readme_path.exists() and readme_path.is_file():
                return readme_path

        return None

    @staticmethod
    def analyze_readme(file_path: Path) -> READMEAnalysis:
        """
        Analyze README file completeness.

        Args:
            file_path: Path to README file

        Returns:
            README analysis results
        """
        if not file_path or not file_path.exists():
            return READMEAnalysis(exists=False)

        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return READMEAnalysis(exists=True, file_path=str(file_path))

        analysis = READMEAnalysis(
            exists=True,
            file_path=str(file_path),
            has_title=bool(MarkdownParser.README_PATTERNS["title"].search(content)),
            has_description=bool(
                MarkdownParser.README_PATTERNS["description"].search(content)
            ),
            has_installation=bool(
                MarkdownParser.README_PATTERNS["installation"].search(content)
            ),
            has_usage=bool(MarkdownParser.README_PATTERNS["usage"].search(content)),
            has_examples=bool(
                MarkdownParser.README_PATTERNS["examples"].search(content)
            ),
            has_api_docs=bool(
                MarkdownParser.README_PATTERNS["api_docs"].search(content)
            ),
            has_contributing=bool(
                MarkdownParser.README_PATTERNS["contributing"].search(content)
            ),
            has_license=bool(
                MarkdownParser.README_PATTERNS["license"].search(content)
            ),
            word_count=len(content.split()),
        )

        # Calculate completeness score
        sections = [
            analysis.has_title,
            analysis.has_description,
            analysis.has_installation,
            analysis.has_usage,
            analysis.has_examples,
            analysis.has_api_docs,
            analysis.has_contributing,
            analysis.has_license,
        ]
        analysis.completeness_score = (sum(sections) / len(sections)) * 100

        return analysis

    @staticmethod
    def extract_code_examples(content: str) -> List[str]:
        """
        Extract code examples from Markdown content.

        Args:
            content: Markdown content

        Returns:
            List of code examples
        """
        # Match fenced code blocks
        pattern = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)
        return pattern.findall(content)

    @staticmethod
    def count_headings(content: str) -> Dict[int, int]:
        """
        Count headings by level.

        Args:
            content: Markdown content

        Returns:
            Dictionary mapping heading level to count
        """
        headings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        for match in re.finditer(r"^(#{1,6})\s+", content, re.MULTILINE):
            level = len(match.group(1))
            headings[level] += 1

        return headings
