"""
MAP Policy Simulation & Elasticity Engine
Author: Derin Girish D G
Description: Models what-if scenario testing for promotional discount ceilings,
recidivism threshold sensitivity, and targeted partner enforcement.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def simulate_discount_elasticity(df: pd.DataFrame, extra_discount_pct: float = 0.0) -> Dict[str, Any]:
    """
    Simulates the effect of expanding promotional discount allowance on compliance and margin erosion.
    
    Args:
        df: DataFrame containing at least ['MAP_Price', 'LPP', 'Advertised_price'].
        extra_discount_pct: Additional discount percentage added to baseline (e.g. 5.0 for +5%).
        
    Returns:
        Dict containing baseline vs simulated counts, deficit recovery, and remaining violations df.
    """
    if df.empty:
        return {
            "baseline_count": 0,
            "simulated_count": 0,
            "absorbed_count": 0,
            "absorption_rate": 0.0,
            "baseline_deficit": 0.0,
            "simulated_deficit": 0.0,
            "recovered_deficit": 0.0,
            "simulated_df": pd.DataFrame()
        }

    # Derive baseline discount percentage
    base_discount = ((df["MAP_Price"] - df["LPP"]) / df["MAP_Price"]) * 100.0
    effective_discount = (base_discount + extra_discount_pct).clip(lower=0.0, upper=100.0)
    
    # Recalculate dynamic simulated LPP floor
    sim_lpp = df["MAP_Price"] * (1.0 - effective_discount / 100.0)
    
    # Flag records that remain non-compliant under the relaxed threshold
    violation_mask = df["Advertised_price"] < sim_lpp
    sim_df = df[violation_mask].copy()
    
    sim_df["Simulated_LPP"] = sim_lpp[violation_mask]
    sim_df["Simulated_Deficit"] = sim_df["Simulated_LPP"] - sim_df["Advertised_price"]

    baseline_count = len(df)
    simulated_count = len(sim_df)
    absorbed_count = baseline_count - simulated_count
    absorption_rate = (absorbed_count / baseline_count * 100.0) if baseline_count > 0 else 0.0

    baseline_deficit = float(df["Price_Difference"].sum()) if "Price_Difference" in df.columns else float((df["LPP"] - df["Advertised_price"]).clip(lower=0).sum())
    simulated_deficit = float(sim_df["Simulated_Deficit"].sum())
    recovered_deficit = max(0.0, baseline_deficit - simulated_deficit)

    return {
        "baseline_count": baseline_count,
        "simulated_count": simulated_count,
        "absorbed_count": absorbed_count,
        "absorption_rate": absorption_rate,
        "baseline_deficit": baseline_deficit,
        "simulated_deficit": simulated_deficit,
        "recovered_deficit": recovered_deficit,
        "simulated_df": sim_df
    }


def simulate_suspension_thresholds(
    df: pd.DataFrame,
    critical_days: int = 12,
    formal_days: int = 7
) -> pd.DataFrame:
    """
    Simulates account suspension counts under alternative recidivism thresholds.
    
    Args:
        df: DataFrame containing at least ['homologated_name', 'Category', 'Violation_date', 'Price_Difference'].
        critical_days: Minimum distinct violation days triggering Critical 30-Day Freeze.
        formal_days: Minimum distinct violation days triggering Formal Suspension.
        
    Returns:
        DataFrame aggregated by (homologated_name, Category) with simulated tier and metrics.
    """
    if df.empty:
        return pd.DataFrame()

    grouped = df.groupby(["homologated_name", "Category"]).agg(
        Total_Infractions=("SKU", "count") if "SKU" in df.columns else ("Price_Difference", "count"),
        Distinct_Violation_Dates=("Violation_date", "nunique"),
        Total_Price_Deficit=("Price_Difference", "sum")
    ).reset_index()

    def classify_tier(days: int) -> str:
        if days >= critical_days:
            return "Critical Suspension (30-Day Freeze)"
        elif days >= formal_days:
            return "Formal Suspension (30-Day Category Freeze)"
        else:
            return "Conditional Probation (48-Hr Cure)"

    grouped["Simulated_Status"] = grouped["Distinct_Violation_Dates"].apply(classify_tier)
    return grouped


def simulate_targeted_enforcement(
    df: pd.DataFrame,
    target_resellers: List[str]
) -> Dict[str, Any]:
    """
    Calculates immediate deficit recovery and violation reduction if specific chronic resellers are cured.
    
    Args:
        df: DataFrame of violations.
        target_resellers: List of reseller homologated names targeted for enforcement.
        
    Returns:
        Dict with deficit recovered, violation drop, and share of total risk.
    """
    if df.empty or not target_resellers:
        return {
            "targeted_sellers_count": 0,
            "targeted_violations": 0,
            "targeted_deficit": 0.0,
            "pct_deficit_recovered": 0.0,
            "pct_violations_reduced": 0.0
        }

    target_mask = df["homologated_name"].isin(target_resellers)
    target_violations = int(target_mask.sum())
    total_violations = len(df)
    
    total_deficit = float(df["Price_Difference"].sum())
    target_deficit = float(df.loc[target_mask, "Price_Difference"].sum())

    pct_deficit_recovered = (target_deficit / total_deficit * 100.0) if total_deficit > 0 else 0.0
    pct_violations_reduced = (target_violations / total_violations * 100.0) if total_violations > 0 else 0.0

    return {
        "targeted_sellers_count": len(target_resellers),
        "targeted_violations": target_violations,
        "targeted_deficit": target_deficit,
        "pct_deficit_recovered": pct_deficit_recovered,
        "pct_violations_reduced": pct_violations_reduced
    }
