"""JSDoc/TSDoc parser for JavaScript and TypeScript files."""

import re
from pathlib import Path
from typing import List, Optional

from ..types import FunctionDoc, DocType


class JSDocParser:
    """Parse JSDoc and TSDoc comments."""

    JSDOC_PATTERN = re.compile(
        r"/\*\*\s*(.*?)\s*\*/\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)",
        re.DOTALL | re.MULTILINE,
    )
    TSDOC_PATTERN = re.compile(
        r"/\*\*\s*(.*?)\s*\*/\s*(?:export\s+)?(?:async\s+)?(?:public|private|protected)?\s*(\w+)\s*\(",
        re.DOTALL | re.MULTILINE,
    )

    @staticmethod
    def parse_file(file_path: Path) -> List[FunctionDoc]:
        """
        Parse JSDoc/TSDoc from a JavaScript or TypeScript file.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of function documentation objects
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return []

        functions = []

        # Parse JSDoc comments
        for match in JSDocParser.JSDOC_PATTERN.finditer(content):
            doc_text, func_name = match.groups()
            line_number = content[: match.start()].count("\n") + 1

            func_doc = JSDocParser._parse_jsdoc_content(
                doc_text, func_name, str(file_path), line_number
            )
            functions.append(func_doc)

        # Parse TSDoc comments (TypeScript)
        if file_path.suffix in [".ts", ".tsx"]:
            for match in JSDocParser.TSDOC_PATTERN.finditer(content):
                doc_text, func_name = match.groups()
                line_number = content[: match.start()].count("\n") + 1

                func_doc = JSDocParser._parse_jsdoc_content(
                    doc_text, func_name, str(file_path), line_number, DocType.TSDOC
                )
                functions.append(func_doc)

        return functions

    @staticmethod
    def _parse_jsdoc_content(
        doc_text: str,
        func_name: str,
        file_path: str,
        line_number: int,
        doc_type: DocType = DocType.JSDOC,
    ) -> FunctionDoc:
        """Parse JSDoc comment content."""
        has_description = bool(re.search(r"^\s*[^@\s]", doc_text, re.MULTILINE))
        has_params = bool(re.search(r"@param", doc_text))
        has_returns = bool(re.search(r"@returns?", doc_text))
        has_examples = bool(re.search(r"@example", doc_text))

        return FunctionDoc(
            name=func_name,
            file_path=file_path,
            line_number=line_number,
            has_description=has_description,
            has_params=has_params,
            has_returns=has_returns,
            has_examples=has_examples,
            doc_type=doc_type,
            raw_doc=doc_text.strip(),
        )

    @staticmethod
    def find_undocumented_functions(file_path: Path) -> List[str]:
        """
        Find functions without JSDoc comments.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of undocumented function names
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return []

        # Find all function declarations
        all_functions = set(
            re.findall(
                r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", content, re.MULTILINE
            )
        )

        # Find documented functions
        documented = set(
            func_name
            for _, func_name in JSDocParser.JSDOC_PATTERN.findall(content)
        )

        return list(all_functions - documented)
