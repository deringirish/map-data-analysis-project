import mysql.connector
from getpass import getpass

# =========================================================
# 1. MYSQL CONNECTION
# =========================================================

password = getpass("Enter MySQL password: ")

connection = mysql.connector.connect(
    host="localhost", port=3306, user="root", password=password, database="MAP_PROJECT"
)

cursor = connection.cursor()

print("Connected to MySQL successfully.\n")


# =========================================================
# 2. TABLES TO VALIDATE
# =========================================================

tables = ["SKU", "PL", "PRICE_LIST", "SELLER_MAPPING", "CATEGORY_MAPPING", "PROMOTION"]


# =========================================================
# 3. COUNT RECORDS
# =========================================================

print("Record counts:")
print("-" * 40)

for table in tables:

    query = f"SELECT COUNT(*) FROM {table}"

    cursor.execute(query)

    count = cursor.fetchone()[0]

    print(f"{table:<20} {count}")


# =========================================================
# 4. CLOSE CONNECTION
# =========================================================

cursor.close()
connection.close()

print("-" * 40)
print("Validation completed.")
