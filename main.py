"""
MAP Compliance & Brand Protection Analytics Engine - Master Orchestration Entrypoint
Author: Derin Girish D G
Description: End-to-end orchestration CLI for data ingestion, policy auditing,
category suspension enforcement, legal notice synthesis, and analytics visualization.
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.enforcement.category_suspension_engine import evaluate_category_suspensions, plot_suspension_overview, sync_suspensions_to_mysql
from src.reporting.generate_visualizations import generate_all_figures
from src.reporting.generate_violation_notices import generate_all_notices_and_update_tables


def run_suspension_pipeline():
    print("\n" + "=" * 65)
    print(" [STAGE 1] CATEGORY SUSPENSION & RECIDIVISM ENFORCEMENT")
    print("=" * 65)
    df = evaluate_category_suspensions()
    plot_suspension_overview(df)
    sync_suspensions_to_mysql(df)


def run_visualization_pipeline():
    print("\n" + "=" * 65)
    print(" [STAGE 2] PUBLICATION-GRADE VISUAL ANALYTICS")
    print("=" * 65)
    generate_all_figures()


def run_notice_pipeline():
    print("\n" + "=" * 65)
    print(" [STAGE 3] AUTOMATED LEGAL WARNING NOTICE GENERATION")
    print("=" * 65)
    generate_all_notices_and_update_tables()


def run_database_population(engine: str = None):
    print("\n" + "=" * 65)
    print(" [DATABASE] INGESTING 3NF RELATIONAL WAREHOUSE")
    print("=" * 65)
    import subprocess
    script = BASE_DIR / "src" / "database" / "database_population.py"
    cmd = [sys.executable, str(script)]
    if engine:
        cmd.extend(["--engine", engine])
    subprocess.run(cmd, check=True)


def run_database_validation(engine: str = None):
    print("\n" + "=" * 65)
    print(" [VALIDATION] RUNNING PRODUCTION RECORD COUNT AUDIT")
    print("=" * 65)
    import subprocess
    script = BASE_DIR / "src" / "database" / "database_validation.py"
    cmd = [sys.executable, str(script)]
    if engine:
        cmd.extend(["--engine", engine])
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Minimum Advertised Price (MAP) Data Analysis & Compliance Engine"
    )
    parser.add_argument(
        "--all", action="store_true", default=False,
        help="Execute all compliance modules (suspensions, charts, and notices)"
    )
    parser.add_argument(
        "--suspend", action="store_true",
        help="Run category suspension evaluation (Charter Objective 4)"
    )
    parser.add_argument(
        "--charts", action="store_true",
        help="Generate all high-resolution visual analytics charts"
    )
    parser.add_argument(
        "--notices", action="store_true",
        help="Generate all 279 .docx category warning notices"
    )
    parser.add_argument(
        "--populate-db", action="store_true",
        help="Execute 3NF database schema batch population"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Execute table record validation audit"
    )
    parser.add_argument(
        "--engine", choices=["auto", "mysql", "sqlite"], default=None,
        help="Target database engine: 'mysql', 'sqlite', or 'auto' (default: auto-fallback to SQLite)"
    )

    args = parser.parse_args()

    # Default to running all reporting/enforcement stages if no specific flag passed
    if not any([args.all, args.suspend, args.charts, args.notices, args.populate_db, args.validate]):
        args.all = True

    print("=" * 65)
    print("   MAP DATA ANALYSIS & COMPLIANCE ENGINE v1.0")
    print("=" * 65)

    if args.populate_db:
        run_database_population(engine=args.engine)

    if args.all or args.suspend:
        run_suspension_pipeline()

    if args.all or args.charts:
        run_visualization_pipeline()

    if args.all or args.notices:
        run_notice_pipeline()

    if args.validate:
        run_database_validation(engine=args.engine)

    print("\n" + "=" * 65)
    print(" Pipeline execution finished successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
