"""Documentation coverage analyzer."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseAnalyzer, AnalyzerError
from .parsers import JSDocParser, DocstringParser, MarkdownParser
from .types import (
    APIDocumentation,
    DocCoverage,
    DocumentationFinding,
    DocumentationMetrics,
    READMEAnalysis,
)


class DocumentationAnalyzer(BaseAnalyzer):
    """
    Analyze documentation coverage across a project.

    Supports:
    - Python docstrings
    - JSDoc/TSDoc comments
    - README completeness
    - API documentation coverage
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize documentation analyzer."""
        super().__init__(config)
        self.project_path = Path(self.config["project_path"])

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "documentation_analyzer"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required in configuration")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path {path} does not exist")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze documentation coverage.

        Args:
            data: Input data (file patterns, exclusions, etc.)

        Returns:
            Analysis results with metrics and findings
        """
        file_patterns = data.get("file_patterns", {})
        exclude_patterns = data.get("exclude_patterns", ["**/node_modules/**", "**/.git/**"])

        # Analyze different aspects
        function_coverage = self._analyze_function_coverage(file_patterns, exclude_patterns)
        class_coverage = self._analyze_class_coverage(file_patterns, exclude_patterns)
        readme_analysis = self._analyze_readme()
        api_documentation = self._analyze_api_documentation()

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            function_coverage, class_coverage, readme_analysis, api_documentation
        )

        metrics = DocumentationMetrics(
            function_coverage=function_coverage,
            class_coverage=class_coverage,
            readme_analysis=readme_analysis,
            api_documentation=api_documentation,
            overall_score=overall_score,
            languages_analyzed=self._get_languages_analyzed(file_patterns),
            total_files_analyzed=self._count_analyzed_files(file_patterns, exclude_patterns),
        )

        findings = self._generate_findings(metrics)

        return self._create_response(
            {
                "metrics": metrics.model_dump(),
                "findings": [f.model_dump() for f in findings],
                "summary": self._generate_summary(metrics),
            }
        )

    def _analyze_function_coverage(
        self, file_patterns: Dict[str, List[str]], exclude_patterns: List[str]
    ) -> DocCoverage:
        """Analyze function documentation coverage."""
        total_functions = 0
        documented_functions = 0
        missing_items = []

        # Python files
        python_files = self._find_files(["**/*.py"], exclude_patterns)
        for file_path in python_files:
            functions, _ = DocstringParser.parse_file(file_path)
            total_functions += len(functions)
            documented_functions += sum(1 for f in functions if f.has_description)

            # Track missing documentation
            undoc_funcs, _ = DocstringParser.find_undocumented_items(file_path)
            missing_items.extend([f"{file_path}:{func}" for func in undoc_funcs])

        # JavaScript/TypeScript files
        js_files = self._find_files(["**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx"], exclude_patterns)
        for file_path in js_files:
            functions = JSDocParser.parse_file(file_path)
            total_functions += len(functions)
            documented_functions += sum(1 for f in functions if f.has_description)

            # Track missing documentation
            undoc_funcs = JSDocParser.find_undocumented_functions(file_path)
            missing_items.extend([f"{file_path}:{func}" for func in undoc_funcs])

        coverage_percentage = (
            (documented_functions / total_functions * 100) if total_functions > 0 else 0.0
        )

        return DocCoverage(
            total_items=total_functions,
            documented_items=documented_functions,
            coverage_percentage=coverage_percentage,
            missing_items=missing_items[:50],  # Limit to first 50
        )

    def _analyze_class_coverage(
        self, file_patterns: Dict[str, List[str]], exclude_patterns: List[str]
    ) -> DocCoverage:
        """Analyze class documentation coverage."""
        total_classes = 0
        documented_classes = 0
        missing_items = []

        # Python files
        python_files = self._find_files(["**/*.py"], exclude_patterns)
        for file_path in python_files:
            _, classes = DocstringParser.parse_file(file_path)
            total_classes += len(classes)
            documented_classes += sum(1 for c in classes if c.has_description)

            # Track missing documentation
            _, undoc_classes = DocstringParser.find_undocumented_items(file_path)
            missing_items.extend([f"{file_path}:{cls}" for cls in undoc_classes])

        coverage_percentage = (
            (documented_classes / total_classes * 100) if total_classes > 0 else 0.0
        )

        return DocCoverage(
            total_items=total_classes,
            documented_items=documented_classes,
            coverage_percentage=coverage_percentage,
            missing_items=missing_items[:50],  # Limit to first 50
        )

    def _analyze_readme(self) -> READMEAnalysis:
        """Analyze README file."""
        readme_path = MarkdownParser.find_readme(self.project_path)
        if readme_path:
            return MarkdownParser.analyze_readme(readme_path)
        return READMEAnalysis(exists=False)

    def _analyze_api_documentation(self) -> APIDocumentation:
        """Analyze API documentation."""
        # Check for OpenAPI/Swagger specs
        has_openapi = any(
            self.project_path.glob(pattern)
            for pattern in ["**/openapi.yaml", "**/openapi.json", "**/swagger.yaml", "**/swagger.json"]
        )

        # Check for GraphQL schema
        has_graphql = any(
            self.project_path.glob(pattern)
            for pattern in ["**/schema.graphql", "**/*.graphql"]
        )

        return APIDocumentation(
            has_openapi_spec=has_openapi,
            has_graphql_schema=has_graphql,
        )

    def _calculate_overall_score(
        self,
        function_coverage: DocCoverage,
        class_coverage: DocCoverage,
        readme_analysis: READMEAnalysis,
        api_documentation: APIDocumentation,
    ) -> float:
        """Calculate overall documentation score."""
        weights = {
            "function_coverage": 0.4,
            "class_coverage": 0.3,
            "readme": 0.2,
            "api": 0.1,
        }

        score = (
            function_coverage.coverage_percentage * weights["function_coverage"]
            + class_coverage.coverage_percentage * weights["class_coverage"]
            + readme_analysis.completeness_score * weights["readme"]
            + (100 if api_documentation.has_openapi_spec or api_documentation.has_graphql_schema else 0)
            * weights["api"]
        )

        return round(score, 2)

    def _generate_findings(self, metrics: DocumentationMetrics) -> List[DocumentationFinding]:
        """Generate findings from metrics."""
        findings = []

        # Function coverage findings
        if metrics.function_coverage.coverage_percentage < 50:
            findings.append(
                DocumentationFinding(
                    severity="critical",
                    category="missing_docs",
                    message=f"Low function documentation coverage: {metrics.function_coverage.coverage_percentage:.1f}%",
                    suggestion="Add docstrings/JSDoc comments to functions",
                )
            )
        elif metrics.function_coverage.coverage_percentage < 80:
            findings.append(
                DocumentationFinding(
                    severity="warning",
                    category="incomplete_docs",
                    message=f"Function documentation coverage needs improvement: {metrics.function_coverage.coverage_percentage:.1f}%",
                    suggestion="Aim for 80%+ documentation coverage",
                )
            )

        # README findings
        if not metrics.readme_analysis.exists:
            findings.append(
                DocumentationFinding(
                    severity="critical",
                    category="missing_docs",
                    message="No README file found",
                    suggestion="Create a README.md with project description, installation, and usage instructions",
                )
            )
        elif metrics.readme_analysis.completeness_score < 60:
            findings.append(
                DocumentationFinding(
                    severity="warning",
                    category="incomplete_docs",
                    message=f"README is incomplete ({metrics.readme_analysis.completeness_score:.1f}% complete)",
                    suggestion="Add missing sections: installation, usage, examples, API docs, contributing, license",
                )
            )

        # API documentation findings
        if not metrics.api_documentation.has_openapi_spec and not metrics.api_documentation.has_graphql_schema:
            findings.append(
                DocumentationFinding(
                    severity="info",
                    category="best_practice",
                    message="No API specification found",
                    suggestion="Consider adding OpenAPI/Swagger or GraphQL schema documentation",
                )
            )

        return findings

    def _generate_summary(self, metrics: DocumentationMetrics) -> str:
        """Generate summary text."""
        return (
            f"Documentation coverage: {metrics.overall_score:.1f}%. "
            f"Functions: {metrics.function_coverage.coverage_percentage:.1f}%, "
            f"Classes: {metrics.class_coverage.coverage_percentage:.1f}%, "
            f"README: {metrics.readme_analysis.completeness_score:.1f}%."
        )

    def _find_files(self, patterns: List[str], exclude_patterns: List[str]) -> List[Path]:
        """Find files matching patterns."""
        files = []
        for pattern in patterns:
            for file_path in self.project_path.glob(pattern):
                # Check exclusions
                if any(file_path.match(ex) for ex in exclude_patterns):
                    continue
                if file_path.is_file():
                    files.append(file_path)
        return files

    def _get_languages_analyzed(self, file_patterns: Dict[str, List[str]]) -> List[str]:
        """Get list of languages analyzed."""
        languages = set()
        if any(self.project_path.glob("**/*.py")):
            languages.add("python")
        if any(self.project_path.glob("**/*.js")) or any(self.project_path.glob("**/*.jsx")):
            languages.add("javascript")
        if any(self.project_path.glob("**/*.ts")) or any(self.project_path.glob("**/*.tsx")):
            languages.add("typescript")
        return list(languages)

    def _count_analyzed_files(self, file_patterns: Dict[str, List[str]], exclude_patterns: List[str]) -> int:
        """Count total files analyzed."""
        all_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx"]
        return len(self._find_files(all_patterns, exclude_patterns))
