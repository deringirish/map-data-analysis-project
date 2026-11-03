"""
Reseller Surveillance & Recidivism Deep-Dive View
Author: Derin Girish
Description: Interactive reseller risk ranking, chronic offender drilldowns, and Charter Obj. 4 suspensions.
"""

from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def render_resellers_view(df_v: pd.DataFrame, df_s: pd.DataFrame):
    """Render Reseller Risk Analysis and Recidivism Suspension Hub."""
    st.subheader("🕵️ Chronic Offender Resellers & Recidivism Enforcement")
    st.caption("Detailed entity-level auditing, repeat infraction strikes, and 30-day category suspensions")

    tab_leaderboard, tab_drilldown, tab_suspensions = st.tabs(
        ["🏆 Top Offender Leaderboard", "🔍 Reseller Drilldown Explorer", "🚨 Category Suspensions Registry"]
    )

    # 1. Top Offender Leaderboard
    with tab_leaderboard:
        st.markdown("#### 📊 Top 10 Chronic Violating Reseller Entities by Cumulative Deficit")
        top_sellers = (
            df_v.groupby("homologated_name")
            .agg(
                Total_Deficit=("Price_Difference", "sum"),
                Infractions=("SKU", "count"),
                Distinct_SKUs=("SKU", "nunique"),
                Marketplaces=("Marketplace", lambda x: ", ".join(sorted(x.unique()))),
            )
            .reset_index()
            .sort_values(by="Total_Deficit", ascending=False)
            .head(10)
        )

        fig_top = px.bar(
            top_sellers,
            x="Total_Deficit",
            y="homologated_name",
            orientation="h",
            title="Top 10 Resellers by Margin Deficit Impact (INR)",
            color="Total_Deficit",
            color_continuous_scale="Reds",
            labels={"Total_Deficit": "Cumulative Deficit (₹)", "homologated_name": "Corporate Reseller"},
        )
        fig_top.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=30, r=30, t=50, b=30),
        )
        st.plotly_chart(fig_top, width="stretch")

        st.dataframe(
            top_sellers.style.format({"Total_Deficit": "₹{:,.2f}", "Infractions": "{:,}"}),
            width="stretch",
            hide_index=True,
        )

    # 2. Reseller Drilldown Explorer
    with tab_drilldown:
        st.markdown("#### 🔎 Entity-Level Violation Investigation")
        all_resellers = sorted(df_v["homologated_name"].unique())
        selected_reseller = st.selectbox("Select Reseller Entity to Inspect:", all_resellers, index=0)

        r_data = df_v[df_v["homologated_name"] == selected_reseller]
        r_suspensions = df_s[df_s["homologated_name"] == selected_reseller]

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Infractions", f"{len(r_data):,}")
        with col_m2:
            st.metric("Cumulative Deficit", f"₹{r_data['Price_Difference'].sum():,.2f}")
        with col_m3:
            st.metric("SKUs Violated", f"{r_data['SKU'].nunique():,}")
        with col_m4:
            is_suspended = len(r_suspensions) > 0
            st.metric(
                "Charter Obj. 4 Status",
                "SUSPENDED" if is_suspended else "ACTIVE",
                delta=f"{len(r_suspensions)} Category Freezes" if is_suspended else "Compliant",
                delta_color="inverse" if is_suspended else "normal",
            )

        st.markdown("##### 📋 Listing Violation Records")
        display_cols = [
            "Violation_date", "SKU", "Category", "Marketplace", "MAP_Price", "LPP", "Advertised_price", "Price_Difference", "Notice_Doc_Path"
        ]
        st.dataframe(
            r_data[display_cols].sort_values(by="Violation_date", ascending=False).style.format(
                {"MAP_Price": "₹{:,.2f}", "LPP": "₹{:,.2f}", "Advertised_price": "₹{:,.2f}", "Price_Difference": "₹{:,.2f}"}
            ),
            width="stretch",
            hide_index=True,
        )

    # 3. Category Suspensions Registry (Charter Objective 4)
    with tab_suspensions:
        st.markdown("#### 🚨 Charter Objective 4: 30-Day Category Suspension Enforcement Registry")
        st.info("Resellers with infractions on 3 or more distinct calendar dates across a category receive an automated 30-day listing freeze.")

        filter_cat = st.multiselect(
            "Filter by Suspended Category:",
            options=sorted(df_s["Category"].unique()),
            default=sorted(df_s["Category"].unique()),
        )
        filtered_susp = df_s[df_s["Category"].isin(filter_cat)]

        st.dataframe(
            filtered_susp[
                [
                    "homologated_name", "Category", "Total_Infractions", "Distinct_Violation_Dates",
                    "Total_Price_Deficit", "Enforcement_Status", "Suspension_Effective_Date", "Suspension_Expiry_Date"
                ]
            ].sort_values(by="Total_Price_Deficit", ascending=False).style.format(
                {"Total_Price_Deficit": "₹{:,.2f}", "Total_Infractions": "{:,}"}
            ),
            width="stretch",
            hide_index=True,
        )
