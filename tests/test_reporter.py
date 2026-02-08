"""
Tests for risk_engine.reporter — B2B and B2C report generation.
"""

import pytest

from risk_engine.calculator import score_case
from risk_engine.reporter import generate_report, _recommendations, _b2c_recommendations


# -----------------------------------------------------------------------
# B2B Report
# -----------------------------------------------------------------------

class TestB2BReport:
    def test_report_contains_title(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "# Risk Assessment Report" in report
        assert b2b_assessment.case_title in report

    def test_report_contains_ale(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "ALE" in report
        assert "Annualized Loss" in report

    def test_report_contains_asset_type(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "Asset Type" in report
        assert "server" in report

    def test_report_contains_sensitivity(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "Sensitivity" in report
        assert "confidential" in report

    def test_report_contains_profile_label(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "Business (B2B)" in report

    def test_report_contains_observables(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "Observable Breakdown" in report
        assert "203.0.113.42" in report

    def test_report_contains_recommendations(self, b2b_assessment):
        score_case(b2b_assessment)
        report = generate_report(b2b_assessment)
        assert "Recommended" in report
        assert "Actions" in report


# -----------------------------------------------------------------------
# B2C Consumer Report
# -----------------------------------------------------------------------

class TestB2CReport:
    def test_report_title(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "Consumer Identity-Theft" in report

    def test_report_contains_recovery_difficulty(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "Recovery Difficulty" in report
        assert "/ 100" in report

    def test_report_contains_exposure_type(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "Exposure Type" in report
        assert "ssn" in report

    def test_report_contains_consumer_profile(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "Consumer (B2C)" in report

    def test_report_does_not_contain_ale(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "Annualized Loss" not in report

    def test_report_contains_consumer_recommendations(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "Recovery Actions" in report

    def test_report_contains_observables(self, b2c_assessment):
        score_case(b2c_assessment)
        report = generate_report(b2c_assessment)
        assert "victim@example.com" in report


# -----------------------------------------------------------------------
# Unscored Case
# -----------------------------------------------------------------------

class TestUnscoredReport:
    def test_error_message_when_not_scored(self):
        from risk_engine.models import CaseRiskAssessment
        assessment = CaseRiskAssessment(case_id="~999", case_title="Unscored")
        report = generate_report(assessment)
        assert "Error" in report
        assert "not been scored" in report


# -----------------------------------------------------------------------
# Recommendation Functions
# -----------------------------------------------------------------------

class TestRecommendations:
    @pytest.mark.parametrize("level", ["Critical", "High", "Medium", "Low", "Info"])
    def test_b2b_recommendations_return_list(self, level):
        recs = _recommendations(level)
        assert isinstance(recs, list)
        assert len(recs) > 0

    @pytest.mark.parametrize("level", ["Critical", "High", "Medium", "Low", "Info"])
    def test_b2c_recommendations_return_list(self, level):
        recs = _b2c_recommendations(level)
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_b2c_critical_includes_credit_freeze(self):
        recs = _b2c_recommendations("Critical")
        combined = " ".join(recs).lower()
        assert "freeze credit" in combined

    def test_b2c_critical_includes_ftc(self):
        recs = _b2c_recommendations("Critical")
        combined = " ".join(recs).lower()
        assert "ftc" in combined or "identitytheft.gov" in combined

    def test_unknown_level_returns_fallback(self):
        recs = _recommendations("Unknown")
        assert len(recs) > 0
        recs_b2c = _b2c_recommendations("Unknown")
        assert len(recs_b2c) > 0
