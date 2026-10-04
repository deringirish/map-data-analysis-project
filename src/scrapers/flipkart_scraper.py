from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import pandas as pd
import re
import time

# ==========================================================
# SETTINGS
# ==========================================================

SEARCHES = {"Laptop": "laptop", "Printer": "printer", "Ink_Toner": "ink toner"}

PRODUCTS_PER_CATEGORY = 5

MARKETPLACE = "Flipkart"
REGION = "India"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRAPED_DIR = PROJECT_ROOT / "data_code" / "scraped"
OUTPUT_FILE = SCRAPED_DIR / "flipkart_seller_table.csv"

SCREENSHOT_FOLDER = SCRAPED_DIR / "screenshots"
SCREENSHOT_FOLDER.mkdir(parents=True, exist_ok=True)


# ==========================================================
# FUNCTION: GET PRODUCT LINKS
# ==========================================================


def get_product_links(page, search_term, required_count):

    print("\n")
    print("========================================")
    print(f"SEARCHING: {search_term}")
    print("========================================")

    # Open Flipkart search URL directly
    search_url = (
        "https://www.flipkart.com/search" f"?q={search_term.replace(' ', '%20')}"
    )

    page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

    page.wait_for_timeout(5000)

    print("Search URL:")
    print(page.url)

    links = page.locator("a")

    product_links = []

    for i in range(links.count()):

        link = links.nth(i)

        href = link.get_attribute("href")

        if not href:
            continue

        if "/p/" not in href:
            continue

        # Remove duplicate links
        if href in product_links:
            continue

        # Convert relative URL to full URL
        if href.startswith("/"):
            full_url = "https://www.flipkart.com" + href
        else:
            full_url = href

        product_links.append(full_url)

        if len(product_links) >= required_count:
            break

    print(f"Product links found: {len(product_links)}")

    return product_links


# ==========================================================
# FUNCTION: EXTRACT PRODUCT DATA
# ==========================================================


def extract_product(page, product_url, category, index):

    print("\n")
    print("----------------------------------------")
    print(f"PRODUCT {index}")
    print("----------------------------------------")

    try:

        # Open product
        page.goto(product_url, wait_until="domcontentloaded", timeout=60000)

        page.wait_for_timeout(4000)

        # ==================================================
        # PRODUCT NAME
        # ==================================================

        product_name = ""

        heading = page.locator("h1").first

        if heading.count() > 0:

            product_name = heading.inner_text().strip()

        product_name = product_name.replace("...more", "").strip()

        # ==================================================
        # SKU / PRODUCT ID
        # ==================================================

        current_url = page.url

        sku = ""

        match = re.search(r"[?&]pid=([A-Z0-9]+)", current_url)

        if match:
            sku = match.group(1)

        # ==================================================
        # SELLER
        # ==================================================

        seller_name = ""

        seller_locator = page.get_by_text(re.compile(r"^Seller:"))

        if seller_locator.count() > 0:

            seller_text = seller_locator.first.inner_text().strip()

            seller_name = seller_text.replace("Seller:", "").strip()

        # ==================================================
        # ADVERTISED PRICE
        # ==================================================

        advertised_price = None

        # First try Flipkart's common current-price class
        price_candidates = page.locator('[class*="Nx9bqj"]')

        for j in range(price_candidates.count()):

            text = price_candidates.nth(j).inner_text().strip()

            if "₹" not in text:
                continue

            cleaned = text.replace("₹", "")
            cleaned = cleaned.replace(",", "")
            cleaned = cleaned.strip()

            try:

                advertised_price = float(cleaned)

                break

            except ValueError:

                continue

        # Fallback
        if advertised_price is None:

            price_candidates = page.locator("div, span")

            for j in range(price_candidates.count()):

                text = price_candidates.nth(j).inner_text().strip()

                if not text.startswith("₹"):
                    continue

                if len(text) > 30:
                    continue

                cleaned = text.replace("₹", "")
                cleaned = cleaned.replace(",", "")
                cleaned = cleaned.strip()

                try:

                    advertised_price = float(cleaned)

                    break

                except ValueError:

                    continue

        # ==================================================
        # SCREENSHOT
        # ==================================================

        if sku:

            screenshot_path = SCREENSHOT_FOLDER / f"{sku}.png"

        else:

            screenshot_path = SCREENSHOT_FOLDER / f"{category}_{index}.png"

        page.screenshot(path=str(screenshot_path), full_page=True)

        # ==================================================
        # COLLECTION TIME
        # ==================================================

        last_time_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ==================================================
        # PRINT RESULT
        # ==================================================

        print("Product Name:")
        print(product_name)

        print("Seller:")
        print(seller_name)

        print("SKU:")
        print(sku)

        print("Price:")
        print(advertised_price)

        print("Screenshot:")
        print(screenshot_path)

        print("Status: SUCCESS")

        # ==================================================
        # RETURN DATA
        # ==================================================

        return {
            "Seller_name": seller_name,
            "SKU": sku,
            "Region": REGION,
            "Category": category,
            "Advertised_price": advertised_price,
            "Marketplace": MARKETPLACE,
            "Screenshot": str(screenshot_path),
            "Live_link": product_url,
            "Last_time_collected": last_time_collected,
        }

    except Exception as e:

        print("Status: FAILED")
        print("Error:", e)

        return None


# ==========================================================
# MAIN PROGRAM
# ==========================================================

all_records = []


with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    # ======================================================
    # PROCESS EACH CATEGORY
    # ======================================================

    for category, search_term in SEARCHES.items():

        product_links = get_product_links(page, search_term, PRODUCTS_PER_CATEGORY)

        print("\n")
        print(f"Starting {category} extraction...")

        for index, product_url in enumerate(product_links, start=1):

            record = extract_product(page, product_url, category, index)

            if record:

                all_records.append(record)

            # Small delay between products
            time.sleep(2)

    # ======================================================
    # CLOSE BROWSER
    # ======================================================

    browser.close()


# ==========================================================
# CREATE DATAFRAME
# ==========================================================

df = pd.DataFrame(all_records)


# ==========================================================
# SAVE CSV
# ==========================================================

df.to_csv(OUTPUT_FILE, index=False)


# ==========================================================
# FINAL SUMMARY
# ==========================================================

print("\n")
print("========================================")
print("FLIPKART SCRAPING COMPLETED")
print("========================================")

print("\nTotal records:")
print(len(df))

print("\nRecords by category:")

if not df.empty:

    print(df["Category"].value_counts())

print("\nCSV file:")
print(OUTPUT_FILE)

print("\n========================================")
