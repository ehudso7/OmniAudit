"""
Web Vitals Impact Analysis Module.

Predicts impact on Core Web Vitals and suggests bundle optimizations.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..types import (
    BundleOptimization,
    PerformanceImpact,
    WebVitalImpact,
    WebVitalMetric,
)


class WebVitalsAnalyzer:
    """Analyzes Web Vitals impact and bundle optimization opportunities."""

    def __init__(self):
        """Initialize Web Vitals analyzer."""
        pass

    def analyze_files(
        self, file_paths: List[Path]
    ) -> tuple[List[WebVitalImpact], List[BundleOptimization]]:
        """Analyze files for Web Vitals impact and bundle optimizations.

        Args:
            file_paths: Files to analyze

        Returns:
            Tuple of (web_vital_impacts, bundle_optimizations)
        """
        web_vital_impacts = []
        bundle_optimizations = []

        # Analyze JavaScript/TypeScript files for frontend performance
        js_files = [
            f
            for f in file_paths
            if f.suffix in (".js", ".jsx", ".ts", ".tsx", ".vue")
        ]

        for file_path in js_files:
            impacts, optimizations = self._analyze_js_file(file_path)
            web_vital_impacts.extend(impacts)
            bundle_optimizations.extend(optimizations)

        # Analyze Python files for backend impact on Web Vitals (TTFB)
        py_files = [f for f in file_paths if f.suffix == ".py"]

        for file_path in py_files:
            impacts = self._analyze_backend_file(file_path)
            web_vital_impacts.extend(impacts)

        return web_vital_impacts, bundle_optimizations

    def _analyze_js_file(
        self, file_path: Path
    ) -> tuple[List[WebVitalImpact], List[BundleOptimization]]:
        """Analyze JavaScript file for Web Vitals and bundle issues.

        Args:
            file_path: JavaScript file to analyze

        Returns:
            Tuple of (impacts, optimizations)
        """
        impacts = []
        optimizations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Detect heavy imports affecting LCP
            large_imports = self._detect_large_imports(content, file_path)
            if large_imports:
                impacts.extend(large_imports)

            # Detect synchronous operations affecting FID
            sync_ops = self._detect_sync_operations(content, file_path)
            if sync_ops:
                impacts.extend(sync_ops)

            # Detect layout shifts (CLS)
            layout_issues = self._detect_layout_shifts(content, file_path)
            if layout_issues:
                impacts.extend(layout_issues)

            # Detect bundle optimization opportunities
            bundle_opts = self._detect_bundle_optimizations(content, file_path)
            if bundle_opts:
                optimizations.extend(bundle_opts)

        except (UnicodeDecodeError, FileNotFoundError):
            pass

        return impacts, optimizations

    def _detect_large_imports(
        self, content: str, file_path: Path
    ) -> List[WebVitalImpact]:
        """Detect large library imports affecting LCP.

        Args:
            content: File content
            file_path: File path

        Returns:
            List of Web Vital impacts
        """
        impacts = []

        # Large libraries that impact LCP
        large_libraries = {
            "moment": {"size": "~70KB", "alternative": "day.js (~2KB)"},
            "lodash": {"size": "~70KB", "alternative": "lodash-es with tree-shaking"},
            "axios": {"size": "~13KB", "alternative": "native fetch API"},
            "jquery": {"size": "~30KB", "alternative": "native DOM APIs"},
        }

        for lib, info in large_libraries.items():
            # Check for direct import
            if re.search(rf"import.*['\"]{lib}['\"]", content) or re.search(
                rf"require\(['\"]{lib}['\"]\)", content
            ):
                impacts.append(
                    WebVitalImpact(
                        metric=WebVitalMetric.LCP,
                        file_path=str(file_path),
                        impact_level=PerformanceImpact.MEDIUM,
                        current_estimate=f"Adding {info['size']} to initial bundle",
                        target_value="< 2.5s for LCP",
                        description=f"Importing large library '{lib}' impacts initial load",
                        suggestions=[
                            f"Replace {lib} with {info['alternative']}",
                            "Use dynamic imports for non-critical code",
                            "Consider code splitting",
                        ],
                    )
                )

        return impacts

    def _detect_sync_operations(
        self, content: str, file_path: Path
    ) -> List[WebVitalImpact]:
        """Detect synchronous operations affecting FID.

        Args:
            content: File content
            file_path: File path

        Returns:
            List of Web Vital impacts
        """
        impacts = []

        # Patterns that block main thread
        blocking_patterns = [
            (r"for\s*\([^)]*\)\s*{[^}]{200,}", "Long synchronous loop"),
            (r"while\s*\([^)]*\)\s*{[^}]{200,}", "Long synchronous while loop"),
            (r"\.map\([^)]{100,}\)", "Complex map operation"),
            (r"JSON\.parse\([^)]+\)", "Synchronous JSON parsing"),
        ]

        for pattern, description in blocking_patterns:
            if re.search(pattern, content, re.DOTALL):
                impacts.append(
                    WebVitalImpact(
                        metric=WebVitalMetric.FID,
                        file_path=str(file_path),
                        impact_level=PerformanceImpact.MEDIUM,
                        target_value="< 100ms for FID",
                        description=f"{description} may block main thread",
                        suggestions=[
                            "Use Web Workers for heavy computations",
                            "Break long tasks into smaller chunks with setTimeout",
                            "Use async/await or requestIdleCallback",
                        ],
                    )
                )
                break  # Only report once per file

        return impacts

    def _detect_layout_shifts(
        self, content: str, file_path: Path
    ) -> List[WebVitalImpact]:
        """Detect potential layout shifts (CLS).

        Args:
            content: File content
            file_path: File path

        Returns:
            List of Web Vital impacts
        """
        impacts = []

        # Patterns that cause layout shifts
        cls_patterns = [
            (
                r"<img\s+(?![^>]*width)[^>]*>",
                "Images without dimensions",
                "Add width and height attributes",
            ),
            (
                r"\.innerHTML\s*=",
                "Dynamic content insertion",
                "Reserve space for dynamic content",
            ),
            (
                r"\.style\.(width|height|top|left)\s*=",
                "Dynamic style changes",
                "Use CSS transforms instead of layout properties",
            ),
        ]

        for pattern, description, suggestion in cls_patterns:
            if re.search(pattern, content):
                impacts.append(
                    WebVitalImpact(
                        metric=WebVitalMetric.CLS,
                        file_path=str(file_path),
                        impact_level=PerformanceImpact.LOW,
                        target_value="< 0.1 for CLS",
                        description=f"{description} may cause layout shifts",
                        suggestions=[
                            suggestion,
                            "Use aspect-ratio CSS property",
                            "Preload fonts to avoid FOIT/FOUT",
                        ],
                    )
                )

        return impacts

    def _detect_bundle_optimizations(
        self, content: str, file_path: Path
    ) -> List[BundleOptimization]:
        """Detect bundle optimization opportunities.

        Args:
            content: File content
            file_path: File path

        Returns:
            List of bundle optimizations
        """
        optimizations = []

        # Tree-shaking opportunities
        if re.search(r"import\s+\*\s+as\s+\w+\s+from", content):
            optimizations.append(
                BundleOptimization(
                    file_path=str(file_path),
                    optimization_type="tree-shaking",
                    impact=PerformanceImpact.MEDIUM,
                    description="Using wildcard import prevents tree-shaking",
                    suggestion=(
                        "Import only needed functions: "
                        "import { specific, functions } from 'module'"
                    ),
                )
            )

        # Dynamic import opportunities
        if re.search(r"import.*react.*Modal", content, re.IGNORECASE) or re.search(
            r"import.*Dialog", content
        ):
            optimizations.append(
                BundleOptimization(
                    file_path=str(file_path),
                    optimization_type="code-splitting",
                    impact=PerformanceImpact.MEDIUM,
                    description="Modal/Dialog components can be lazy-loaded",
                    suggestion=(
                        "Use React.lazy() or dynamic import() "
                        "for modal components"
                    ),
                )
            )

        # Lazy loading opportunities
        heavy_components = ["Chart", "Editor", "Calendar", "Map"]
        for component in heavy_components:
            if re.search(rf"import.*{component}", content):
                optimizations.append(
                    BundleOptimization(
                        file_path=str(file_path),
                        optimization_type="lazy-loading",
                        impact=PerformanceImpact.HIGH,
                        description=f"{component} component is heavy and can be lazy-loaded",
                        suggestion=(
                            f"Lazy load {component} component to reduce initial bundle"
                        ),
                    )
                )

        return optimizations

    def _analyze_backend_file(self, file_path: Path) -> List[WebVitalImpact]:
        """Analyze backend file for TTFB impact.

        Args:
            file_path: Python file to analyze

        Returns:
            List of Web Vital impacts
        """
        impacts = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Check for slow operations in request handlers
            # This is a simplified heuristic
            if "def " in source and any(
                keyword in source.lower()
                for keyword in ["request", "handler", "view", "endpoint"]
            ):
                # Check for slow operations
                slow_ops = []

                if ".sleep(" in source:
                    slow_ops.append("time.sleep() in request handler")

                if re.search(r"for\s+.*\s+in\s+.*\.all\(\)", source):
                    slow_ops.append("Iterating over all database records")

                if slow_ops:
                    impacts.append(
                        WebVitalImpact(
                            metric=WebVitalMetric.TTFB,
                            file_path=str(file_path),
                            impact_level=PerformanceImpact.HIGH,
                            target_value="< 600ms for TTFB",
                            description="Slow operations in request handler affect TTFB",
                            suggestions=[
                                "Use pagination for large datasets",
                                "Add database indexes",
                                "Use caching for expensive operations",
                                "Consider async processing for slow tasks",
                            ],
                        )
                    )

        except (UnicodeDecodeError, FileNotFoundError):
            pass

        return impacts

    def calculate_bundle_savings(
        self, optimizations: List[BundleOptimization]
    ) -> int:
        """Calculate total potential bundle size savings.

        Args:
            optimizations: List of bundle optimizations

        Returns:
            Total potential savings in bytes
        """
        total = 0
        for opt in optimizations:
            if opt.potential_savings:
                total += opt.potential_savings

        return total
