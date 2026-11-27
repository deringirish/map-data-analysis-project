"""
Automated Executive C-Suite 1-Page Briefing Generator
Author: Derin Girish D G
Description: Compiles macro KPIs and renders EXECUTIVE_C_SUITE_BRIEFING.html and .md.
"""

import sys
from pathlib import Path
from string import Template
from typing import Any, Dict
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.analytics.business_kpis import calculate_pareto_concentration
from src.config.finance_config import STATUS_CRITICAL, STATUS_FORMAL, STATUS_PROBATION

DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"
HTML_TEMPLATE_PATH = Path(__file__).resolve().parent / "briefing_template.html"


def compile_executive_metrics() -> Dict[str, Any]:
    """Compiles macro KPIs for the C-Suite briefing."""
    pm_path = DATA_PATH / "price_monitoring_table.csv"
    v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
    susp_path = DATA_PATH / "suspended_categories_table.csv"
    susp_df = pd.read_csv(susp_path) if susp_path.exists() else pd.DataFrame()

    total_audits = len(pd.read_csv(pm_path, usecols=["SKU"])) if pm_path.exists() else len(v_df)
    violations_count = len(v_df)
    compliance_rate = ((total_audits - violations_count) / total_audits) * 100.0 if total_audits > 0 else 0.0
    total_deficit = float(v_df["Price_Difference"].sum())

    _, pareto_stats = calculate_pareto_concentration()

    crit_count = int((susp_df["Enforcement_Status"] == STATUS_CRITICAL).sum()) if not susp_df.empty else 0
    formal_count = int((susp_df["Enforcement_Status"] == STATUS_FORMAL).sum()) if not susp_df.empty else 0
    prob_count = int((susp_df["Enforcement_Status"] == STATUS_PROBATION).sum()) if not susp_df.empty else 0

    mkt_summary = (
        v_df.groupby("Marketplace")
        .agg(Count=("SKU", "count"), Deficit=("Price_Difference", "sum"))
        .reset_index()
        .sort_values("Deficit", ascending=False)
    )
    top_mkt = mkt_summary.iloc[0]["Marketplace"] if not mkt_summary.empty else "N/A"
    top_mkt_deficit = float(mkt_summary.iloc[0]["Deficit"]) if not mkt_summary.empty else 0.0

    return {
        "total_audits": total_audits,
        "violations_count": violations_count,
        "compliance_rate": compliance_rate,
        "total_deficit": total_deficit,
        "total_sellers": pareto_stats["total_resellers"],
        "sellers_80_pct": pareto_stats["resellers_for_80pct_deficit"],
        "total_suspensions": len(susp_df),
        "critical_suspensions": crit_count,
        "formal_suspensions": formal_count,
        "probation_count": prob_count,
        "top_marketplace": top_mkt,
        "top_marketplace_deficit": top_mkt_deficit,
        "mkt_summary": mkt_summary,
    }


def generate_html_briefing(metrics: Dict[str, Any]) -> str:
    """Renders the responsive executive HTML briefing from briefing_template.html."""
    template = Template(HTML_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.safe_substitute(
        compliance_rate=f"{metrics['compliance_rate']:.1f}",
        total_deficit_m=f"{metrics['total_deficit'] / 1e6:.2f}",
        critical_suspensions=f"{metrics['critical_suspensions']:,}",
        critical_suspensions_raw=metrics["critical_suspensions"],
        sellers_80_pct=metrics["sellers_80_pct"],
        total_sellers=metrics["total_sellers"],
        pareto_deficit_m=f"{metrics['total_deficit'] * 0.8 / 1e6:.2f}",
        top_marketplace=metrics["top_marketplace"],
        top_marketplace_deficit_m=f"{metrics['top_marketplace_deficit'] / 1e6:.2f}",
        total_audits=f"{metrics['total_audits']:,}",
        violations_count=f"{metrics['violations_count']:,}",
    )


def generate_markdown_briefing(metrics: Dict[str, Any]) -> str:
    """Generates an executive Markdown briefing document."""
    return f"""# ⚖️ Executive C-Suite Intelligence Briefing
**Omnichannel Minimum Advertised Price (MAP) Surveillance & Legal Enforcement Lifecycle**  
*Surveillance Window: 2025-12-21 to 2026-01-05 (15 Days) | Scope: IND, USA, UK, CAN, UAE*

---

## 📊 1. Macro Compliance Scorecard

| Metric | Measured Value | Business Interpretation |
| :--- | :---: | :--- |
| **Global Market Compliance** | **{metrics['compliance_rate']:.1f}%** | Listings adhering to established statutory MAP/LPP floors. |
| **Cumulative Margin Deficit** | **₹{metrics['total_deficit'] / 1e6:.2f}M** | Total monetary undercutting inflicted on authorized distributor margins. |
| **Total Infractions Flagged** | **{metrics['violations_count']:,}** | Filtered actionable breaches out of {metrics['total_audits']:,} daily feed observations. |
| **Reseller Accounts Frozen** | **{metrics['critical_suspensions']:,}** | High-recidivism accounts placed under mandatory 30-day wholesale freeze. |
| **Pareto Offender Core** | **{metrics['sellers_80_pct']} Resellers** | **80% of price deficit** is driven by just {metrics['sellers_80_pct']} corporate entities. |

---

## ⚖️ 2. Legal Enforcement Actions Executed

* **279 Itemized Warning Notices:** Formatted `.docx` legal notices generated with executive callouts, sub-category audit tables, and 48-hour cure mandates.
* **Charter Objective 4 Escalations:**
  * **Critical Suspension (30-Day Freeze):** {metrics['critical_suspensions']} accounts (≥ 12 violation days).
  * **Formal Suspension (30-Day Category Freeze):** {metrics['formal_suspensions']} accounts (7-11 violation days).
  * **Conditional Probation (48-Hr Cure):** {metrics['probation_count']} accounts (< 7 violation days).

---

## 🎯 3. Strategic Executive Roadmap (Next Quarter)

1. **Targeted Enforcement:** Concentrate legal remedies on the {metrics['sellers_80_pct']} Pareto entities to eliminate 80% of margin loss (₹{metrics['total_deficit'] * 0.8 / 1e6:.2f}M).
2. **Dynamic Promotional Ceiling:** Authorize a +2.0% holiday promotional discount window to absorb benign promotional bursts without compromising MAP integrity.
3. **Cross-Marketplace Monitoring:** Deploy automated price-matching monitors across top channels ({metrics['top_marketplace']}, etc.) to intercept cascading undercutting.

---
*Confidential — For Internal C-Suite Steering Committee Only*
"""


def main() -> None:
    """Entrypoint to generate both HTML and Markdown executive briefings."""
    print("[INFO] Compiling executive metrics from production warehouse tables...")
    metrics = compile_executive_metrics()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = REPORTS_DIR / "EXECUTIVE_C_SUITE_BRIEFING.html"
    md_path = REPORTS_DIR / "EXECUTIVE_C_SUITE_BRIEFING.md"

    html_path.write_text(generate_html_briefing(metrics), encoding="utf-8")
    print(f"[OK] Generated Executive HTML Briefing -> {html_path.name}")

    md_path.write_text(generate_markdown_briefing(metrics), encoding="utf-8")
    print(f"[OK] Generated Executive Markdown Briefing -> {md_path.name}")


if __name__ == "__main__":
    main()
