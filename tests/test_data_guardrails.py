"""
Unit Tests for Ingestion Data Guardrails & Observability
"""

import pytest
import pandas as pd
from src.database.data_guardrails import validate_marketplace_feed


def test_guardrails_clean_feed():
    valid_data = pd.DataFrame([
        {
            "Seller_name": "Retailer A",
            "SKU": "SKU_1001",
            "Region": "IND",
            "Advertised_price": 45000.0,
            "Marketplace": "Amazon",
            "Screenshot": "shot1.png",
            "Live_link": "http://amazon.in/p/1",
            "Last time collected": "2025-12-25"
        },
        {
            "Seller_name": "Retailer B",
            "SKU": "SKU_1002",
            "Region": "USA",
            "Advertised_price": 599.99,
            "Marketplace": "eBay",
            "Screenshot": "shot2.png",
            "Live_link": "http://ebay.com/p/2",
            "Last time collected": "2025-12-26"
        }
    ])
    healthy, metrics, q_df = validate_marketplace_feed(valid_data)
    assert healthy is True
    assert metrics["clean_records"] == 2
    assert metrics["quarantined_records"] == 0
    assert len(q_df) == 0


def test_guardrails_quarantine_anomalies():
    corrupted_data = pd.DataFrame([
        {
            # Invalid price (zero)
            "Seller_name": "Store X",
            "SKU": "SKU_99",
            "Advertised_price": 0.0,
            "Last time collected": "2025-12-25"
        },
        {
            # Missing SKU
            "Seller_name": "Store Y",
            "SKU": None,
            "Advertised_price": 100.0,
            "Last time collected": "2025-12-25"
        },
        {
            # Missing Seller
            "Seller_name": "",
            "SKU": "SKU_88",
            "Advertised_price": 200.0,
            "Last time collected": "2025-12-25"
        },
        {
            # Malformed Date
            "Seller_name": "Store Z",
            "SKU": "SKU_77",
            "Advertised_price": 300.0,
            "Last time collected": "INVALID_DATE_FORMAT"
        }
    ])
    healthy, metrics, q_df = validate_marketplace_feed(corrupted_data)
    assert healthy is False
    assert metrics["quarantined_records"] == 4
    assert metrics["invalid_prices"] == 1
    assert metrics["missing_skus"] == 1
    assert metrics["missing_sellers"] == 1
    assert metrics["invalid_dates"] == 1
