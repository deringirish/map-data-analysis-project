import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import mysql.connector
from getpass import getpass

# =========================================================
# 1. PATH CONFIGURATION
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"

# =========================================================
# 2. MYSQL CONNECTION
# =========================================================
mysql_user = os.environ.get("MYSQL_USER", "root")
mysql_password = os.environ.get("MYSQL_PASSWORD")

if not mysql_password:
    try:
        mysql_password = getpass(f"Enter MySQL password for user '{mysql_user}': ")
    except Exception:
        mysql_password = ""

print(f"Connecting to MySQL ({mysql_user}@localhost:3306)...")

try:
    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user=mysql_user,
        password=mysql_password,
        autocommit=False
    )
    cursor = connection.cursor()
    print(" Connected to MySQL server successfully.")
except mysql.connector.Error as err:
    print(f" Connection failed: {err}")
    sys.exit(1)

try:
    # =========================================================
    # 3. INITIALIZE DATABASE & SCHEMA
    # =========================================================
    cursor.execute("CREATE DATABASE IF NOT EXISTS MAP_PROJECT;")
    cursor.execute("USE MAP_PROJECT;")
    
    # Run create_tables.sql
    ddl_file = Path(__file__).resolve().parent / "create_tables.sql"
    if ddl_file.exists():
        ddl_script = ddl_file.read_text(encoding="utf-8")
        # Split on semicolon, omitting delimiters/comments
        statements = [s.strip() for s in ddl_script.split(";") if s.strip()]
        for stmt in statements:
            if not stmt.upper().startswith("--"):
                cursor.execute(stmt)
        connection.commit()
        print(" Schema verified and all tables initialized.")

    # =========================================================
    # 4. TRUNCATE EXISTING TABLES (IN REVERSE DEPENDENCY ORDER)
    # =========================================================
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables_to_truncate = [
        "VIOLATION_TABLE",
        "PRICE_MONITORING_TABLE",
        "SELLER_TABLE",
        "PROMOTION",
        "CATEGORY_MAPPING",
        "PRICE_LIST",
        "PL",
        "SELLER_MAPPING",
        "SKU"
    ]
    for tbl in tables_to_truncate:
        cursor.execute(f"TRUNCATE TABLE {tbl};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    connection.commit()
    print(" Cleared existing tables for fresh batch population.\n")

    # =========================================================
    # 5. POPULATE MASTER & MAPPING TABLES
    # =========================================================
    
    # 5.1 SKU TABLE
    sku_df = pd.read_csv(DATA_PATH / "sku_table.csv")
    sku_data = [(row["PN"], row["SKU"]) for _, row in sku_df.iterrows()]
    cursor.executemany("INSERT INTO SKU (PN, SKU) VALUES (%s, %s)", sku_data)
    print(f"✓ SKU:                    {cursor.rowcount:,} rows inserted.")

    # 5.2 PL TABLE
    pl_df = pd.read_csv(DATA_PATH / "pl_table.csv")
    pl_data = [(row["PL"], row["SKU"], row["SUB_CATEGORY"]) for _, row in pl_df.iterrows()]
    cursor.executemany("INSERT INTO PL (PL, SKU, SUB_CATEGORY) VALUES (%s, %s, %s)", pl_data)
    print(f"✓ PL:                     {cursor.rowcount:,} rows inserted.")

    # 5.3 PRICE LIST TABLE
    price_df = pd.read_csv(DATA_PATH / "price_list_table.csv")
    price_data = [(row["PL"], row["SKU"], float(row["MAP"]), float(row["LPP"])) for _, row in price_df.iterrows()]
    cursor.executemany("INSERT INTO PRICE_LIST (PL, SKU, MAP, LPP) VALUES (%s, %s, %s, %s)", price_data)
    print(f"✓ PRICE_LIST:             {cursor.rowcount:,} rows inserted.")

    # 5.4 SELLER MAPPING TABLE
    seller_map_df = pd.read_csv(DATA_PATH / "seller_mapping_table.csv")
    seller_map_data = [(row["SELLER_NAME"], row["HOMOLOGATED_NAME"]) for _, row in seller_map_df.iterrows()]
    cursor.executemany("INSERT INTO SELLER_MAPPING (SELLER_NAME, HOMOLOGATED_NAME) VALUES (%s, %s)", seller_map_data)
    print(f"✓ SELLER_MAPPING:         {cursor.rowcount:,} rows inserted.")

    # 5.5 CATEGORY MAPPING TABLE
    cat_map_df = pd.read_csv(DATA_PATH / "category_mapping_table.csv")
    cat_map_data = [(row["CATEGORY"], row["SUB_CATEGORY"], row["PL"], row["SKU"]) for _, row in cat_map_df.iterrows()]
    cursor.executemany("INSERT INTO CATEGORY_MAPPING (CATEGORY, SUB_CATEGORY, PL, SKU) VALUES (%s, %s, %s, %s)", cat_map_data)
    print(f"✓ CATEGORY_MAPPING:       {cursor.rowcount:,} rows inserted.")

    # 5.6 PROMOTION TABLE
    prom_df = pd.read_csv(DATA_PATH / "promotion_table.csv").dropna(subset=["PL", "SKU", "SEASON", "PROMOTION"])
    prom_data = [(row["PL"], row["SKU"], row["SEASON"], row["PROMOTION"]) for _, row in prom_df.iterrows()]
    cursor.executemany("INSERT INTO PROMOTION (PL, SKU, SEASON, PROMOTION) VALUES (%s, %s, %s, %s)", prom_data)
    print(f"✓ PROMOTION:              {cursor.rowcount:,} rows inserted.")

    connection.commit()

    # =========================================================
    # 6. BATCH POPULATE LARGE DATASETS (10,000 ROWS/CHUNK)
    # =========================================================
    CHUNK_SIZE = 10000

    # 6.1 SELLER TABLE (147,900 Rows)
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
    print(f"✓ SELLER_TABLE:           {len(seller_df):,} rows inserted.")

    # 6.2 PRICE MONITORING TABLE (147,900 Rows)
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
    print(f"✓ PRICE_MONITORING_TABLE: {len(pm_df):,} rows inserted.")

    # 6.3 VIOLATION TABLE (15,936 Rows)
    print("\nIngesting VIOLATION_TABLE (15,936 rows in batches)...")
    v_df = pd.read_csv(DATA_PATH / "violation_table.csv")
    v_insert_query = """
    INSERT INTO VIOLATION_TABLE
    (SKU, Violation_date, PL, Category, Sub_category, Region, Marketplace, seller_name, 
     homologated_name, MAP_Price, LPP, Advertised_price, Season, Promotion, Promotional_price, 
     Screenshot, Violation_Type, Price_Difference)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            float(r["Price_Difference"]) if pd.notna(r["Price_Difference"]) else None
        ))
        if len(v_records) >= CHUNK_SIZE:
            cursor.executemany(v_insert_query, v_records)
            connection.commit()
            v_records = []
    if v_records:
        cursor.executemany(v_insert_query, v_records)
        connection.commit()
    print(f"✓ VIOLATION_TABLE:        {len(v_df):,} rows inserted.")

    # =========================================================
    # 7. FINAL AUDIT & SUMMARY VERIFICATION
    # =========================================================
    all_tables = [
        "SKU", "PL", "PRICE_LIST", "SELLER_MAPPING", 
        "CATEGORY_MAPPING", "PROMOTION", "SELLER_TABLE", 
        "PRICE_MONITORING_TABLE", "VIOLATION_TABLE"
    ]
    print("\n=========================================================")
    print("           FINAL DATABASE POPULATION SUMMARY             ")
    print("=========================================================")
    for tbl in all_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        print(f"• {tbl:<25} {cnt:>10,} rows")
    print("=========================================================")
    print(" All 9 tables populated and committed to MySQL.")

except Exception as err:
    connection.rollback()
    print(f"\n Error occurred during database population: {err}")
    raise
finally:
    cursor.close()
    connection.close()
    print("\nMySQL connection closed.")
