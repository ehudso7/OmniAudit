"""WCAG 2.1 compliance checker."""

import re
from pathlib import Path
from typing import List
from html.parser import HTMLParser

from ..types import AccessibilityIssue, Severity, WCAGCompliance, WCAGLevel


class WCAGHTMLParser(HTMLParser):
    """HTML parser for WCAG compliance checking."""

    def __init__(self):
        super().__init__()
        self.issues: List[AccessibilityIssue] = []
        self.current_file = ""
        self.line_num = 0
        self.img_count = 0
        self.img_with_alt = 0
        self.input_count = 0
        self.input_with_label = 0
        self.has_main_landmark = False
        self.heading_levels = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        """Handle start tags."""
        self.line_num = self.getpos()[0]
        attrs_dict = dict(attrs)

        # Check images for alt text (WCAG 1.1.1)
        if tag == "img":
            self.img_count += 1
            if "alt" not in attrs_dict:
                self.issues.append(
                    AccessibilityIssue(
                        severity=Severity.ERROR,
                        rule="WCAG 1.1.1",
                        message="Image missing alt attribute",
                        file_path=self.current_file,
                        line_number=self.line_num,
                        element=f"<{tag}>",
                        suggestion="Add alt attribute to describe the image",
                        wcag_criterion="1.1.1 Non-text Content (Level A)",
                    )
                )
            else:
                self.img_with_alt += 1

        # Check form inputs for labels (WCAG 3.3.2)
        if tag == "input" and attrs_dict.get("type") not in ["submit", "button", "hidden"]:
            self.input_count += 1
            if "id" in attrs_dict and "aria-label" not in attrs_dict:
                # Need to track if there's a corresponding label
                pass

        # Check for main landmark
        if tag == "main" or attrs_dict.get("role") == "main":
            self.has_main_landmark = True

        # Check heading hierarchy (WCAG 1.3.1)
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            self.heading_levels.append(level)

        # Check for button/link text (WCAG 2.4.4)
        if tag in ["a", "button"]:
            if "aria-label" not in attrs_dict and "title" not in attrs_dict:
                # Will need to check inner text later
                pass

        # Check for language attribute on html tag (WCAG 3.1.1)
        if tag == "html":
            if "lang" not in attrs_dict:
                self.issues.append(
                    AccessibilityIssue(
                        severity=Severity.ERROR,
                        rule="WCAG 3.1.1",
                        message="HTML element missing lang attribute",
                        file_path=self.current_file,
                        line_number=self.line_num,
                        element="<html>",
                        suggestion="Add lang attribute (e.g., <html lang='en'>)",
                        wcag_criterion="3.1.1 Language of Page (Level A)",
                    )
                )

        # Check for form controls without labels (WCAG 1.3.1, 3.3.2)
        if tag == "input" and attrs_dict.get("type") not in ["submit", "button", "hidden"]:
            if "aria-label" not in attrs_dict and "aria-labelledby" not in attrs_dict:
                self.issues.append(
                    AccessibilityIssue(
                        severity=Severity.WARNING,
                        rule="WCAG 3.3.2",
                        message="Form input may be missing associated label",
                        file_path=self.current_file,
                        line_number=self.line_num,
                        element=f"<{tag}>",
                        suggestion="Associate input with label using 'for' attribute or aria-label",
                        wcag_criterion="3.3.2 Labels or Instructions (Level A)",
                    )
                )


class WCAGChecker:
    """WCAG 2.1 AA compliance checker."""

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
    }

    @staticmethod
    def check_file(file_path: Path, level: WCAGLevel = WCAGLevel.AA) -> WCAGCompliance:
        """
        Check WCAG compliance for an HTML file.

        Args:
            file_path: Path to HTML file
            level: WCAG level to check (A, AA, AAA)

        Returns:
            WCAG compliance results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return WCAGCompliance(level=level)

        parser = WCAGHTMLParser()
        parser.current_file = str(file_path)

        try:
            parser.feed(content)
        except Exception:
            # HTML parsing error
            pass

        # Check heading hierarchy
        if parser.heading_levels:
            issues = WCAGChecker._check_heading_hierarchy(
                parser.heading_levels, str(file_path)
            )
            parser.issues.extend(issues)

        # Check for main landmark
        if not parser.has_main_landmark:
            parser.issues.append(
                AccessibilityIssue(
                    severity=Severity.WARNING,
                    rule="WCAG 1.3.1",
                    message="Page missing main landmark",
                    file_path=str(file_path),
                    line_number=None,
                    element=None,
                    suggestion="Add <main> element or role='main' to identify main content",
                    wcag_criterion="1.3.1 Info and Relationships (Level A)",
                )
            )

        # Calculate compliance metrics
        total_checks = (
            parser.img_count + parser.input_count + len(parser.heading_levels) + 2
        )  # +2 for lang and main
        passed_checks = parser.img_with_alt + total_checks - len(parser.issues)
        failed_checks = len([i for i in parser.issues if i.severity == Severity.ERROR])
        warnings = len([i for i in parser.issues if i.severity == Severity.WARNING])

        compliance_percentage = (
            (passed_checks / total_checks * 100) if total_checks > 0 else 100.0
        )

        return WCAGCompliance(
            level=level,
            total_checks=total_checks,
            passed_checks=max(0, passed_checks),
            failed_checks=failed_checks,
            warnings=warnings,
            compliance_percentage=compliance_percentage,
            issues=parser.issues,
        )

    @staticmethod
    def _check_heading_hierarchy(
        heading_levels: List[int], file_path: str
    ) -> List[AccessibilityIssue]:
        """Check heading hierarchy for skipped levels."""
        issues = []

        for i in range(len(heading_levels) - 1):
            current = heading_levels[i]
            next_level = heading_levels[i + 1]

            # Check for skipped levels
            if next_level > current + 1:
                issues.append(
                    AccessibilityIssue(
                        severity=Severity.WARNING,
                        rule="WCAG 1.3.1",
                        message=f"Heading hierarchy skipped from h{current} to h{next_level}",
                        file_path=file_path,
                        line_number=None,
                        element=f"<h{next_level}>",
                        suggestion="Use sequential heading levels (h1, h2, h3, etc.)",
                        wcag_criterion="1.3.1 Info and Relationships (Level A)",
                    )
                )

        # Check if starts with h1
        if heading_levels and heading_levels[0] != 1:
            issues.append(
                AccessibilityIssue(
                    severity=Severity.WARNING,
                    rule="WCAG 1.3.1",
                    message=f"Page should start with h1, but starts with h{heading_levels[0]}",
                    file_path=file_path,
                    line_number=None,
                    element=f"<h{heading_levels[0]}>",
                    suggestion="Use h1 for the main page heading",
                    wcag_criterion="1.3.1 Info and Relationships (Level A)",
                )
            )

        return issues
