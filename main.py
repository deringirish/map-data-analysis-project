"""
MAP Policy Compliance Project - Main Execution Script
Author: Derin Girish
Description: Runs the automated MAP violation notice generation engine and updates audit records.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from src.reporting.generate_violation_notices import generate_all_notices_and_update_tables


def main():
    print("=" * 65)
    print(" MAP COMPLIANCE: VIOLATION NOTICE GENERATION ENGINE")
    print("=" * 65)
    print("1. Reading violation records from database / violation table...")
    print("2. Grouping violations by Seller and Product Category...")
    print("3. Generating category-level .docx warning notices with itemized sub-categories...")
    print("4. Updating Notice_Doc_Path in violation audit records...")
    print("-" * 65)
    
    generate_all_notices_and_update_tables()
    
    print("=" * 65)
    print(" Pipeline execution finished successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
