"""
Executive KPI Overview & Global Surveillance View
Author: Derin Girish
Description: Interactive executive overview, KPI metric cards, time series trends, and marketplace profiles.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render_overview_view(df_v: pd.DataFrame, df_s: pd.DataFrame):
    """Render Executive KPI Overview & Surveillance Analytics."""
    st.subheader("🎯 Executive KPI Overview & Holiday Surveillance Scope")
    st.caption("Surveillance trajectory across 147,900 omni-channel listings (Dec 21, 2025 – Jan 05, 2026)")

    # 1. KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    total_violations = len(df_v)
    total_deficit = df_v["Price_Difference"].sum()
    active_suspensions = len(df_s)
    unique_sellers = df_v["homologated_name"].nunique()

    with col1:
        st.metric(
            label="Total Policy Violations",
            value=f"{total_violations:,}",
            help="Total confirmed listings advertising below authorized MAP or LPP floors",
        )
    with col2:
        st.metric(
            label="Cumulative Margin at Risk",
            value=f"₹{total_deficit / 1e7:.2f} Cr",
            delta=f"₹{total_deficit:,.0f} Total Deficit",
            delta_color="inverse",
            help="Total monetary shortfall between advertised price and authorized floor in INR",
        )
    with col3:
        st.metric(
            label="Category Suspensions",
            value=f"{active_suspensions:,}",
            delta="Charter Obj. 4 Enforced",
            help="Resellers with 3+ distinct date recidivism infractions placed on 30-day listing freeze",
        )
    with col4:
        st.metric(
            label="Monitored Rogue Entities",
            value=f"{unique_sellers:,}",
            help="Distinct corporate parent reseller entities flagged across channels",
        )

    st.markdown("---")

    # 2. Charts Row: Daily Violation Trend & Marketplace Breakdown
    c_left, c_right = st.columns([6, 4])

    with c_left:
        st.markdown("#### 📈 Holiday Shopping Surveillance Trajectory (Daily Trend)")
        daily_counts = (
            df_v.groupby(df_v["Violation_date"].dt.date)
            .agg(Violations=("SKU", "count"), Total_Deficit=("Price_Difference", "sum"))
            .reset_index()
        )
        daily_counts["Violation_date"] = pd.to_datetime(daily_counts["Violation_date"])

        fig_trend = px.area(
            daily_counts,
            x="Violation_date",
            y="Violations",
            title="Daily Policy Infraction Surges Across Holiday Shopping Window",
            labels={"Violation_date": "Surveillance Date", "Violations": "Infraction Count"},
            color_discrete_sequence=["#6366f1"],
        )
        fig_trend.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=30, t=50, b=30),
            hovermode="x unified",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with c_right:
        st.markdown("#### 🛒 Infractions by Marketplace Channel")
        mp_data = (
            df_v.groupby("Marketplace")
            .agg(Count=("SKU", "count"), Deficit=("Price_Difference", "sum"))
            .reset_index()
            .sort_values(by="Count", ascending=True)
        )

        fig_mp = px.bar(
            mp_data,
            x="Count",
            y="Marketplace",
            orientation="h",
            title="Violation Volume by E-Commerce Channel",
            color="Count",
            color_continuous_scale="Purples",
            text="Count",
        )
        fig_mp.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=30, t=50, b=30),
            showlegend=False,
        )
        st.plotly_chart(fig_mp, use_container_width=True)

    # 3. Bottom Row: Category Breakdown & Spot FX Cross-Border Telemetry
    col_cat, col_fx = st.columns([5, 5])

    with col_cat:
        st.markdown("#### 📦 Product Division Breakdown")
        cat_data = (
            df_v.groupby("Category")
            .agg(Count=("SKU", "count"), Deficit=("Price_Difference", "sum"))
            .reset_index()
        )
        fig_cat = px.pie(
            cat_data,
            names="Category",
            values="Count",
            title="Violations by Division (PC vs PH vs PS)",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        fig_cat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=30, t=50, b=30),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_fx:
        st.markdown("#### 🌐 Cross-Border Source Regions")
        region_data = (
            df_v.groupby("Region")
            .agg(Count=("SKU", "count"), Total_Deficit=("Price_Difference", "sum"))
            .reset_index()
            .sort_values(by="Total_Deficit", ascending=False)
        )
        fig_reg = px.bar(
            region_data,
            x="Region",
            y="Total_Deficit",
            title="Cumulative Deficit (INR) by Source Region",
            color="Total_Deficit",
            color_continuous_scale="Reds",
        )
        fig_reg.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=30, t=50, b=30),
            yaxis_title="Deficit in INR (₹)",
        )
        st.plotly_chart(fig_reg, use_container_width=True)
