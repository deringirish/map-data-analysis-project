"""
Interactive Visual Analytics & Deep Deficit Exploration View
Author: Derin Girish
Description: Distribution histograms, price scatter comparisons, sub-category treemaps, and data export.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render_analytics_view(df_v: pd.DataFrame):
    """Render Advanced Visual Analytics and Deficit Distribution."""
    st.subheader("🔬 Advanced Price Variance & Deficit Distribution Analytics")
    st.caption("Statistical exploration of undercutting margins, sub-category distribution, and raw telemetry export")

    col_box, col_scatter = st.columns([5, 5])

    # 1. Deficit Box Plot by Category
    with col_box:
        st.markdown("#### 📦 Deficit Severity Spread by Division")
        fig_box = px.box(
            df_v,
            x="Category",
            y="Price_Difference",
            color="Category",
            title="Price Deficit Distribution (INR) across PC, PH, PS",
            points="outliers",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_box.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=30, t=50, b=30),
            yaxis_title="Deficit in INR (₹)",
            showlegend=False,
        )
        st.plotly_chart(fig_box, width="stretch")

    # 2. Scatter Plot: Advertised Price vs. Authorized MAP Price
    with col_scatter:
        st.markdown("#### ⚖️ Advertised Price vs. Statutory MAP Floor")
        sample_df = df_v.sample(min(2500, len(df_v)), random_state=42)

        fig_scatter = px.scatter(
            sample_df,
            x="MAP_Price",
            y="Advertised_price",
            color="Category",
            hover_data=["SKU", "homologated_name", "Marketplace", "Price_Difference"],
            title="Advertised Price vs. Statutory MAP Floor (Sampled)",
            opacity=0.65,
        )
        # Add y = x reference line
        max_val = max(sample_df["MAP_Price"].max(), sample_df["Advertised_price"].max())
        fig_scatter.add_trace(
            go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode="lines",
                line=dict(color="red", dash="dash", width=1.5),
                name="MAP Parity Threshold (y = x)",
            )
        )
        fig_scatter.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=30, t=50, b=30),
            xaxis_title="Statutory MAP (₹)",
            yaxis_title="Advertised Offer Price (₹)",
        )
        st.plotly_chart(fig_scatter, width="stretch")

    # 3. Treemap: Sub-Category Hierarchy
    st.markdown("#### 🗺️ Sub-Category Infraction Treemap")
    treemap_data = (
        df_v.groupby(["Category", "Sub_category", "Marketplace"])
        .agg(Infractions=("SKU", "count"), Total_Deficit=("Price_Difference", "sum"))
        .reset_index()
    )

    fig_tree = px.treemap(
        treemap_data,
        path=["Category", "Sub_category", "Marketplace"],
        values="Total_Deficit",
        color="Total_Deficit",
        color_continuous_scale="Viridis",
        title="Hierarchical Treemap of Cumulative Price Deficit by Sub-Category",
    )
    fig_tree.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig_tree, width="stretch")

    # 4. Filtered Data Download
    st.markdown("---")
    st.markdown("#### 📥 Export Audit Telemetry")
    csv_data = df_v.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered Violation Dataset (CSV)",
        data=csv_data,
        file_name="MAP_Violations_Audit_Export.csv",
        mime="text/csv",
    )
