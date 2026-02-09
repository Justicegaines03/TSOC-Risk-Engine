"""
Tests for risk_engine.calculator — B2B and B2C scoring paths.
"""

import pytest

from risk_engine.calculator import (
    classify_risk,
    compute_impact,
    compute_likelihood,
    score_case,
    score_observable,
)
from risk_engine.models import AnalyzerResult, ObservableRisk


# -----------------------------------------------------------------------
# compute_likelihood
# -----------------------------------------------------------------------

class TestComputeLikelihood:
    def test_empty_results(self):
        assert compute_likelihood([]) == 0.0

    def test_single_malicious(self, malicious_result):
        lh = compute_likelihood([malicious_result])
        assert lh == 1.0

    def test_single_safe(self, safe_result):
        lh = compute_likelihood([safe_result])
        assert lh == pytest.approx(0.1)

    def test_single_info(self, info_result):
        lh = compute_likelihood([info_result])
        assert lh == 0.0

    def test_mixed_verdicts(self, malicious_result, safe_result):
        lh = compute_likelihood([malicious_result, safe_result])
        # avg of 1.0 and 0.1 = 0.55, no consensus boost (only 1 malicious)
        assert lh == pytest.approx(0.55)

    def test_consensus_boost(self):
        """Two independent malicious analyzers should trigger the 1.25x boost."""
        results = [
            AnalyzerResult(analyzer_name="VT", level="malicious", score=10.0),
            AnalyzerResult(analyzer_name="HIBP", level="malicious", score=5.0),
        ]
        lh = compute_likelihood(results)
        # avg = 1.0, boosted to 1.25, capped at 1.0
        assert lh == 1.0

    def test_consensus_boost_with_mixed(self):
        """Consensus boost applies even with non-malicious results in the mix."""
        results = [
            AnalyzerResult(analyzer_name="VT", level="malicious", score=10.0),
            AnalyzerResult(analyzer_name="HIBP", level="malicious", score=5.0),
            AnalyzerResult(analyzer_name="Whois", level="info", score=0.0),
        ]
        lh = compute_likelihood(results)
        # avg = (1.0 + 1.0 + 0.0) / 3 = 0.6667, boosted to 0.8333
        assert lh == pytest.approx(0.8333, abs=0.01)

    def test_no_consensus_with_single_malicious(self, malicious_result, info_result):
        lh = compute_likelihood([malicious_result, info_result])
        # avg = 0.5, only 1 malicious analyzer — no boost
        assert lh == pytest.approx(0.5)

    def test_capped_at_one(self):
        """Likelihood should never exceed 1.0 even with boost."""
        results = [
            AnalyzerResult(analyzer_name="VT", level="malicious", score=10.0),
            AnalyzerResult(analyzer_name="HIBP", level="malicious", score=5.0),
            AnalyzerResult(analyzer_name="Abuse", level="malicious", score=5.0),
        ]
        lh = compute_likelihood(results)
        assert lh <= 1.0


# -----------------------------------------------------------------------
# compute_impact — B2B
# -----------------------------------------------------------------------

class TestComputeImpactB2B:
    def test_server_internal(self):
        impact = compute_impact("server", "internal", profile="b2b")
        assert impact == 50_000 * 2.0

    def test_workstation_public(self):
        impact = compute_impact("workstation", "public", profile="b2b")
        assert impact == 5_000 * 1.0

    def test_database_restricted(self):
        impact = compute_impact("database", "restricted", profile="b2b")
        assert impact == 500_000 * 10.0

    def test_critical_infra_confidential(self):
        impact = compute_impact("critical_infra", "confidential", profile="b2b")
        assert impact == 2_000_000 * 5.0

    def test_unknown_asset_uses_default(self):
        impact = compute_impact("unknown_thing", "internal", profile="b2b")
        # Falls back to DEFAULT_ASSET_VALUE (50000) * 2.0
        assert impact == 50_000 * 2.0


