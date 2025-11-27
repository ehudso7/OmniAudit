"""
Tests for the Priority Scorer component.
"""

import pytest
from datetime import datetime, timedelta

from omniaudit.harmonizer.priority_scorer import PriorityScorer
from omniaudit.harmonizer.types import Finding, ImpactLevel, PriorityConfig
from omniaudit.models.ai_models import Severity


class TestPriorityScorer:
    """Test suite for PriorityScorer class."""

    @pytest.fixture
    def config(self):
        """Create default priority configuration."""
        return PriorityConfig()

    @pytest.fixture
    def scorer(self, config):
        """Create PriorityScorer instance."""
        return PriorityScorer(config)

    def test_scorer_initialization(self, scorer):
        """Test that PriorityScorer initializes correctly."""
        assert scorer is not None
        assert scorer.config is not None

    def test_severity_scoring(self, scorer):
        """Test that severity affects priority score."""
        critical_finding = Finding(
            id="f1",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.CRITICAL,
            category="security",
            message="Critical security issue",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        low_finding = Finding(
            id="f2",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.LOW,
            category="quality",
            message="Minor style issue",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        findings = [critical_finding, low_finding]
        scores = scorer.score_findings(findings)

        critical_score, _, _ = scores["f1"]
        low_score, _, _ = scores["f2"]

        # Critical should have higher score than low
        assert critical_score > low_score

    def test_business_critical_paths(self):
        """Test that business-critical paths get higher scores."""
        config = PriorityConfig(business_critical_paths=["/src/payment/", "/src/auth/"])
        scorer = PriorityScorer(config)

        critical_path_finding = Finding(
            id="f1",
            analyzer_name="test",
            file_path="/src/payment/checkout.py",
            severity=Severity.MEDIUM,
            category="security",
            message="Issue in payment module",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        normal_finding = Finding(
            id="f2",
            analyzer_name="test",
            file_path="/src/utils/helper.py",
            severity=Severity.MEDIUM,
            category="security",
            message="Issue in utility module",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        findings = [critical_path_finding, normal_finding]
        scores = scorer.score_findings(findings)

        critical_score, _, _ = scores["f1"]
        normal_score, _, _ = scores["f2"]

        # Business-critical path should have higher score
        assert critical_score > normal_score

    def test_frequency_scoring(self, scorer):
        """Test that frequent issues get higher scores."""
        # Create multiple findings with same rule
        findings = [
            Finding(
                id=f"f{i}",
                analyzer_name="test",
                file_path=f"/src/file{i}.py",
                severity=Severity.MEDIUM,
                category="quality",
                rule_id="C001" if i < 5 else "C002",  # C001 appears more frequently
                message="Issue detected",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
            for i in range(7)
        ]

        scores = scorer.score_findings(findings)

        # Findings with frequent rule (C001) should have higher scores
        c001_scores = [scores[f"f{i}"][0] for i in range(5)]
        c002_scores = [scores[f"f{i}"][0] for i in range(5, 7)]

        avg_c001 = sum(c001_scores) / len(c001_scores)
        avg_c002 = sum(c002_scores) / len(c002_scores)

        # More frequent rule should have higher average score
        assert avg_c001 >= avg_c002

    def test_age_scoring(self, scorer):
        """Test that age affects priority score."""
        now = datetime.utcnow()

        new_finding = Finding(
            id="f1",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.MEDIUM,
            category="quality",
            message="New issue",
            timestamp=now.isoformat() + "Z",
        )

        old_finding = Finding(
            id="f2",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.MEDIUM,
            category="quality",
            message="Old issue",
            timestamp=(now - timedelta(days=100)).isoformat() + "Z",
        )

        findings = [new_finding, old_finding]
        scores = scorer.score_findings(findings)

        new_score, _, _ = scores["f1"]
        old_score, _, _ = scores["f2"]

        # Newer findings should have higher score (easier to fix in context)
        assert new_score >= old_score

    def test_impact_level_assignment(self, scorer):
        """Test that impact levels are assigned correctly."""
        high_priority_finding = Finding(
            id="f1",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.CRITICAL,
            category="security",
            message="Critical security vulnerability",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        low_priority_finding = Finding(
            id="f2",
            analyzer_name="test",
            file_path="/tests/test_utils.py",
            severity=Severity.INFO,
            category="style",
            message="Minor style issue in tests",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        findings = [high_priority_finding, low_priority_finding]
        scores = scorer.score_findings(findings)

        _, high_impact, _ = scores["f1"]
        _, low_impact, _ = scores["f2"]

        # Check that impact levels are assigned
        assert high_impact is not None
        assert low_impact is not None

        # High priority should have higher impact
        impact_order = {
            ImpactLevel.CRITICAL: 5,
            ImpactLevel.HIGH: 4,
            ImpactLevel.MEDIUM: 3,
            ImpactLevel.LOW: 2,
            ImpactLevel.NEGLIGIBLE: 1,
        }

        assert impact_order[high_impact] > impact_order[low_impact]

    def test_business_impact_assessment(self, scorer):
        """Test business impact text generation."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/src/payment/billing.py",
                severity=Severity.HIGH,
                category="security",
                message="Security issue in payment",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/src/auth/login.py",
                severity=Severity.HIGH,
                category="security",
                message="Authentication issue",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        scores = scorer.score_findings(findings)

        _, _, payment_impact = scores["f1"]
        _, _, auth_impact = scores["f2"]

        # Both should have business impact assessments
        assert payment_impact is not None
        assert auth_impact is not None
        assert len(payment_impact) > 0
        assert len(auth_impact) > 0

    def test_priority_distribution(self, scorer):
        """Test priority distribution statistics."""
        findings = [
            Finding(
                id=f"f{i}",
                analyzer_name="test",
                file_path=f"/src/file{i}.py",
                severity=Severity.HIGH if i % 2 == 0 else Severity.LOW,
                category="quality",
                message="Finding",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
            for i in range(10)
        ]

        scores = scorer.score_findings(findings)
        distribution = scorer.get_priority_distribution(scores)

        assert "total" in distribution
        assert "by_impact" in distribution
        assert "avg_score" in distribution
        assert "min_score" in distribution
        assert "max_score" in distribution
        assert "score_ranges" in distribution

        assert distribution["total"] == 10
        assert distribution["avg_score"] >= 0
        assert distribution["min_score"] <= distribution["max_score"]

    def test_weight_validation(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError):
            # Weights don't sum to 1.0
            PriorityConfig(
                severity_weight=0.5,
                frequency_weight=0.3,
                impact_weight=0.3,  # Total = 1.1
                age_weight=0.0,
            )

    def test_custom_weights(self):
        """Test scoring with custom weights."""
        # Emphasize severity heavily
        config = PriorityConfig(
            severity_weight=0.8,
            frequency_weight=0.1,
            impact_weight=0.05,
            age_weight=0.05,
        )
        scorer = PriorityScorer(config)

        critical_finding = Finding(
            id="f1",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.CRITICAL,
            category="security",
            message="Critical issue",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        low_finding = Finding(
            id="f2",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.LOW,
            category="quality",
            message="Low issue",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        findings = [critical_finding, low_finding]
        scores = scorer.score_findings(findings)

        critical_score, _, _ = scores["f1"]
        low_score, _, _ = scores["f2"]

        # With heavy severity weighting, difference should be significant
        assert critical_score - low_score > 30

    def test_empty_findings(self, scorer):
        """Test scoring with empty findings list."""
        scores = scorer.score_findings([])

        assert len(scores) == 0

    def test_single_finding(self, scorer):
        """Test scoring with single finding."""
        finding = Finding(
            id="f1",
            analyzer_name="test",
            file_path="/src/main.py",
            severity=Severity.MEDIUM,
            category="quality",
            message="Test finding",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        scores = scorer.score_findings([finding])

        assert len(scores) == 1
        assert "f1" in scores

        score, impact, business_impact = scores["f1"]
        assert 0 <= score <= 100
        assert impact is not None
        assert business_impact is not None
