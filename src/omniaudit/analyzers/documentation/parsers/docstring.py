"""Python docstring parser."""

import ast
import re
from pathlib import Path
from typing import List, Optional

from ..types import FunctionDoc, ClassDoc, DocType


class DocstringParser:
    """Parse Python docstrings."""

    @staticmethod
    def parse_file(file_path: Path) -> tuple[List[FunctionDoc], List[ClassDoc]]:
        """
        Parse docstrings from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Tuple of (function docs, class docs)
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except (IOError, SyntaxError, UnicodeDecodeError):
            return [], []

        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_doc = DocstringParser._parse_function(
                    node, str(file_path)
                )
                functions.append(func_doc)
            elif isinstance(node, ast.ClassDef):
                class_doc = DocstringParser._parse_class(
                    node, str(file_path)
                )
                classes.append(class_doc)

        return functions, classes

    @staticmethod
    def _parse_function(node: ast.FunctionDef, file_path: str) -> FunctionDoc:
        """Parse function docstring."""
        docstring = ast.get_docstring(node)

        if docstring:
            # Check for different docstring styles
            has_description = len(docstring.strip()) > 0
            has_params = bool(
                re.search(
                    r"(?:Args?|Parameters?|Params?):", docstring, re.IGNORECASE
                )
            )
            has_returns = bool(
                re.search(r"(?:Returns?|Yields?):", docstring, re.IGNORECASE)
            )
            has_examples = bool(
                re.search(r"(?:Examples?|Usage):", docstring, re.IGNORECASE)
            )
        else:
            has_description = has_params = has_returns = has_examples = False

        return FunctionDoc(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            has_description=has_description,
            has_params=has_params,
            has_returns=has_returns,
            has_examples=has_examples,
            doc_type=DocType.DOCSTRING if docstring else None,
            raw_doc=docstring,
        )

    @staticmethod
    def _parse_class(node: ast.ClassDef, file_path: str) -> ClassDoc:
        """Parse class docstring."""
        docstring = ast.get_docstring(node)

        if docstring:
            has_description = len(docstring.strip()) > 0
            has_attributes = bool(
                re.search(r"(?:Attributes?):", docstring, re.IGNORECASE)
            )
            has_examples = bool(
                re.search(r"(?:Examples?|Usage):", docstring, re.IGNORECASE)
            )

            # Check if methods are documented
            method_count = sum(
                1 for n in node.body if isinstance(n, ast.FunctionDef)
            )
            documented_methods = sum(
                1
                for n in node.body
                if isinstance(n, ast.FunctionDef) and ast.get_docstring(n)
            )
            has_methods_documented = (
                documented_methods > 0 if method_count > 0 else True
            )
        else:
            has_description = has_attributes = has_examples = False
            has_methods_documented = False

        return ClassDoc(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            has_description=has_description,
            has_attributes=has_attributes,
            has_methods_documented=has_methods_documented,
            has_examples=has_examples,
            doc_type=DocType.DOCSTRING if docstring else None,
            raw_doc=docstring,
        )

    @staticmethod
    def find_undocumented_items(
        file_path: Path,
    ) -> tuple[List[str], List[str]]:
        """
        Find undocumented functions and classes.

        Args:
            file_path: Path to the Python file

        Returns:
            Tuple of (undocumented functions, undocumented classes)
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except (IOError, SyntaxError, UnicodeDecodeError):
            return [], []

        undocumented_functions = []
        undocumented_classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private methods (starting with _)
                if not node.name.startswith("_") and not ast.get_docstring(node):
                    undocumented_functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    undocumented_classes.append(node.name)

        return undocumented_functions, undocumented_classes
