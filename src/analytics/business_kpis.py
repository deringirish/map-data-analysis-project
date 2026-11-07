"""
Commercial Impact & Executive Business KPIs Subsystem
Author: Derin Girish D G
Description: Computes executive-level compliance rate trajectories, cumulative margin at risk,
Pareto concentration curves (80/20 rule), and channel conflict indices.
"""

import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_compliance_rate_trajectory() -> pd.DataFrame:
    """
    Computes daily compliance rates across the 15-day surveillance window:
    Compliance_Rate % = (Total_Audits - Violations) / Total_Audits * 100
    """
    pm_path = DATA_PATH / "price_monitoring_table.csv"
    v_path = DATA_PATH / "violation_table.csv"

    if not pm_path.exists() or not v_path.exists():
        raise FileNotFoundError("Price monitoring or violation table missing.")

    pm_df = pd.read_csv(pm_path, usecols=["Violation_date", "SKU"])
    v_df = pd.read_csv(v_path, usecols=["Violation_date", "SKU"])

    total_daily = pm_df.groupby("Violation_date").size().rename("Total_Observations")
    violation_daily = v_df.groupby("Violation_date").size().rename("Violation_Count")

    summary = pd.concat([total_daily, violation_daily], axis=1).fillna(0).reset_index()
    summary["Compliant_Count"] = summary["Total_Observations"] - summary["Violation_Count"]
    summary["Compliance_Rate_Pct"] = (summary["Compliant_Count"] / summary["Total_Observations"]) * 100.0
    summary["Violation_Rate_Pct"] = 100.0 - summary["Compliance_Rate_Pct"]

    return summary.sort_values("Violation_date").reset_index(drop=True)


def calculate_pareto_concentration() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes Pareto distribution (80/20 Lorenz concentration) of financial deficit
    across parent corporate resellers.
    """
    v_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_path, usecols=["homologated_name", "Price_Difference"])

    seller_deficit = v_df.groupby("homologated_name")["Price_Difference"].sum().sort_values(ascending=False).reset_index()
    total_deficit = seller_deficit["Price_Difference"].sum()
    seller_deficit["Share_Pct"] = (seller_deficit["Price_Difference"] / total_deficit) * 100.0
    seller_deficit["Cumulative_Deficit"] = seller_deficit["Price_Difference"].cumsum()
    seller_deficit["Cumulative_Pct"] = (seller_deficit["Cumulative_Deficit"] / total_deficit) * 100.0
    seller_deficit["Rank"] = range(1, len(seller_deficit) + 1)
    seller_deficit["Reseller_Percentile"] = (seller_deficit["Rank"] / len(seller_deficit)) * 100.0

    # Find 80% cutoff
    pareto_80_sellers = seller_deficit[seller_deficit["Cumulative_Pct"] <= 80.0]
    cutoff_count = len(pareto_80_sellers) + 1
    total_sellers = len(seller_deficit)
    pct_sellers_for_80_deficit = (cutoff_count / total_sellers) * 100.0

    stats = {
        "total_resellers": total_sellers,
        "total_deficit_inr": float(total_deficit),
        "resellers_for_80pct_deficit": cutoff_count,
        "pct_resellers_for_80pct_deficit": round(pct_sellers_for_80_deficit, 2)
    }

    return seller_deficit, stats


def compute_channel_conflict_index() -> pd.DataFrame:
    """
    Evaluates channel friction score across retail marketplaces by measuring:
    1. Violation density per channel
    2. Total deficit volume
    3. Average margin undercut per non-compliant listing
    """
    v_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_path)

    channel_summary = v_df.groupby("Marketplace").agg(
        Total_Infractions=("SKU", "count"),
        Total_Deficit=("Price_Difference", "sum"),
        Mean_Deficit=("Price_Difference", "mean"),
        Median_Deficit=("Price_Difference", "median"),
        Max_Deficit=("Price_Difference", "max")
    ).reset_index()

    total_v = channel_summary["Total_Infractions"].sum()
    total_d = channel_summary["Total_Deficit"].sum()

    channel_summary["Infraction_Share_Pct"] = (channel_summary["Total_Infractions"] / total_v) * 100.0
    channel_summary["Deficit_Share_Pct"] = (channel_summary["Total_Deficit"] / total_d) * 100.0

    # Channel Conflict Index: Weighted normalized combination of frequency and deficit severity
    channel_summary["Channel_Conflict_Score"] = (
        0.5 * channel_summary["Infraction_Share_Pct"] + 0.5 * channel_summary["Deficit_Share_Pct"]
    ).round(2)

    return channel_summary.sort_values("Channel_Conflict_Score", ascending=False).reset_index(drop=True)


def generate_executive_kpi_summary() -> Dict[str, Any]:
    """Generates holistic executive scorecard metrics."""
    pm_path = DATA_PATH / "price_monitoring_table.csv"
    v_path = DATA_PATH / "violation_table.csv"
    susp_path = DATA_PATH / "suspended_categories_table.csv"

    total_audits = len(pd.read_csv(pm_path, usecols=["SKU"]))
    v_df = pd.read_csv(v_path, usecols=["Price_Difference", "homologated_name", "SKU"])
    susp_df = pd.read_csv(susp_path) if susp_path.exists() else pd.DataFrame()

    total_violations = len(v_df)
    total_deficit = float(v_df["Price_Difference"].sum())
    overall_compliance_rate = ((total_audits - total_violations) / total_audits) * 100.0

    _, pareto_stats = calculate_pareto_concentration()

    kpis = {
        "total_marketplace_audits": total_audits,
        "total_policy_violations": total_violations,
        "overall_compliance_rate_pct": round(overall_compliance_rate, 2),
        "total_financial_deficit_inr": round(total_deficit, 2),
        "distinct_resellers_violating": int(v_df["homologated_name"].nunique()),
        "distinct_skus_violated": int(v_df["SKU"].nunique()),
        "critical_suspensions": int((susp_df["Enforcement_Status"] == "CRITICAL_SUSPENSION").sum()) if not susp_df.empty else 0,
        "formal_suspensions": int((susp_df["Enforcement_Status"] == "FORMAL_SUSPENSION").sum()) if not susp_df.empty else 0,
        "conditional_probations": int((susp_df["Enforcement_Status"] == "CONDITIONAL_PROBATION").sum()) if not susp_df.empty else 0,
        "pareto_summary": pareto_stats
    }

    return kpis


if __name__ == "__main__":
    print("=" * 65)
    print(" EXECUTIVE COMMERCIAL IMPACT & BUSINESS KPIS AUDIT")
    print("=" * 65)
    kpis = generate_executive_kpi_summary()
    print(f"Total Market Observations:     {kpis['total_marketplace_audits']:,}")
    print(f"Total Flagged Violations:      {kpis['total_policy_violations']:,}")
    print(f"Global Compliance Rate:        {kpis['overall_compliance_rate_pct']}%")
    print(f"Cumulative Deficit Below MAP:  INR {kpis['total_financial_deficit_inr']:,.2f}")
    print(f"Active Critical Freezes:       {kpis['critical_suspensions']}")
    print(f"Pareto Concentration (80%):    Top {kpis['pareto_summary']['resellers_for_80pct_deficit']} resellers ({kpis['pareto_summary']['pct_resellers_for_80pct_deficit']}%) drive 80% of price erosion.")
    print("=" * 65)
