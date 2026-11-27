"""
Interactive Streamlit Business Intelligence Dashboard (Main Shell)
Author: Derin Girish D G
Description: Loads datasets, renders sidebar filters & KPIs, and delegates to modular tab views.
"""

from pathlib import Path
import pandas as pd
import streamlit as st

from src.dashboard.tab_compliance import render_compliance_tab
from src.dashboard.tab_marketplace import render_marketplace_tab
from src.dashboard.tab_overview import render_overview_tab
from src.dashboard.tab_simulator import render_simulator_tab

try:
    st.set_page_config(
        page_title="MAP Compliance & Brand Protection BI Hub",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"


@st.cache_data
def load_data():
    """Loads violation, price monitoring audit, and suspension tables."""
    pm_path = DATA_PATH / "price_monitoring_table.csv"
    pm_df = (
        pd.read_csv(pm_path, usecols=["Violation_date", "Category", "Marketplace", "SKU"])
        if pm_path.exists()
        else pd.DataFrame()
    )
    v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
    susp_path = DATA_PATH / "suspended_categories_table.csv"
    susp_df = pd.read_csv(susp_path) if susp_path.exists() else pd.DataFrame()
    return pm_df, v_df, susp_df


def main():
    st.title("⚖️ Minimum Advertised Price (MAP) Compliance & BI Hub")
    st.markdown(
        "**Multi-Channel Omnichannel Retail Surveillance & Legal Enforcement Intelligence**  \n"
        "*Surveillance Cycle: 2025-12-21 to 2026-01-05 | Monitored Regions: IND, USA, UK, CAN, UAE*"
    )
    st.divider()

    try:
        pm_df, v_df, susp_df = load_data()
    except Exception as e:
        st.error(f"Error loading datasets: {e}")
        return

    # Sidebar Filters
    st.sidebar.header("🔍 Surveillance Telemetry Filters")
    all_categories = sorted(v_df["Category"].dropna().unique())
    selected_categories = st.sidebar.multiselect("Product Category", all_categories, default=all_categories)

    all_markets = sorted(v_df["Marketplace"].dropna().unique())
    selected_markets = st.sidebar.multiselect("Marketplace Channel", all_markets, default=all_markets)

    min_date = pd.to_datetime(v_df["Violation_date"]).min().date()
    max_date = pd.to_datetime(v_df["Violation_date"]).max().date()
    date_range = st.sidebar.date_input("Surveillance Window", [min_date, max_date], min_value=min_date, max_value=max_date)
    start_d, end_d = (str(date_range[0]), str(date_range[1])) if len(date_range) == 2 else (str(min_date), str(max_date))

    briefing_file = REPORTS_DIR / "EXECUTIVE_C_SUITE_BRIEFING.html"
    if briefing_file.exists():
        st.sidebar.divider()
        st.sidebar.markdown("### 📄 C-Suite Deliverables")
        st.sidebar.download_button(
            label="📥 Download Executive Briefing (HTML)",
            data=briefing_file.read_text(encoding="utf-8"),
            file_name="EXECUTIVE_C_SUITE_BRIEFING.html",
            mime="text/html",
            help="Download a clean, responsive, 1-page executive summary formatted for C-Suite presentation.",
        )

    # Filter telemetry
    filtered_v = v_df[
        (v_df["Category"].isin(selected_categories))
        & (v_df["Marketplace"].isin(selected_markets))
        & (v_df["Violation_date"] >= start_d)
        & (v_df["Violation_date"] <= end_d)
    ].copy()

    if not pm_df.empty:
        total_audits = len(
            pm_df[
                (pm_df["Category"].isin(selected_categories))
                & (pm_df["Marketplace"].isin(selected_markets))
                & (pm_df["Violation_date"] >= start_d)
                & (pm_df["Violation_date"] <= end_d)
            ]
        )
    else:
        total_audits = len(filtered_v)

    total_violations = len(filtered_v)
    compliance_rate = ((total_audits - total_violations) / total_audits) * 100.0 if total_audits > 0 else 0.0
    total_deficit = filtered_v["Price_Difference"].sum()

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Market Audits", f"{total_audits:,}")
    kpi2.metric("Violations Flagged", f"{total_violations:,}", delta=f"-{total_violations:,}", delta_color="inverse")
    kpi3.metric("Global Compliance Rate", f"{compliance_rate:.1f}%")
    kpi4.metric("Cumulative Price Deficit", f"₹{total_deficit / 1e6:.2f}M")
    kpi5.metric("Reseller Suspensions", f"{len(susp_df):,}")

    st.write("")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview & Time-Series",
        "📊 Marketplace & Deficit Concentration",
        "🚨 Reseller Compliance & Legal Notices",
        "🎛️ What-If Policy Simulator & Elasticity",
    ])

    with tab1:
        render_overview_tab(filtered_v)
    with tab2:
        render_marketplace_tab(filtered_v)
    with tab3:
        render_compliance_tab(v_df, susp_df)
    with tab4:
        render_simulator_tab(filtered_v)


if __name__ == "__main__":
    main()
