import os
import sys
import mysql.connector
from getpass import getpass

# =========================================================
# 1. MYSQL CONNECTION
# =========================================================
mysql_user = os.environ.get("MYSQL_USER", "root")
mysql_password = os.environ.get("MYSQL_PASSWORD")

if not mysql_password:
    try:
        mysql_password = getpass(f"Enter MySQL password for user '{mysql_user}': ")
    except Exception:
        mysql_password = ""

print(f"Connecting to MySQL ({mysql_user}@localhost:3306/MAP_PROJECT)...")

try:
    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user=mysql_user,
        password=mysql_password,
        database="MAP_PROJECT"
    )
    cursor = connection.cursor()
    print(" Connected successfully.\n")
except mysql.connector.Error as err:
    print(f" Connection failed: {err}")
    sys.exit(1)

# =========================================================
# 2. VALIDATE ALL 9 TABLES
# =========================================================
tables = [
    "SKU",
    "PL",
    "PRICE_LIST",
    "SELLER_MAPPING",
    "CATEGORY_MAPPING",
    "PROMOTION",
    "SELLER_TABLE",
    "PRICE_MONITORING_TABLE",
    "VIOLATION_TABLE"
]

print("=========================================================")
print("            MAP_PROJECT TABLE RECORD AUDIT               ")
print("=========================================================")
for tbl in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        count = cursor.fetchone()[0]
        print(f"• {tbl:<25} {count:>10,} rows")
    except mysql.connector.Error as e:
        print(f"• {tbl:<25} ERROR: {e}")

print("=========================================================")

cursor.close()
connection.close()
print("Validation completed.")