# -----------------------------------------------------------------------
# compute_impact — B2C
# -----------------------------------------------------------------------

class TestComputeImpactB2C:
    def test_email_only(self):
        impact = compute_impact("", "", profile="consumer", exposure_type="email_only")
        assert impact == 15.0

    def test_ssn(self):
        impact = compute_impact("", "", profile="consumer", exposure_type="ssn")
        assert impact == 85.0

    def test_ssn_and_dl(self):
        impact = compute_impact("", "", profile="consumer", exposure_type="ssn_and_dl")
        assert impact == 95.0

    def test_bank_account(self):
        impact = compute_impact("", "", profile="consumer", exposure_type="bank_account")
        assert impact == 60.0

    def test_unknown_exposure_uses_default(self):
        impact = compute_impact("", "", profile="consumer", exposure_type="unknown")
        # Falls back to DEFAULT_EXPOSURE_TYPE ("email_only") = 15
        assert impact == 15.0


# -----------------------------------------------------------------------
# classify_risk — B2B
# -----------------------------------------------------------------------

class TestClassifyRiskB2B:
    def test_critical(self):
        assert classify_risk(500_000, profile="b2b") == "Critical"
        assert classify_risk(999_999, profile="b2b") == "Critical"

    def test_high(self):
        assert classify_risk(100_000, profile="b2b") == "High"
        assert classify_risk(499_999, profile="b2b") == "High"

    def test_medium(self):
        assert classify_risk(10_000, profile="b2b") == "Medium"

    def test_low(self):
        assert classify_risk(1_000, profile="b2b") == "Low"

    def test_info(self):
        assert classify_risk(999, profile="b2b") == "Info"
        assert classify_risk(0, profile="b2b") == "Info"


# -----------------------------------------------------------------------
# classify_risk — B2C
# -----------------------------------------------------------------------

class TestClassifyRiskB2C:
    def test_critical(self):
        assert classify_risk(80, profile="consumer") == "Critical"
        assert classify_risk(95, profile="consumer") == "Critical"

    def test_high(self):
        assert classify_risk(60, profile="consumer") == "High"
        assert classify_risk(79, profile="consumer") == "High"

    def test_medium(self):
        assert classify_risk(35, profile="consumer") == "Medium"

    def test_low(self):
        assert classify_risk(15, profile="consumer") == "Low"

    def test_info(self):
        assert classify_risk(14, profile="consumer") == "Info"
        assert classify_risk(0, profile="consumer") == "Info"


# -----------------------------------------------------------------------
# score_case — end-to-end
# -----------------------------------------------------------------------

class TestScoreCase:
    def test_b2b_score(self, b2b_assessment):
        risk = score_case(b2b_assessment)
        assert risk.likelihood > 0.0
        assert risk.impact_dollars == 50_000 * 5.0  # server * confidential
        assert risk.ale == pytest.approx(risk.likelihood * risk.impact_dollars, abs=1.0)
        assert risk.risk_level in ("Critical", "High", "Medium", "Low", "Info")
        assert b2b_assessment.risk_score is risk

    def test_b2c_score(self, b2c_assessment):
        risk = score_case(b2c_assessment)
        assert risk.likelihood > 0.0
        assert risk.impact_dollars == 85.0  # SSN exposure weight
        assert risk.ale == pytest.approx(risk.likelihood * 85.0, abs=1.0)
        assert risk.risk_level in ("Critical", "High", "Medium", "Low", "Info")

    def test_empty_case(self, empty_assessment):
        risk = score_case(empty_assessment)
        assert risk.likelihood == 0.0
        assert risk.ale == 0.0
        assert risk.risk_level == "Info"

    def test_score_observable_sets_likelihood(self, ip_observable, malicious_result):
        obs_risk = ObservableRisk(
            observable=ip_observable,
            analyzer_results=[malicious_result],
        )
        lh = score_observable(obs_risk)
        assert lh == obs_risk.likelihood
        assert lh > 0.0
