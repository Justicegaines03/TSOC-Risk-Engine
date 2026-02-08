"""
Tests for risk_engine.models — data model construction and defaults.
"""

from risk_engine.models import (
    AnalyzerResult,
    CaseRiskAssessment,
    Observable,
    ObservableRisk,
    RiskScore,
)


class TestObservable:
    def test_required_fields(self):
        obs = Observable(id="1", data_type="ip", value="8.8.8.8")
        assert obs.id == "1"
        assert obs.data_type == "ip"
        assert obs.value == "8.8.8.8"

    def test_defaults(self):
        obs = Observable(id="1", data_type="ip", value="8.8.8.8")
        assert obs.tlp == 2
        assert obs.tags == []


class TestAnalyzerResult:
    def test_required_fields(self):
        r = AnalyzerResult(analyzer_name="VT", level="malicious", score=10.0)
        assert r.analyzer_name == "VT"
        assert r.level == "malicious"
        assert r.score == 10.0

    def test_defaults(self):
        r = AnalyzerResult(analyzer_name="VT", level="safe", score=0.0)
        assert r.namespace == ""
        assert r.predicate == ""
        assert r.raw_value == ""


class TestObservableRisk:
    def test_defaults(self):
        obs = Observable(id="1", data_type="ip", value="1.2.3.4")
        risk = ObservableRisk(observable=obs)
        assert risk.analyzer_results == []
        assert risk.likelihood == 0.0


class TestRiskScore:
    def test_construction(self):
        score = RiskScore(
            likelihood=0.8,
            impact_dollars=100_000,
            ale=80_000,
            risk_level="High",
        )
        assert score.likelihood == 0.8
        assert score.impact_dollars == 100_000
        assert score.ale == 80_000
        assert score.risk_level == "High"


class TestCaseRiskAssessment:
    def test_defaults(self):
        a = CaseRiskAssessment(case_id="~1", case_title="Test")
        assert a.case_severity == 2
        assert a.profile == "b2b"
        assert a.asset_type == "server"
        assert a.sensitivity == "internal"
        assert a.exposure_type == "email_only"
        assert a.observables == []
        assert a.risk_score is None
        assert a.timestamp  # should be a non-empty ISO string

    def test_b2c_profile(self):
        a = CaseRiskAssessment(
            case_id="~2",
            case_title="Consumer Case",
            profile="consumer",
            exposure_type="ssn",
        )
        assert a.profile == "consumer"
        assert a.exposure_type == "ssn"

    def test_timestamp_is_iso(self):
        a = CaseRiskAssessment(case_id="~3", case_title="Test")
        # Should be parseable as ISO format
        from datetime import datetime
        dt = datetime.fromisoformat(a.timestamp)
        assert dt is not None
