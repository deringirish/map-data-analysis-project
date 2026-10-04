import re
from urllib.parse import unquote
from datetime import datetime
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

# =========================================================
# SETTINGS
# =========================================================

SEARCHES = {"Laptop": "laptop", "Printer": "printer", "Ink_Toner": "ink toner"}

PRODUCTS_PER_CATEGORY = 5


# =========================================================
# START PLAYWRIGHT
# =========================================================

with sync_playwright() as p:

    # =====================================================
    # 1. LAUNCH BROWSER
    # =====================================================

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    # =====================================================
    # 2. CREATE SCREENSHOT FOLDER
    # =====================================================

    project_root = Path(__file__).resolve().parents[2]
    scraped_dir = project_root / "data_code" / "scraped"
    screenshot_folder = scraped_dir / "screenshots"
    screenshot_folder.mkdir(parents=True, exist_ok=True)

    # =====================================================
    # 3. CREATE LIST FOR FINAL SELLER TABLE
    # =====================================================

    seller_records = []

    # =====================================================
    # 4. LOOP THROUGH CATEGORIES
    # =====================================================

    for category, search_term in SEARCHES.items():

        print("\n")
        print("##################################################")
        print(f"CATEGORY: {category}")
        print(f"SEARCH TERM: {search_term}")
        print("##################################################")

        # =================================================
        # OPEN AMAZON
        # =================================================

        page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=60000)

        page.wait_for_timeout(3000)

        # =================================================
        # SEARCH PRODUCT
        # =================================================

        search_box = page.locator("#twotabsearchtextbox")

        search_box.fill(search_term)

        search_box.press("Enter")

        page.wait_for_timeout(5000)

        # =================================================
        # FIND PRODUCT CARDS
        # =================================================

        products = page.locator('[data-component-type="s-search-result"]')

        total_products = products.count()

        print("Number of products found:", total_products)

        products_to_scrape = min(PRODUCTS_PER_CATEGORY, total_products)

        print("Products to scrape:", products_to_scrape)

        # =================================================
        # STORE SEARCH RESULTS FIRST
        # =================================================

        search_products = []

        for i in range(products_to_scrape):

            print("\n")
            print("------------------------------------------")
            print(f"READING {category} SEARCH RESULT {i + 1}")
            print("------------------------------------------")

            product = products.nth(i)

            # =============================================
            # PRODUCT NAME
            # =============================================

            product_name = None

            title_spans = product.locator("h2 span")

            if title_spans.count() > 0:

                texts = []

                for j in range(title_spans.count()):

                    text = title_spans.nth(j).inner_text().strip()

                    if text:

                        texts.append(text)

                if texts:

                    product_name = max(texts, key=len)

            # Fallback
            if not product_name:

                headings = product.locator("h2")

                if headings.count() > 0:

                    texts = []

                    for j in range(headings.count()):

                        text = headings.nth(j).inner_text().strip()

                        if text:

                            texts.append(text)

                    if texts:

                        product_name = max(texts, key=len)

            # =============================================
            # CHECK PRODUCT NAME
            # =============================================

            if not product_name:

                print("Product name not found. Skipping.")

                continue

            print("Product name:", product_name)

            # =============================================
            # ADVERTISED PRICE
            # =============================================

            price_element = product.locator(".a-price-whole")

            if price_element.count() > 0:

                price_text = price_element.nth(0).inner_text().strip()

                try:

                    advertised_price = float(price_text.replace(",", ""))

                except ValueError:

                    advertised_price = None

            else:

                advertised_price = None

            print("Advertised price:", advertised_price)

            # =============================================
            # FIND PRODUCT LINK
            # =============================================

            href = None

            product_link = product.get_by_role("link", name=product_name)

            if product_link.count() > 0:

                href = product_link.first.get_attribute("href")

            # Fallback
            if not href:

                all_links = product.locator("a")

                for j in range(all_links.count()):

                    candidate_href = all_links.nth(j).get_attribute("href")

                    if not candidate_href:

                        continue

                    decoded_candidate = unquote(candidate_href)

                    if re.search(r"/dp/[A-Z0-9]{10}", decoded_candidate):

                        href = candidate_href

                        break

                    if re.search(r"/gp/product/[A-Z0-9]{10}", decoded_candidate):

                        href = candidate_href

                        break

            # =============================================
            # CHECK LINK
            # =============================================

            if not href:

                print("Product link not found. Skipping.")

                continue

            # =============================================
            # DECODE URL
            # =============================================

            decoded_href = unquote(href)

            # =============================================
            # EXTRACT ASIN
            # =============================================

            asin_match = re.search(r"/dp/([A-Z0-9]{10})", decoded_href)

            if not asin_match:

                asin_match = re.search(r"/gp/product/([A-Z0-9]{10})", decoded_href)

            if not asin_match:

                print("ASIN not found. Skipping.")

                continue

            # =================================================
            # ASIN USED AS SKU
            # =================================================

            sku = asin_match.group(1)

            # =================================================
            # PRODUCT URL
            # =================================================

            product_url = f"https://www.amazon.in/dp/{sku}"

            print("SKU:", sku)

            print("Product URL:", product_url)

            # =================================================
            # STORE SEARCH RESULT
            # =================================================

            search_products.append(
                {
                    "Category": category,
                    "Product_name": product_name,
                    "Advertised_price": advertised_price,
                    "SKU": sku,
                    "Product_URL": product_url,
                }
            )

        # =================================================
        # SCRAPE PRODUCT PAGES
        # =================================================

        print("\n")
        print("------------------------------------------")
        print(f"STARTING {category} PRODUCT PAGE SCRAPING")
        print("------------------------------------------")

        for i, product_data in enumerate(search_products, start=1):

            print("\n")
            print(f"PROCESSING {category} PRODUCT {i}")

            # =============================================
            # GET STORED VALUES
            # =============================================

            category = product_data["Category"]

            product_name = product_data["Product_name"]

            advertised_price = product_data["Advertised_price"]

            sku = product_data["SKU"]

            product_url = product_data["Product_URL"]

            print("Product name:", product_name)

            print("Advertised price:", advertised_price)

            print("SKU:", sku)

            print("Product URL:", product_url)

            # =============================================
            # OPEN PRODUCT PAGE
            # =============================================

            try:

                page.goto(product_url, wait_until="domcontentloaded", timeout=60000)

                page.wait_for_timeout(4000)

            except Exception as e:

                print("Could not open product page:", e)

                continue

            # =============================================
            # SELLER
            # =============================================

            seller_element = page.locator("#sellerProfileTriggerId")

            if seller_element.count() > 0:

                seller_name = seller_element.first.inner_text().strip()

            else:

                seller_name = None

            print("Seller name:", seller_name)

            # =============================================
            # SCREENSHOT
            # =============================================

            screenshot_path = screenshot_folder / f"{sku}.png"

            try:

                page.screenshot(path=str(screenshot_path), full_page=True)

                print("Screenshot saved:", screenshot_path)

            except Exception as e:

                screenshot_path = None

                print("Screenshot failed:", e)

            # =============================================
            # LAST TIME COLLECTED
            # =============================================

            last_time_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print("Last time collected:", last_time_collected)

            # =============================================
            # REGION
            # =============================================

            region = "India"

            # =============================================
            # CREATE SELLER RECORD
            # =============================================

            seller_record = {
                "Seller_name": seller_name,
                "SKU": sku,
                "Region": region,
                "Category": category,
                "Advertised_price": advertised_price,
                "Marketplace": "Amazon",
                "Screenshot": (str(screenshot_path) if screenshot_path else None),
                "Live_link": product_url,
                "Last_time_collected": last_time_collected,
            }

            # =============================================
            # ADD RECORD
            # =============================================

            seller_records.append(seller_record)

    # =====================================================
    # CREATE DATAFRAME
    # =====================================================

    seller_table = pd.DataFrame(seller_records)

    # =====================================================
    # ORDER COLUMNS
    # =====================================================

    seller_table = seller_table[
        [
            "Seller_name",
            "SKU",
            "Region",
            "Category",
            "Advertised_price",
            "Marketplace",
            "Screenshot",
            "Live_link",
            "Last_time_collected",
        ]
    ]

    # =====================================================
    # DISPLAY SELLER TABLE
    # =====================================================

    print("\n")
    print("##################################################")
    print("FINAL AMAZON SELLER TABLE")
    print("##################################################")

    print(seller_table.to_string(index=False))

    # =====================================================
    # SAVE CSV
    # =====================================================

    csv_path = scraped_dir / "amazon_seller_table.csv"

    seller_table.to_csv(csv_path, index=False)

    # =====================================================
    # SUMMARY
    # =====================================================

    print("\n")
    print("##################################################")
    print("AMAZON SCRAPING COMPLETED")
    print("##################################################")

    print("Total records:", len(seller_table))

    print("Laptop records:", len(seller_table[seller_table["Category"] == "Laptop"]))

    print("Printer records:", len(seller_table[seller_table["Category"] == "Printer"]))

    print(
        "Ink/Toner records:", len(seller_table[seller_table["Category"] == "Ink_Toner"])
    )

    print("CSV file:", csv_path)

    # =====================================================
    # CLOSE BROWSER
    # =====================================================

    browser.close()
