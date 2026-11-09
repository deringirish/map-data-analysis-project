"""
Centralized Financial & Pricing Configuration Module
Author: Derin Girish D G
Description: Houses dynamic margin calculation rules, currency conversion rates, and baseline floor derivation utilities.
"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import openpyxl

BASE_DIR = Path(__file__).resolve().parents[2]
LPP_EXCEL_PATH = BASE_DIR / "data_inputs" / "master_catalog" / "lpp_calcuation.xlsx"

# Standard Base-to-INR Foreign Exchange Spot Conversion Rates
FX_RATES: Dict[str, float] = {
    "IND": 1.00,      # Base Currency: Indian Rupee (INR)
    "USA": 83.25,     # USD to INR
    "UK": 105.50,     # GBP to INR
    "CAN": 61.40,     # CAD to INR
    "UAE": 22.65      # AED to INR
}

# Currency Symbols mapping
CURRENCY_SYMBOLS: Dict[str, str] = {
    "IND": "₹",
    "USA": "$",
    "UK": "£",
    "CAN": "CA$",
    "UAE": "AED "
}


def load_margin_matrix(excel_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Parses authorized margin reduction percentages from lpp_calcuation.xlsx.
    Fallback values apply if spreadsheet is missing or unreadable.
    """
    path = excel_path or LPP_EXCEL_PATH
    if path.exists():
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb["Sheet1"]
            data = []
            for row in sheet.iter_rows(values_only=True):
                if row[0] and any(row[0].startswith(f"{i}.") for i in range(1, 10)):
                    clean_subcat = row[0].split(". ", 1)[-1].strip()
                    hp_margin = float(row[1]) if row[1] is not None else 0.0
                    dell_margin = float(row[2]) if row[2] is not None else 0.0
                    data.append({
                        "Sub_category": clean_subcat,
                        "HP_Margin": hp_margin,
                        "Dell_Margin": dell_margin
                    })
            if data:
                return pd.DataFrame(data)
        except Exception as e:
            print(f"[WARN] Error reading dynamic LPP Excel: {e}. Using fallback defaults.")

    # Canonical Fallback Matrix
    return pd.DataFrame([
        {"Sub_category": "Laptop", "HP_Margin": 0.034, "Dell_Margin": 0.078},
        {"Sub_category": "Monitor", "HP_Margin": 0.012, "Dell_Margin": 0.056},
        {"Sub_category": "Toner", "HP_Margin": 0.091, "Dell_Margin": 0.023},
        {"Sub_category": "Laserjet", "HP_Margin": 0.065, "Dell_Margin": 0.035},
        {"Sub_category": "Inkjet", "HP_Margin": 0.012, "Dell_Margin": 0.056},
        {"Sub_category": "Desktop", "HP_Margin": 0.091, "Dell_Margin": 0.023},
        {"Sub_category": "Ink", "HP_Margin": 0.065, "Dell_Margin": 0.035},
    ])


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
