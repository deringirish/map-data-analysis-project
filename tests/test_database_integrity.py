"""
Unit Tests for Database Schemas & Table Integrity
"""

import pytest
import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
SQLITE_DDL = BASE_DIR / "src" / "database" / "create_tables_sqlite.sql"


def test_sqlite_ddl_execution():
    assert SQLITE_DDL.exists()
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.executescript(SQLITE_DDL.read_text(encoding="utf-8"))

    # Verify all 10 tables exist in SQLite master
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    expected = [
        "SKU", "PL", "PRICE_LIST", "SELLER_MAPPING", "CATEGORY_MAPPING",
        "PROMOTION", "SELLER_TABLE", "PRICE_MONITORING_TABLE",
        "VIOLATION_TABLE", "SUSPENDED_CATEGORIES"
    ]
    for exp in expected:
        assert exp in tables, f"Table {exp} was not created."

    conn.close()
