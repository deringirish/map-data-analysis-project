"""
Interactive Streamlit Business Intelligence Dashboard
Author: Derin Girish D G
Description: Executive analytics portal for multi-channel Minimum Advertised Price (MAP) compliance,
statistical hypothesis testing, Pareto concentration, and reseller enforcement intelligence.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="MAP Compliance & Brand Protection BI Hub",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Color Palette
NAVY = "#1F4E79"
CRIMSON = "#B42828"
TEAL = "#0F766E"
AMBER = "#D9822B"
SLATE = "#475569"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"


@st.cache_data
def load_data():
    """Loads violation, suspension, and price monitoring tables."""
    v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
    susp_df = pd.read_csv(DATA_PATH / "suspended_categories_table.csv") if (DATA_PATH / "suspended_categories_table.csv").exists() else pd.DataFrame()
    return v_df, susp_df


def main():
    st.title("⚖️ Minimum Advertised Price (MAP) Compliance & BI Hub")
    st.markdown(
        "**Multi-Channel Omnichannel Retail Surveillance & Legal Enforcement Intelligence**  \n"
        "*Surveillance Cycle: 2025-12-21 to 2026-01-05 | Monitored Regions: IND, USA, UK, CAN, UAE*"
    )
    st.divider()

    try:
        v_df, susp_df = load_data()
    except Exception as e:
        st.error(f"Error loading datasets: {e}")
        return

    # Sidebar Filters
    st.sidebar.header("🔍 Surveillance Telemetry Filters")
    all_categories = sorted(v_df["Category"].dropna().unique())
    selected_categories = st.sidebar.multiselect("Product Category", all_categories, default=all_categories)

    all_markets = sorted(v_df["Marketplace"].dropna().unique())
    selected_markets = st.sidebar.multiselect("Marketplace Channel", all_markets, default=all_markets)

    # Date Range Filter
    min_date = pd.to_datetime(v_df["Violation_date"]).min().date()
    max_date = pd.to_datetime(v_df["Violation_date"]).max().date()
    date_range = st.sidebar.date_input("Surveillance Window", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        start_d, end_d = str(date_range[0]), str(date_range[1])
    else:
        start_d, end_d = str(min_date), str(max_date)

    # Apply Filters
    filtered_v = v_df[
        (v_df["Category"].isin(selected_categories)) &
        (v_df["Marketplace"].isin(selected_markets)) &
        (v_df["Violation_date"] >= start_d) &
        (v_df["Violation_date"] <= end_d)
    ].copy()

    # Executive KPI Cards
    total_audits = 147900  # Total observations across 15 daily feeds
    total_violations = len(filtered_v)
    compliance_rate = ((total_audits - total_violations) / total_audits) * 100.0
    total_deficit = filtered_v["Price_Difference"].sum()
    active_suspensions = len(susp_df)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Market Audits", f"{total_audits:,}")
    kpi2.metric("Violations Flagged", f"{total_violations:,}", delta=f"-{total_violations:,}", delta_color="inverse")
    kpi3.metric("Global Compliance Rate", f"{compliance_rate:.1f}%")
    kpi4.metric("Cumulative Price Deficit", f"₹{total_deficit / 1e6:.2f}M")
    kpi5.metric("Reseller Suspensions", f"{active_suspensions:,}")

    st.write("")

    # Navigation Tabs
    tab1, tab2, tab3 = st.tabs([
        "📈 Executive Overview & Time-Series",
        "📊 Marketplace & Statistical Rigor",
        "🚨 Reseller Compliance & Legal Notices"
    ])

    # -------------------------------------------------------------
    # TAB 1: EXECUTIVE OVERVIEW
    # -------------------------------------------------------------
    with tab1:
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Daily Non-Compliance Incident Trajectory")
            daily_trend = filtered_v.groupby("Violation_date").agg(
                Violations=("SKU", "count"),
                Deficit=("Price_Difference", "sum")
            ).reset_index()

            fig_trend = px.area(
                daily_trend, x="Violation_date", y="Violations",
                title="15-Day Holiday Price Undercutting Volume",
                labels={"Violation_date": "Surveillance Date", "Violations": "Incident Count"},
                color_discrete_sequence=[TEAL]
            )
            fig_trend.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_trend, use_container_width=True)

        with col_right:
            st.subheader("Infractions by Product Division")
            cat_counts = filtered_v["Category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            cat_labels = {"PC": "Personal Computers (PC)", "PH": "Print Hardware (PH)", "PS": "Supplies (PS)"}
            cat_counts["Category_Name"] = cat_counts["Category"].map(cat_labels).fillna(cat_counts["Category"])

            fig_pie = px.pie(
                cat_counts, values="Count", names="Category_Name",
                hole=0.45,
                color_discrete_sequence=[NAVY, TEAL, AMBER]
            )
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Top 10 Reseller Entities by Margin Erosion")
        top_resellers = filtered_v.groupby("homologated_name").agg(
            Total_Deficit=("Price_Difference", "sum"),
            Violations=("SKU", "count")
        ).reset_index().sort_values("Total_Deficit", ascending=False).head(10)

        fig_bar = px.bar(
            top_resellers, x="Total_Deficit", y="homologated_name", orientation="h",
            labels={"Total_Deficit": "Cumulative Deficit (INR ₹)", "homologated_name": "Parent Corporate Entity"},
            color="Total_Deficit", color_continuous_scale="Reds"
        )
        fig_bar.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------------------------------------
    # TAB 2: MARKETPLACE & STATISTICAL RIGOR
    # -------------------------------------------------------------
    with tab2:
        st.subheader("Marketplace Channel Deficit & Infraction Breakdown")
        mkt_summary = filtered_v.groupby("Marketplace").agg(
            Incident_Count=("SKU", "count"),
            Total_Deficit=("Price_Difference", "sum"),
            Median_Deficit=("Price_Difference", "median"),
            Mean_Deficit=("Price_Difference", "mean")
        ).reset_index().sort_values("Incident_Count", ascending=False)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            fig_mkt = px.bar(
                mkt_summary, x="Marketplace", y="Incident_Count",
                color="Marketplace",
                color_discrete_sequence=[NAVY, TEAL, CRIMSON, AMBER, SLATE],
                title="Violation Volume by Marketplace Channel"
            )
            st.plotly_chart(fig_mkt, use_container_width=True)

        with col_m2:
            fig_def = px.bar(
                mkt_summary, x="Marketplace", y="Total_Deficit",
                color="Marketplace",
                color_discrete_sequence=[NAVY, TEAL, CRIMSON, AMBER, SLATE],
                title="Cumulative Deficit (INR ₹) by Marketplace Channel"
            )
            st.plotly_chart(fig_def, use_container_width=True)

        st.subheader("📊 Inferential Statistical Tests & Hypothesis Verification")
        st.info(
            "**Kruskal-Wallis Test across Marketplaces:** H = 10.6029 (p = 0.0141)  \n"
            "*Interpretation:* Statistically significant difference in undercutting depth across platforms (p < 0.05).  \n"
            "**Pairwise Mann-Whitney Test (Amazon vs Flipkart):** p = 0.00257 (Flipkart Median Deficit: ₹3,049.72 vs Amazon: ₹2,459.68).  \n"
            "**One-Way ANOVA across Product Categories:** F = 1157.03 (p < 0.0001)."
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.subheader("Pareto Concentration Curve (80/20 Rule)")
            res_df = filtered_v.groupby("homologated_name")["Price_Difference"].sum().sort_values(ascending=False).reset_index()
            res_df["Cumulative_Deficit"] = res_df["Price_Difference"].cumsum()
            res_df["Cumulative_Pct"] = (res_df["Cumulative_Deficit"] / res_df["Price_Difference"].sum()) * 100.0
            res_df["Reseller_Rank"] = range(1, len(res_df) + 1)
            res_df["Reseller_Pct"] = (res_df["Reseller_Rank"] / len(res_df)) * 100.0

            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Scatter(x=res_df["Reseller_Pct"], y=res_df["Cumulative_Pct"], mode="lines", line=dict(color=CRIMSON, width=3), name="Deficit Concentration"))
            fig_pareto.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(color=SLATE, dash="dash"), name="Equality Baseline"))
            fig_pareto.add_hline(y=80, line_dash="dot", line_color=NAVY, annotation_text="80% Deficit Threshold")
            fig_pareto.update_layout(xaxis_title="% of Reseller Accounts", yaxis_title="Cumulative % of Financial Deficit", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pareto, use_container_width=True)

        with col_p2:
            st.subheader("Price Undercutting Deficit Distribution")
            fig_hist = px.histogram(
                filtered_v[filtered_v["Price_Difference"] < filtered_v["Price_Difference"].quantile(0.95)],
                x="Price_Difference", nbins=40, color_discrete_sequence=[NAVY],
                title="Undercut Magnitude Density (Trimmed at 95th Percentile)"
            )
            fig_hist.update_layout(xaxis_title="Price Deficit Below Floor (INR ₹)", yaxis_title="Frequency", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_hist, use_container_width=True)

    # -------------------------------------------------------------
    # TAB 3: RESELLER COMPLIANCE & LEGAL NOTICES
    # -------------------------------------------------------------
    with tab3:
        st.subheader("🚨 Legal Escalation & Category Suspension Ledger")
        st.markdown(
            "Pursuant to **Charter Objective 4**, chronic non-compliant resellers are categorized into 3 legal escalation tiers:  \n"
            "- **CRITICAL SUSPENSION (12+ Days):** 30-Day Wholesale Freeze & Catalog De-listing  \n"
            "- **FORMAL SUSPENSION (7-11 Days):** 30-Day Category Freeze Pending Cure  \n"
            "- **CONDITIONAL PROBATION (<7 Days):** 48-Hour Final Cure Notice"
        )

        if not susp_df.empty:
            status_filter = st.multiselect(
                "Filter by Enforcement Status",
                options=sorted(susp_df["Enforcement_Status"].unique()),
                default=sorted(susp_df["Enforcement_Status"].unique())
            )
            search_query = st.text_input("Search Reseller Name", "")

            filtered_susp = susp_df[susp_df["Enforcement_Status"].isin(status_filter)]
            if search_query:
                filtered_susp = filtered_susp[filtered_susp["homologated_name"].str.contains(search_query, case=False, na=False)]

            display_cols = [
                "homologated_name", "Category", "Enforcement_Status", "Total_Infractions",
                "Distinct_Violation_Dates", "Total_Price_Deficit", "Suspension_Duration_Days",
                "Suspension_Effective_Date", "Suspension_Expiry_Date"
            ]
            st.dataframe(
                filtered_susp[display_cols].style.format({
                    "Total_Price_Deficit": "₹{:,.2f}",
                    "Total_Infractions": "{:,}",
                    "Distinct_Violation_Dates": "{:,}"
                }),
                use_container_width=True,
                height=450
            )

        st.subheader("📁 Automated Legal Warning Notice Explorer")
        st.markdown(
            "Every non-compliant `(Homologated_Reseller, Category)` group has a formal **279 `.docx` warning notice** generated in `data_processed/reports/notices/`."
        )

        all_notice_resellers = sorted(v_df["homologated_name"].dropna().unique())
        selected_reseller = st.selectbox("Select Reseller for Case File Dossier", all_notice_resellers)

        if selected_reseller:
            res_violations = v_df[v_df["homologated_name"] == selected_reseller]
            st.write(f"**Audit Profile:** {selected_reseller}")
            c1, c2, c3 = st.columns(3)
            c1.write(f"• Total Violations: **{len(res_violations):,}**")
            c2.write(f"• Total Price Deficit: **₹{res_violations['Price_Difference'].sum():,.2f}**")
            c3.write(f"• Markets Active: **{', '.join(res_violations['Marketplace'].dropna().unique())}**")

            st.dataframe(
                res_violations[["Violation_date", "Category", "Sub_category", "SKU", "Marketplace", "Advertised_price", "MAP_Price", "LPP", "Price_Difference", "Notice_Doc_Path"]].head(25),
                use_container_width=True
            )


if __name__ == "__main__":
    main()
