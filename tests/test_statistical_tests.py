"""
Unit Tests for Statistical Rigor and Analytical Metrics
"""

import pytest
import pandas as pd
import numpy as np
from src.analytics.statistical_tests import compute_distribution_moments, perform_marketplace_kruskal_wallis, perform_category_anova
from src.analytics.business_kpis import calculate_compliance_rate_trajectory, calculate_pareto_concentration, compute_channel_conflict_index


def test_compute_distribution_moments():
    data = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0])
    moments = compute_distribution_moments(data)
    assert moments["count"] == 9
    assert moments["mean"] == 50.0
    assert moments["median"] == 50.0
    assert moments["min"] == 10.0
    assert moments["max"] == 90.0
    assert "skewness" in moments
    assert "kurtosis" in moments


def test_kruskal_wallis_live():
    res = perform_marketplace_kruskal_wallis()
    assert "h_statistic" in res
    assert "p_value" in res
    assert res["p_value"] < 0.05


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
