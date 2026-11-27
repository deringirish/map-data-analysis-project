"""
Dashboard Tab 4: Interactive What-If Policy Simulator & Elasticity
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.policy_simulator import (
    simulate_discount_elasticity,
    simulate_suspension_thresholds,
    simulate_targeted_enforcement,
)
from src.dashboard.theme import AMBER, CRIMSON, CYAN, TEAL, apply_dark_theme


def render_simulator_tab(filtered_v: pd.DataFrame) -> None:
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
            help="Models the effect of granting authorized retailers additional promotional discount margin during seasonal promotions.",
        )
        sim_res = simulate_discount_elasticity(filtered_v, extra_discount_pct=extra_disc)

        m1, m2, m3 = st.columns(3)
        m1.metric("Simulated Violations", f"{sim_res['simulated_count']:,}", delta=f"-{sim_res['absorbed_count']:,}", delta_color="inverse")
        m2.metric("Violations Absorbed", f"{sim_res['absorption_rate']:.1f}%")
        m3.metric("Deficit Recovered", f"₹{sim_res['recovered_deficit'] / 1e6:.2f}M")

        comp_df = pd.DataFrame(
            {
                "Policy State": ["Baseline Policy", "Simulated Policy", "Absorbed / Cured"],
                "Incident Count": [sim_res["baseline_count"], sim_res["simulated_count"], sim_res["absorbed_count"]],
            }
        )
        fig_comp = px.bar(
            comp_df,
            x="Policy State",
            y="Incident Count",
            color="Policy State",
            color_discrete_sequence=[CRIMSON, CYAN, TEAL],
            title=f"Infraction Absorption at +{extra_disc}% Discount Allowance",
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
            tier_counts,
            values="Accounts",
            names="Status",
            hole=0.45,
            color="Status",
            color_discrete_map={
                "Critical Suspension (30-Day Freeze)": CRIMSON,
                "Formal Suspension (30-Day Category Freeze)": AMBER,
                "Conditional Probation (48-Hr Cure)": CYAN,
            },
            title=f"Account Distribution (Crit: {crit_val}d, Formal: {formal_val}d)",
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
        default=top_10_resellers[:5],
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
