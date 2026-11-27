"""
Reproducible ETL Pipeline Orchestrator
Author: Derin Girish D G
Description: Thin orchestrator combining Stage 1 (ingest.py) and Stage 2 (monitor.py).
"""

from typing import Tuple
import pandas as pd

from src.etl.ingest import DATA_INPUTS_DIR, run_ingestion_pipeline
from src.etl.monitor import run_monitoring_pipeline


def run_full_etl() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes Stage 1 (raw ingestion) and Stage 2 (price monitoring & violation auditing)."""
    run_ingestion_pipeline()
    return run_monitoring_pipeline()


if __name__ == "__main__":
    run_full_etl()
