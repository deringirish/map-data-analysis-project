"""
Unit Tests for MySQL Database Schema & Table Integrity
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MYSQL_DDL = BASE_DIR / "src" / "database" / "create_tables.sql"


def test_mysql_ddl_schema():
    assert MYSQL_DDL.exists(), f"MySQL DDL missing at {MYSQL_DDL}"
    ddl_text = MYSQL_DDL.read_text(encoding="utf-8")

    expected_tables = [
        "SKU", "PL", "PRICE_LIST", "SELLER_MAPPING", "CATEGORY_MAPPING",
        "PROMOTION", "SELLER_TABLE", "PRICE_MONITORING_TABLE",
        "VIOLATION_TABLE", "SUSPENDED_CATEGORIES",
    ]
    for tbl in expected_tables:
        assert re.search(rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{tbl}\b", ddl_text, re.IGNORECASE), (
            f"Table {tbl} missing from MySQL DDL."
        )

    assert "PRIMARY KEY" in ddl_text.upper()
    assert "FOREIGN KEY" in ddl_text.upper()
