"""
MAP Relational Database Population Subsystem (MySQL 8.0)
Author: Derin Girish D G
Description: Automated batch ingestion into the 3NF MySQL relational warehouse.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import pandas as pd
from dotenv import load_dotenv

# Ensure console supports utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"

load_dotenv(dotenv_path=BASE_DIR / ".env")

TABLES_CLEAR_ORDER = [
    "SUSPENDED_CATEGORIES",
    "VIOLATION_TABLE",
    "PRICE_MONITORING_TABLE",
    "SELLER_TABLE",
    "PROMOTION",
    "CATEGORY_MAPPING",
    "PRICE_LIST",
    "PL",
    "SELLER_MAPPING",
    "SKU",
]


def _insert_dataframe_in_batches(
    cursor,
    conn,
    table_name: str,
    df: pd.DataFrame,
    csv_cols: List[str],
    db_cols: List[str],
    placeholder: str,
    chunk_size: int = 10000,
) -> int:
    """Inserts a DataFrame into a SQL table using vectorized NaN->None conversion and batched executemany."""
    work_df = df.copy()
    for col in csv_cols:
        if col not in work_df.columns:
            work_df[col] = None
    work_df = work_df[csv_cols]
    work_df = work_df.astype(object).where(pd.notna(work_df), None)

    placeholders = ", ".join([placeholder] * len(db_cols))
    cols_sql = ", ".join(db_cols)
    query = f"INSERT INTO {table_name} ({cols_sql}) VALUES ({placeholders})"

    rows = list(work_df.itertuples(index=False, name=None))
    total = len(rows)
    for start in range(0, total, chunk_size):
        cursor.executemany(query, rows[start : start + chunk_size])
        conn.commit()
    print(f"[OK] {table_name:<23} {total:>10,} rows inserted.")
    return total


def _populate_all_tables(cursor, conn, placeholder: str = "%s") -> None:
    """Shared 10-table 3NF ingestion pipeline for MySQL."""
    specs: List[Tuple[str, str, List[str], List[str]]] = [
        ("SKU", "sku_table.csv", ["PN", "SKU"], ["PN", "SKU"]),
        ("PL", "pl_table.csv", ["PL", "SKU", "SUB_CATEGORY"], ["PL", "SKU", "SUB_CATEGORY"]),
        ("PRICE_LIST", "price_list_table.csv", ["PL", "SKU", "MAP", "LPP"], ["PL", "SKU", "MAP", "LPP"]),
        ("SELLER_MAPPING", "seller_mapping_table.csv", ["SELLER_NAME", "HOMOLOGATED_NAME"], ["SELLER_NAME", "HOMOLOGATED_NAME"]),
        ("CATEGORY_MAPPING", "category_mapping_table.csv", ["CATEGORY", "SUB_CATEGORY", "PL", "SKU"], ["CATEGORY", "SUB_CATEGORY", "PL", "SKU"]),
    ]

    for tbl, csv_name, csv_cols, db_cols in specs:
        df = pd.read_csv(DATA_PATH / csv_name)
        _insert_dataframe_in_batches(cursor, conn, tbl, df, csv_cols, db_cols, placeholder)

    prom_df = pd.read_csv(DATA_PATH / "promotion_table.csv").dropna(subset=["PL", "SKU", "SEASON", "PROMOTION"])
    _insert_dataframe_in_batches(
        cursor, conn, "PROMOTION", prom_df,
        ["PL", "SKU", "SEASON", "PROMOTION"], ["PL", "SKU", "SEASON", "PROMOTION"], placeholder,
    )

    seller_df = pd.read_csv(DATA_PATH / "seller_table.csv")
    _insert_dataframe_in_batches(
        cursor, conn, "SELLER_TABLE", seller_df,
        ["Seller_name", "SKU", "Region", "Advertised_price", "Marketplace", "Screenshot", "Live_link", "Last time collected"],
        ["Seller_name", "SKU", "Region", "Advertised_price", "Marketplace", "Screenshot", "Live_link", "Last_time_collected"],
        placeholder,
    )

    pm_df = pd.read_csv(DATA_PATH / "price_monitoring_table.csv")
    pm_cols = [
        "SKU", "Violation_date", "PL", "Category", "Sub_category", "Region", "Marketplace",
        "seller_name", "homologated_name", "MAP_Price", "LPP", "Advertised_price", "Season", "Promotional_price",
    ]
    _insert_dataframe_in_batches(cursor, conn, "PRICE_MONITORING_TABLE", pm_df, pm_cols, pm_cols, placeholder)

    v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
    v_cols = [
        "SKU", "Violation_date", "PL", "Category", "Sub_category", "Region", "Marketplace",
        "seller_name", "homologated_name", "MAP_Price", "LPP", "Advertised_price", "Season",
        "Promotion", "Promotional_price", "Screenshot", "Violation_Type", "Price_Difference", "Notice_Doc_Path",
    ]
    _insert_dataframe_in_batches(cursor, conn, "VIOLATION_TABLE", v_df, v_cols, v_cols, placeholder)

    susp_csv = DATA_PATH / "suspended_categories_table.csv"
    if susp_csv.exists():
        susp_df = pd.read_csv(susp_csv)
        susp_cols = [
            "homologated_name", "Category", "Total_Infractions", "Distinct_Violation_Dates",
            "Distinct_SKUs_Violated", "Marketplaces_Audited", "Earliest_Violation", "Latest_Violation",
            "Max_Single_Deficit", "Total_Price_Deficit", "Enforcement_Status", "Legal_Remedy",
            "Suspension_Duration_Days", "Suspension_Effective_Date", "Suspension_Expiry_Date",
        ]
        _insert_dataframe_in_batches(cursor, conn, "SUSPENDED_CATEGORIES", susp_df, susp_cols, susp_cols, placeholder)


def _print_summary(cursor, engine_label: str) -> None:
    print("\n=========================================================")
    print(f"      FINAL DATABASE POPULATION SUMMARY ({engine_label})     ")
    print("=========================================================")
    for tbl in TABLES_CLEAR_ORDER:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        print(f"• {tbl:<25} {cnt:>10,} rows")
    print("=========================================================")


def populate_mysql() -> None:
    """Populates 3NF schema and all datasets into MySQL server."""
    import mysql.connector

    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", 3306))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")

    print(f"Connecting to MySQL ({mysql_user}@{mysql_host}:{mysql_port})...")
    connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        autocommit=False,
    )
    cursor = connection.cursor()
    print(" Connected to MySQL server successfully.")

    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS MAP_PROJECT;")
        cursor.execute("USE MAP_PROJECT;")

        ddl_file = Path(__file__).resolve().parent / "create_tables.sql"
        if ddl_file.exists():
            ddl_script = ddl_file.read_text(encoding="utf-8")
            for stmt in (s.strip() for s in ddl_script.split(";") if s.strip()):
                clean_stmt = "\n".join(
                    line for line in stmt.splitlines() if not line.strip().startswith("--")
                ).strip()
                if clean_stmt:
                    cursor.execute(clean_stmt)
            connection.commit()
            print(" Schema verified and all tables initialized.")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for tbl in TABLES_CLEAR_ORDER:
            cursor.execute(f"TRUNCATE TABLE {tbl};")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        connection.commit()
        print(" Cleared existing tables for fresh batch population.\n")

        _populate_all_tables(cursor, connection, placeholder="%s")
        _print_summary(cursor, "MYSQL")
        print(" All 10 tables populated and committed to MySQL.")
    except Exception as err:
        connection.rollback()
        print(f"\n Error occurred during MySQL database population: {err}")
        raise
    finally:
        cursor.close()
        connection.close()


def validate_mysql() -> None:
    """Verifies live table row counts across all 10 tables in MySQL 8.0."""
    import mysql.connector

    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", 3306))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE", "MAP_PROJECT")

    connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database,
    )
    cursor = connection.cursor()
    print("\n=========================================================")
    print("       MAP_PROJECT TABLE RECORD AUDIT (MYSQL)            ")
    print("=========================================================")
    total_records = 0
    for tbl in reversed(TABLES_CLEAR_ORDER):
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        count = cursor.fetchone()[0]
        total_records += count
        print(f"- {tbl:<25} {count:>10,} rows")
    print("=========================================================")
    print(f"Total Database Rows Audited: {total_records:,}")
    print("=========================================================")
    cursor.close()
    connection.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="3NF MySQL Database Population & Validation")
    parser.add_argument("--validate", action="store_true", help="Run MySQL row count validation audit only")
    args = parser.parse_args()

    try:
        if args.validate:
            validate_mysql()
        else:
            populate_mysql()
    except Exception as e:
        print(f"[ERROR] MySQL operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
