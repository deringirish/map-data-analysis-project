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


def run_suspension_pipeline(as_of_date: str = None):
    print("\n" + "=" * 65)
    print(" [STAGE 1] CATEGORY SUSPENSION & RECIDIVISM ENFORCEMENT")
    print("=" * 65)
    df = evaluate_category_suspensions(as_of_date=as_of_date)
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


def run_guardrails_pipeline():
    from src.database.data_guardrails import run_data_guardrails
    run_data_guardrails()


def run_stats_pipeline():
    from src.analytics.statistical_tests import run_full_statistical_battery
    run_full_statistical_battery()


def run_test_suite():
    import subprocess
    print("\n" + "=" * 65)
    print(" [TESTS] EXECUTING PYTEST AUTOMATED UNIT & INTEGRITY SUITE")
    print("=" * 65)
    subprocess.run([sys.executable, "-m", "pytest", "-v"], check=True)


def run_dashboard():
    import subprocess
    print("\n" + "=" * 65)
    print(" [DASHBOARD] LAUNCHING STREAMLIT BI HUB (PORT 8501)")
    print("=" * 65)
    app_path = BASE_DIR / "src" / "dashboard" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


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
        "--guardrails", action="store_true",
        help="Execute ingestion data quality and schema conformance guardrails audit"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Execute inferential statistical hypothesis testing battery (Kruskal-Wallis, ANOVA)"
    )
    parser.add_argument(
        "--tests", action="store_true",
        help="Execute pytest automated unit & integrity test suite"
    )
    parser.add_argument(
        "--dashboard", action="store_true",
        help="Launch interactive Streamlit BI application"
    )
    parser.add_argument(
        "--engine", choices=["auto", "mysql", "sqlite"], default=None,
        help="Target database engine: 'mysql', 'sqlite', or 'auto' (default: auto-fallback to SQLite)"
    )
    parser.add_argument(
        "--as-of-date", type=str, default=None,
        help="Audit reference date for category suspensions (YYYY-MM-DD). Defaults to latest date + 1 day."
    )

    args = parser.parse_args()

    # Default to running all reporting/enforcement stages if no specific flag passed
    if not any([args.all, args.suspend, args.charts, args.notices, args.populate_db, args.validate, args.guardrails, args.stats, args.tests, args.dashboard]):
        args.all = True

    print("=" * 65)
    print("   MAP DATA ANALYSIS & COMPLIANCE ENGINE v1.0")
    print("=" * 65)

    if args.tests:
        run_test_suite()

    if args.guardrails or args.all:
        run_guardrails_pipeline()

    if args.populate_db:
        run_database_population(engine=args.engine)

    if args.all or args.suspend:
        run_suspension_pipeline(as_of_date=args.as_of_date)

    if args.all or args.charts:
        run_visualization_pipeline()

    if args.all or args.notices:
        run_notice_pipeline()

    if args.stats or args.all:
        run_stats_pipeline()

    if args.validate:
        run_database_validation(engine=args.engine)

    if args.dashboard:
        run_dashboard()

    print("\n" + "=" * 65)
    print(" Pipeline execution finished successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
