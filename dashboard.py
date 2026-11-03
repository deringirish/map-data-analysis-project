"""
Master Interactive Streamlit BI Dashboard for MAP Compliance Engine
Author: Derin Girish
Usage: streamlit run dashboard.py
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from src.dashboard.data_loader import load_violations_data, load_suspensions_data
from src.dashboard.views.overview import render_overview_view
from src.dashboard.views.resellers import render_resellers_view
from src.dashboard.views.analytics import render_analytics_view

# Page Configuration
st.set_page_config(
    page_title="MAP Compliance & Brand Protection BI Hub",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished enterprise look
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        div[data-testid="metric-container"] {
            background-color: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(148, 163, 184, 0.15);
            padding: 1rem;
            border-radius: 0.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    # 1. Load Data
    df_violations = load_violations_data()
    df_suspensions = load_suspensions_data()

    if df_violations.empty:
        st.error("No violation data available. Run database ingestion pipeline first.")
        return

    # 2. Sidebar Navigation & Global Filters
    st.sidebar.title("⚖️ MAP Intelligence Hub")
    st.sidebar.caption("Enterprise Brand Protection & Reseller Audit Suite")
    st.sidebar.markdown("---")

    # View Mode Selector
    view_mode = st.sidebar.radio(
        "Navigation Menu:",
        options=[
            "📊 Executive KPI Overview",
            "🕵️ Reseller Surveillance & Recidivism",
            "🔬 Deep Visual Analytics",
        ],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Omni-Channel Filters")

    # Marketplace Filter
    all_marketplaces = sorted(df_violations["Marketplace"].unique())
    selected_marketplaces = st.sidebar.multiselect(
        "Marketplace Channels:",
        options=all_marketplaces,
        default=all_marketplaces,
    )

    # Category Filter
    all_categories = sorted(df_violations["Category"].unique())
    selected_categories = st.sidebar.multiselect(
        "Product Divisions:",
        options=all_categories,
        default=all_categories,
    )

    # Date Range Filter
    min_date = df_violations["Violation_date"].min().date()
    max_date = df_violations["Violation_date"].max().date()
    selected_dates = st.sidebar.date_input(
        "Surveillance Window:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Filter DataFrame
    filtered_df = df_violations.copy()
    if selected_marketplaces:
        filtered_df = filtered_df[filtered_df["Marketplace"].isin(selected_marketplaces)]
    if selected_categories:
        filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = filtered_df[
            (filtered_df["Violation_date"].dt.date >= start_date)
            & (filtered_df["Violation_date"].dt.date <= end_date)
        ]

    # Sidebar Summary Footnote
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"**Filtered Records:** {len(filtered_df):,} / {len(df_violations):,} ({len(filtered_df)/len(df_violations)*100:.1f}%)"
    )
    st.sidebar.caption("Author: **Derin Girish** | License: **MIT**")

    # 3. View Routing
    if view_mode == "📊 Executive KPI Overview":
        render_overview_view(filtered_df, df_suspensions)
    elif view_mode == "🕵️ Reseller Surveillance & Recidivism":
        render_resellers_view(filtered_df, df_suspensions)
    elif view_mode == "🔬 Deep Visual Analytics":
        render_analytics_view(filtered_df)


if __name__ == "__main__":
    main()
