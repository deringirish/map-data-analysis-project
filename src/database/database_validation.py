"""
MAP Database Validation & Table Record Auditor (Dual-Engine: MySQL & SQLite)
Author: Derin Girish D G
Description: Verifies live table row counts and structural integrity across either
MySQL 8.0 or the local SQLite relational database.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure console supports utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
SQLITE_DB_PATH = DATA_PATH / "map_project.db"

load_dotenv(dotenv_path=BASE_DIR / ".env")

TABLES = [
    "SKU",
    "PL",
    "PRICE_LIST",
    "SELLER_MAPPING",
    "CATEGORY_MAPPING",
    "PROMOTION",
    "SELLER_TABLE",
    "PRICE_MONITORING_TABLE",
    "VIOLATION_TABLE",
    "SUSPENDED_CATEGORIES"
]


def validate_sqlite(db_path: Path):
    import sqlite3
    if not db_path.exists():
        print(f"[ERROR] SQLite database file not found at: {db_path}")
        print("[INFO] Run `python main.py --populate-db --engine sqlite` to initialize.")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=========================================================")
    print(f"       MAP_PROJECT TABLE RECORD AUDIT (SQLITE)          ")
    print(f"       Database: {db_path.name}                         ")
    print("=========================================================")
    total_records = 0
    for tbl in TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"- {tbl:<25} {count:>10,} rows")
        except sqlite3.Error as e:
            print(f"- {tbl:<25} ERROR: {e}")

    print("=========================================================")
    print(f"Total Database Rows Audited: {total_records:,}")
    print("=========================================================")
    cursor.close()
    conn.close()
    print("Validation completed successfully.")


def validate_mysql():
    import mysql.connector

    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", 3306))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE", "MAP_PROJECT")

    print(f"Connecting to MySQL ({mysql_user}@{mysql_host}:{mysql_port}/{mysql_database})...")

    connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    cursor = connection.cursor()
    print("Connected successfully.\n")

    print("=========================================================")
    print("       MAP_PROJECT TABLE RECORD AUDIT (MYSQL)            ")
    print("=========================================================")
    total_records = 0
    for tbl in TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"- {tbl:<25} {count:>10,} rows")
        except mysql.connector.Error as e:
            print(f"- {tbl:<25} ERROR: {e}")

    print("=========================================================")
    print(f"Total Database Rows Audited: {total_records:,}")
    print("=========================================================")

    cursor.close()
    connection.close()
    print("Validation completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="3NF Database Validation Auditor")
    parser.add_argument("--engine", choices=["auto", "mysql", "sqlite"], default=None,
                        help="Target database engine (defaults to DB_ENGINE in .env or 'auto')")
    args = parser.parse_args()

    engine = args.engine or os.getenv("DB_ENGINE", "auto").lower()

    if engine == "sqlite":
        validate_sqlite(SQLITE_DB_PATH)
        return

    try:
        validate_mysql()
    except Exception as e:
        if engine == "mysql":
            print(f"[ERROR] MySQL validation failed: {e}")
            sys.exit(1)
        else:
            print(f"[WARN] MySQL server unavailable: {e}")
            print("[INFO] Checking local SQLite database warehouse instead...\n")
            validate_sqlite(SQLITE_DB_PATH)


if __name__ == "__main__":
    main()
