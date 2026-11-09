"""
Unit and Integration Tests for Predictive Reseller Recidivism Risk Engine
Author: Derin Girish D G
Description: Verifies feature engineering, model training, cross-validation metrics,
probability calibration, risk tier stratifications, and corporate aggregation.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.analytics.recidivism_predictor import RecidivismPredictor, run_recidivism_pipeline

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
VIOLATION_CSV = DATA_PATH / "violation_table.csv"


@pytest.fixture(scope="module")
def violation_data():
    """Loads violation dataset for testing."""
    assert VIOLATION_CSV.exists(), f"Violation table missing at {VIOLATION_CSV}"
    df = pd.read_csv(VIOLATION_CSV)
    return df


def test_extract_temporal_features(violation_data):
    """Verifies temporal train feature extraction generates valid X and y."""
    predictor = RecidivismPredictor(random_state=42)
    X, y = predictor.extract_temporal_features(violation_data, split_date="2025-12-28")

    assert not X.empty, "Feature matrix X should not be empty."
    assert len(X) == len(y), "X and y lengths must match."
    assert set(predictor.FEATURE_COLS).issubset(X.columns), "All required feature columns must be present in X."
    assert not X.isna().any().any(), "X should have zero missing values."
    assert set(y.unique()).issubset({0, 1}), "Target y must be binary {0, 1}."
    assert y.sum() > 0, "There should be at least one positive recidivism target."


def test_extract_full_window_features(violation_data):
    """Verifies full-window feature extraction covers all reseller cohorts."""
    predictor = RecidivismPredictor(random_state=42)
    full_cohorts = predictor.extract_full_window_features(violation_data)

    assert not full_cohorts.empty, "Full cohorts dataframe must not be empty."
    assert len(full_cohorts) == 279, f"Expected 279 cohorts, found {len(full_cohorts)}."
    assert "homologated_name" in full_cohorts.columns
    assert "Category" in full_cohorts.columns
    assert "total_deficit" in full_cohorts.columns
    assert (full_cohorts["violations"] > 0).all(), "All cohorts must have at least one violation."


def test_model_training_and_metrics(violation_data):
    """Verifies that model training yields robust cross-validation metrics and feature importances."""
    predictor = RecidivismPredictor(random_state=42)
    X, y = predictor.extract_temporal_features(violation_data)
    metrics = predictor.train(X, y)

    assert "random_forest" in metrics
    assert "logistic_regression" in metrics
    assert "feature_importances" in metrics

    rf_metrics = metrics["random_forest"]
    assert rf_metrics["roc_auc"] >= 0.85, f"Expected ROC-AUC >= 0.85, got {rf_metrics['roc_auc']}"
    assert rf_metrics["accuracy"] >= 0.80, f"Expected Accuracy >= 0.80, got {rf_metrics['accuracy']}"

    importances = metrics["feature_importances"]
    assert len(importances) == len(predictor.FEATURE_COLS)
    assert np.isclose(sum(importances.values()), 1.0, atol=1e-3), "Feature importances must sum to ~1.0."


def test_predict_cohort_risk_bounds_and_tiers(violation_data):
    """Verifies risk score calibration in [0, 1] and accurate risk tier classifications."""
    predictor = RecidivismPredictor(random_state=42)
    X, y = predictor.extract_temporal_features(violation_data)
    predictor.train(X, y)

    full_cohorts = predictor.extract_full_window_features(violation_data)
    scored = predictor.predict_cohort_risk(full_cohorts)

    assert len(scored) == 279
    assert (scored["Recidivism_Risk_Score"] >= 0.0).all(), "Risk scores cannot be negative."
    assert (scored["Recidivism_Risk_Score"] <= 1.0).all(), "Risk scores cannot exceed 1.0."
    assert set(scored["Risk_Tier"].unique()).issubset({"🔴 High Risk", "🟡 Moderate Risk", "🟢 Low Risk"})

    # Check high-risk cohorts have score >= 0.70
    high_risk = scored[scored["Risk_Tier"] == "🔴 High Risk"]
    assert (high_risk["Recidivism_Risk_Score"] >= 0.70).all()

    # Check low-risk cohorts have score < 0.30
    low_risk = scored[scored["Risk_Tier"] == "🟢 Low Risk"]
    assert (low_risk["Recidivism_Risk_Score"] < 0.30).all()


def test_corporate_risk_aggregation(violation_data):
    """Verifies aggregation to 100 corporate parent entities."""
    predictor = RecidivismPredictor(random_state=42)
    X, y = predictor.extract_temporal_features(violation_data)
    predictor.train(X, y)

    full_cohorts = predictor.extract_full_window_features(violation_data)
    scored = predictor.predict_cohort_risk(full_cohorts)
    corp = predictor.aggregate_corporate_risk(scored)

    assert len(corp) == 100, f"Expected 100 corporate resellers, got {len(corp)}."
    assert (corp["Max_Risk_Score"] >= corp["Mean_Risk_Score"]).all(), "Max risk score must be >= Mean risk score."
    assert set(corp["Overall_Corporate_Tier"].unique()).issubset({"🔴 High Risk", "🟡 Moderate Risk", "🟢 Low Risk"})
    assert corp["Total_Corporate_Deficit"].sum() > 0


def test_run_recidivism_pipeline_e2e(tmp_path):
    """Verifies full end-to-end pipeline execution and file generation."""
    pred, cohorts_df, corp_df = run_recidivism_pipeline(output_dir=tmp_path)

    assert (tmp_path / "recidivism_risk_cohorts.csv").exists()
    assert (tmp_path / "recidivism_risk_corporate.csv").exists()
    assert len(cohorts_df) == 279
    assert len(corp_df) == 100
