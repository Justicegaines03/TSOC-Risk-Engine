"""
Risk Calculator — The Math

Converts Cortex analyzer verdicts into a quantitative financial risk score.

    Likelihood  (0-1)   × Impact ($)  =  ALE ($)
    ──────────────────   ───────────      ──────
    From analyzer        From asset       Annualized
    verdicts             value +          Loss
                         sensitivity      Expectancy
"""

from __future__ import annotations

import logging
from typing import List

from risk_engine import config
from risk_engine.models import (
    AnalyzerResult,
    CaseRiskAssessment,
    ObservableRisk,
    RiskScore,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Likelihood
# -----------------------------------------------------------------------

def compute_likelihood(results: List[AnalyzerResult]) -> float:
    """Compute a likelihood score (0.0 – 1.0) from a set of analyzer verdicts.

    Algorithm
    ---------
    1. Map each verdict level to its configured weight.
    2. Take the weighted average.
    3. If multiple *independent* analyzers agree on "malicious", apply a
       consensus boost (capped at 1.0).
    """
    if not results:
        return 0.0

    weights = [
        config.VERDICT_WEIGHTS.get(r.level, 0.0) for r in results
    ]
    avg = sum(weights) / len(weights)

    # Consensus boost
    unique_analyzers = len({r.analyzer_name for r in results if r.level == "malicious"})

    if unique_analyzers >= config.MALICIOUS_CONSENSUS_THRESHOLD:
        avg *= config.MALICIOUS_CONSENSUS_BOOST
        logger.debug(
            "Consensus boost applied (%d independent malicious verdicts)",
            unique_analyzers,
        )

    return min(avg, 1.0)


# -----------------------------------------------------------------------
# Impact
# -----------------------------------------------------------------------

def compute_impact(
    asset_type: str,
    sensitivity: str,
    *,
    profile: str = "b2b",
    exposure_type: str = "",
) -> float:
    """Compute impact from asset type (B2B) or exposure type (B2C).

    B2B:  Impact ($) = base_asset_value × sensitivity_multiplier
    B2C:  Impact     = exposure_severity_score  (0-100)
    """
    if profile == "consumer":
        return float(
            config.B2C_EXPOSURE_WEIGHTS.get(
                exposure_type.lower(), config.B2C_EXPOSURE_WEIGHTS[config.DEFAULT_EXPOSURE_TYPE]
            )
        )

    # B2B path (default)
    base = config.ASSET_VALUES.get(
        asset_type.lower(), config.DEFAULT_ASSET_VALUE
    )
    multiplier = config.SENSITIVITY_MULTIPLIERS.get(
        sensitivity.lower(), config.SENSITIVITY_MULTIPLIERS[config.DEFAULT_SENSITIVITY]
    )
    return float(base * multiplier)


# -----------------------------------------------------------------------
# Risk Level
# -----------------------------------------------------------------------

def classify_risk(ale: float, *, profile: str = "b2b") -> str:
    """Map a score to a human-readable risk level.

    B2B uses dollar-based ALE thresholds; B2C uses 0-100 severity thresholds.
    """
    thresholds = (
        config.B2C_SEVERITY_THRESHOLDS if profile == "consumer"
        else config.RISK_THRESHOLDS
    )

    if ale >= thresholds["critical"]:
        return "Critical"
    if ale >= thresholds["high"]:
        return "High"
    if ale >= thresholds["medium"]:
        return "Medium"
    if ale >= thresholds["low"]:
        return "Low"
    return "Info"


# -----------------------------------------------------------------------
# Top-level scoring
# -----------------------------------------------------------------------

def score_observable(observable_risk: ObservableRisk) -> float:
    """Score a single observable and set its likelihood in-place. Returns the likelihood."""
    likelihood = compute_likelihood(observable_risk.analyzer_results)
    observable_risk.likelihood = likelihood
    return likelihood


def score_case(assessment: CaseRiskAssessment) -> RiskScore:
    """Score an entire case and attach the RiskScore.

    Case-level likelihood is the *maximum* observable likelihood (worst-case)
    because a single highly-malicious indicator is enough to drive risk.

    Supports both B2B (ALE in dollars) and B2C consumer (severity 0-100)
    profiles via assessment.profile.
    """
    profile = assessment.profile

    # Score each observable
    likelihoods: List[float] = []
    for obs_risk in assessment.observables:
        lh = score_observable(obs_risk)
        likelihoods.append(lh)

    # Case likelihood = max across observables (worst-case driver)
    case_likelihood = max(likelihoods) if likelihoods else 0.0

    # Impact — B2B uses asset value × sensitivity; B2C uses exposure weight
    impact = compute_impact(
        assessment.asset_type,
        assessment.sensitivity,
        profile=profile,
        exposure_type=assessment.exposure_type,
    )

    # Composite score: ALE for B2B, Recovery Difficulty for B2C
    composite = case_likelihood * impact

    risk = RiskScore(
        likelihood=round(case_likelihood, 4),
        impact_dollars=round(impact, 2),
        ale=round(composite, 2),
        risk_level=classify_risk(composite, profile=profile),
    )
    assessment.risk_score = risk

    score_label = "ALE" if profile == "b2b" else "severity"
    logger.info(
        "Case %s scored [%s]: likelihood=%.2f, impact=%.2f, %s=%.2f (%s)",
        assessment.case_id,
        profile,
        risk.likelihood,
        risk.impact_dollars,
        score_label,
        risk.ale,
        risk.risk_level,
    )
    return risk
