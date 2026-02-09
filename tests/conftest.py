"""
Shared test fixtures for the SOC Risk Engine test suite.

Provides sample B2B and B2C CaseRiskAssessment objects with
pre-built observables and analyzer results.
"""

import pytest

from risk_engine.models import (
    AnalyzerResult,
    CaseRiskAssessment,
    Observable,
    ObservableRisk,
)


# ---------------------------------------------------------------------------
# Analyzer Results
# ---------------------------------------------------------------------------

@pytest.fixture
def malicious_result():
    return AnalyzerResult(
        analyzer_name="VirusTotal_GetReport_3_1",
        level="malicious",
        score=15.0,
        namespace="VT",
        predicate="Score",
        raw_value="15/68",
    )


@pytest.fixture
def suspicious_result():
    return AnalyzerResult(
        analyzer_name="AbuseIPDB_1_0",
        level="suspicious",
        score=75.0,
        namespace="AbuseIPDB",
        predicate="Confidence",
        raw_value="75%",
    )


@pytest.fixture
def safe_result():
    return AnalyzerResult(
        analyzer_name="URLhaus_2_0",
        level="safe",
        score=0.0,
        namespace="URLhaus",
        predicate="Status",
        raw_value="not_listed",
    )


@pytest.fixture
def info_result():
    return AnalyzerResult(
        analyzer_name="Whois_1_0",
        level="info",
        score=0.0,
        namespace="Whois",
        predicate="Registrar",
        raw_value="GoDaddy",
    )


# ---------------------------------------------------------------------------
# Observables
# ---------------------------------------------------------------------------

@pytest.fixture
def ip_observable():
    return Observable(id="obs-1", data_type="ip", value="203.0.113.42", tlp=2)


@pytest.fixture
def email_observable():
    return Observable(id="obs-2", data_type="mail", value="victim@example.com", tlp=2)


# ---------------------------------------------------------------------------
# B2B Assessment
# ---------------------------------------------------------------------------

@pytest.fixture
def b2b_assessment(ip_observable, malicious_result, suspicious_result):
    return CaseRiskAssessment(
        case_id="~100",
        case_title="Suspicious Network Activity",
        case_severity=3,
        profile="b2b",
        asset_type="server",
        sensitivity="confidential",
        observables=[
            ObservableRisk(
                observable=ip_observable,
                analyzer_results=[malicious_result, suspicious_result],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# B2C Consumer Assessment
# ---------------------------------------------------------------------------

@pytest.fixture
def b2c_assessment(email_observable, malicious_result):
    return CaseRiskAssessment(
        case_id="~200",
        case_title="Consumer Identity Theft Report",
        case_severity=2,
        profile="consumer",
        exposure_type="ssn",
        observables=[
            ObservableRisk(
                observable=email_observable,
                analyzer_results=[malicious_result],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Empty Assessment (no observables)
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_assessment():
    return CaseRiskAssessment(
        case_id="~300",
        case_title="Empty Case",
        case_severity=1,
        profile="b2b",
        asset_type="workstation",
        sensitivity="public",
        observables=[],
    )
