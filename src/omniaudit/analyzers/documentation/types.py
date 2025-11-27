"""Type definitions for documentation analyzer."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DocType(str, Enum):
    """Documentation types."""

    JSDOC = "jsdoc"
    TSDOC = "tsdoc"
    DOCSTRING = "docstring"
    MARKDOWN = "markdown"
    INLINE = "inline"


class DocCoverage(BaseModel):
    """Documentation coverage metrics."""

    total_items: int = Field(default=0, description="Total documentable items")
    documented_items: int = Field(default=0, description="Items with documentation")
    coverage_percentage: float = Field(default=0.0, description="Coverage percentage")
    missing_items: List[str] = Field(default_factory=list, description="Items missing docs")


class FunctionDoc(BaseModel):
    """Function documentation details."""

    name: str
    file_path: str
    line_number: int
    has_description: bool = False
    has_params: bool = False
    has_returns: bool = False
    has_examples: bool = False
    doc_type: Optional[DocType] = None
    raw_doc: Optional[str] = None


class ClassDoc(BaseModel):
    """Class documentation details."""

    name: str
    file_path: str
    line_number: int
    has_description: bool = False
    has_attributes: bool = False
    has_methods_documented: bool = False
    has_examples: bool = False
    doc_type: Optional[DocType] = None
    raw_doc: Optional[str] = None


class READMEAnalysis(BaseModel):
    """README file analysis."""

    exists: bool = False
    file_path: Optional[str] = None
    has_title: bool = False
    has_description: bool = False
    has_installation: bool = False
    has_usage: bool = False
    has_examples: bool = False
    has_api_docs: bool = False
    has_contributing: bool = False
    has_license: bool = False
    word_count: int = 0
    completeness_score: float = 0.0


class APIDocumentation(BaseModel):
    """API documentation analysis."""

    total_endpoints: int = 0
    documented_endpoints: int = 0
    coverage_percentage: float = 0.0
    has_openapi_spec: bool = False
    has_graphql_schema: bool = False
    missing_endpoints: List[str] = Field(default_factory=list)


class DocumentationMetrics(BaseModel):
    """Overall documentation metrics."""

    function_coverage: DocCoverage
    class_coverage: DocCoverage
    readme_analysis: READMEAnalysis
    api_documentation: APIDocumentation
    overall_score: float = Field(default=0.0, description="Overall documentation score")
    languages_analyzed: List[str] = Field(default_factory=list)
    total_files_analyzed: int = 0


class DocumentationFinding(BaseModel):
    """Individual documentation finding."""

    severity: str = Field(description="critical, warning, or info")
    category: str = Field(description="missing_docs, incomplete_docs, or best_practice")
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
