"""I18n detectors."""

from .hardcoded_strings import HardcodedStringDetector
from .completeness import CompletenessChecker

__all__ = ["HardcodedStringDetector", "CompletenessChecker"]
