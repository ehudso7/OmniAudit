"""Quality detectors package."""

from .antipatterns import AntiPatternDetector
from .complexity import ComplexityDetector
from .dead_code import DeadCodeDetector
from .duplication import DuplicationDetector

__all__ = [
    "AntiPatternDetector",
    "ComplexityDetector",
    "DeadCodeDetector",
    "DuplicationDetector",
]
