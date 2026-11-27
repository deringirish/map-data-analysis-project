"""
Unit Tests for Business KPIs & Concentration Metrics
"""

from src.analytics.business_kpis import (
    calculate_compliance_rate_trajectory,
    calculate_pareto_concentration,
    compute_channel_conflict_index,
)


def test_compliance_rate_trajectory_live():
    df = calculate_compliance_rate_trajectory()
    assert not df.empty
    assert "Compliance_Rate_Pct" in df.columns


def test_pareto_concentration_live():
    df, stats = calculate_pareto_concentration()
    assert not df.empty
    assert "Cumulative_Pct" in df.columns
    assert stats["total_resellers"] > 0
    assert stats["resellers_for_80pct_deficit"] <= stats["total_resellers"]


def test_channel_conflict_index_live():
    df = compute_channel_conflict_index()
    assert not df.empty
    assert "Channel_Conflict_Score" in df.columns
    assert "Marketplace" in df.columns
