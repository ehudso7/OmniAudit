"""
Root Cause Analyzer using AI and Heuristics.

This module identifies root causes of findings using AI-powered analysis
and heuristic-based pattern recognition.
"""

import os
from typing import List, Optional

from omniaudit.harmonizer.types import Finding, RootCauseConfig, RootCauseInfo

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class RootCauseAnalyzer:
    """
    Analyzes findings to identify root causes using AI and heuristics.

    Uses both AI-powered analysis (when available) and rule-based heuristics
    to identify underlying causes of issues rather than just symptoms.
    """

    # Heuristic patterns for common root causes
    ROOT_CAUSE_PATTERNS = {
        "lack_of_input_validation": [
            "injection",
            "xss",
            "sql injection",
            "command injection",
            "path traversal",
        ],
        "insufficient_error_handling": [
            "unhandled exception",
            "error not caught",
            "missing try-catch",
            "unchecked error",
        ],
        "insecure_configuration": [
            "hardcoded",
            "default password",
            "exposed credentials",
            "insecure default",
        ],
        "poor_code_organization": [
            "high complexity",
            "too many lines",
            "god object",
            "long method",
            "duplicate code",
        ],
        "missing_tests": [
            "no tests",
            "untested",
            "low coverage",
            "missing test case",
        ],
        "dependency_issues": [
            "vulnerable dependency",
            "outdated package",
            "deprecated",
            "unmaintained",
        ],
        "race_condition": [
            "thread safety",
            "concurrent access",
            "synchronization",
            "atomic operation",
        ],
        "memory_management": [
            "memory leak",
            "buffer overflow",
            "dangling pointer",
            "resource leak",
        ],
    }

    def __init__(self, config: RootCauseConfig, anthropic_api_key: Optional[str] = None):
        """
        Initialize root cause analyzer.

        Args:
            config: Root cause analysis configuration
            anthropic_api_key: Optional Anthropic API key for AI analysis
        """
        self.config = config
        self._client: Optional[Anthropic] = None

        if config.use_ai and ANTHROPIC_AVAILABLE and anthropic_api_key:
            self._client = Anthropic(api_key=anthropic_api_key)

    def analyze(
        self, finding: Finding, correlated_findings: Optional[List[Finding]] = None
    ) -> Optional[RootCauseInfo]:
        """
        Analyze a finding to identify its root cause.

        Args:
            finding: Finding to analyze
            correlated_findings: Optional list of correlated findings

        Returns:
            RootCauseInfo if root cause identified, None otherwise
        """
        if not self.config.enabled:
            return None

        # Try AI analysis first if available
        if self.config.use_ai and self._client:
            root_cause = self._analyze_with_ai(finding, correlated_findings)
            if root_cause and root_cause.confidence >= self.config.min_confidence:
                return root_cause

        # Fallback to heuristic analysis
        return self._analyze_with_heuristics(finding, correlated_findings)

    def _analyze_with_ai(
        self, finding: Finding, correlated_findings: Optional[List[Finding]] = None
    ) -> Optional[RootCauseInfo]:
        """
        Use AI to analyze root cause.

        Args:
            finding: Finding to analyze
            correlated_findings: Correlated findings for context

        Returns:
            RootCauseInfo if successful, None otherwise
        """
        if not self._client:
            return None

        try:
            # Build prompt
            prompt = self._build_ai_prompt(finding, correlated_findings)

            # Call Anthropic API
            response = self._client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text

            # Extract root cause from response
            return self._parse_ai_response(response_text, finding)

        except Exception:
            # Fall back to heuristics on error
            return None

    def _build_ai_prompt(
        self, finding: Finding, correlated_findings: Optional[List[Finding]] = None
    ) -> str:
        """
        Build prompt for AI root cause analysis.

        Args:
            finding: Finding to analyze
            correlated_findings: Correlated findings

        Returns:
            Prompt string
        """
        prompt = f"""Analyze this code quality finding to identify its root cause.

**Finding Details:**
- Category: {finding.category}
- Severity: {finding.severity}
- File: {finding.file_path}
- Line: {finding.line_number or 'N/A'}
- Message: {finding.message}
- Rule ID: {finding.rule_id or 'N/A'}
"""

        if finding.code_snippet:
            prompt += f"\n**Code Snippet:**\n```\n{finding.code_snippet}\n```\n"

        if correlated_findings:
            prompt += f"\n**Correlated Findings ({len(correlated_findings)}):**\n"
            for cf in correlated_findings[:3]:  # Limit to 3 for brevity
                prompt += f"- {cf.category}: {cf.message} ({cf.file_path})\n"

        prompt += """
**Task:**
Identify the root cause of this issue. Consider:
1. Is this a symptom of a deeper problem?
2. What underlying issue caused this?
3. Are there related patterns in the codebase?

Respond in this format:
ROOT_CAUSE: [One sentence describing the root cause]
CONTRIBUTING_FACTORS: [Comma-separated list of contributing factors]
EVIDENCE: [Key evidence supporting this root cause]
CONFIDENCE: [0.0-1.0 confidence score]
RELATED_PATTERNS: [Common patterns that might exist elsewhere]
"""

        return prompt

    def _parse_ai_response(self, response: str, finding: Finding) -> Optional[RootCauseInfo]:
        """
        Parse AI response into RootCauseInfo.

        Args:
            response: AI response text
            finding: Original finding

        Returns:
            RootCauseInfo if parsing successful, None otherwise
        """
        try:
            lines = response.strip().split("\n")
            data = {}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    data[key] = value.strip()

            # Extract fields
            primary_cause = data.get("root_cause", "Unknown root cause")
            factors = [
                f.strip()
                for f in data.get("contributing_factors", "").split(",")
                if f.strip()
            ]
            evidence = [e.strip() for e in data.get("evidence", "").split(",") if e.strip()]
            confidence_str = data.get("confidence", "0.5")
            patterns = [
                p.strip() for p in data.get("related_patterns", "").split(",") if p.strip()
            ]

            # Parse confidence
            try:
                confidence = float(confidence_str)
            except ValueError:
                confidence = 0.5

            return RootCauseInfo(
                primary_cause=primary_cause,
                contributing_factors=factors[:5],  # Limit to 5
                evidence=evidence[:5],
                confidence=confidence,
                related_patterns=patterns[:5],
            )

        except Exception:
            return None

    def _analyze_with_heuristics(
        self, finding: Finding, correlated_findings: Optional[List[Finding]] = None
    ) -> Optional[RootCauseInfo]:
        """
        Use heuristic rules to identify root cause.

        Args:
            finding: Finding to analyze
            correlated_findings: Correlated findings

        Returns:
            RootCauseInfo based on heuristics
        """
        message_lower = finding.message.lower()

        # Check each root cause pattern
        for root_cause, keywords in self.ROOT_CAUSE_PATTERNS.items():
            if any(keyword in message_lower for keyword in keywords):
                # Found a match
                return self._build_heuristic_root_cause(
                    root_cause, finding, correlated_findings
                )

        # No specific pattern matched, create generic root cause
        return self._build_generic_root_cause(finding, correlated_findings)

    def _build_heuristic_root_cause(
        self,
        root_cause_type: str,
        finding: Finding,
        correlated_findings: Optional[List[Finding]] = None,
    ) -> RootCauseInfo:
        """
        Build RootCauseInfo from heuristic pattern match.

        Args:
            root_cause_type: Type of root cause identified
            finding: Original finding
            correlated_findings: Correlated findings

        Returns:
            RootCauseInfo
        """
        # Map root cause types to descriptions
        descriptions = {
            "lack_of_input_validation": "Insufficient input validation and sanitization",
            "insufficient_error_handling": "Inadequate error handling and exception management",
            "insecure_configuration": "Insecure configuration or hardcoded credentials",
            "poor_code_organization": "Poor code organization and high complexity",
            "missing_tests": "Insufficient test coverage",
            "dependency_issues": "Vulnerable or outdated dependencies",
            "race_condition": "Potential race condition or concurrency issue",
            "memory_management": "Memory management or resource leak issue",
        }

        primary_cause = descriptions.get(
            root_cause_type, f"Issue related to {root_cause_type.replace('_', ' ')}"
        )

        # Build contributing factors
        contributing_factors = [f"{finding.category} category issue"]

        if finding.severity.value in ["critical", "high"]:
            contributing_factors.append("High severity indicates systemic problem")

        if correlated_findings and len(correlated_findings) > 2:
            contributing_factors.append(
                f"Multiple related issues found ({len(correlated_findings)} correlated)"
            )

        # Build evidence
        evidence = [f"Finding message: {finding.message[:100]}"]

        if finding.rule_id:
            evidence.append(f"Rule {finding.rule_id} triggered")

        if finding.code_snippet:
            evidence.append("Code snippet indicates problematic pattern")

        # Confidence based on pattern strength
        confidence = 0.7  # Heuristic confidence is moderate

        # Related patterns
        related_patterns = [
            f"Similar {root_cause_type.replace('_', ' ')} issues may exist elsewhere"
        ]

        if finding.file_path:
            directory = os.path.dirname(finding.file_path)
            related_patterns.append(f"Check other files in {directory}")

        return RootCauseInfo(
            primary_cause=primary_cause,
            contributing_factors=contributing_factors[:5],
            evidence=evidence[:5],
            confidence=confidence,
            related_patterns=related_patterns[:5],
        )

    def _build_generic_root_cause(
        self, finding: Finding, correlated_findings: Optional[List[Finding]] = None
    ) -> RootCauseInfo:
        """
        Build generic root cause when no specific pattern matches.

        Args:
            finding: Finding to analyze
            correlated_findings: Correlated findings

        Returns:
            Generic RootCauseInfo
        """
        primary_cause = f"{finding.category.title()} issue: {finding.message[:80]}"

        contributing_factors = [
            f"Detected by analyzer: {finding.analyzer_name}",
        ]

        if correlated_findings:
            contributing_factors.append(f"{len(correlated_findings)} correlated findings")

        evidence = [f"Finding in {finding.file_path}"]

        if finding.line_number:
            evidence.append(f"Line {finding.line_number}")

        # Lower confidence for generic analysis
        confidence = 0.5

        related_patterns = [f"Review similar {finding.category} issues"]

        return RootCauseInfo(
            primary_cause=primary_cause,
            contributing_factors=contributing_factors[:5],
            evidence=evidence[:5],
            confidence=confidence,
            related_patterns=related_patterns[:5],
        )

    def analyze_batch(
        self, findings: List[Finding], correlations: dict[str, List[str]]
    ) -> dict[str, Optional[RootCauseInfo]]:
        """
        Analyze multiple findings for root causes.

        Args:
            findings: List of findings to analyze
            correlations: Map of finding IDs to correlated finding IDs

        Returns:
            Dict mapping finding IDs to root cause info
        """
        # Create finding lookup
        finding_map = {f.id: f for f in findings}

        results = {}
        for finding in findings:
            # Get correlated findings
            corr_ids = correlations.get(finding.id, [])
            corr_findings = [finding_map[cid] for cid in corr_ids if cid in finding_map]

            # Analyze
            root_cause = self.analyze(finding, corr_findings)
            results[finding.id] = root_cause

        return results
