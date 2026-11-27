"""
Dashboard Tab 2: Marketplace Channel Deficit & Pareto Concentration
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.theme import AMBER, BLUE, CRIMSON, CYAN, SLATE, apply_dark_theme


def render_marketplace_tab(filtered_v: pd.DataFrame) -> None:
    st.subheader("Marketplace Channel Deficit & Infraction Breakdown")
    mkt_summary = (
        filtered_v.groupby("Marketplace")
        .agg(
            Incident_Count=("SKU", "count"),
            Total_Deficit=("Price_Difference", "sum"),
            Median_Deficit=("Price_Difference", "median"),
            Mean_Deficit=("Price_Difference", "mean"),
        )
        .reset_index()
        .sort_values("Incident_Count", ascending=False)
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        fig_mkt = px.bar(
            mkt_summary,
            x="Marketplace",
            y="Incident_Count",
            color="Marketplace",
            color_discrete_sequence=[BLUE, CYAN, CRIMSON, AMBER, SLATE],
            title="Violation Volume by Marketplace Channel",
        )
        st.plotly_chart(apply_dark_theme(fig_mkt), width="stretch")

    with col_m2:
        fig_def = px.bar(
            mkt_summary,
            x="Marketplace",
            y="Total_Deficit",
            color="Marketplace",
            color_discrete_sequence=[BLUE, CYAN, CRIMSON, AMBER, SLATE],
            title="Cumulative Deficit (INR ₹) by Marketplace Channel",
        )
        st.plotly_chart(apply_dark_theme(fig_def), width="stretch")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("Pareto Concentration Curve (80/20 Rule)")
        res_df = (
            filtered_v.groupby("homologated_name")["Price_Difference"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        total_def = res_df["Price_Difference"].sum()
        res_df["Cumulative_Deficit"] = res_df["Price_Difference"].cumsum()
        res_df["Cumulative_Pct"] = (res_df["Cumulative_Deficit"] / total_def * 100.0) if total_def > 0 else 0.0
        res_df["Reseller_Rank"] = range(1, len(res_df) + 1)
        res_df["Reseller_Pct"] = (res_df["Reseller_Rank"] / len(res_df) * 100.0) if len(res_df) > 0 else 0.0

        fig_pareto = go.Figure()
        fig_pareto.add_trace(
            go.Scatter(
                x=res_df["Reseller_Pct"],
                y=res_df["Cumulative_Pct"],
                mode="lines",
                line=dict(color=CRIMSON, width=3),
                name="Deficit Concentration",
            )
        )
        fig_pareto.add_trace(
            go.Scatter(
                x=[0, 100],
                y=[0, 100],
                mode="lines",
                line=dict(color=SLATE, dash="dash"),
                name="Equality Baseline",
            )
        )
        fig_pareto.add_hline(y=80, line_dash="dot", line_color=CYAN, annotation_text="80% Deficit Threshold")
        fig_pareto.update_layout(
            xaxis_title="% of Reseller Accounts",
            yaxis_title="Cumulative % of Financial Deficit",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(apply_dark_theme(fig_pareto), width="stretch")

    with col_p2:
        st.subheader("Price Undercutting Deficit Distribution")
        fig_hist = px.histogram(
            filtered_v[filtered_v["Price_Difference"] < filtered_v["Price_Difference"].quantile(0.95)],
            x="Price_Difference",
            nbins=40,
            color_discrete_sequence=[BLUE],
            title="Undercut Magnitude Density (Trimmed at 95th Percentile)",
        )
        fig_hist.update_layout(
            xaxis_title="Price Deficit Below Floor (INR ₹)",
            yaxis_title="Frequency",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(apply_dark_theme(fig_hist), width="stretch")
