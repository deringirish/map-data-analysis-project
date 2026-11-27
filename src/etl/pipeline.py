"""
Reproducible Multi-Format ETL & Price Monitoring Pipeline
Author: Derin Girish D G
Description: Extracts and normalizes raw master catalogs (XML, JSON, YAML, Excel)
and daily marketplace CSV feeds into 3NF database tables and compliance audit ledgers.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple
import yaml
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_INPUTS_DIR = BASE_DIR / "data_inputs"
DATA_PROCESSED_DIR = BASE_DIR / "data_processed"
DB_TABLES_DIR = DATA_PROCESSED_DIR / "database_tables"
INTERMEDIATE_DIR = DATA_PROCESSED_DIR / "intermediate"

ACTIVE_SEASON = "Q4"

# Canonical Spot FX Rates used for cross-border monitoring parity (Local -> INR)
MONITORING_FX_RATES: Dict[str, float] = {
    "IND": 1.0,
    "USA": 83.50,
    "CAN": 61.50,
    "UK": 105.00,
    "UAE": 22.70,
}

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
    """
    Stage 1 ETL: Parses XML, JSON, YAML, Excel master catalogs and 15 daily CSV feeds,
    derives LPP floors, and exports normalized 3NF tables and intermediate artifacts.
    """
    db_tables_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse XML SKU Catalog
    xml_path = inputs_dir / "master_catalog" / "PN_SKU.xml"
    root = ET.parse(xml_path).getroot()
    records = [
        {sub.tag.strip(): (sub.text.strip() if sub.text else None) for sub in child}
        for child in root
    ]
    sku_raw = pd.DataFrame(records)
    sku_raw.columns = [col.upper() if col.lower() == "sku" else col for col in sku_raw.columns]
    sku_table_data = sku_raw.drop_duplicates(subset=["SKU"], keep="first").reset_index(drop=True)

    # 2. Parse JSON Product Taxonomy
    json_path = inputs_dir / "master_catalog" / "product_info.json"
    product_info = pd.read_json(json_path).rename(columns={"sku": "SKU"})
    split_series = product_info["PL"].str.strip().str.split("_")
    product_info["COMPANY"] = split_series.str[0].str[:-2]
    product_info["CATEGORY"] = split_series.str[-2]
    product_info["SUB_CATEGORY"] = split_series.str[-1]
    product_info = product_info[~product_info["SUB_CATEGORY"].isin(["UNK", "SJ"])].reset_index(drop=True)
    product_info = product_info.drop_duplicates(subset=["SKU"], keep="first").reset_index(drop=True)
    product_info["SUB_CATEGORY"] = product_info["SUB_CATEGORY"].replace(SUB_CATEGORY_MAP)
    derived_product_info = product_info.copy()

    # 3. Parse YAML MAP Pricing
    yaml_path = inputs_dir / "master_catalog" / "MAP_PL_SKU.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)
    product_info_with_map = pd.DataFrame(yaml_data).rename(columns={"sku": "SKU"})
    product_info_with_map = product_info_with_map.drop_duplicates(subset=["SKU"], keep="first").reset_index(drop=True)
    derived_product_info = derived_product_info.merge(
        product_info_with_map[["SKU", "MAP"]], on="SKU", how="inner"
    )

    # 4. Ingest Seller Alias Mapping
    seller_file = inputs_dir / "master_catalog" / "seller_name.xlsx"
    seller_data = pd.read_excel(seller_file).rename(
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
    lpp_file = inputs_dir / "master_catalog" / "lpp_calcuation.xlsx"
    lpp_data = pd.read_excel(lpp_file, usecols="B:D", skiprows=5, nrows=8).rename(
        columns={"Sub_category": "SUB_CATEGORY", "Hp": "HP", "Dell": "DELL"}
    )
    lpp_data["SUB_CATEGORY"] = lpp_data["SUB_CATEGORY"].str.replace(r"^\d+\.\s*", "", regex=True)
    lpp_matrix = lpp_data.set_index("SUB_CATEGORY").to_dict()

    derived_product_info["LPP"] = derived_product_info.apply(
        lambda r: round(r["MAP"] * (1.0 - lpp_matrix.get(r["COMPANY"], {}).get(r["SUB_CATEGORY"], 0.0)), 2),
        axis=1,
    )

    # 6. Ingest Promotion Rules & Eligibility
    promo_file = inputs_dir / "master_catalog" / "promotion_sku.xlsx"
    promotion_condition = pd.read_excel(promo_file, usecols="B:F", skiprows=6, nrows=4).rename(
        columns={
            "Category": "CATEGORY",
            "Q1 (Nov-Jan)": "Q1",
            "Q2 (Feb-Apr)": "Q2",
            "Q3 (May-Jul)": "Q3",
            "Q4 (Aug-Oct)": "Q4",
        }
    )
    promotion_condition["CATEGORY"] = promotion_condition["CATEGORY"].replace(
        {"Supply": "SUP", "Print Hardware": "PH", "PC": "PC"}
    )
    promotional_skus = pd.read_excel(promo_file, usecols="B", skiprows=15, header=None)
    promotional_skus.columns = ["SKU"]
    promotional_skus = promotional_skus.dropna().drop_duplicates().reset_index(drop=True)
    promotional_skus["SKU"] = promotional_skus["SKU"].astype(str).str.strip()

    promotion_data = promotional_skus.merge(
        derived_product_info[["SKU", "PL", "CATEGORY"]], on="SKU", how="inner"
    )
    promotion_data["SEASON"] = ACTIVE_SEASON
    q4_lookup = promotion_condition.set_index("CATEGORY")["Q4"].to_dict()
    promotion_data["PROMOTION"] = promotion_data["CATEGORY"].map(q4_lookup)

    # 7. Construct 3NF Master Tables
    sku_table = sku_table_data[["PN", "SKU"]].copy()
    pl_table = derived_product_info[["PL", "SKU", "SUB_CATEGORY"]].copy()
    price_list_table = derived_product_info[["PL", "SKU", "MAP", "LPP"]].copy()
    seller_mapping_table = seller_data[["SELLER_NAME", "HOMOLOGATED_NAME"]].copy()
    category_mapping_table = derived_product_info[["CATEGORY", "SUB_CATEGORY", "PL", "SKU"]].copy()
    promotion_table = promotion_data[["PL", "SKU", "SEASON", "PROMOTION"]].copy()

    # 8. Batch Ingest Daily Marketplace CSV Feeds
    seller_files = sorted((inputs_dir / "marketplace_feeds" / "daily_seller_feeds").glob("*.csv"))
    seller_dfs = []
    for f in seller_files:
        df = pd.read_csv(f)
        df["Last time collected"] = f.stem
        seller_dfs.append(df)
    seller_table_raw = pd.concat(seller_dfs, ignore_index=True)

    seller_table = seller_table_raw.rename(
        columns={"region": "Region", "adv_price": "Advertised_price", "live_link": "Live_link"}
    )
    seller_table["Screenshot"] = seller_table.get("Screenshot", pd.Series(dtype=str)).fillna("")
    seller_table["Live_link"] = seller_table.get("Live_link", pd.Series(dtype=str)).fillna("")
    seller_table = seller_table[
        ["Seller_name", "SKU", "Region", "Advertised_price", "Marketplace", "Screenshot", "Live_link", "Last time collected"]
    ]

    db_exports = {
        "sku_table.csv": sku_table,
        "pl_table.csv": pl_table,
        "price_list_table.csv": price_list_table,
        "seller_mapping_table.csv": seller_mapping_table,
        "category_mapping_table.csv": category_mapping_table,
        "promotion_table.csv": promotion_table,
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


def run_monitoring_pipeline(
    db_tables_dir: Path = DB_TABLES_DIR,
    intermediate_dir: Path = INTERMEDIATE_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Stage 2 ETL: Joins daily feeds with master catalogs, normalizes currencies to INR,
    applies seasonal promotion rules, and generates price_monitoring_table.csv & violation_table.csv.
    """
    seller_df = pd.read_csv(db_tables_dir / "seller_table.csv")
    seller_map_df = pd.read_csv(db_tables_dir / "seller_mapping_table.csv")
    cat_map_df = pd.read_csv(db_tables_dir / "category_mapping_table.csv")
    price_list_df = pd.read_csv(db_tables_dir / "price_list_table.csv")
    prom_tab_df = pd.read_csv(db_tables_dir / "promotion_table.csv")
    promotional_skus_df = pd.read_csv(intermediate_dir / "promotional_skus.csv")

    authorized_promotional_skus = set(promotional_skus_df["SKU"].dropna().unique())

    merged_df = (
        seller_df.merge(seller_map_df, left_on="Seller_name", right_on="SELLER_NAME", how="left")
        .merge(cat_map_df, on="SKU", how="left")
        .merge(price_list_df[["SKU", "MAP", "LPP"]], on="SKU", how="left")
    )
    q4_promo = prom_tab_df[prom_tab_df["SEASON"] == ACTIVE_SEASON][["SKU", "PROMOTION"]].drop_duplicates(subset=["SKU"])
    merged_df = merged_df.merge(q4_promo, on="SKU", how="left")

    merged_df["FX_Rate"] = merged_df["Region"].map(MONITORING_FX_RATES).fillna(1.0)
    merged_df["Advertised_price_INR"] = np.round(merged_df["Advertised_price"] * merged_df["FX_Rate"], 2)

    in_promo_sku = merged_df["SKU"].isin(authorized_promotional_skus)
    is_pc = merged_df["CATEGORY"] == "PC"
    is_sup_ink = merged_df["CATEGORY"].isin(["SUP", "Supply"]) & (
        merged_df["SUB_CATEGORY"].astype(str).str.lower() == "ink"
    )
    is_ph_laser = merged_df["CATEGORY"].isin(["PH", "Print Hardware"]) & (
        merged_df["SUB_CATEGORY"].astype(str).str.lower().str.contains("laser", na=False)
    )
    is_promo_eligible = in_promo_sku & (is_pc | is_sup_ink | is_ph_laser)

    merged_df["Promotion"] = np.where(is_promo_eligible, merged_df["PROMOTION"], np.nan)
    merged_df["Season"] = ACTIVE_SEASON

    # Vectorized Promotional_price calculation
    adv = merged_df["Advertised_price"]
    cat_str = merged_df["CATEGORY"].astype(str).str.strip()
    subcat_str = merged_df["SUB_CATEGORY"].astype(str).str.strip().str.lower()
    region_str = merged_df["Region"].astype(str).str.strip().str.upper()

    usd_rate = MONITORING_FX_RATES.get("USA", 83.50)
    laser_discount = np.where(region_str == "IND", 10.0 * usd_rate, 10.0)

    merged_df["Promotional_price"] = np.where(
        in_promo_sku & (cat_str == "PC"),
        np.round(adv * 0.85, 2),
        np.where(
            in_promo_sku & cat_str.isin(["SUP", "Supply"]) & (subcat_str == "ink"),
            np.round(adv * 0.80, 2),
            np.where(
                in_promo_sku & cat_str.isin(["PH", "Print Hardware"]) & subcat_str.str.contains("laser", na=False),
                np.round(np.maximum(0.0, adv - laser_discount), 2),
                adv,
            ),
        ),
    )

    # Vectorized Violation_Type & Price_Difference
    has_catalog = merged_df["MAP"].notna() & merged_df["LPP"].notna()
    below_lpp = has_catalog & (merged_df["Advertised_price_INR"] < merged_df["LPP"])
    unauth_disc = has_catalog & (~below_lpp) & (~in_promo_sku) & (merged_df["Advertised_price_INR"] < merged_df["MAP"])

    merged_df["Violation_Type"] = np.select(
        [below_lpp, unauth_disc],
        ["Price Below LPP", "Unauthorized Discount (Non-Promotional SKU)"],
        default=None,
    )
    merged_df["Price_Difference"] = np.where(
        below_lpp,
        np.round(merged_df["LPP"] - merged_df["Advertised_price_INR"], 2),
        np.where(
            unauth_disc,
            np.round(merged_df["MAP"] - merged_df["Advertised_price_INR"], 2),
            np.nan,
        ),
    )

    master_df = merged_df.rename(
        columns={
            "Last time collected": "Violation_date",
            "CATEGORY": "Category",
            "SUB_CATEGORY": "Sub_category",
            "Seller_name": "seller_name",
            "HOMOLOGATED_NAME": "homologated_name",
            "MAP": "MAP_Price",
        }
    )

    pm_columns = [
        "SKU", "Violation_date", "PL", "Category", "Sub_category", "Region", "Marketplace",
        "seller_name", "homologated_name", "MAP_Price", "LPP", "Advertised_price", "Season", "Promotional_price",
    ]
    v_columns = [
        "SKU", "Violation_date", "PL", "Category", "Sub_category", "Region", "Marketplace",
        "seller_name", "homologated_name", "MAP_Price", "LPP", "Advertised_price", "Season",
        "Promotion", "Promotional_price", "Screenshot", "Violation_Type", "Price_Difference",
    ]

    price_monitoring_table = master_df[pm_columns].copy()
    violation_table = master_df[master_df["Violation_Type"].notna()][v_columns].copy()

    price_monitoring_table.to_csv(db_tables_dir / "price_monitoring_table.csv", index=False)
    violation_table.to_csv(db_tables_dir / "violation_table.csv", index=False)

    print(
        f"[ETL Stage 2] Exported price_monitoring_table.csv ({len(price_monitoring_table):,} rows) "
        f"and violation_table.csv ({len(violation_table):,} rows)."
    )
    return price_monitoring_table, violation_table


def run_full_etl() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes Stage 1 (raw ingestion) and Stage 2 (price monitoring & violation auditing)."""
    run_ingestion_pipeline()
    return run_monitoring_pipeline()


if __name__ == "__main__":
    run_full_etl()
