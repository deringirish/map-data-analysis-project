"""
Unit tests for MAP Policy Simulator & Elasticity Engine
"""

import pandas as pd
import pytest
from src.analytics.policy_simulator import (
    simulate_discount_elasticity,
    simulate_suspension_thresholds,
    simulate_targeted_enforcement
)


@pytest.fixture
def sample_violations_df():
    return pd.DataFrame({
        "SKU": ["SKU1", "SKU2", "SKU3", "SKU4"],
        "MAP_Price": [1000.0, 2000.0, 500.0, 1200.0],
        "LPP": [900.0, 1800.0, 450.0, 1080.0],  # 10% base discount
        "Advertised_price": [880.0, 1750.0, 400.0, 1070.0],
        "Price_Difference": [20.0, 50.0, 50.0, 10.0],
        "homologated_name": ["Alpha Retail", "Alpha Retail", "Beta Electronics", "Gamma Corp"],
        "Category": ["PC", "PC", "PH", "PS"],
        "Violation_date": ["2025-12-21", "2025-12-22", "2025-12-21", "2025-12-25"]
    })


def test_simulate_discount_elasticity_zero_extra(sample_violations_df):
    result = simulate_discount_elasticity(sample_violations_df, extra_discount_pct=0.0)
    assert result["baseline_count"] == 4
    assert result["simulated_count"] == 4
    assert result["absorbed_count"] == 0
    assert result["absorption_rate"] == 0.0


def test_simulate_discount_elasticity_absorbs_minor_breaches(sample_violations_df):
    # Base discount was 10% (LPP=900, 1800, 450, 1080)
    # Extra 5% -> 15% discount (LPP=850, 1700, 425, 1020)
    # Advertised:
    # SKU1: 880 >= 850 (cured!)
    # SKU2: 1750 >= 1700 (cured!)
    # SKU3: 400 < 425 (still violation)
    # SKU4: 1070 >= 1020 (cured!)
    result = simulate_discount_elasticity(sample_violations_df, extra_discount_pct=5.0)
    assert result["baseline_count"] == 4
    assert result["simulated_count"] == 1
    assert result["absorbed_count"] == 3
    assert result["absorption_rate"] == 75.0
    assert result["recovered_deficit"] > 0


def test_simulate_suspension_thresholds(sample_violations_df):
    # Alpha Retail in PC has 2 distinct dates
    # Beta in PH has 1 date
    # Gamma in PS has 1 date
    # If critical = 2, formal = 1: Alpha becomes Critical, others Formal
    res = simulate_suspension_thresholds(sample_violations_df, critical_days=2, formal_days=1)
    assert len(res) == 3
    alpha = res[(res["homologated_name"] == "Alpha Retail") & (res["Category"] == "PC")].iloc[0]
    assert alpha["Simulated_Status"] == "Critical Suspension (30-Day Freeze)"


def test_simulate_targeted_enforcement(sample_violations_df):
    res = simulate_targeted_enforcement(sample_violations_df, ["Alpha Retail"])
    assert res["targeted_sellers_count"] == 1
    assert res["targeted_violations"] == 2
    assert res["pct_violations_reduced"] == 50.0
    assert res["pct_deficit_recovered"] > 0
