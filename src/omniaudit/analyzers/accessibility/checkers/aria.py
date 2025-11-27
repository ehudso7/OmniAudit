"""ARIA attribute validator."""

import re
from pathlib import Path
from typing import Dict, List, Set
from html.parser import HTMLParser

from ..types import AccessibilityIssue, ARIAValidation, Severity


class ARIAHTMLParser(HTMLParser):
    """HTML parser for ARIA validation."""

    # Valid ARIA roles
    VALID_ROLES: Set[str] = {
        "alert",
        "alertdialog",
        "application",
        "article",
        "banner",
        "button",
        "checkbox",
        "complementary",
        "contentinfo",
        "dialog",
        "directory",
        "document",
        "feed",
        "figure",
        "form",
        "grid",
        "gridcell",
        "group",
        "heading",
        "img",
        "link",
        "list",
        "listbox",
        "listitem",
        "log",
        "main",
        "marquee",
        "math",
        "menu",
        "menubar",
        "menuitem",
        "menuitemcheckbox",
        "menuitemradio",
        "navigation",
        "none",
        "note",
        "option",
        "presentation",
        "progressbar",
        "radio",
        "radiogroup",
        "region",
        "row",
        "rowgroup",
        "rowheader",
        "scrollbar",
        "search",
        "searchbox",
        "separator",
        "slider",
        "spinbutton",
        "status",
        "switch",
        "tab",
        "table",
        "tablist",
        "tabpanel",
        "term",
        "textbox",
        "timer",
        "toolbar",
        "tooltip",
        "tree",
        "treegrid",
        "treeitem",
    }

    # Deprecated ARIA roles
    DEPRECATED_ROLES: Set[str] = {"directory"}

    # Required ARIA attributes for specific roles
    REQUIRED_ATTRS: Dict[str, List[str]] = {
        "checkbox": ["aria-checked"],
        "radio": ["aria-checked"],
        "slider": ["aria-valuenow", "aria-valuemin", "aria-valuemax"],
        "spinbutton": ["aria-valuenow", "aria-valuemin", "aria-valuemax"],
        "scrollbar": ["aria-valuenow", "aria-valuemin", "aria-valuemax"],
        "combobox": ["aria-expanded"],
        "tab": ["aria-selected"],
    }

    def __init__(self):
        super().__init__()
        self.issues: List[AccessibilityIssue] = []
        self.current_file = ""
        self.total_aria_elements = 0
        self.valid_aria = 0
        self.invalid_aria = 0
        self.missing_required = 0
        self.deprecated = 0

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        """Handle start tags with ARIA attributes."""
        line_num = self.getpos()[0]
        attrs_dict = dict(attrs)

        # Check for ARIA attributes
        aria_attrs = {k: v for k, v in attrs_dict.items() if k.startswith("aria-")}
        role = attrs_dict.get("role")

        if aria_attrs or role:
            self.total_aria_elements += 1

        # Validate role
        if role:
            if role not in self.VALID_ROLES:
                self.invalid_aria += 1
                self.issues.append(
                    AccessibilityIssue(
                        severity=Severity.ERROR,
                        rule="ARIA-ROLE",
                        message=f"Invalid ARIA role: '{role}'",
                        file_path=self.current_file,
                        line_number=line_num,
                        element=f"<{tag}>",
                        suggestion=f"Use a valid ARIA role from the WAI-ARIA specification",
                        wcag_criterion="4.1.2 Name, Role, Value (Level A)",
                    )
                )
            elif role in self.DEPRECATED_ROLES:
                self.deprecated += 1
                self.issues.append(
                    AccessibilityIssue(
                        severity=Severity.WARNING,
                        rule="ARIA-DEPRECATED",
                        message=f"Deprecated ARIA role: '{role}'",
                        file_path=self.current_file,
                        line_number=line_num,
                        element=f"<{tag}>",
                        suggestion="Use a non-deprecated ARIA role",
                        wcag_criterion="4.1.2 Name, Role, Value (Level A)",
                    )
                )
            else:
                self.valid_aria += 1

                # Check required attributes for role
                if role in self.REQUIRED_ATTRS:
                    required = self.REQUIRED_ATTRS[role]
                    missing = [attr for attr in required if attr not in attrs_dict]

                    if missing:
                        self.missing_required += 1
                        self.issues.append(
                            AccessibilityIssue(
                                severity=Severity.ERROR,
                                rule="ARIA-REQUIRED",
                                message=f"Role '{role}' missing required attributes: {', '.join(missing)}",
                                file_path=self.current_file,
                                line_number=line_num,
                                element=f"<{tag}>",
                                suggestion=f"Add required attributes: {', '.join(missing)}",
                                wcag_criterion="4.1.2 Name, Role, Value (Level A)",
                            )
                        )

        # Validate ARIA attributes
        for attr, value in aria_attrs.items():
            # Check for common ARIA attribute mistakes
            if attr == "aria-labelledby" or attr == "aria-describedby":
                # Value should be valid ID references
                if not value or not re.match(r"^[\w\s-]+$", value):
                    self.issues.append(
                        AccessibilityIssue(
                            severity=Severity.WARNING,
                            rule="ARIA-ATTR",
                            message=f"Invalid {attr} value: should reference element ID(s)",
                            file_path=self.current_file,
                            line_number=line_num,
                            element=f"<{tag}>",
                            suggestion=f"Ensure {attr} references valid element IDs",
                            wcag_criterion="4.1.2 Name, Role, Value (Level A)",
                        )
                    )

            elif attr in ["aria-checked", "aria-selected", "aria-expanded"]:
                # Boolean/tristate attributes
                if value not in ["true", "false", "mixed", "undefined"]:
                    self.invalid_aria += 1
                    self.issues.append(
                        AccessibilityIssue(
                            severity=Severity.ERROR,
                            rule="ARIA-ATTR",
                            message=f"Invalid {attr} value: '{value}' (should be true, false, mixed, or undefined)",
                            file_path=self.current_file,
                            line_number=line_num,
                            element=f"<{tag}>",
                            suggestion=f"Use valid boolean/tristate value for {attr}",
                            wcag_criterion="4.1.2 Name, Role, Value (Level A)",
                        )
                    )


class ARIAChecker:
    """ARIA attribute validator."""

    @staticmethod
    def validate_file(file_path: Path) -> ARIAValidation:
        """
        Validate ARIA attributes in an HTML file.

        Args:
            file_path: Path to HTML file

        Returns:
            ARIA validation results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return ARIAValidation()

        parser = ARIAHTMLParser()
        parser.current_file = str(file_path)

        try:
            parser.feed(content)
        except Exception:
            # HTML parsing error
            pass

        return ARIAValidation(
            total_aria_elements=parser.total_aria_elements,
            valid_aria_usage=parser.valid_aria,
            invalid_aria_usage=parser.invalid_aria,
            missing_required_attrs=parser.missing_required,
            deprecated_attrs=parser.deprecated,
            issues=parser.issues,
        )
