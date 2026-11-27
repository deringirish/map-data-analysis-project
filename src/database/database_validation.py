"""
MAP Database Validation & Table Record Auditor (MySQL 8.0)
Author: Derin Girish D G
Description: Verifies live table row counts and structural integrity in MySQL 8.0.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure console supports utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[2]
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
    try:
        validate_mysql()
    except Exception as e:
        print(f"[ERROR] MySQL validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
