"""
MAP Compliance & Brand Protection Analytics Engine - Category Suspension Module
Author: Derin Girish D G
Description: Enforces Project Charter Objective 4: Evaluates persistent resellers across
surveillance cycles and formally suspends categories for chronic non-compliant partners.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from dotenv import load_dotenv

# Path configuration
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Load environment configuration
load_dotenv(dotenv_path=BASE_DIR / ".env")


def evaluate_category_suspensions(as_of_date: str = None) -> pd.DataFrame:
    """
    Evaluates violation history by Reseller and Product Category to determine
    formal Category Suspension actions under the Authorized Reseller Agreement.
    Audit date is dynamically determined from the dataset (latest date + 1 day)
    or explicitly provided via `as_of_date`.
    """
    v_table_path = DATA_PATH / "violation_table.csv"
    if not v_table_path.exists():
        raise FileNotFoundError(f"Violation table not found at: {v_table_path}")

    v_df = pd.read_csv(v_table_path)
    print(f"Loaded {len(v_df):,} violation instances for suspension assessment.")

    # Aggregate by Reseller x Category
    agg_df = v_df.groupby(["homologated_name", "Category"]).agg(
        Total_Infractions=("SKU", "count"),
        Distinct_Violation_Dates=("Violation_date", "nunique"),
        Distinct_SKUs_Violated=("SKU", "nunique"),
        Marketplaces_Audited=("Marketplace", lambda m: ", ".join(sorted(m.dropna().unique()))),
        Earliest_Violation=("Violation_date", "min"),
        Latest_Violation=("Violation_date", "max"),
        Max_Single_Deficit=("Price_Difference", "max"),
        Total_Price_Deficit=("Price_Difference", "sum")
    ).reset_index()

    # Determine Suspension Tier & Action
    def classify_suspension(row):
        dates = row["Distinct_Violation_Dates"]
        if dates >= 12:
            return (
                "CRITICAL_SUSPENSION",
                "30-Day Complete Wholesale Freeze & Catalog De-listing",
                30
            )
        elif dates >= 7:
            return (
                "FORMAL_SUSPENSION",
                "30-Day Category Suspension Pending Formal Cure",
                30
            )
        else:
            return (
                "CONDITIONAL_PROBATION",
                "48-Hour Final Cure Notice Before Automatic Category Deactivation",
                0
            )

    results = agg_df.apply(classify_suspension, axis=1)
    agg_df["Enforcement_Status"] = [r[0] for r in results]
    agg_df["Legal_Remedy"] = [r[1] for r in results]
    agg_df["Suspension_Duration_Days"] = [r[2] for r in results]

    # Calculate effective dates dynamically
    if as_of_date:
        audit_date = datetime.strptime(str(as_of_date), "%Y-%m-%d")
    else:
        max_date_str = str(v_df["Violation_date"].dropna().max())
        if max_date_str and max_date_str != "nan":
            audit_date = datetime.strptime(max_date_str, "%Y-%m-%d") + timedelta(days=1)
        else:
            audit_date = datetime.now()

    agg_df["Suspension_Effective_Date"] = audit_date.strftime("%Y-%m-%d")
    agg_df["Suspension_Expiry_Date"] = agg_df.apply(
        lambda r: (audit_date + timedelta(days=int(r["Suspension_Duration_Days"]))).strftime("%Y-%m-%d")
        if r["Suspension_Duration_Days"] > 0 else "N/A (Probationary)",
        axis=1
    )

    # Sort by total deficit descending
    agg_df = agg_df.sort_values("Total_Price_Deficit", ascending=False).reset_index(drop=True)

    # Export to reports and database_tables
    audit_csv = REPORTS_DIR / "category_suspensions_audit.csv"
    table_csv = DATA_PATH / "suspended_categories_table.csv"

    agg_df.to_csv(audit_csv, index=False)
    agg_df.to_csv(table_csv, index=False)

    print(f" Category Suspension Ledger successfully generated:")
    print(f" -> Audit Report: {audit_csv}")
    print(f" -> Database Table CSV: {table_csv}")
    print("\nSummary of Category Enforcement Actions:")
    print(agg_df["Enforcement_Status"].value_counts().to_string())

    return agg_df


def plot_suspension_overview(agg_df: pd.DataFrame):
    """Generates visual chart for Category Suspension actions."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Status Counts
    status_counts = agg_df["Enforcement_Status"].value_counts()
    colors = ["#B42828", "#D9822B", "#1F4E79"]

    bars = ax1.bar(status_counts.index, status_counts.values, color=colors[:len(status_counts)], width=0.5)
    ax1.set_ylabel("Category Accounts Affected", fontsize=11, fontweight="bold")
    ax1.set_title("Reseller Category Suspension Breakdown (N=279)", fontsize=12, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f"{int(h)} accounts\n({h/len(agg_df)*100:.1f}%)",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    # Right: Financial Deficit Exposure by Suspension Tier
    tier_deficit = agg_df.groupby("Enforcement_Status")["Total_Price_Deficit"].sum() / 1e6
    tier_deficit = tier_deficit.reindex(status_counts.index)

    bars2 = ax2.bar(tier_deficit.index, tier_deficit.values, color=colors[:len(tier_deficit)], width=0.5)
    ax2.set_ylabel("Financial Exposure Deficit (Million ₹)", fontsize=11, fontweight="bold")
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"₹{y:.1f}M"))
    ax2.set_title("Total Revenue Discrepancy by Enforcement Tier", fontsize=12, fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in bars2:
        h = bar.get_height()
        ax2.annotate(f"₹{h:.1f}M",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    plt.tight_layout()
    output_file = FIGURES_DIR / "06_category_suspension_status.png"
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f" Saved: {output_file.name}")


def sync_suspensions_to_mysql(agg_df: pd.DataFrame):
    """Syncs the suspension ledger to MySQL or SQLite depending on available engine."""
    records = []
    for _, r in agg_df.iterrows():
        records.append((
            str(r["homologated_name"]),
            str(r["Category"]),
            int(r["Total_Infractions"]),
            int(r["Distinct_Violation_Dates"]),
            int(r["Distinct_SKUs_Violated"]),
            str(r["Marketplaces_Audited"]),
            str(r["Earliest_Violation"]),
            str(r["Latest_Violation"]),
            float(r["Max_Single_Deficit"]),
            float(r["Total_Price_Deficit"]),
            str(r["Enforcement_Status"]),
            str(r["Legal_Remedy"]),
            int(r["Suspension_Duration_Days"]),
            str(r["Suspension_Effective_Date"]),
            str(r["Suspension_Expiry_Date"])
        ))

    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", 3306))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE", "MAP_PROJECT")

    mysql_synced = False
    if mysql_password:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS SUSPENDED_CATEGORIES;")
            cur.execute("""
            CREATE TABLE SUSPENDED_CATEGORIES (
                id INT AUTO_INCREMENT PRIMARY KEY,
                homologated_name VARCHAR(255),
                Category VARCHAR(50),
                Total_Infractions INT,
                Distinct_Violation_Dates INT,
                Distinct_SKUs_Violated INT,
                Marketplaces_Audited TEXT,
                Earliest_Violation DATE,
                Latest_Violation DATE,
                Max_Single_Deficit DECIMAL(12,2),
                Total_Price_Deficit DECIMAL(12,2),
                Enforcement_Status VARCHAR(50),
                Legal_Remedy TEXT,
                Suspension_Duration_Days INT,
                Suspension_Effective_Date DATE,
                Suspension_Expiry_Date VARCHAR(50),
                INDEX idx_susp_seller (homologated_name),
                INDEX idx_susp_cat (Category),
                INDEX idx_susp_status (Enforcement_Status)
            );
            """)

            insert_query = """
            INSERT INTO SUSPENDED_CATEGORIES (
                homologated_name, Category, Total_Infractions, Distinct_Violation_Dates,
                Distinct_SKUs_Violated, Marketplaces_Audited, Earliest_Violation, Latest_Violation,
                Max_Single_Deficit, Total_Price_Deficit, Enforcement_Status, Legal_Remedy,
                Suspension_Duration_Days, Suspension_Effective_Date, Suspension_Expiry_Date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            cur.executemany(insert_query, records)
            conn.commit()
            cur.close()
            conn.close()
            mysql_synced = True
            print(f" Successfully loaded {len(records):,} category suspension records into MySQL `SUSPENDED_CATEGORIES` table.")
        except Exception as e:
            print(f" MySQL synchronization notice: {e}")

    # Fallback or complement to local SQLite
    sqlite_db = DATA_PATH / "map_project.db"
    if not mysql_synced or sqlite_db.exists():
        try:
            import sqlite3
            s_conn = sqlite3.connect(str(sqlite_db))
            s_cur = s_conn.cursor()
            s_cur.execute("DROP TABLE IF EXISTS SUSPENDED_CATEGORIES;")
            s_cur.execute("""
            CREATE TABLE SUSPENDED_CATEGORIES (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homologated_name TEXT,
                Category TEXT,
                Total_Infractions INTEGER,
                Distinct_Violation_Dates INTEGER,
                Distinct_SKUs_Violated INTEGER,
                Marketplaces_Audited TEXT,
                Earliest_Violation DATE,
                Latest_Violation DATE,
                Max_Single_Deficit REAL,
                Total_Price_Deficit REAL,
                Enforcement_Status TEXT,
                Legal_Remedy TEXT,
                Suspension_Duration_Days INTEGER,
                Suspension_Effective_Date DATE,
                Suspension_Expiry_Date TEXT
            );
            """)
            s_insert = """
            INSERT INTO SUSPENDED_CATEGORIES (
                homologated_name, Category, Total_Infractions, Distinct_Violation_Dates,
                Distinct_SKUs_Violated, Marketplaces_Audited, Earliest_Violation, Latest_Violation,
                Max_Single_Deficit, Total_Price_Deficit, Enforcement_Status, Legal_Remedy,
                Suspension_Duration_Days, Suspension_Effective_Date, Suspension_Expiry_Date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            s_cur.executemany(s_insert, records)
            s_conn.commit()
            s_cur.close()
            s_conn.close()
            print(f" Successfully synced {len(records):,} category suspension records into SQLite `SUSPENDED_CATEGORIES` ({sqlite_db.name}).")
        except Exception as se:
            print(f" SQLite synchronization notice: {se}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Category Suspension Evaluation Engine")
    parser.add_argument("--as-of-date", type=str, default=None,
                        help="Audit reference date (YYYY-MM-DD). Defaults to latest date + 1 day.")
    args = parser.parse_args()

    print("=" * 65)
    print(" MAP COMPLIANCE: CATEGORY SUSPENSION ENFORCEMENT ENGINE")
    print("=" * 65)
    df = evaluate_category_suspensions(as_of_date=args.as_of_date)
    plot_suspension_overview(df)
    sync_suspensions_to_mysql(df)
    print("=" * 65)
    print(" Category Suspension Evaluation completed successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
