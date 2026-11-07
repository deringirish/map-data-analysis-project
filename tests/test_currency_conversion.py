"""
Unit Tests for Cross-Border Currency Conversion & Spot FX Rates
"""

import pytest
from src.config.finance_config import convert_to_inr, FX_RATES


def test_convert_to_inr_base_currency():
    assert convert_to_inr(1500.0, "IND") == 1500.0
    assert convert_to_inr(1500.0, "ind") == 1500.0


def test_convert_to_inr_usd():
    # 100 USD at 83.25 -> 8325.0
    assert convert_to_inr(100.0, "USA") == 8325.0


def test_convert_to_inr_gbp():
    # 10 GBP at 105.50 -> 1055.0
    assert convert_to_inr(10.0, "UK") == 1055.0


def test_convert_to_inr_cad():
    # 50 CAD at 61.40 -> 3070.0
    assert convert_to_inr(50.0, "CAN") == 3070.0


def test_convert_to_inr_aed():
    # 100 AED at 22.65 -> 2265.0
    assert convert_to_inr(100.0, "UAE") == 2265.0


def test_convert_to_inr_unknown_region_fallback():
    # Unknown defaults to 1.0 multiplier
    assert convert_to_inr(500.0, "UNKNOWN_REGION") == 500.0
