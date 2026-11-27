"""
Integration Tests for Reproducible ETL Pipeline (src/etl/pipeline.py)
"""

from pathlib import Path
from src.etl.pipeline import run_ingestion_pipeline, run_monitoring_pipeline, DATA_INPUTS_DIR


def test_etl_pipeline_e2e(tmp_path):
    db_dir = tmp_path / "database_tables"
    inter_dir = tmp_path / "intermediate"

    db_exports = run_ingestion_pipeline(
        inputs_dir=DATA_INPUTS_DIR,
        db_tables_dir=db_dir,
        intermediate_dir=inter_dir,
    )
    assert "sku_table.csv" in db_exports
    assert len(db_exports["seller_table.csv"]) == 147900
    assert (inter_dir / "promotional_skus.csv").exists()

    pm_df, v_df = run_monitoring_pipeline(db_tables_dir=db_dir, intermediate_dir=inter_dir)
    assert len(pm_df) == 147900
    assert len(v_df) > 0
    assert (db_dir / "price_monitoring_table.csv").exists()
    assert (db_dir / "violation_table.csv").exists()
