"""
Dashboard Tab 3: Reseller Category Suspensions & Legal Warning Notice Explorer
"""

import pandas as pd
import streamlit as st


def render_compliance_tab(v_df: pd.DataFrame, susp_df: pd.DataFrame) -> None:
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
            default=sorted(susp_df["Enforcement_Status"].unique()),
        )
        search_query = st.text_input("Search Reseller Name", "")

        filtered_susp = susp_df[susp_df["Enforcement_Status"].isin(status_filter)]
        if search_query:
            filtered_susp = filtered_susp[
                filtered_susp["homologated_name"].str.contains(search_query, case=False, na=False)
            ]

        display_cols = [
            "homologated_name",
            "Category",
            "Enforcement_Status",
            "Total_Infractions",
            "Distinct_Violation_Dates",
            "Total_Price_Deficit",
            "Suspension_Duration_Days",
            "Suspension_Effective_Date",
            "Suspension_Expiry_Date",
        ]
        st.dataframe(
            filtered_susp[display_cols].style.format(
                {
                    "Total_Price_Deficit": "₹{:,.2f}",
                    "Total_Infractions": "{:,}",
                    "Distinct_Violation_Dates": "{:,}",
                }
            ),
            width="stretch",
            height=450,
        )

    st.subheader("📁 Automated Legal Warning Notice Explorer")
    st.markdown(
        "Every non-compliant `(Homologated_Reseller, Category)` group has a formal **`.docx` warning notice** "
        "generated in `data_processed/reports/notices/`."
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
            res_violations[
                [
                    "Violation_date",
                    "Category",
                    "Sub_category",
                    "SKU",
                    "Marketplace",
                    "Advertised_price",
                    "MAP_Price",
                    "LPP",
                    "Price_Difference",
                    "Notice_Doc_Path",
                ]
            ].head(25),
            width="stretch",
        )
