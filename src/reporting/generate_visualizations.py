"""
MAP Compliance & Brand Protection Analytics Engine - Visualization Generator
Generates publication-quality charts and graphs for executive reporting and documentation.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

# Set paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
FIGURES_DIR = BASE_DIR / "data_processed" / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Set high-resolution aesthetics
plt.rcParams["font.sans-serif"] = "Segoe UI, Arial, sans-serif"
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.dpi"] = 300
sns.set_theme(style="whitegrid", palette="muted")

# Corporate brand colors
NAVY = "#1F4E79"
CRIMSON = "#B42828"
AMBER = "#D9822B"
TEAL = "#0F766E"
SLATE = "#475569"


def load_data():
    """Loads violation and price monitoring tables."""
    vio_path = DATA_PATH / "violation_table.csv"
    if not vio_path.exists():
        raise FileNotFoundError(f"Violation table not found at: {vio_path}")
    return pd.read_csv(vio_path)


def plot_violations_by_marketplace(df: pd.DataFrame):
    """Chart 1: Total Violations and Lost Margin / Deficit by Marketplace."""
    mkt_summary = df.groupby("Marketplace").agg(
        total_violations=("SKU", "count"),
        total_deficit=("Price_Difference", "sum")
    ).reset_index().sort_values("total_violations", ascending=False)

    fig, ax1 = plt.subplots(figsize=(10, 5.5))

    x = range(len(mkt_summary))
    bars = ax1.bar(x, mkt_summary["total_violations"], color=NAVY, width=0.5, label="Total Violations")
    ax1.set_ylabel("Violation Incidents (Count)", fontsize=11, fontweight="bold", color=NAVY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(mkt_summary["Marketplace"], fontsize=10, fontweight="bold")
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # Annotate bar values
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f"{int(height):,}",
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    # Secondary axis for total deficit
    ax2 = ax1.twinx()
    ax2.plot(x, mkt_summary["total_deficit"] / 1e6, color=CRIMSON, marker="o", linewidth=2.5, markersize=8, label="Total Price Deficit (M ₹)")
    ax2.set_ylabel("Total Price Deficit (Million ₹)", fontsize=11, fontweight="bold", color=CRIMSON)
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"₹{y:.1f}M"))
    ax2.grid(False)

    plt.title("MAP Policy Violations & Price Deficit by Marketplace", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    output_file = FIGURES_DIR / "01_violations_by_marketplace.png"
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f" Saved: {output_file.name}")


def plot_top_violating_resellers(df: pd.DataFrame):
    """Chart 2: Top 10 Habitual Offender Corporate Resellers by Total Deficit."""
    top_sellers = df.groupby("homologated_name").agg(
        total_deficit=("Price_Difference", "sum"),
        incident_count=("SKU", "count")
    ).reset_index().sort_values("total_deficit", ascending=True).tail(10)

    fig, ax = plt.subplots(figsize=(11, 6))

    bars = ax.barh(top_sellers["homologated_name"], top_sellers["total_deficit"] / 1e6, color=CRIMSON, height=0.6)
    ax.set_xlabel("Cumulative Pricing Deficit Below MAP/LPP (Million ₹)", fontsize=11, fontweight="bold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"₹{x:.1f}M"))
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # Annotate incident count and values
    for bar, (_, row) in zip(bars, top_sellers.iterrows()):
        width = bar.get_width()
        ax.annotate(f"₹{width:.2f}M ({int(row['incident_count'])} alerts)",
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(6, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9, fontweight="bold", color=SLATE)

    plt.title("Top 10 Reseller Entities by Financial Deficit (Holiday Surveillance)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    output_file = FIGURES_DIR / "02_top_10_violating_resellers.png"
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f" Saved: {output_file.name}")


def plot_daily_violation_trend(df: pd.DataFrame):
    """Chart 3: 15-Day Temporal Trend of Violations Across Holiday Surveillance Cycle."""
    daily = df.groupby("Violation_date").agg(
        violations=("SKU", "count"),
        deficit=("Price_Difference", "sum")
    ).reset_index().sort_values("Violation_date")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(daily["Violation_date"], daily["violations"], color=TEAL, marker="s", linewidth=2.5, markersize=6, label="Daily Violation Count")
    ax.fill_between(daily["Violation_date"], daily["violations"], color=TEAL, alpha=0.15)
    ax.set_ylabel("Violation Incidents per Day", fontsize=11, fontweight="bold", color=TEAL)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
    ax.set_xticks(range(len(daily)))
    ax.set_xticklabels(daily["Violation_date"], rotation=35, ha="right", fontsize=9.5)
    ax.grid(True, linestyle="--", alpha=0.5)

    # Highlight peak date
    max_row = daily.loc[daily["violations"].idxmax()]
    ax.annotate(f"Surveillance Peak\n({max_row['Violation_date']}: {int(max_row['violations']):,} alerts)",
                xy=(max_row["Violation_date"], max_row["violations"]),
                xytext=(-60, 20), textcoords="offset points",
                ha="center", va="bottom", fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=CRIMSON, lw=1.5),
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF3F3", edgecolor=CRIMSON, lw=1))

    plt.title("Temporal Trajectory of MAP Policy Breaches (2025-12-21 to 2026-01-05)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    output_file = FIGURES_DIR / "03_daily_violation_trend.png"
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f" Saved: {output_file.name}")


def plot_category_infraction_breakdown(df: pd.DataFrame):
    """Chart 4: Product Category Distribution of Non-Compliant SKU Listings."""
    cat_counts = df["Category"].value_counts()
    category_labels = {
        "PC": "Personal Computers (PC)",
        "PH": "Print Hardware (PH)",
        "PS": "Print Supplies (PS)"
    }
    labels = [category_labels.get(c, c) for c in cat_counts.index]
    colors = [NAVY, TEAL, AMBER]

    fig, ax = plt.subplots(figsize=(7, 6))
    wedges, texts, autotexts = ax.pie(
        cat_counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        explode=(0.04, 0.04, 0.04),
        textprops=dict(fontsize=10.5, fontweight="bold"),
        wedgeprops=dict(width=0.6, edgecolor="white", linewidth=2)
    )

    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(11)

    plt.title(f"MAP Infraction Volume by Product Division (N={len(df):,})", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    output_file = FIGURES_DIR / "04_category_infraction_breakdown.png"
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f" Saved: {output_file.name}")


def plot_price_deficit_distribution(df: pd.DataFrame):
    """Chart 5: Statistical Distribution of Price Discrepancies / Deficits (INR)."""
    fig, ax = plt.subplots(figsize=(10, 5))

    sns.histplot(df["Price_Difference"], bins=50, kde=True, color=NAVY, ax=ax, line_kws={"linewidth": 2, "color": CRIMSON})
    ax.set_xlabel("Under-MAP Price Deficit (INR ₹)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Frequency (Incident Count)", fontsize=11, fontweight="bold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"₹{int(x):,}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
    ax.grid(True, linestyle="--", alpha=0.5)

    # Reference lines for median and 90th percentile
    med = df["Price_Difference"].median()
    p90 = df["Price_Difference"].quantile(0.90)

    ax.axvline(med, color=TEAL, linestyle="--", linewidth=1.8, label=f"Median Deficit: ₹{med:,.0f}")
    ax.axvline(p90, color=CRIMSON, linestyle="--", linewidth=1.8, label=f"90th Percentile: ₹{p90:,.0f}")
    ax.legend(frameon=True, fontsize=10)

    plt.title("Distribution of Price Undercutting Magnitude (Discrepancy Severity)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    output_file = FIGURES_DIR / "05_price_deficit_distribution.png"
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f" Saved: {output_file.name}")


def generate_all_figures():
    """Master controller to generate and export all figures."""
    print("=" * 60)
    print(" GENERATING HIGH-RESOLUTION ANALYTICAL FIGURES")
    print("=" * 60)
    df = load_data()
    print(f"Loaded {len(df):,} records from {DATA_PATH / 'violation_table.csv'}")

    plot_violations_by_marketplace(df)
    plot_top_violating_resellers(df)
    plot_daily_violation_trend(df)
    plot_category_infraction_breakdown(df)
    plot_price_deficit_distribution(df)

    # Generate master dashboard preview
    try:
        from src.reporting.generate_dashboard_preview import create_dashboard_preview
        create_dashboard_preview()
    except Exception as e:
        print(f" Warning: Could not generate dashboard preview: {e}")

    print("=" * 60)
    print(f" All 5 publication-quality figures successfully saved to:")
    print(f" -> {FIGURES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_figures()
