"""
Auto-Fix Generator with Confidence Scoring.

This module generates automatic fixes for findings with confidence scores
and validation steps.
"""

import hashlib
from typing import List, Optional

from omniaudit.harmonizer.types import (
    AutoFix,
    ConfidenceLevel,
    Finding,
    FixGenerationConfig,
    FixStrategy,
    RootCauseInfo,
)

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class FixGenerator:
    """
    Generates automatic fixes for findings using AI and template-based approaches.

    Provides:
    - Template-based fixes for common issues
    - AI-generated fixes for complex problems
    - Confidence scoring for each fix
    - Validation steps and prerequisites
    """

    # Fix templates for common issues
    FIX_TEMPLATES = {
        # Security fixes
        "hardcoded_credential": {
            "strategy": FixStrategy.SUGGESTED,
            "description": "Move hardcoded credentials to environment variables",
            "base_confidence": 0.85,
            "template": "Replace hardcoded value with environment variable lookup",
            "risks": ["Ensure environment variable is set in all environments"],
            "prerequisites": ["Set up environment variable management"],
            "validation": [
                "Verify environment variable is loaded",
                "Test application with new configuration",
            ],
        },
        "sql_injection": {
            "strategy": FixStrategy.SUGGESTED,
            "description": "Use parameterized queries to prevent SQL injection",
            "base_confidence": 0.90,
            "template": "Replace string concatenation with parameterized query",
            "risks": ["Ensure query syntax is preserved", "Test with various inputs"],
            "prerequisites": ["Understand current query logic"],
            "validation": [
                "Test with malicious inputs",
                "Verify query results are correct",
                "Check performance impact",
            ],
        },
        # Code quality fixes
        "high_complexity": {
            "strategy": FixStrategy.MANUAL,
            "description": "Refactor to reduce cyclomatic complexity",
            "base_confidence": 0.60,
            "template": "Break down into smaller functions with single responsibilities",
            "risks": ["May change code behavior if not careful"],
            "prerequisites": ["Understand current code logic", "Have good test coverage"],
            "validation": ["Run all tests", "Review refactored code"],
        },
        "duplicate_code": {
            "strategy": FixStrategy.SUGGESTED,
            "description": "Extract duplicated code into shared function",
            "base_confidence": 0.75,
            "template": "Create new function and replace duplicates with calls",
            "risks": ["Ensure all duplicates have same behavior"],
            "prerequisites": ["Identify all duplicate instances"],
            "validation": ["Test each replacement", "Verify no behavior change"],
        },
        "missing_docstring": {
            "strategy": FixStrategy.AUTOMATED,
            "description": "Add docstring to function/class",
            "base_confidence": 0.95,
            "template": "Generate docstring from function signature and implementation",
            "risks": [],
            "prerequisites": [],
            "validation": ["Verify docstring accuracy"],
        },
        # Style fixes
        "line_too_long": {
            "strategy": FixStrategy.AUTOMATED,
            "description": "Break long line into multiple lines",
            "base_confidence": 0.90,
            "template": "Split line at logical break points",
            "risks": [],
            "prerequisites": [],
            "validation": ["Verify syntax is valid", "Run code formatter"],
        },
        "missing_whitespace": {
            "strategy": FixStrategy.AUTOMATED,
            "description": "Add required whitespace",
            "base_confidence": 0.98,
            "template": "Add whitespace according to style guide",
            "risks": [],
            "prerequisites": [],
            "validation": ["Run linter"],
        },
    }

    def __init__(self, config: FixGenerationConfig, anthropic_api_key: Optional[str] = None):
        """
        Initialize fix generator.

        Args:
            config: Fix generation configuration
            anthropic_api_key: Optional Anthropic API key for AI-generated fixes
        """
        self.config = config
        self._client: Optional[Anthropic] = None

        if config.use_ai and ANTHROPIC_AVAILABLE and anthropic_api_key:
            self._client = Anthropic(api_key=anthropic_api_key)

    def generate_fixes(
        self,
        finding: Finding,
        root_cause: Optional[RootCauseInfo] = None,
    ) -> List[AutoFix]:
        """
        Generate fixes for a finding.

        Args:
            finding: Finding to generate fixes for
            root_cause: Optional root cause analysis

        Returns:
            List of AutoFix suggestions
        """
        if not self.config.enabled:
            return []

        fixes = []

        # Try template-based fixes first
        template_fixes = self._generate_template_fixes(finding, root_cause)
        fixes.extend(template_fixes)

        # Try AI-generated fixes if enabled and not enough fixes
        if self.config.use_ai and self._client and len(fixes) < self.config.max_fixes_per_finding:
            ai_fixes = self._generate_ai_fixes(finding, root_cause)
            fixes.extend(ai_fixes)

        # Filter by confidence threshold
        fixes = [f for f in fixes if f.confidence_score >= self.config.min_confidence]

        # Limit to max fixes
        fixes = fixes[: self.config.max_fixes_per_finding]

        return fixes

    def _generate_template_fixes(
        self, finding: Finding, root_cause: Optional[RootCauseInfo] = None
    ) -> List[AutoFix]:
        """
        Generate fixes using predefined templates.

        Args:
            finding: Finding to fix
            root_cause: Optional root cause

        Returns:
            List of template-based fixes
        """
        fixes = []

        # Try to match finding to a template
        message_lower = finding.message.lower()
        rule_id_lower = (finding.rule_id or "").lower()

        for template_key, template in self.FIX_TEMPLATES.items():
            # Check if template applies
            if self._template_applies(template_key, message_lower, rule_id_lower):
                fix = self._build_fix_from_template(
                    finding, template_key, template, root_cause
                )
                fixes.append(fix)

        return fixes

    def _template_applies(self, template_key: str, message: str, rule_id: str) -> bool:
        """
        Check if a template applies to a finding.

        Args:
            template_key: Template identifier
            message: Finding message (lowercase)
            rule_id: Finding rule ID (lowercase)

        Returns:
            True if template applies
        """
        # Simple keyword matching
        keywords = template_key.replace("_", " ").split()

        # Check if any keyword appears in message or rule ID
        return any(keyword in message or keyword in rule_id for keyword in keywords)

    def _build_fix_from_template(
        self,
        finding: Finding,
        template_key: str,
        template: dict,
        root_cause: Optional[RootCauseInfo] = None,
    ) -> AutoFix:
        """
        Build an AutoFix from a template.

        Args:
            finding: Finding to fix
            template_key: Template key
            template: Template data
            root_cause: Optional root cause

        Returns:
            AutoFix instance
        """
        # Generate unique fix ID
        fix_id = self._generate_fix_id(finding.id, template_key)

        # Get confidence level
        confidence_score = template["base_confidence"]

        # Adjust confidence based on root cause
        if root_cause and root_cause.confidence > 0.7:
            confidence_score = min(1.0, confidence_score + 0.05)

        confidence_level = self._score_to_level(confidence_score)

        # Estimate effort
        effort = self._estimate_effort(finding, template["strategy"])

        return AutoFix(
            fix_id=fix_id,
            finding_id=finding.id,
            strategy=template["strategy"],
            description=template["description"],
            code_change=None,  # Template fixes don't include actual code
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            estimated_effort_minutes=effort,
            risks=template.get("risks", []),
            prerequisites=template.get("prerequisites", []),
            validation_steps=template.get("validation", []),
        )

    def _generate_ai_fixes(
        self, finding: Finding, root_cause: Optional[RootCauseInfo] = None
    ) -> List[AutoFix]:
        """
        Generate fixes using AI.

        Args:
            finding: Finding to fix
            root_cause: Optional root cause

        Returns:
            List of AI-generated fixes
        """
        if not self._client:
            return []

        try:
            # Build prompt
            prompt = self._build_fix_prompt(finding, root_cause)

            # Call API
            response = self._client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text
            return self._parse_ai_fix_response(response_text, finding)

        except Exception:
            # Return empty list on error
            return []

    def _build_fix_prompt(self, finding: Finding, root_cause: Optional[RootCauseInfo]) -> str:
        """
        Build prompt for AI fix generation.

        Args:
            finding: Finding to fix
            root_cause: Optional root cause

        Returns:
            Prompt string
        """
        prompt = f"""Generate a fix for this code issue.

**Finding:**
- Category: {finding.category}
- Severity: {finding.severity}
- Message: {finding.message}
- File: {finding.file_path}
- Line: {finding.line_number or 'N/A'}
"""

        if finding.code_snippet:
            prompt += f"\n**Code:**\n```\n{finding.code_snippet}\n```\n"

        if root_cause:
            prompt += f"\n**Root Cause:** {root_cause.primary_cause}\n"

        prompt += """
**Task:**
Suggest 1-2 practical fixes. For each fix, provide:

FIX 1:
DESCRIPTION: [Brief description of the fix]
STRATEGY: [AUTOMATED/SUGGESTED/MANUAL]
CONFIDENCE: [0.0-1.0 confidence score]
EFFORT_MINUTES: [Estimated minutes to implement]
RISKS: [Comma-separated list of risks]
VALIDATION: [Comma-separated list of validation steps]

Be practical and specific. Focus on fixes that can realistically be implemented.
"""

        return prompt

    def _parse_ai_fix_response(self, response: str, finding: Finding) -> List[AutoFix]:
        """
        Parse AI fix response into AutoFix objects.

        Args:
            response: AI response
            finding: Original finding

        Returns:
            List of AutoFix objects
        """
        fixes = []

        # Split by fix sections
        fix_sections = response.split("FIX ")
        for section in fix_sections[1:]:  # Skip first empty section
            try:
                fix = self._parse_fix_section(section, finding)
                if fix:
                    fixes.append(fix)
            except Exception:
                continue

        return fixes

    def _parse_fix_section(self, section: str, finding: Finding) -> Optional[AutoFix]:
        """
        Parse a single fix section.

        Args:
            section: Fix section text
            finding: Original finding

        Returns:
            AutoFix if successful, None otherwise
        """
        lines = section.strip().split("\n")
        data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                data[key] = value.strip()

        # Extract required fields
        description = data.get("description", "AI-generated fix")
        strategy_str = data.get("strategy", "SUGGESTED").upper()
        confidence_str = data.get("confidence", "0.7")
        effort_str = data.get("effort_minutes", "30")

        # Parse strategy
        try:
            strategy = FixStrategy[strategy_str]
        except (KeyError, ValueError):
            strategy = FixStrategy.SUGGESTED

        # Parse confidence
        try:
            confidence_score = float(confidence_str)
        except ValueError:
            confidence_score = 0.7

        # Parse effort
        try:
            effort = int(effort_str)
        except ValueError:
            effort = 30

        # Parse risks and validation
        risks = [r.strip() for r in data.get("risks", "").split(",") if r.strip()]
        validation = [v.strip() for v in data.get("validation", "").split(",") if v.strip()]

        # Generate fix ID
        fix_id = self._generate_fix_id(finding.id, "ai_fix")

        return AutoFix(
            fix_id=fix_id,
            finding_id=finding.id,
            strategy=strategy,
            description=description,
            code_change=None,
            confidence_score=confidence_score,
            confidence_level=self._score_to_level(confidence_score),
            estimated_effort_minutes=effort,
            risks=risks[:5],
            prerequisites=[],
            validation_steps=validation[:5],
        )

    def _generate_fix_id(self, finding_id: str, template_key: str) -> str:
        """
        Generate unique fix ID.

        Args:
            finding_id: Finding ID
            template_key: Template or fix type

        Returns:
            Unique fix ID
        """
        combined = f"{finding_id}:{template_key}"
        hash_digest = hashlib.md5(combined.encode()).hexdigest()[:12]
        return f"fix_{hash_digest}"

    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """
        Convert confidence score to level.

        Args:
            score: Confidence score (0.0-1.0)

        Returns:
            ConfidenceLevel
        """
        if score >= 0.90:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.75:
            return ConfidenceLevel.HIGH
        elif score >= 0.50:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _estimate_effort(self, finding: Finding, strategy: FixStrategy) -> int:
        """
        Estimate effort in minutes.

        Args:
            finding: Finding to fix
            strategy: Fix strategy

        Returns:
            Estimated minutes
        """
        # Base effort by strategy
        base_effort = {
            FixStrategy.AUTOMATED: 5,
            FixStrategy.SUGGESTED: 15,
            FixStrategy.MANUAL: 60,
            FixStrategy.INFEASIBLE: 0,
        }

        effort = base_effort.get(strategy, 30)

        # Adjust by severity
        if finding.severity.value in ["critical", "high"]:
            effort = int(effort * 1.5)

        return effort

    def get_auto_applicable_fixes(self, fixes: List[AutoFix]) -> List[AutoFix]:
        """
        Get fixes that can be automatically applied.

        Args:
            fixes: List of fixes

        Returns:
            Fixes that meet auto-apply threshold
        """
        return [
            fix
            for fix in fixes
            if fix.confidence_score >= self.config.auto_apply_threshold
            and fix.strategy == FixStrategy.AUTOMATED
        ]
