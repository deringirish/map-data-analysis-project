"""
Statistical Rigor & Hypothesis Testing Subsystem
Author: Derin Girish D G
Description: Rigorous inferential statistical tests, distribution moment metrics,
and non-parametric hypothesis tests for cross-marketplace price variance.
"""

import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np
from scipy import stats

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"


def compute_distribution_moments(series: pd.Series) -> Dict[str, float]:
    """Computes distribution shape metrics: Mean, Median, Std, Skewness, Kurtosis, IQR."""
    clean = series.dropna()
    q25, q75 = clean.quantile(0.25), clean.quantile(0.75)
    return {
        "count": int(len(clean)),
        "mean": float(clean.mean()),
        "std_dev": float(clean.std()),
        "median": float(clean.median()),
        "iqr": float(q75 - q25),
        "q25": float(q25),
        "q75": float(q75),
        "min": float(clean.min()),
        "max": float(clean.max()),
        "skewness": float(stats.skew(clean)),
        "kurtosis": float(stats.kurtosis(clean))
    }


def perform_marketplace_kruskal_wallis() -> Dict[str, Any]:
    """
    Kruskal-Wallis H-Test:
    Evaluates whether the distributions of price undercutting deficits differ
    significantly across the observed marketplace platforms.
    H0: Price deficits across all marketplaces share identical population medians.
    H1: At least one marketplace exhibits a statistically distinct undercutting distribution.
    """
    v_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_path, usecols=["Marketplace", "Price_Difference"])

    groups = [group["Price_Difference"].values for _, group in v_df.groupby("Marketplace")]
    h_stat, p_val = stats.kruskal(*groups)

    is_significant = bool(p_val < 0.05)
    interpretation = (
        "Statistically significant divergence in undercutting severity across marketplaces (p < 0.05). "
        "Reject H0: Marketplace algorithms or reseller cohorts behave with distinct pricing aggression."
        if is_significant else
        "No statistically significant difference observed across marketplaces (fail to reject H0)."
    )

    return {
        "test_name": "Kruskal-Wallis H-Test",
        "h_statistic": round(float(h_stat), 4),
        "p_value": float(p_val),
        "is_significant_at_alpha_0_05": is_significant,
        "interpretation": interpretation
    }


def perform_pairwise_mann_whitney(market_a: str = "Amazon", market_b: str = "Flipkart") -> Dict[str, Any]:
    """
    Mann-Whitney U Test:
    Pairwise comparison testing whether Market A exhibits greater under-MAP severity than Market B.
    """
    v_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_path, usecols=["Marketplace", "Price_Difference"])

    vals_a = v_df[v_df["Marketplace"].str.contains(market_a, case=False, na=False)]["Price_Difference"].dropna()
    vals_b = v_df[v_df["Marketplace"].str.contains(market_b, case=False, na=False)]["Price_Difference"].dropna()

    if len(vals_a) == 0 or len(vals_b) == 0:
        return {"error": f"One or both marketplaces ({market_a}, {market_b}) lack violation records."}

    u_stat, p_val = stats.mannwhitneyu(vals_a, vals_b, alternative="two-sided")

    return {
        "test_name": f"Mann-Whitney U Test ({market_a} vs {market_b})",
        "sample_size_a": len(vals_a),
        "sample_size_b": len(vals_b),
        "median_a": float(vals_a.median()),
        "median_b": float(vals_b.median()),
        "u_statistic": float(u_stat),
        "p_value": float(p_val),
        "is_significant": bool(p_val < 0.05)
    }


def perform_category_anova() -> Dict[str, Any]:
    """
    One-Way ANOVA:
    Tests whether mean price deficits differ significantly across product divisions (PC, PH, PS).
    """
    v_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_path, usecols=["Category", "Price_Difference"])

    groups = [group["Price_Difference"].values for _, group in v_df.groupby("Category")]
    f_stat, p_val = stats.f_oneway(*groups)

    return {
        "test_name": "One-Way ANOVA (Category Deficit Variance)",
        "f_statistic": round(float(f_stat), 4),
        "p_value": float(p_val),
        "is_significant": bool(p_val < 0.05)
    }


def run_full_statistical_battery() -> Dict[str, Any]:
    """Executes the full suite of statistical verification tests."""
    v_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_path, usecols=["Price_Difference"])

    print("=" * 65)
    print(" INFERENTIAL STATISTICAL RIGOR & HYPOTHESIS TESTING BATTERY")
    print("=" * 65)

    moments = compute_distribution_moments(v_df["Price_Difference"])
    print(f"Price Deficit Distribution (N={moments['count']:,}):")
    print(f"- Mean: INR {moments['mean']:,.2f} | Std Dev: INR {moments['std_dev']:,.2f}")
    print(f"- Median: INR {moments['median']:,.2f} | IQR: INR {moments['iqr']:,.2f}")
    print(f"- Skewness: {moments['skewness']:.3f} | Kurtosis: {moments['kurtosis']:.3f}")
    print("-----------------------------------------------------------------")

    kw = perform_marketplace_kruskal_wallis()
    print(f"Kruskal-Wallis Test (Marketplaces): H={kw['h_statistic']}, p={kw['p_value']:.4e}")
    print(f"-> {kw['interpretation']}")
    print("-----------------------------------------------------------------")

    mw = perform_pairwise_mann_whitney("Amazon", "Flipkart")
    print(f"Pairwise Mann-Whitney (Amazon vs Flipkart): p={mw.get('p_value', 1.0):.4e}")
    print(f"-> Amazon Median: INR {mw.get('median_a', 0):,.2f} vs Flipkart Median: INR {mw.get('median_b', 0):,.2f}")
    print("-----------------------------------------------------------------")

    anova = perform_category_anova()
    print(f"One-Way ANOVA (Product Categories): F={anova['f_statistic']}, p={anova['p_value']:.4e}")
    print("=================================================================\n")

    return {
        "distribution_moments": moments,
        "kruskal_wallis": kw,
        "mann_whitney_amazon_flipkart": mw,
        "category_anova": anova
    }


if __name__ == "__main__":
    run_full_statistical_battery()
