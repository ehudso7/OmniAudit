"""Type definitions for accessibility analyzer."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class WCAGLevel(str, Enum):
    """WCAG compliance levels."""

    A = "A"
    AA = "AA"
    AAA = "AAA"


class Severity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AccessibilityIssue(BaseModel):
    """Individual accessibility issue."""

    severity: Severity
    rule: str = Field(description="WCAG rule identifier")
    message: str
    file_path: str
    line_number: Optional[int] = None
    element: Optional[str] = None
    suggestion: str
    wcag_criterion: Optional[str] = None


class WCAGCompliance(BaseModel):
    """WCAG compliance metrics."""

    level: WCAGLevel
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0
    compliance_percentage: float = 0.0
    issues: List[AccessibilityIssue] = Field(default_factory=list)


class ARIAValidation(BaseModel):
    """ARIA attribute validation results."""

    total_aria_elements: int = 0
    valid_aria_usage: int = 0
    invalid_aria_usage: int = 0
    missing_required_attrs: int = 0
    deprecated_attrs: int = 0
    issues: List[AccessibilityIssue] = Field(default_factory=list)


class ColorContrastResult(BaseModel):
    """Color contrast analysis result."""

    foreground: str
    background: str
    ratio: float
    wcag_aa_normal: bool = Field(description="Passes WCAG AA for normal text (4.5:1)")
    wcag_aa_large: bool = Field(description="Passes WCAG AA for large text (3:1)")
    wcag_aaa_normal: bool = Field(description="Passes WCAG AAA for normal text (7:1)")
    wcag_aaa_large: bool = Field(description="Passes WCAG AAA for large text (4.5:1)")
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class SemanticHTMLMetrics(BaseModel):
    """Semantic HTML usage metrics."""

    total_elements: int = 0
    semantic_elements: int = 0
    non_semantic_elements: int = 0
    semantic_percentage: float = 0.0
    div_soup_count: int = Field(default=0, description="Excessive div nesting")
    heading_structure_valid: bool = True
    landmark_roles_present: bool = False
    issues: List[AccessibilityIssue] = Field(default_factory=list)


class AccessibilityMetrics(BaseModel):
    """Overall accessibility metrics."""

    wcag_compliance: WCAGCompliance
    aria_validation: ARIAValidation
    semantic_html: SemanticHTMLMetrics
    color_contrast_issues: List[ColorContrastResult] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, description="Overall accessibility score")
    files_analyzed: int = 0
    total_issues: int = 0


class AccessibilitySummary(BaseModel):
    """Summary of accessibility analysis."""

    total_critical_issues: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    wcag_aa_compliance: float = 0.0
    recommendation: str = ""
