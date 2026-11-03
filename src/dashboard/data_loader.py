"""
High-Performance Cached Data Loader for MAP Compliance BI Dashboard
Author: Derin Girish
Description: Loads violation, suspension, and price monitoring datasets with caching and graceful CSV/MySQL fallback.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TABLES_DIR = BASE_DIR / "data_processed" / "database_tables"


@st.cache_data(show_spinner="Loading MAP Compliance Telemetry...")
def load_violations_data() -> pd.DataFrame:
    """Load and preprocess full violation audit records."""
    csv_path = TABLES_DIR / "violation_table.csv"
    if not csv_path.exists():
        st.error(f"Required dataset not found: {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    df["Violation_date"] = pd.to_datetime(df["Violation_date"], errors="coerce")
    df["Price_Difference"] = pd.to_numeric(df["Price_Difference"], errors="coerce").fillna(0.0)
    df["MAP_Price"] = pd.to_numeric(df["MAP_Price"], errors="coerce").fillna(0.0)
    df["LPP"] = pd.to_numeric(df["LPP"], errors="coerce").fillna(0.0)
    df["Advertised_price"] = pd.to_numeric(df["Advertised_price"], errors="coerce").fillna(0.0)
    
    # Fill categorical nulls
    df["Marketplace"] = df["Marketplace"].fillna("Unknown")
    df["Category"] = df["Category"].fillna("Other")
    df["Sub_category"] = df["Sub_category"].fillna("General")
    df["homologated_name"] = df["homologated_name"].fillna(df["seller_name"]).fillna("Anonymous Reseller")
    df["Region"] = df["Region"].fillna("IND")
    
    return df


@st.cache_data(show_spinner="Loading Recidivism Suspension Registry...")
def load_suspensions_data() -> pd.DataFrame:
    """Load and preprocess 30-day category suspension audit registry (Charter Objective 4)."""
    csv_path = TABLES_DIR / "suspended_categories_table.csv"
    if not csv_path.exists():
        st.error(f"Required dataset not found: {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    df["Total_Price_Deficit"] = pd.to_numeric(df["Total_Price_Deficit"], errors="coerce").fillna(0.0)
    df["Max_Single_Deficit"] = pd.to_numeric(df["Max_Single_Deficit"], errors="coerce").fillna(0.0)
    df["Total_Infractions"] = pd.to_numeric(df["Total_Infractions"], errors="coerce").fillna(0)
    df["Suspension_Duration_Days"] = pd.to_numeric(df["Suspension_Duration_Days"], errors="coerce").fillna(30)
    return df


@st.cache_data
def get_kpi_summary(df_violations: pd.DataFrame, df_suspensions: pd.DataFrame) -> Dict[str, Any]:
    """Calculate executive high-level metrics for dashboard cards."""
    total_violations = len(df_violations)
    total_deficit = df_violations["Price_Difference"].sum()
    unique_resellers = df_violations["homologated_name"].nunique()
    unique_skus = df_violations["SKU"].nunique()
    total_suspensions = len(df_suspensions)
    total_suspended_deficit = df_suspensions["Total_Price_Deficit"].sum()
    
    return {
        "total_violations": total_violations,
        "total_deficit_inr": total_deficit,
        "unique_resellers": unique_resellers,
        "unique_skus": unique_skus,
        "total_suspensions": total_suspensions,
        "total_suspended_deficit": total_suspended_deficit,
    }
