"""
Dashboard Tab 1: Executive Overview & Time-Series Trajectory
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.theme import AMBER, BLUE, CYAN, apply_dark_theme


def render_overview_tab(filtered_v: pd.DataFrame) -> None:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Daily Non-Compliance Incident Trajectory")
        daily_trend = filtered_v.groupby("Violation_date").agg(
            Violations=("SKU", "count"),
            Deficit=("Price_Difference", "sum"),
        ).reset_index()

        fig_trend = px.area(
            daily_trend,
            x="Violation_date",
            y="Violations",
            title="15-Day Holiday Price Undercutting Volume",
            labels={"Violation_date": "Surveillance Date", "Violations": "Incident Count"},
            color_discrete_sequence=[CYAN],
        )
        fig_trend.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(apply_dark_theme(fig_trend), width="stretch")

    with col_right:
        st.subheader("Infractions by Product Division")
        cat_counts = filtered_v["Category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        cat_labels = {"PC": "Personal Computers (PC)", "PH": "Print Hardware (PH)", "PS": "Supplies (PS)"}
        cat_counts["Category_Name"] = cat_counts["Category"].map(cat_labels).fillna(cat_counts["Category"])

        fig_pie = px.pie(
            cat_counts,
            values="Count",
            names="Category_Name",
            hole=0.45,
            color_discrete_sequence=[BLUE, CYAN, AMBER],
        )
        fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(apply_dark_theme(fig_pie), width="stretch")

    st.subheader("Top 10 Reseller Entities by Margin Erosion")
    top_resellers = (
        filtered_v.groupby("homologated_name")
        .agg(Total_Deficit=("Price_Difference", "sum"), Violations=("SKU", "count"))
        .reset_index()
        .sort_values("Total_Deficit", ascending=False)
        .head(10)
    )

    fig_bar = px.bar(
        top_resellers,
        x="Total_Deficit",
        y="homologated_name",
        orientation="h",
        labels={"Total_Deficit": "Cumulative Deficit (INR ₹)", "homologated_name": "Parent Corporate Entity"},
        color="Total_Deficit",
        color_continuous_scale="Reds",
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(apply_dark_theme(fig_bar), width="stretch")
