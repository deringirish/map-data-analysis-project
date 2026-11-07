"""
Unit Tests for Lowest Promotional Price (LPP) and Margin Derivation
"""

import pytest
from src.config.finance_config import calculate_lpp, load_margin_matrix


def test_calculate_lpp_standard_decimal():
    # 10,000 MAP with 3.4% discount (0.034) -> 9,660.00
    res = calculate_lpp(10000.0, 0.034)
    assert res == 9660.0


def test_calculate_lpp_percentage_integer():
    # 10,000 MAP with 10% discount (10.0) -> 9,000.00
    res = calculate_lpp(10000.0, 10.0)
    assert res == 9000.0


def test_calculate_lpp_zero_discount():
    res = calculate_lpp(5000.0, 0.0)
    assert res == 5000.0


def test_calculate_lpp_full_discount():
    res = calculate_lpp(5000.0, 1.0)
    assert res == 0.0


def test_calculate_lpp_negative_discount_clamped():
    # Negative discount should clamp to 0.0 margin
    res = calculate_lpp(5000.0, -0.05)
    assert res == 5000.0


def test_load_margin_matrix_shape():
    df = load_margin_matrix()
    assert not df.empty
    assert "Sub_category" in df.columns
    assert "HP_Margin" in df.columns
    assert "Dell_Margin" in df.columns
    assert len(df) >= 7
