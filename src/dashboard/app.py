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

from src.analytics.policy_simulator import (
    simulate_discount_elasticity,
    simulate_suspension_thresholds,
    simulate_targeted_enforcement
)

# Configure page
st.set_page_config(
    page_title="MAP Compliance & Brand Protection BI Hub",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme High-Contrast Palette
CYAN = "#00D2FF"
CRIMSON = "#FF4B4B"
TEAL = "#00E676"
AMBER = "#FFA726"
SLATE = "#94A3B8"
BLUE = "#3B82F6"
PURPLE = "#AB47BC"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"


def apply_dark_theme(fig):
    """Applies modern dark-theme styling with transparent background to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA", family="sans-serif")
    )
    return fig


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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview & Time-Series",
        "📊 Marketplace & Statistical Rigor",
        "🚨 Reseller Compliance & Legal Notices",
        "🎛️ What-If Policy Simulator & Elasticity"
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
                color_discrete_sequence=[CYAN]
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
                cat_counts, values="Count", names="Category_Name",
                hole=0.45,
                color_discrete_sequence=[BLUE, CYAN, AMBER]
            )
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(apply_dark_theme(fig_pie), width="stretch")

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
        st.plotly_chart(apply_dark_theme(fig_bar), width="stretch")

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
                color_discrete_sequence=[BLUE, CYAN, CRIMSON, AMBER, SLATE],
                title="Violation Volume by Marketplace Channel"
            )
            st.plotly_chart(apply_dark_theme(fig_mkt), width="stretch")

        with col_m2:
            fig_def = px.bar(
                mkt_summary, x="Marketplace", y="Total_Deficit",
                color="Marketplace",
                color_discrete_sequence=[BLUE, CYAN, CRIMSON, AMBER, SLATE],
                title="Cumulative Deficit (INR ₹) by Marketplace Channel"
            )
            st.plotly_chart(apply_dark_theme(fig_def), width="stretch")

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
            fig_pareto.add_hline(y=80, line_dash="dot", line_color=CYAN, annotation_text="80% Deficit Threshold")
            fig_pareto.update_layout(xaxis_title="% of Reseller Accounts", yaxis_title="Cumulative % of Financial Deficit", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(apply_dark_theme(fig_pareto), width="stretch")

        with col_p2:
            st.subheader("Price Undercutting Deficit Distribution")
            fig_hist = px.histogram(
                filtered_v[filtered_v["Price_Difference"] < filtered_v["Price_Difference"].quantile(0.95)],
                x="Price_Difference", nbins=40, color_discrete_sequence=[BLUE],
                title="Undercut Magnitude Density (Trimmed at 95th Percentile)"
            )
            fig_hist.update_layout(xaxis_title="Price Deficit Below Floor (INR ₹)", yaxis_title="Frequency", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(apply_dark_theme(fig_hist), width="stretch")

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
                width="stretch",
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
                width="stretch"
            )

    # -------------------------------------------------------------
    # TAB 4: WHAT-IF POLICY SIMULATOR & ELASTICITY
    # -------------------------------------------------------------
    with tab4:
        st.subheader("🎛️ Executive What-If Policy Simulation & Decision Support")
        st.markdown(
            "Model how **commercial policy adjustments** (promotional discount allowances, recidivism cutoffs, "
            "and targeted partner cures) impact market compliance and protect gross margins."
        )

        sim_col1, sim_col2 = st.columns([1, 1])

        with sim_col1:
            st.markdown("#### 1. Promotional Discount Allowance Sensitivity")
            extra_disc = st.slider(
                "Expand Promotional Discount Allowance (+%)",
                min_value=0.0,
                max_value=15.0,
                value=2.0,
                step=0.5,
                help="Models the effect of granting authorized retailers additional promotional discount margin during seasonal promotions."
            )
            sim_res = simulate_discount_elasticity(filtered_v, extra_discount_pct=extra_disc)

            # Metric Cards
            m1, m2, m3 = st.columns(3)
            m1.metric("Simulated Violations", f"{sim_res['simulated_count']:,}", delta=f"-{sim_res['absorbed_count']:,}", delta_color="inverse")
            m2.metric("Violations Absorbed", f"{sim_res['absorption_rate']:.1f}%")
            m3.metric("Deficit Recovered", f"₹{sim_res['recovered_deficit'] / 1e6:.2f}M")

            # Comparison Bar Chart
            comp_df = pd.DataFrame({
                "Policy State": ["Baseline Policy", "Simulated Policy", "Absorbed / Cured"],
                "Incident Count": [sim_res["baseline_count"], sim_res["simulated_count"], sim_res["absorbed_count"]]
            })
            fig_comp = px.bar(
                comp_df, x="Policy State", y="Incident Count", color="Policy State",
                color_discrete_sequence=[CRIMSON, CYAN, TEAL],
                title=f"Infraction Absorption at +{extra_disc}% Discount Allowance"
            )
            st.plotly_chart(apply_dark_theme(fig_comp), width="stretch")

        with sim_col2:
            st.markdown("#### 2. Recidivism Escalation Policy Sensitivity")
            crit_val = st.slider("Critical Freeze Threshold (Days)", min_value=6, max_value=15, value=12)
            formal_val = st.slider("Formal Suspension Threshold (Days)", min_value=3, max_value=10, value=7)

            sim_susp = simulate_suspension_thresholds(filtered_v, critical_days=crit_val, formal_days=formal_val)
            tier_counts = sim_susp["Simulated_Status"].value_counts().reset_index()
            tier_counts.columns = ["Status", "Accounts"]

            fig_susp_sim = px.pie(
                tier_counts, values="Accounts", names="Status",
                hole=0.45,
                color="Status",
                color_discrete_map={
                    "Critical Suspension (30-Day Freeze)": CRIMSON,
                    "Formal Suspension (30-Day Category Freeze)": AMBER,
                    "Conditional Probation (48-Hr Cure)": CYAN
                },
                title=f"Account Distribution (Crit: {crit_val}d, Formal: {formal_val}d)"
            )
            st.plotly_chart(apply_dark_theme(fig_susp_sim), width="stretch")

        st.divider()
        st.markdown("#### 3. Strategic Targeted Reseller Cure Simulator")
        st.markdown(
            "Simulate the financial and operational impact of **bringing specific high-deficit chronic resellers into full compliance**."
        )

        top_10_resellers = list(
            filtered_v.groupby("homologated_name")["Price_Difference"].sum().sort_values(ascending=False).head(10).index
        )
        selected_targets = st.multiselect(
            "Select Target Corporate Reseller Entities to Enforce / Cure",
            options=sorted(filtered_v["homologated_name"].dropna().unique()),
            default=top_10_resellers[:5]
        )

        target_res = simulate_targeted_enforcement(filtered_v, selected_targets)
        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Targeted Accounts", f"{target_res['targeted_sellers_count']}")
        tc2.metric("Violations Eliminated", f"{target_res['targeted_violations']:,}")
        tc3.metric("Deficit Recovered", f"₹{target_res['targeted_deficit'] / 1e6:.2f}M")
        tc4.metric("Share of Total Deficit", f"{target_res['pct_deficit_recovered']:.1f}%")

        if selected_targets:
            st.info(
                f"💡 **Strategic Executive Takeaway:** Curing compliance on just **{target_res['targeted_sellers_count']} parent resellers** "
                f"recovers **₹{target_res['targeted_deficit'] / 1e6:.2f} Million ({target_res['pct_deficit_recovered']:.1f}%)** of all margin erosion "
                f"across the market, while eliminating **{target_res['targeted_violations']:,}** infractions."
            )


if __name__ == "__main__":
    main()
