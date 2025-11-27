"""Color contrast analyzer for WCAG compliance."""

import re
from pathlib import Path
from typing import List, Optional, Tuple

from ..types import ColorContrastResult


class ContrastChecker:
    """Check color contrast ratios for WCAG compliance."""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB.

        Args:
            hex_color: Hex color code (e.g., '#FFFFFF' or 'FFF')

        Returns:
            RGB tuple
        """
        hex_color = hex_color.lstrip("#")

        # Handle shorthand hex
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])

        try:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return (0, 0, 0)  # Default to black on error

    @staticmethod
    def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
        """
        Calculate relative luminance.

        Args:
            rgb: RGB color tuple

        Returns:
            Relative luminance value
        """
        # Convert to sRGB
        rgb_srgb = []
        for val in rgb:
            val = val / 255.0
            if val <= 0.03928:
                val = val / 12.92
            else:
                val = ((val + 0.055) / 1.055) ** 2.4
            rgb_srgb.append(val)

        # Calculate luminance
        return 0.2126 * rgb_srgb[0] + 0.7152 * rgb_srgb[1] + 0.0722 * rgb_srgb[2]

    @staticmethod
    def calculate_contrast_ratio(
        color1: str, color2: str
    ) -> float:
        """
        Calculate contrast ratio between two colors.

        Args:
            color1: First color (hex)
            color2: Second color (hex)

        Returns:
            Contrast ratio
        """
        rgb1 = ContrastChecker.hex_to_rgb(color1)
        rgb2 = ContrastChecker.hex_to_rgb(color2)

        lum1 = ContrastChecker.calculate_luminance(rgb1)
        lum2 = ContrastChecker.calculate_luminance(rgb2)

        # Ensure lighter color is in numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        return (lighter + 0.05) / (darker + 0.05)

    @staticmethod
    def check_contrast(
        foreground: str, background: str, file_path: Optional[str] = None, line_number: Optional[int] = None
    ) -> ColorContrastResult:
        """
        Check if color combination meets WCAG contrast requirements.

        Args:
            foreground: Foreground color (hex)
            background: Background color (hex)
            file_path: Optional file path
            line_number: Optional line number

        Returns:
            Color contrast result
        """
        ratio = ContrastChecker.calculate_contrast_ratio(foreground, background)

        return ColorContrastResult(
            foreground=foreground,
            background=background,
            ratio=round(ratio, 2),
            wcag_aa_normal=ratio >= 4.5,  # WCAG AA normal text
            wcag_aa_large=ratio >= 3.0,  # WCAG AA large text (18pt+)
            wcag_aaa_normal=ratio >= 7.0,  # WCAG AAA normal text
            wcag_aaa_large=ratio >= 4.5,  # WCAG AAA large text
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def extract_colors_from_css(file_path: Path) -> List[ColorContrastResult]:
        """
        Extract and check color combinations from CSS file.

        Args:
            file_path: Path to CSS file

        Returns:
            List of contrast check results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return []

        results = []

        # Simple pattern to find color and background-color pairs
        # This is a simplified approach - a full CSS parser would be more robust
        color_pattern = re.compile(r"color:\s*(#[0-9a-fA-F]{3,6})", re.IGNORECASE)
        bg_pattern = re.compile(
            r"background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})", re.IGNORECASE
        )

        lines = content.split("\n")
        current_rule_colors = {}

        for line_num, line in enumerate(lines, 1):
            # Look for color declarations
            color_match = color_pattern.search(line)
            bg_match = bg_pattern.search(line)

            if color_match:
                current_rule_colors["foreground"] = color_match.group(1)
                current_rule_colors["line"] = line_num

            if bg_match:
                current_rule_colors["background"] = bg_match.group(1)

            # Check if we have both colors in this rule
            if "foreground" in current_rule_colors and "background" in current_rule_colors:
                result = ContrastChecker.check_contrast(
                    current_rule_colors["foreground"],
                    current_rule_colors["background"],
                    str(file_path),
                    current_rule_colors.get("line"),
                )
                results.append(result)
                current_rule_colors = {}

            # Reset on closing brace
            if "}" in line:
                current_rule_colors = {}

        return results

    @staticmethod
    def extract_colors_from_html(file_path: Path) -> List[ColorContrastResult]:
        """
        Extract and check inline color styles from HTML.

        Args:
            file_path: Path to HTML file

        Returns:
            List of contrast check results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return []

        results = []

        # Find inline styles with color combinations
        style_pattern = re.compile(
            r'style="([^"]*(?:color|background)[^"]*)"', re.IGNORECASE
        )

        for match in style_pattern.finditer(content):
            style = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            # Extract colors from style
            color_match = re.search(r"color:\s*(#[0-9a-fA-F]{3,6})", style, re.IGNORECASE)
            bg_match = re.search(
                r"background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})", style, re.IGNORECASE
            )

            if color_match and bg_match:
                result = ContrastChecker.check_contrast(
                    color_match.group(1),
                    bg_match.group(1),
                    str(file_path),
                    line_num,
                )
                results.append(result)

        return results
