"""
Stage 2 ETL: Cross-Border Currency Normalization & MAP/LPP Violation Auditing
Author: Derin Girish D G
Description: Mirrors Notebook 02 — joins daily feeds with master catalogs, normalizes
currencies to INR, applies Q4 promotion rules, and writes monitoring & violation ledgers.
"""

import sys
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config.finance_config import FX_RATES

DB_TABLES_DIR = BASE_DIR / "data_processed" / "database_tables"
INTERMEDIATE_DIR = BASE_DIR / "data_processed" / "intermediate"
ACTIVE_SEASON = "Q4"


def run_monitoring_pipeline(
    db_tables_dir: Path = DB_TABLES_DIR,
    intermediate_dir: Path = INTERMEDIATE_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates price_monitoring_table.csv and violation_table.csv from ingested tables."""
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

    merged_df["FX_Rate"] = merged_df["Region"].map(FX_RATES).fillna(1.0)
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

    usd_rate = FX_RATES.get("USA", 83.50)
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
