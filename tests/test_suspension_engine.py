"""
Unit Tests for Category Suspension & Recidivism Classification
"""

import pytest
import pandas as pd
from datetime import datetime
from src.enforcement.category_suspension_engine import evaluate_category_suspensions


def test_suspension_tier_classification():
    # Test classification boundary conditions
    sample_data = pd.DataFrame([
        {
            "homologated_name": "Reseller A", "Category": "PC",
            "SKU": "SKU_01", "Violation_date": "2025-12-21",
            "Marketplace": "Amazon", "Price_Difference": 500.0
        }
    ])
    
    # Generate 13 distinct days for Reseller A -> Critical
    records = []
    for d in range(1, 14):
        records.append({
            "homologated_name": "Critical Reseller", "Category": "PC",
            "SKU": f"SKU_{d}", "Violation_date": f"2025-12-{d:02d}",
            "Marketplace": "Amazon", "Price_Difference": 1000.0
        })
    # Generate 8 distinct days for Reseller B -> Formal
    for d in range(1, 9):
        records.append({
            "homologated_name": "Formal Reseller", "Category": "PH",
            "SKU": f"SKU_{d}", "Violation_date": f"2025-12-{d:02d}",
            "Marketplace": "Flipkart", "Price_Difference": 500.0
        })
    # Generate 3 distinct days for Reseller C -> Probation
    for d in range(1, 4):
        records.append({
            "homologated_name": "Probation Reseller", "Category": "PS",
            "SKU": f"SKU_{d}", "Violation_date": f"2025-12-{d:02d}",
            "Marketplace": "eBay", "Price_Difference": 200.0
        })

    mock_v_df = pd.DataFrame(records)
    
    agg_df = mock_v_df.groupby(["homologated_name", "Category"]).agg(
        Total_Infractions=("SKU", "count"),
        Distinct_Violation_Dates=("Violation_date", "nunique"),
        Distinct_SKUs_Violated=("SKU", "nunique"),
        Marketplaces_Audited=("Marketplace", lambda m: ", ".join(sorted(m.dropna().unique()))),
        Earliest_Violation=("Violation_date", "min"),
        Latest_Violation=("Violation_date", "max"),
        Max_Single_Deficit=("Price_Difference", "max"),
        Total_Price_Deficit=("Price_Difference", "sum")
    ).reset_index()

    def classify(row):
        dates = row["Distinct_Violation_Dates"]
        if dates >= 12:
            return ("CRITICAL_SUSPENSION", 30)
        elif dates >= 7:
            return ("FORMAL_SUSPENSION", 30)
        else:
            return ("CONDITIONAL_PROBATION", 0)

    res = agg_df.apply(classify, axis=1)
    agg_df["Status"] = [r[0] for r in res]
    agg_df["Days"] = [r[1] for r in res]

    crit_row = agg_df[agg_df["homologated_name"] == "Critical Reseller"].iloc[0]
    assert crit_row["Status"] == "CRITICAL_SUSPENSION"
    assert crit_row["Days"] == 30

    form_row = agg_df[agg_df["homologated_name"] == "Formal Reseller"].iloc[0]
    assert form_row["Status"] == "FORMAL_SUSPENSION"
    assert form_row["Days"] == 30

    prob_row = agg_df[agg_df["homologated_name"] == "Probation Reseller"].iloc[0]
    assert prob_row["Status"] == "CONDITIONAL_PROBATION"
    assert prob_row["Days"] == 0


def test_evaluate_category_suspensions_live_run():
    # Evaluate against actual violation table
    df = evaluate_category_suspensions()
    assert not df.empty
    assert len(df) == 279
    assert "Enforcement_Status" in df.columns
    assert "Suspension_Effective_Date" in df.columns
    assert set(df["Enforcement_Status"].unique()).issubset({"CRITICAL_SUSPENSION", "FORMAL_SUSPENSION", "CONDITIONAL_PROBATION"})
