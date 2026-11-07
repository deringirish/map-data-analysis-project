"""
MAP Relational Database Population Subsystem (Dual-Engine: MySQL 8.0 & SQLite 3)
Author: Derin Girish D G
Description: Automated batch ingestion into 3NF relational warehouse with zero-downtime
automatic fallback to local SQLite when MySQL server is unreachable.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Ensure console supports utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# =========================================================
# 1. LOAD CONFIGURATION & ENVIRONMENT VARIABLES
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
SQLITE_DB_PATH = DATA_PATH / "map_project.db"

# Load environment variables from .env file at project root
load_dotenv(dotenv_path=BASE_DIR / ".env")


def populate_sqlite(db_path: Path):
    """Populates 3NF schema and all datasets into a local SQLite database."""
    import sqlite3
    print(f"\n=========================================================")
    print(f" [ENGINE: SQLITE] POPULATING 3NF WAREHOUSE: {db_path.name}")
    print("=========================================================")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    # 1. Execute SQLite DDL Schema
    ddl_file = Path(__file__).resolve().parent / "create_tables_sqlite.sql"
    if ddl_file.exists():
        cursor.executescript(ddl_file.read_text(encoding="utf-8"))
    
    # 2. Clear existing records
    tables_to_truncate = [
        "SUSPENDED_CATEGORIES", "VIOLATION_TABLE", "PRICE_MONITORING_TABLE",
        "SELLER_TABLE", "PROMOTION", "CATEGORY_MAPPING", "PRICE_LIST", "PL",
        "SELLER_MAPPING", "SKU"
    ]
    for tbl in tables_to_truncate:
        cursor.execute(f"DELETE FROM {tbl};")
    conn.commit()
    print("Cleared existing tables for fresh batch population.\n")

    # 3. Master & Taxonomy Tables
    sku_df = pd.read_csv(DATA_PATH / "sku_table.csv")
    sku_data = [(row["PN"], row["SKU"]) for _, row in sku_df.iterrows()]
    cursor.executemany("INSERT INTO SKU (PN, SKU) VALUES (?, ?)", sku_data)
    print(f"[OK] SKU:                    {len(sku_data):,} rows inserted.")

    pl_df = pd.read_csv(DATA_PATH / "pl_table.csv")
    pl_data = [(row["PL"], row["SKU"], row["SUB_CATEGORY"]) for _, row in pl_df.iterrows()]
    cursor.executemany("INSERT INTO PL (PL, SKU, SUB_CATEGORY) VALUES (?, ?, ?)", pl_data)
    print(f"[OK] PL:                     {len(pl_data):,} rows inserted.")

    price_df = pd.read_csv(DATA_PATH / "price_list_table.csv")
    price_data = [(row["PL"], row["SKU"], float(row["MAP"]), float(row["LPP"])) for _, row in price_df.iterrows()]
    cursor.executemany("INSERT INTO PRICE_LIST (PL, SKU, MAP, LPP) VALUES (?, ?, ?, ?)", price_data)
    print(f"[OK] PRICE_LIST:             {len(price_data):,} rows inserted.")

    seller_map_df = pd.read_csv(DATA_PATH / "seller_mapping_table.csv")
    seller_map_data = [(row["SELLER_NAME"], row["HOMOLOGATED_NAME"]) for _, row in seller_map_df.iterrows()]
    cursor.executemany("INSERT INTO SELLER_MAPPING (SELLER_NAME, HOMOLOGATED_NAME) VALUES (?, ?)", seller_map_data)
    print(f"[OK] SELLER_MAPPING:         {len(seller_map_data):,} rows inserted.")

    cat_map_df = pd.read_csv(DATA_PATH / "category_mapping_table.csv")
    cat_map_data = [(row["CATEGORY"], row["SUB_CATEGORY"], row["PL"], row["SKU"]) for _, row in cat_map_df.iterrows()]
    cursor.executemany("INSERT INTO CATEGORY_MAPPING (CATEGORY, SUB_CATEGORY, PL, SKU) VALUES (?, ?, ?, ?)", cat_map_data)
    print(f"[OK] CATEGORY_MAPPING:       {len(cat_map_data):,} rows inserted.")

    prom_df = pd.read_csv(DATA_PATH / "promotion_table.csv").dropna(subset=["PL", "SKU", "SEASON", "PROMOTION"])
    prom_data = [(row["PL"], row["SKU"], row["SEASON"], row["PROMOTION"]) for _, row in prom_df.iterrows()]
    cursor.executemany("INSERT INTO PROMOTION (PL, SKU, SEASON, PROMOTION) VALUES (?, ?, ?, ?)", prom_data)
    print(f"[OK] PROMOTION:              {len(prom_data):,} rows inserted.")

    conn.commit()

    # 4. Large Datasets Ingestion
    CHUNK_SIZE = 10000

    print("\nIngesting SELLER_TABLE (147,900 rows in batches)...")
    seller_df = pd.read_csv(DATA_PATH / "seller_table.csv")
    seller_insert = """
    INSERT INTO SELLER_TABLE 
    (Seller_name, SKU, Region, Advertised_price, Marketplace, Screenshot, Live_link, Last_time_collected)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    seller_records = []
    for _, r in seller_df.iterrows():
        seller_records.append((
            str(r["Seller_name"]) if pd.notna(r["Seller_name"]) else None,
            str(r["SKU"]) if pd.notna(r["SKU"]) else None,
            str(r["Region"]) if pd.notna(r["Region"]) else None,
            float(r["Advertised_price"]) if pd.notna(r["Advertised_price"]) else None,
            str(r["Marketplace"]) if pd.notna(r["Marketplace"]) else None,
            str(r["Screenshot"]) if pd.notna(r["Screenshot"]) else None,
            str(r["Live_link"]) if pd.notna(r["Live_link"]) else None,
            str(r["Last time collected"]) if pd.notna(r["Last time collected"]) else None
        ))
        if len(seller_records) >= CHUNK_SIZE:
            cursor.executemany(seller_insert, seller_records)
            conn.commit()
            seller_records = []
    if seller_records:
        cursor.executemany(seller_insert, seller_records)
        conn.commit()
    print(f"[OK] SELLER_TABLE:           {len(seller_df):,} rows inserted.")

    print("\nIngesting PRICE_MONITORING_TABLE (147,900 rows in batches)...")
    pm_df = pd.read_csv(DATA_PATH / "price_monitoring_table.csv")
    pm_insert = """
    INSERT INTO PRICE_MONITORING_TABLE
    (SKU, Violation_date, PL, Category, Sub_category, Region, Marketplace, seller_name, 
     homologated_name, MAP_Price, LPP, Advertised_price, Season, Promotional_price)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    pm_records = []
    for _, r in pm_df.iterrows():
        pm_records.append((
            str(r["SKU"]) if pd.notna(r["SKU"]) else None,
            str(r["Violation_date"]) if pd.notna(r["Violation_date"]) else None,
            str(r["PL"]) if pd.notna(r["PL"]) else None,
            str(r["Category"]) if pd.notna(r["Category"]) else None,
            str(r["Sub_category"]) if pd.notna(r["Sub_category"]) else None,
            str(r["Region"]) if pd.notna(r["Region"]) else None,
            str(r["Marketplace"]) if pd.notna(r["Marketplace"]) else None,
            str(r["seller_name"]) if pd.notna(r["seller_name"]) else None,
            str(r["homologated_name"]) if pd.notna(r["homologated_name"]) else None,
            float(r["MAP_Price"]) if pd.notna(r["MAP_Price"]) else None,
            float(r["LPP"]) if pd.notna(r["LPP"]) else None,
            float(r["Advertised_price"]) if pd.notna(r["Advertised_price"]) else None,
            str(r["Season"]) if pd.notna(r["Season"]) else None,
            float(r["Promotional_price"]) if pd.notna(r["Promotional_price"]) else None
        ))
        if len(pm_records) >= CHUNK_SIZE:
            cursor.executemany(pm_insert, pm_records)
            conn.commit()
            pm_records = []
    if pm_records:
        cursor.executemany(pm_insert, pm_records)
        conn.commit()
    print(f"[OK] PRICE_MONITORING_TABLE: {len(pm_df):,} rows inserted.")

    print("\nIngesting VIOLATION_TABLE (15,936 rows in batches)...")
    v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
    v_insert = """
    INSERT INTO VIOLATION_TABLE
    (SKU, Violation_date, PL, Category, Sub_category, Region, Marketplace, seller_name, 
     homologated_name, MAP_Price, LPP, Advertised_price, Season, Promotion, Promotional_price, 
     Screenshot, Violation_Type, Price_Difference, Notice_Doc_Path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    v_records = []
    for _, r in v_df.iterrows():
        v_records.append((
            str(r["SKU"]) if pd.notna(r["SKU"]) else None,
            str(r["Violation_date"]) if pd.notna(r["Violation_date"]) else None,
            str(r["PL"]) if pd.notna(r["PL"]) else None,
            str(r["Category"]) if pd.notna(r["Category"]) else None,
            str(r["Sub_category"]) if pd.notna(r["Sub_category"]) else None,
            str(r["Region"]) if pd.notna(r["Region"]) else None,
            str(r["Marketplace"]) if pd.notna(r["Marketplace"]) else None,
            str(r["seller_name"]) if pd.notna(r["seller_name"]) else None,
            str(r["homologated_name"]) if pd.notna(r["homologated_name"]) else None,
            float(r["MAP_Price"]) if pd.notna(r["MAP_Price"]) else None,
            float(r["LPP"]) if pd.notna(r["LPP"]) else None,
            float(r["Advertised_price"]) if pd.notna(r["Advertised_price"]) else None,
            str(r["Season"]) if pd.notna(r["Season"]) else None,
            str(r["Promotion"]) if pd.notna(r["Promotion"]) else None,
            float(r["Promotional_price"]) if pd.notna(r["Promotional_price"]) else None,
            str(r["Screenshot"]) if pd.notna(r["Screenshot"]) else None,
            str(r["Violation_Type"]) if pd.notna(r["Violation_Type"]) else None,
            float(r["Price_Difference"]) if pd.notna(r["Price_Difference"]) else None,
            str(r["Notice_Doc_Path"]) if pd.notna(r.get("Notice_Doc_Path")) else None
        ))
        if len(v_records) >= CHUNK_SIZE:
            cursor.executemany(v_insert, v_records)
            conn.commit()
            v_records = []
    if v_records:
        cursor.executemany(v_insert, v_records)
        conn.commit()
    print(f"[OK] VIOLATION_TABLE:        {len(v_df):,} rows inserted.")

    susp_csv = DATA_PATH / "suspended_categories_table.csv"
    if susp_csv.exists():
        print("\nIngesting SUSPENDED_CATEGORIES (279 rows)...")
        susp_df = pd.read_csv(susp_csv)
        susp_insert = """
        INSERT INTO SUSPENDED_CATEGORIES (
            homologated_name, Category, Total_Infractions, Distinct_Violation_Dates,
            Distinct_SKUs_Violated, Marketplaces_Audited, Earliest_Violation, Latest_Violation,
            Max_Single_Deficit, Total_Price_Deficit, Enforcement_Status, Legal_Remedy,
            Suspension_Duration_Days, Suspension_Effective_Date, Suspension_Expiry_Date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        susp_records = []
        for _, r in susp_df.iterrows():
            susp_records.append((
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
        cursor.executemany(susp_insert, susp_records)
        conn.commit()
        print(f"[OK] SUSPENDED_CATEGORIES:   {len(susp_df):,} rows inserted.")

    # 5. Verification Summary
    print("\n=========================================================")
    print("           FINAL DATABASE POPULATION SUMMARY (SQLITE)    ")
    print("=========================================================")
    for tbl in tables_to_truncate:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        print(f"• {tbl:<25} {cnt:>10,} rows")
    print("=========================================================")
    print(f" All 10 tables successfully populated into SQLite ({db_path.name}).")
    cursor.close()
    conn.close()


def populate_mysql():
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
        autocommit=False
    )
    cursor = connection.cursor()
    print(" Connected to MySQL server successfully.")

    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS MAP_PROJECT;")
        cursor.execute("USE MAP_PROJECT;")
        
        ddl_file = Path(__file__).resolve().parent / "create_tables.sql"
        if ddl_file.exists():
            ddl_script = ddl_file.read_text(encoding="utf-8")
            statements = [s.strip() for s in ddl_script.split(";") if s.strip()]
            for stmt in statements:
                clean_lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
                clean_stmt = "\n".join(clean_lines).strip()
                if clean_stmt:
                    cursor.execute(clean_stmt)
            connection.commit()
            print(" Schema verified and all tables initialized.")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        tables_to_truncate = [
            "SUSPENDED_CATEGORIES", "VIOLATION_TABLE", "PRICE_MONITORING_TABLE",
            "SELLER_TABLE", "PROMOTION", "CATEGORY_MAPPING", "PRICE_LIST", "PL",
            "SELLER_MAPPING", "SKU"
        ]
        for tbl in tables_to_truncate:
            cursor.execute(f"TRUNCATE TABLE {tbl};")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        connection.commit()
        print(" Cleared existing tables for fresh batch population.\n")

        # Master tables
        sku_df = pd.read_csv(DATA_PATH / "sku_table.csv")
        sku_data = [(row["PN"], row["SKU"]) for _, row in sku_df.iterrows()]
        cursor.executemany("INSERT INTO SKU (PN, SKU) VALUES (%s, %s)", sku_data)
        print(f"[OK] SKU:                    {cursor.rowcount:,} rows inserted.")

        pl_df = pd.read_csv(DATA_PATH / "pl_table.csv")
        pl_data = [(row["PL"], row["SKU"], row["SUB_CATEGORY"]) for _, row in pl_df.iterrows()]
        cursor.executemany("INSERT INTO PL (PL, SKU, SUB_CATEGORY) VALUES (%s, %s, %s)", pl_data)
        print(f"[OK] PL:                     {cursor.rowcount:,} rows inserted.")

        price_df = pd.read_csv(DATA_PATH / "price_list_table.csv")
        price_data = [(row["PL"], row["SKU"], float(row["MAP"]), float(row["LPP"])) for _, row in price_df.iterrows()]
        cursor.executemany("INSERT INTO PRICE_LIST (PL, SKU, MAP, LPP) VALUES (%s, %s, %s, %s)", price_data)
        print(f"[OK] PRICE_LIST:             {cursor.rowcount:,} rows inserted.")

        seller_map_df = pd.read_csv(DATA_PATH / "seller_mapping_table.csv")
        seller_map_data = [(row["SELLER_NAME"], row["HOMOLOGATED_NAME"]) for _, row in seller_map_df.iterrows()]
        cursor.executemany("INSERT INTO SELLER_MAPPING (SELLER_NAME, HOMOLOGATED_NAME) VALUES (%s, %s)", seller_map_data)
        print(f"[OK] SELLER_MAPPING:         {cursor.rowcount:,} rows inserted.")

        cat_map_df = pd.read_csv(DATA_PATH / "category_mapping_table.csv")
        cat_map_data = [(row["CATEGORY"], row["SUB_CATEGORY"], row["PL"], row["SKU"]) for _, row in cat_map_df.iterrows()]
        cursor.executemany("INSERT INTO CATEGORY_MAPPING (CATEGORY, SUB_CATEGORY, PL, SKU) VALUES (%s, %s, %s, %s)", cat_map_data)
        print(f"[OK] CATEGORY_MAPPING:       {cursor.rowcount:,} rows inserted.")

        prom_df = pd.read_csv(DATA_PATH / "promotion_table.csv").dropna(subset=["PL", "SKU", "SEASON", "PROMOTION"])
        prom_data = [(row["PL"], row["SKU"], row["SEASON"], row["PROMOTION"]) for _, row in prom_df.iterrows()]
        cursor.executemany("INSERT INTO PROMOTION (PL, SKU, SEASON, PROMOTION) VALUES (%s, %s, %s, %s)", prom_data)
        print(f"[OK] PROMOTION:              {cursor.rowcount:,} rows inserted.")

        connection.commit()

        CHUNK_SIZE = 10000

        print("\nIngesting SELLER_TABLE (147,900 rows in batches)...")
        seller_df = pd.read_csv(DATA_PATH / "seller_table.csv")
        seller_insert_query = """
        INSERT INTO SELLER_TABLE 
        (Seller_name, SKU, Region, Advertised_price, Marketplace, Screenshot, Live_link, Last_time_collected)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        seller_records = []
        for _, r in seller_df.iterrows():
            seller_records.append((
                str(r["Seller_name"]) if pd.notna(r["Seller_name"]) else None,
                str(r["SKU"]) if pd.notna(r["SKU"]) else None,
                str(r["Region"]) if pd.notna(r["Region"]) else None,
                float(r["Advertised_price"]) if pd.notna(r["Advertised_price"]) else None,
                str(r["Marketplace"]) if pd.notna(r["Marketplace"]) else None,
                str(r["Screenshot"]) if pd.notna(r["Screenshot"]) else None,
                str(r["Live_link"]) if pd.notna(r["Live_link"]) else None,
                str(r["Last time collected"]) if pd.notna(r["Last time collected"]) else None
            ))
            if len(seller_records) >= CHUNK_SIZE:
                cursor.executemany(seller_insert_query, seller_records)
                connection.commit()
                seller_records = []
        if seller_records:
            cursor.executemany(seller_insert_query, seller_records)
            connection.commit()
        print(f"[OK] SELLER_TABLE:           {len(seller_df):,} rows inserted.")

        print("\nIngesting PRICE_MONITORING_TABLE (147,900 rows in batches)...")
        pm_df = pd.read_csv(DATA_PATH / "price_monitoring_table.csv")
        pm_insert_query = """
        INSERT INTO PRICE_MONITORING_TABLE
        (SKU, Violation_date, PL, Category, Sub_category, Region, Marketplace, seller_name, 
         homologated_name, MAP_Price, LPP, Advertised_price, Season, Promotional_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        pm_records = []
        for _, r in pm_df.iterrows():
            pm_records.append((
                str(r["SKU"]) if pd.notna(r["SKU"]) else None,
                str(r["Violation_date"]) if pd.notna(r["Violation_date"]) else None,
                str(r["PL"]) if pd.notna(r["PL"]) else None,
                str(r["Category"]) if pd.notna(r["Category"]) else None,
                str(r["Sub_category"]) if pd.notna(r["Sub_category"]) else None,
                str(r["Region"]) if pd.notna(r["Region"]) else None,
                str(r["Marketplace"]) if pd.notna(r["Marketplace"]) else None,
                str(r["seller_name"]) if pd.notna(r["seller_name"]) else None,
                str(r["homologated_name"]) if pd.notna(r["homologated_name"]) else None,
                float(r["MAP_Price"]) if pd.notna(r["MAP_Price"]) else None,
                float(r["LPP"]) if pd.notna(r["LPP"]) else None,
                float(r["Advertised_price"]) if pd.notna(r["Advertised_price"]) else None,
                str(r["Season"]) if pd.notna(r["Season"]) else None,
                float(r["Promotional_price"]) if pd.notna(r["Promotional_price"]) else None
            ))
            if len(pm_records) >= CHUNK_SIZE:
                cursor.executemany(pm_insert_query, pm_records)
                connection.commit()
                pm_records = []
        if pm_records:
            cursor.executemany(pm_insert_query, pm_records)
            connection.commit()
        print(f"[OK] PRICE_MONITORING_TABLE: {len(pm_df):,} rows inserted.")

        print("\nIngesting VIOLATION_TABLE (15,936 rows in batches)...")
        v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
        v_insert_query = """
        INSERT INTO VIOLATION_TABLE
        (SKU, Violation_date, PL, Category, Sub_category, Region, Marketplace, seller_name, 
         homologated_name, MAP_Price, LPP, Advertised_price, Season, Promotion, Promotional_price, 
         Screenshot, Violation_Type, Price_Difference, Notice_Doc_Path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        v_records = []
        for _, r in v_df.iterrows():
            v_records.append((
                str(r["SKU"]) if pd.notna(r["SKU"]) else None,
                str(r["Violation_date"]) if pd.notna(r["Violation_date"]) else None,
                str(r["PL"]) if pd.notna(r["PL"]) else None,
                str(r["Category"]) if pd.notna(r["Category"]) else None,
                str(r["Sub_category"]) if pd.notna(r["Sub_category"]) else None,
                str(r["Region"]) if pd.notna(r["Region"]) else None,
                str(r["Marketplace"]) if pd.notna(r["Marketplace"]) else None,
                str(r["seller_name"]) if pd.notna(r["seller_name"]) else None,
                str(r["homologated_name"]) if pd.notna(r["homologated_name"]) else None,
                float(r["MAP_Price"]) if pd.notna(r["MAP_Price"]) else None,
                float(r["LPP"]) if pd.notna(r["LPP"]) else None,
                float(r["Advertised_price"]) if pd.notna(r["Advertised_price"]) else None,
                str(r["Season"]) if pd.notna(r["Season"]) else None,
                str(r["Promotion"]) if pd.notna(r["Promotion"]) else None,
                float(r["Promotional_price"]) if pd.notna(r["Promotional_price"]) else None,
                str(r["Screenshot"]) if pd.notna(r["Screenshot"]) else None,
                str(r["Violation_Type"]) if pd.notna(r["Violation_Type"]) else None,
                float(r["Price_Difference"]) if pd.notna(r["Price_Difference"]) else None,
                str(r["Notice_Doc_Path"]) if pd.notna(r.get("Notice_Doc_Path")) else None
            ))
            if len(v_records) >= CHUNK_SIZE:
                cursor.executemany(v_insert_query, v_records)
                connection.commit()
                v_records = []
        if v_records:
            cursor.executemany(v_insert_query, v_records)
            connection.commit()
        print(f"[OK] VIOLATION_TABLE:        {len(v_df):,} rows inserted.")

        susp_csv = DATA_PATH / "suspended_categories_table.csv"
        if susp_csv.exists():
            print("\nIngesting SUSPENDED_CATEGORIES (279 rows)...")
            susp_df = pd.read_csv(susp_csv)
            susp_insert = """
            INSERT INTO SUSPENDED_CATEGORIES (
                homologated_name, Category, Total_Infractions, Distinct_Violation_Dates,
                Distinct_SKUs_Violated, Marketplaces_Audited, Earliest_Violation, Latest_Violation,
                Max_Single_Deficit, Total_Price_Deficit, Enforcement_Status, Legal_Remedy,
                Suspension_Duration_Days, Suspension_Effective_Date, Suspension_Expiry_Date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            susp_records = []
            for _, r in susp_df.iterrows():
                susp_records.append((
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
            cursor.executemany(susp_insert, susp_records)
            connection.commit()
            print(f"[OK] SUSPENDED_CATEGORIES:   {len(susp_df):,} rows inserted.")

        print("\n=========================================================")
        print("           FINAL DATABASE POPULATION SUMMARY (MYSQL)     ")
        print("=========================================================")
        for tbl in tables_to_truncate:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            cnt = cursor.fetchone()[0]
            print(f"• {tbl:<25} {cnt:>10,} rows")
        print("=========================================================")
        print(" All 10 tables populated and committed to MySQL.")

    except Exception as err:
        connection.rollback()
        print(f"\n Error occurred during MySQL database population: {err}")
        raise
    finally:
        cursor.close()
        connection.close()


def main():
    parser = argparse.ArgumentParser(description="3NF Database Population Engine")
    parser.add_argument("--engine", choices=["auto", "mysql", "sqlite"], default=None,
                        help="Database engine (defaults to DB_ENGINE in .env or 'auto')")
    args = parser.parse_args()

    engine = args.engine or os.getenv("DB_ENGINE", "auto").lower()

    if engine == "sqlite":
        populate_sqlite(SQLITE_DB_PATH)
        return

    # Try MySQL first if engine is mysql or auto
    try:
        populate_mysql()
    except Exception as e:
        if engine == "mysql":
            print(f"[ERROR] MySQL population failed: {e}")
            sys.exit(1)
        else:
            print(f"\n[WARN] MySQL server unavailable: {e}")
            print("[INFO] Seamlessly falling back to local SQLite relational database...")
            populate_sqlite(SQLITE_DB_PATH)


if __name__ == "__main__":
    main()
