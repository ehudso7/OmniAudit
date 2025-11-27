"""Type definitions for i18n analyzer."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class I18nFramework(str, Enum):
    """Supported i18n frameworks."""

    REACT_I18NEXT = "react-i18next"
    VUE_I18N = "vue-i18n"
    ANGULAR_I18N = "angular-i18n"
    GETTEXT = "gettext"
    CUSTOM = "custom"


class HardcodedString(BaseModel):
    """Hardcoded string detection."""

    text: str
    file_path: str
    line_number: int
    context: str = Field(description="Code context where string was found")
    confidence: float = Field(
        default=1.0, description="Confidence that this is a user-facing string (0-1)"
    )
    suggestion: str = ""


class TranslationFile(BaseModel):
    """Translation file information."""

    locale: str
    file_path: str
    total_keys: int = 0
    translated_keys: int = 0
    missing_keys: List[str] = Field(default_factory=list)
    extra_keys: List[str] = Field(default_factory=list)


class PluralizationCheck(BaseModel):
    """Pluralization handling check."""

    key: str
    locale: str
    has_plural_forms: bool = False
    missing_forms: List[str] = Field(default_factory=list)
    file_path: str


class LocaleSupport(BaseModel):
    """Locale support information."""

    locale: str
    completeness: float = Field(description="Translation completeness percentage")
    missing_count: int = 0
    extra_count: int = 0
    has_pluralization: bool = False


class I18nMetrics(BaseModel):
    """Overall i18n metrics."""

    framework_detected: Optional[I18nFramework] = None
    hardcoded_strings: List[HardcodedString] = Field(default_factory=list)
    translation_files: List[TranslationFile] = Field(default_factory=list)
    locale_support: List[LocaleSupport] = Field(default_factory=list)
    pluralization_checks: List[PluralizationCheck] = Field(default_factory=list)
    base_locale: Optional[str] = None
    total_translation_keys: int = 0
    average_completeness: float = 0.0
    overall_score: float = 0.0
    files_analyzed: int = 0


class I18nFinding(BaseModel):
    """Individual i18n finding."""

    severity: str = Field(description="critical, warning, or info")
    category: str = Field(
        description="hardcoded_strings, missing_translations, pluralization, or locale_support"
    )
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
