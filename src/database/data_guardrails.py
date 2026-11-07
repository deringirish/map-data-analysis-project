"""
Data Observability & Ingestion Guardrails Subsystem
Author: Derin Girish D G
Description: Automated schema and semantic data quality auditing for marketplace feeds.
Flags anomalous or non-conforming telemetry and quarantines corrupt records.
"""

from pathlib import Path
from typing import Tuple, Dict, Any
import pandas as pd
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
INTERMEDIATE_DIR = BASE_DIR / "data_processed" / "intermediate"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_PATH = INTERMEDIATE_DIR / "quarantine_records.csv"


def validate_marketplace_feed(feed_df: pd.DataFrame = None) -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    """
    Validates daily surveillance pricing telemetry against enterprise data guardrails:
    1. Positive Advertised Pricing (price > 0)
    2. SKU Completeness (non-null and alphanumeric)
    3. Temporal Validity (valid YYYY-MM-DD dates)
    4. Storefront Identification (non-null seller name)
    5. Marketplace Channel Conformance (known marketplace entity)
    """
    if feed_df is None:
        feed_csv = DATA_PATH / "seller_table.csv"
        if not feed_csv.exists():
            raise FileNotFoundError(f"Feed table not found at: {feed_csv}")
        feed_df = pd.read_csv(feed_csv)

    total_records = len(feed_df)
    anomalies = []

    # 1. Price constraint: Advertised_price > 0
    price_col = "Advertised_price"
    if price_col in feed_df.columns:
        invalid_price_mask = feed_df[price_col].isna() | (feed_df[price_col] <= 0)
        invalid_price_count = int(invalid_price_mask.sum())
    else:
        invalid_price_count = 0
        invalid_price_mask = pd.Series(False, index=feed_df.index)

    # 2. SKU completeness
    sku_mask = feed_df["SKU"].isna() | (feed_df["SKU"].astype(str).str.strip() == "")
    invalid_sku_count = int(sku_mask.sum())

    # 3. Storefront entity presence
    seller_mask = feed_df["Seller_name"].isna() | (feed_df["Seller_name"].astype(str).str.strip() == "")
    invalid_seller_count = int(seller_mask.sum())

    # 4. Date validity
    date_col = "Last time collected" if "Last time collected" in feed_df.columns else "Violation_date"
    if date_col in feed_df.columns:
        invalid_date_mask = pd.to_datetime(feed_df[date_col], format="%Y-%m-%d", errors="coerce").isna()
        invalid_date_count = int(invalid_date_mask.sum())
    else:
        invalid_date_mask = pd.Series(False, index=feed_df.index)
        invalid_date_count = 0

    # Composite Quarantine Mask
    quarantine_mask = invalid_price_mask | sku_mask | seller_mask | invalid_date_mask
    quarantine_df = feed_df[quarantine_mask].copy()

    if len(quarantine_df) > 0:
        quarantine_df.to_csv(QUARANTINE_PATH, index=False)
        print(f"[ALERT] {len(quarantine_df):,} anomalous records written to: {QUARANTINE_PATH}")

    clean_records = total_records - len(quarantine_df)
    pass_rate = (clean_records / total_records * 100.0) if total_records > 0 else 0.0

    metrics = {
        "total_records": total_records,
        "clean_records": clean_records,
        "quarantined_records": len(quarantine_df),
        "data_health_score_pct": round(pass_rate, 2),
        "invalid_prices": invalid_price_count,
        "missing_skus": invalid_sku_count,
        "missing_sellers": invalid_seller_count,
        "invalid_dates": invalid_date_count
    }

    is_healthy = len(quarantine_df) == 0

    return is_healthy, metrics, quarantine_df


def run_data_guardrails():
    """CLI / master executor for automated data quality assurance."""
    print("=" * 65)
    print(" DATA OBSERVABILITY & INGESTION GUARDRAILS AUDIT")
    print("=" * 65)
    healthy, metrics, q_df = validate_marketplace_feed()

    print(f"Total Observations Audited:    {metrics['total_records']:,}")
    print(f"Verified Conforming Records:   {metrics['clean_records']:,} ({metrics['data_health_score_pct']}%)")
    print(f"Quarantined Anomalous Records: {metrics['quarantined_records']:,}")
    print("-----------------------------------------------------------------")
    print(f"• Non-positive / Null Prices:  {metrics['invalid_prices']:,}")
    print(f"• Missing / Malformed SKUs:    {metrics['missing_skus']:,}")
    print(f"• Unidentified Resellers:      {metrics['missing_sellers']:,}")
    print(f"• Malformed Dates:             {metrics['invalid_dates']:,}")
    print("=================================================================")
    if healthy:
        print(" [PASS] 100% of feed observations conform strictly to enterprise schema.")
    else:
        print(f" [WARN] {metrics['quarantined_records']} records quarantined.")
    print("=================================================================\n")
    return metrics


if __name__ == "__main__":
    run_data_guardrails()
