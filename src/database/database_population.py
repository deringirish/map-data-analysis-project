import pandas as pd
import mysql.connector
from getpass import getpass
from pathlib import Path

# =========================================================
# 1. DATA PATH
# =========================================================

# Current file: src/database/database_population.py
# CSV files: data_code/derived/

DATA_PATH = Path(__file__).resolve().parents[2] / "data_code" / "derived"


# =========================================================
# 2. MYSQL CONNECTION
# =========================================================

password = getpass("Enter MySQL password: ")

connection = mysql.connector.connect(
    host="localhost", port=3306, user="root", password=password, database="MAP_PROJECT"
)

cursor = connection.cursor()

print("Connected to MySQL successfully.")


try:

    # =====================================================
    # 3. CSV FILE PATHS
    # =====================================================

    sku_file = DATA_PATH / "sku_table.csv"
    pl_file = DATA_PATH / "pl_table.csv"
    price_list_file = DATA_PATH / "price_list_table.csv"
    seller_mapping_file = DATA_PATH / "seller_mapping_table.csv"
    category_mapping_file = DATA_PATH / "category_mapping_table.csv"
    promotion_file = DATA_PATH / "promotion_table.csv"

    # =====================================================
    # 4. CHECK CSV FILES
    # =====================================================

    files = {
        "SKU": sku_file,
        "PL": pl_file,
        "PRICE_LIST": price_list_file,
        "SELLER_MAPPING": seller_mapping_file,
        "CATEGORY_MAPPING": category_mapping_file,
        "PROMOTION": promotion_file,
    }

    for table_name, file_path in files.items():

        if not file_path.exists():
            raise FileNotFoundError(f"{table_name} CSV file not found:\n{file_path}")

    print("All CSV files found successfully.")

    # =====================================================
    # 5. READ CSV FILES
    # =====================================================

    sku_table = pd.read_csv(sku_file)

    pl_table = pd.read_csv(pl_file)

    price_list_table = pd.read_csv(price_list_file)

    seller_mapping_table = pd.read_csv(seller_mapping_file)

    category_mapping_table = pd.read_csv(category_mapping_file)

    promotion_table = pd.read_csv(promotion_file)

    print("All CSV files loaded successfully.")

    # =====================================================
    # 6. INSERT SKU TABLE
    # =====================================================

    sku_query = """
    INSERT INTO SKU (PN, SKU)
    VALUES (%s, %s)
    """

    sku_data = [(row["PN"], row["SKU"]) for _, row in sku_table.iterrows()]

    cursor.executemany(sku_query, sku_data)

    print(f"SKU: {cursor.rowcount} rows inserted.")

    # =====================================================
    # 7. INSERT PL TABLE
    # =====================================================

    pl_query = """
    INSERT INTO PL (PL, SKU, SUB_CATEGORY)
    VALUES (%s, %s, %s)
    """

    pl_data = [
        (row["PL"], row["SKU"], row["SUB_CATEGORY"]) for _, row in pl_table.iterrows()
    ]

    cursor.executemany(pl_query, pl_data)

    print(f"PL: {cursor.rowcount} rows inserted.")

    # =====================================================
    # 8. INSERT PRICE LIST TABLE
    # =====================================================

    price_list_query = """
    INSERT INTO PRICE_LIST (PL, SKU, MAP, LPP)
    VALUES (%s, %s, %s, %s)
    """

    price_list_data = [
        (row["PL"], row["SKU"], row["MAP"], row["LPP"])
        for _, row in price_list_table.iterrows()
    ]

    cursor.executemany(price_list_query, price_list_data)

    print(f"PRICE_LIST: {cursor.rowcount} rows inserted.")

    # =====================================================
    # 9. INSERT SELLER MAPPING TABLE
    # =====================================================

    seller_mapping_query = """
    INSERT INTO SELLER_MAPPING
    (SELLER_NAME, HOMOLOGATED_NAME)
    VALUES (%s, %s)
    """

    seller_mapping_data = [
        (row["SELLER_NAME"], row["HOMOLOGATED_NAME"])
        for _, row in seller_mapping_table.iterrows()
    ]

    cursor.executemany(seller_mapping_query, seller_mapping_data)

    print(f"SELLER_MAPPING: " f"{cursor.rowcount} rows inserted.")

    # =====================================================
    # 10. INSERT CATEGORY MAPPING TABLE
    # =====================================================

    category_mapping_query = """
    INSERT INTO CATEGORY_MAPPING
    (CATEGORY, SUB_CATEGORY, PL, SKU)
    VALUES (%s, %s, %s, %s)
    """

    category_mapping_data = [
        (row["CATEGORY"], row["SUB_CATEGORY"], row["PL"], row["SKU"])
        for _, row in category_mapping_table.iterrows()
    ]

    cursor.executemany(category_mapping_query, category_mapping_data)

    print(f"CATEGORY_MAPPING: " f"{cursor.rowcount} rows inserted.")

    # =====================================================
    # 11. CHECK PROMOTION DATA
    # =====================================================

    invalid_promotion = promotion_table[
        promotion_table[["PL", "SKU", "SEASON", "PROMOTION"]].isna().any(axis=1)
    ].copy()

    if not invalid_promotion.empty:

        print("\nWARNING: Invalid promotion records found:")

        print(invalid_promotion)

        print(f"\nNumber of invalid promotion records: " f"{len(invalid_promotion)}")

    # Keep only valid promotion records
    valid_promotion_table = promotion_table.dropna(
        subset=["PL", "SKU", "SEASON", "PROMOTION"]
    ).copy()

    # =====================================================
    # 12. INSERT PROMOTION TABLE
    # =====================================================

    promotion_query = """
    INSERT INTO PROMOTION
    (PL, SKU, SEASON, PROMOTION)
    VALUES (%s, %s, %s, %s)
    """

    promotion_data = [
        (row["PL"], row["SKU"], row["SEASON"], row["PROMOTION"])
        for _, row in valid_promotion_table.iterrows()
    ]

    cursor.executemany(promotion_query, promotion_data)

    print(f"PROMOTION: " f"{cursor.rowcount} valid rows inserted.")

    # =====================================================
    # 13. COMMIT ALL DATA
    # =====================================================

    connection.commit()

    print("\nAll valid data inserted successfully.")

    # =====================================================
    # 14. DATABASE ROW COUNTS
    # =====================================================

    tables = [
        "SKU",
        "PL",
        "PRICE_LIST",
        "SELLER_MAPPING",
        "CATEGORY_MAPPING",
        "PROMOTION",
    ]

    print("\nDatabase row counts:")

    for table in tables:

        cursor.execute(f"SELECT COUNT(*) FROM {table}")

        count = cursor.fetchone()[0]

        print(f"{table}: {count}")


except Exception as error:

    # =====================================================
    # 15. ROLLBACK IF ANY ERROR OCCURS
    # =====================================================

    connection.rollback()

    print("\nERROR OCCURRED.")

    print("All database changes have been rolled back.")

    print(f"\nError: {error}")

    raise


finally:

    # =====================================================
    # 16. CLOSE CONNECTION
    # =====================================================

    cursor.close()

    connection.close()

    print("\nMySQL connection closed.")
