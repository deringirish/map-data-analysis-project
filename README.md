# Minimum Advertised Price (MAP) Compliance & Analysis System

An end-to-end data engineering and analytics solution for tracking and enforcing **Minimum Advertised Price (MAP)** policies across e-commerce marketplaces (Amazon, Flipkart, eBay, Snapdeal).

---

## 📁 Project Directory Structure

```text
Map Data Analysis Project/
│
├── data_given/                           # UNTOUCHED external reference materials & inputs
│   ├── task_1/                           # Project Charter, Data Dictionary, Session 1 PDF
│   ├── task_2/                           # Raw inputs (PN_SKU.xml, product_info.json, MAP_PL_SKU.yaml,
│   │                                     #   seller_name.xlsx, lpp_calcuation.xlsx, promotion_sku.xlsx)
│   ├── task_3/                           # Marketplace seller data feeds
│   │   └── seller_data/                  #   15 Daily CSVs (2025-12-21.csv to 2026-01-05.csv)
│   └── meeting_notes_2024_09_12/         # 15 session slides & review meeting screenshots
│
├── data_code/                            # WORKING DATA produced and used by your code
│   ├── database_tables/                  # Production 3NF tables loaded directly into MySQL
│   │                                     #   (sku_table.csv, pl_table.csv, price_list_table.csv,
│   │                                     #    seller_mapping_table.csv, category_mapping_table.csv,
│   │                                     #    promotion_table.csv, seller_table.csv)
│   ├── intermediate/                     # Working tables & reference lookup matrices
│   │                                     #   (derived_product_info.csv, lpp_data.csv,
│   │                                     #    promotion_condition.csv, promotional_skus.csv)
│   ├── scraped/                          # Real-time web scraping outputs
│   │   ├── amazon_seller_table.csv       # Scraped Amazon seller records
│   │   ├── flipkart_seller_table.csv     # Scraped Flipkart seller records
│   │   └── screenshots/                  # Audit proof listing screenshots (.png)
│   └── evidence/                         # Verification screenshots
│       └── database_validation/          #   MySQL table count & schema verification screenshots
│
├── src/                                  # ALL project implementation code & notebooks
│   ├── notebooks/                        # Jupyter Notebooks
│   │   └── data_population.ipynb         # Data preparation, LPP calculation & export pipeline
│   ├── database/                         # Database schema & ingestion scripts
│   │   ├── create_tables.sql             # MySQL DDL for MAP_PROJECT schema
│   │   ├── database_population.py        # Ingestion script to populate MySQL from database_tables/
│   │   ├── database_validator.sql        # Verification queries
│   │   └── database_validation.py        # Python verification script
│   └── scrapers/                         # Automated e-commerce scrapers (Playwright)
│       ├── amazon_scraper.py             # Scrapes Amazon.in listings & captures screenshots
│       └── flipkart_scraper.py           # Scrapes Flipkart listings & captures screenshots
│
├── .venv/                                # Single, unified virtual environment (uv)
├── pyproject.toml                        # Project dependencies (uv-managed)
├── uv.lock                               # Locked dependency versions
├── .python-version                       # Target Python version (3.14.7)
├── .gitignore                            # Standard Python ignore rules
├── main.py                               # Entry script
└── README.md                             # Documentation & usage guide
```

---

## 🚀 Setup & Execution

### 1. Environment Setup
The project uses `uv` for fast package management:
```powershell
# Sync/install all dependencies in .venv
uv sync
```

### 2. Running Data Preparation (Notebook)
Open `src/notebooks/data_population.ipynb` in VS Code or Jupyter Notebook:
* **Inputs**: Reads raw XML, JSON, YAML, and Excel files from `../../data_given/task_2/`
* **Outputs**: Generates clean, normalized relational CSV tables into `../../data_code/derived/`

### 3. Populating MySQL Database
1. Run `src/database/create_tables.sql` in MySQL to initialize `MAP_PROJECT` schema:
   ```sql
   source src/database/create_tables.sql;
   ```
2. Ingest the normalized tables:
   ```powershell
   python src/database/database_population.py
   ```
3. Validate row counts:
   ```powershell
   python src/database/database_validation.py
   ```

### 4. Running Web Scrapers
To scrape real-time marketplace prices and save screenshots for evidence:
```powershell
# Amazon Scraper
python src/scrapers/amazon_scraper.py

# Flipkart Scraper
python src/scrapers/flipkart_scraper.py
```
Outputs and evidence screenshots are automatically saved to `data_code/scraped/`.
