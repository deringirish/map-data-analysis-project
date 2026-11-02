import os
import sys
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_port = int(os.getenv("MYSQL_PORT", 3306))
mysql_user = os.getenv("MYSQL_USER", "root")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_database = os.getenv("MYSQL_DATABASE", "MAP_PROJECT")

if mysql_password is None:
    from getpass import getpass
    try:
        mysql_password = getpass(f"Enter MySQL password for user '{mysql_user}': ")
    except Exception:
        mysql_password = ""

print(f"Connecting to MySQL ({mysql_user}@{mysql_host}:{mysql_port}/{mysql_database})...")

try:
    connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    cursor = connection.cursor()
    print(" Connected successfully.\n")
except mysql.connector.Error as err:
    print(f" Connection failed: {err}")
    print("\n Tip: Check your MYSQL_PASSWORD in the .env file.")
    sys.exit(1)

tables = [
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
