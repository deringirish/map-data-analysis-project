"""
Centralized Financial & Pricing Configuration Module
Author: Derin Girish D G
Description: Houses dynamic margin calculation rules, currency conversion rates, and baseline floor derivation utilities.
"""

from typing import Dict

# Standard Base-to-INR Foreign Exchange Spot Conversion Rates
FX_RATES: Dict[str, float] = {
    "IND": 1.00,      # Base Currency: Indian Rupee (INR)
    "USA": 83.25,     # USD to INR
    "UK": 105.50,     # GBP to INR
    "CAN": 61.40,     # CAD to INR
    "UAE": 22.65      # AED to INR
}

# Canonical Enforcement Status Constants (shared across enforcement, briefing, and KPIs)
STATUS_CRITICAL = "CRITICAL_SUSPENSION"
STATUS_FORMAL = "FORMAL_SUSPENSION"
STATUS_PROBATION = "CONDITIONAL_PROBATION"


def convert_to_inr(price: float, region: str) -> float:
    """Normalizes local marketplace price to Indian Rupee (INR)."""
    rate = FX_RATES.get(region.upper(), 1.0)
    return round(float(price) * rate, 2)


def calculate_lpp(map_price: float, discount_percentage: float) -> float:
    """
    Computes Lowest Promotional Price (LPP) floor:
    LPP = MAP * (1 - Discount%)
    """
    margin_ratio = discount_percentage if discount_percentage <= 1.0 else (discount_percentage / 100.0)
    margin_ratio = max(0.0, min(margin_ratio, 1.0))
    return round(float(map_price) * (1.0 - margin_ratio), 2)
