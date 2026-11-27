"""
Stage 1 ETL: Raw Multi-Format Catalog & Feed Ingestion
Author: Derin Girish D G
Description: Mirrors Notebook 01 — parses XML, JSON, YAML, Excel master catalogs and
15 daily marketplace CSV feeds, derives LPP floors, and exports normalized 3NF CSVs.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict
import yaml
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_INPUTS_DIR = BASE_DIR / "data_inputs"
DATA_PROCESSED_DIR = BASE_DIR / "data_processed"
DB_TABLES_DIR = DATA_PROCESSED_DIR / "database_tables"
INTERMEDIATE_DIR = DATA_PROCESSED_DIR / "intermediate"

ACTIVE_SEASON = "Q4"

SUB_CATEGORY_MAP = {
    "TON": "Toner",
    "LJ": "Laserjet",
    "IJ": "Inkjet",
    "INK": "Ink",
    "Laptop": "Laptop",
    "Monitor": "Monitor",
    "Desktop": "Desktop",
}


def run_ingestion_pipeline(
    inputs_dir: Path = DATA_INPUTS_DIR,
    db_tables_dir: Path = DB_TABLES_DIR,
    intermediate_dir: Path = INTERMEDIATE_DIR,
) -> Dict[str, pd.DataFrame]:
    """Parses raw master catalogs and daily CSV feeds into 3NF CSV tables."""
    db_tables_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse XML SKU Catalog
    root = ET.parse(inputs_dir / "master_catalog" / "PN_SKU.xml").getroot()
    records = [{sub.tag.strip(): (sub.text.strip() if sub.text else None) for sub in child} for child in root]
    sku_raw = pd.DataFrame(records)
    sku_raw.columns = [col.upper() if col.lower() == "sku" else col for col in sku_raw.columns]
    sku_table_data = sku_raw.drop_duplicates(subset=["SKU"], keep="first").reset_index(drop=True)

    # 2. Parse JSON Product Taxonomy
    product_info = pd.read_json(inputs_dir / "master_catalog" / "product_info.json").rename(columns={"sku": "SKU"})
    split_series = product_info["PL"].str.strip().str.split("_")
    product_info["COMPANY"] = split_series.str[0].str[:-2]
    product_info["CATEGORY"] = split_series.str[-2]
    product_info["SUB_CATEGORY"] = split_series.str[-1]
    product_info = product_info[~product_info["SUB_CATEGORY"].isin(["UNK", "SJ"])].reset_index(drop=True)
    product_info = product_info.drop_duplicates(subset=["SKU"], keep="first").reset_index(drop=True)
    product_info["SUB_CATEGORY"] = product_info["SUB_CATEGORY"].replace(SUB_CATEGORY_MAP)
    derived_product_info = product_info.copy()

    # 3. Parse YAML MAP Pricing
    with open(inputs_dir / "master_catalog" / "MAP_PL_SKU.yaml", "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)
    product_info_with_map = pd.DataFrame(yaml_data).rename(columns={"sku": "SKU"})
    product_info_with_map = product_info_with_map.drop_duplicates(subset=["SKU"], keep="first").reset_index(drop=True)
    derived_product_info = derived_product_info.merge(product_info_with_map[["SKU", "MAP"]], on="SKU", how="inner")

    # 4. Ingest Seller Alias Mapping
    seller_data = pd.read_excel(inputs_dir / "master_catalog" / "seller_name.xlsx").rename(
        columns={"Ssellers_name": "SELLER_NAME", "homologated_sellers": "HOMOLOGATED_NAME"}
    )
    seller_data["SELLER_NAME"] = seller_data["SELLER_NAME"].astype(str).str.strip()
    seller_data["HOMOLOGATED_NAME"] = seller_data["HOMOLOGATED_NAME"].astype(str).str.strip()
    seller_data = (
        seller_data[seller_data["SELLER_NAME"].str.lower() != "seller"]
        .drop_duplicates(subset=["SELLER_NAME"], keep="first")
        .reset_index(drop=True)
    )

    # 5. Ingest Brand Discount Matrix & Compute LPP
    lpp_data = pd.read_excel(
        inputs_dir / "master_catalog" / "lpp_calcuation.xlsx", usecols="B:D", skiprows=5, nrows=8
    ).rename(columns={"Sub_category": "SUB_CATEGORY", "Hp": "HP", "Dell": "DELL"})
    lpp_data["SUB_CATEGORY"] = lpp_data["SUB_CATEGORY"].str.replace(r"^\d+\.\s*", "", regex=True)
    lpp_matrix = lpp_data.set_index("SUB_CATEGORY").to_dict()
    derived_product_info["LPP"] = derived_product_info.apply(
        lambda r: round(r["MAP"] * (1.0 - lpp_matrix.get(r["COMPANY"], {}).get(r["SUB_CATEGORY"], 0.0)), 2),
        axis=1,
    )

    # 6. Ingest Promotion Rules & Eligibility
    promo_file = inputs_dir / "master_catalog" / "promotion_sku.xlsx"
    promotion_condition = pd.read_excel(promo_file, usecols="B:F", skiprows=6, nrows=4).rename(
        columns={"Category": "CATEGORY", "Q1 (Nov-Jan)": "Q1", "Q2 (Feb-Apr)": "Q2", "Q3 (May-Jul)": "Q3", "Q4 (Aug-Oct)": "Q4"}
    )
    promotion_condition["CATEGORY"] = promotion_condition["CATEGORY"].replace(
        {"Supply": "SUP", "Print Hardware": "PH", "PC": "PC"}
    )
    promotional_skus = pd.read_excel(promo_file, usecols="B", skiprows=15, header=None)
    promotional_skus.columns = ["SKU"]
    promotional_skus = promotional_skus.dropna().drop_duplicates().reset_index(drop=True)
    promotional_skus["SKU"] = promotional_skus["SKU"].astype(str).str.strip()

    promotion_data = promotional_skus.merge(derived_product_info[["SKU", "PL", "CATEGORY"]], on="SKU", how="inner")
    promotion_data["SEASON"] = ACTIVE_SEASON
    promotion_data["PROMOTION"] = promotion_data["CATEGORY"].map(promotion_condition.set_index("CATEGORY")["Q4"].to_dict())

    # 7. Batch Ingest Daily Marketplace CSV Feeds
    seller_files = sorted((inputs_dir / "marketplace_feeds" / "daily_seller_feeds").glob("*.csv"))
    seller_dfs = []
    for f in seller_files:
        df = pd.read_csv(f)
        df["Last time collected"] = f.stem
        seller_dfs.append(df)
    seller_table = pd.concat(seller_dfs, ignore_index=True).rename(
        columns={"region": "Region", "adv_price": "Advertised_price", "live_link": "Live_link"}
    )
    seller_table["Screenshot"] = seller_table.get("Screenshot", pd.Series(dtype=str)).fillna("")
    seller_table["Live_link"] = seller_table.get("Live_link", pd.Series(dtype=str)).fillna("")
    seller_table = seller_table[
        ["Seller_name", "SKU", "Region", "Advertised_price", "Marketplace", "Screenshot", "Live_link", "Last time collected"]
    ]

    db_exports = {
        "sku_table.csv": sku_table_data[["PN", "SKU"]].copy(),
        "pl_table.csv": derived_product_info[["PL", "SKU", "SUB_CATEGORY"]].copy(),
        "price_list_table.csv": derived_product_info[["PL", "SKU", "MAP", "LPP"]].copy(),
        "seller_mapping_table.csv": seller_data[["SELLER_NAME", "HOMOLOGATED_NAME"]].copy(),
        "category_mapping_table.csv": derived_product_info[["CATEGORY", "SUB_CATEGORY", "PL", "SKU"]].copy(),
        "promotion_table.csv": promotion_data[["PL", "SKU", "SEASON", "PROMOTION"]].copy(),
        "seller_table.csv": seller_table,
    }
    for filename, df in db_exports.items():
        df.to_csv(db_tables_dir / filename, index=False)

    intermediate_exports = {
        "derived_product_info.csv": derived_product_info,
        "lpp_data.csv": lpp_data,
        "promotion_condition.csv": promotion_condition,
        "promotional_skus.csv": promotional_skus,
    }
    for filename, df in intermediate_exports.items():
        df.to_csv(intermediate_dir / filename, index=False)

    print(f"[ETL Stage 1] Exported {len(db_exports)} master/feed tables and {len(intermediate_exports)} intermediate files.")
    return db_exports
