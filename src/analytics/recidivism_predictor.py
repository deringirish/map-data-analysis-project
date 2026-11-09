"""
Predictive Reseller Recidivism Risk Engine (Machine Learning Layer)
Author: Derin Girish D G
Description: Machine learning models (Random Forest classifier and regularized Logistic
Regression baseline) for predicting reseller recidivism risk, non-compliance velocity,
and chronic margin erosion across retail partner cohorts.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score

# Ensure console supports utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
REPORTS_DIR = BASE_DIR / "data_processed" / "reports"


class RecidivismPredictor:
    """
    Supervised predictive risk engine for retail reseller recidivism.
    Utilizes temporal-split cross-validation to predict chronic price erosion
    and persistent non-compliance from early-window behavioral telemetry.
    """

    FEATURE_COLS = [
        "violations",
        "active_days",
        "distinct_skus",
        "marketplaces",
        "avg_deficit",
        "max_deficit",
        "avg_discount_pct",
        "max_discount_pct",
        "velocity",
        "major_rate",
    ]

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.rf_model: Optional[RandomForestClassifier] = None
        self.lr_pipeline: Optional[Pipeline] = None
        self.model_metrics: Dict[str, Any] = {}
        self.feature_importances: Dict[str, float] = {}

    def extract_temporal_features(
        self,
        violation_df: pd.DataFrame,
        split_date: str = "2025-12-28"
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Partitions surveillance window into T1 (early observation) and T2 (outcome).
        Extracts behavioral features from T1 and defines chronic recidivism targets in T2.
        """
        df = violation_df.copy()
        df["Violation_date"] = pd.to_datetime(df["Violation_date"])
        if "discount_pct" not in df.columns:
            df["discount_pct"] = (df["Price_Difference"] / df["LPP"]) * 100.0

        ts_split = pd.Timestamp(split_date)
        t1_df = df[df["Violation_date"] <= ts_split]
        t2_df = df[df["Violation_date"] > ts_split]

        # Aggregate T1 behavioral features
        t1_cohorts = t1_df.groupby(["homologated_name", "Category"]).agg(
            violations=("SKU", "count"),
            active_days=("Violation_date", "nunique"),
            distinct_skus=("SKU", "nunique"),
            marketplaces=("Marketplace", "nunique"),
            avg_deficit=("Price_Difference", "mean"),
            max_deficit=("Price_Difference", "max"),
            avg_discount_pct=("discount_pct", "mean"),
            max_discount_pct=("discount_pct", "max"),
            major_count=("Price_Difference", lambda x: (x > 5000).sum())
        ).reset_index()

        t1_cohorts["velocity"] = t1_cohorts["violations"] / t1_cohorts["active_days"]
        t1_cohorts["major_rate"] = t1_cohorts["major_count"] / t1_cohorts["violations"]

        # Aggregate T2 outcome telemetry
        t2_cohorts = t2_df.groupby(["homologated_name", "Category"]).agg(
            t2_violations=("SKU", "count"),
            t2_days=("Violation_date", "nunique"),
            t2_total_deficit=("Price_Difference", "sum")
        ).reset_index()

        train_df = pd.merge(t1_cohorts, t2_cohorts, on=["homologated_name", "Category"], how="outer").fillna(0)

        # Target: Chronic recidivist active on >= 7 of 8 T2 days and causing >= 70th percentile margin deficit
        deficit_cutoff = train_df["t2_total_deficit"].quantile(0.70)
        train_df["target"] = (
            (train_df["t2_days"] >= 7) & (train_df["t2_total_deficit"] >= deficit_cutoff)
        ).astype(int)

        X = train_df[self.FEATURE_COLS].copy()
        y = train_df["target"].copy()

        return X, y

    def extract_full_window_features(self, violation_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts aggregated behavioral telemetry across the entire surveillance window
        for active operational scoring and risk tiering.
        """
        df = violation_df.copy()
        df["Violation_date"] = pd.to_datetime(df["Violation_date"])
        if "discount_pct" not in df.columns:
            df["discount_pct"] = (df["Price_Difference"] / df["LPP"]) * 100.0

        cohorts = df.groupby(["homologated_name", "Category"]).agg(
            violations=("SKU", "count"),
            active_days=("Violation_date", "nunique"),
            distinct_skus=("SKU", "nunique"),
            marketplaces=("Marketplace", "nunique"),
            avg_deficit=("Price_Difference", "mean"),
            max_deficit=("Price_Difference", "max"),
            total_deficit=("Price_Difference", "sum"),
            avg_discount_pct=("discount_pct", "mean"),
            max_discount_pct=("discount_pct", "max"),
            major_count=("Price_Difference", lambda x: (x > 5000).sum())
        ).reset_index()

        cohorts["velocity"] = cohorts["violations"] / cohorts["active_days"]
        cohorts["major_rate"] = cohorts["major_count"] / cohorts["violations"]

        return cohorts

    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Trains champion Random Forest classifier and baseline regularized Logistic Regression.
        Computes 5-fold cross-validation metrics and feature importances.
        """
        # Champion Model: Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=4,
            min_samples_leaf=3,
            random_state=self.random_state
        )

        # Baseline Model: Scaled Logistic Regression
        lr = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=self.random_state, max_iter=1000))
        ])

        scoring = ["roc_auc", "accuracy", "precision", "recall", "f1"]
        cv_rf = cross_validate(rf, X, y, cv=5, scoring=scoring)
        cv_lr = cross_validate(lr, X, y, cv=5, scoring=scoring)

        rf.fit(X, y)
        lr.fit(X, y)

        self.rf_model = rf
        self.lr_pipeline = lr

        # Extract feature importances
        importances = pd.Series(rf.feature_importances_, index=self.FEATURE_COLS).sort_values(ascending=False)
        self.feature_importances = importances.to_dict()

        self.model_metrics = {
            "random_forest": {
                "roc_auc": float(cv_rf["test_roc_auc"].mean()),
                "roc_auc_std": float(cv_rf["test_roc_auc"].std()),
                "accuracy": float(cv_rf["test_accuracy"].mean()),
                "accuracy_std": float(cv_rf["test_accuracy"].std()),
                "precision": float(cv_rf["test_precision"].mean()),
                "precision_std": float(cv_rf["test_precision"].std()),
                "recall": float(cv_rf["test_recall"].mean()),
                "recall_std": float(cv_rf["test_recall"].std()),
                "f1": float(cv_rf["test_f1"].mean()),
                "f1_std": float(cv_rf["test_f1"].std()),
            },
            "logistic_regression": {
                "roc_auc": float(cv_lr["test_roc_auc"].mean()),
                "roc_auc_std": float(cv_lr["test_roc_auc"].std()),
                "accuracy": float(cv_lr["test_accuracy"].mean()),
                "accuracy_std": float(cv_lr["test_accuracy"].std()),
                "precision": float(cv_lr["test_precision"].mean()),
                "precision_std": float(cv_lr["test_precision"].std()),
                "recall": float(cv_lr["test_recall"].mean()),
                "recall_std": float(cv_lr["test_recall"].std()),
                "f1": float(cv_lr["test_f1"].mean()),
                "f1_std": float(cv_lr["test_f1"].std()),
            },
            "feature_importances": self.feature_importances
        }

        return self.model_metrics

    def predict_cohort_risk(self, cohorts_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates calibrated Recidivism Risk Score (0.0 - 1.0), assigns risk tiers,
        and determines operational legal remedy recommendations.
        """
        if self.rf_model is None:
            raise RuntimeError("Model must be trained prior to calling predict_cohort_risk.")

        scoring_feats = cohorts_df[self.FEATURE_COLS].copy()
        # Scale 15-day cumulative count features to 8-day reference window for rate consistency
        scoring_feats["violations"] = scoring_feats["violations"] * (8.0 / 15.0)
        scoring_feats["active_days"] = np.minimum(8.0, scoring_feats["active_days"] * (8.0 / 15.0))

        risk_scores = self.rf_model.predict_proba(scoring_feats)[:, 1]

        scored_df = cohorts_df.copy()
        scored_df["Recidivism_Risk_Score"] = np.round(risk_scores, 4)
        scored_df["Risk_Score_Pct"] = np.round(risk_scores * 100.0, 1)

        # Assign Risk Tiers
        def map_tier(score: float) -> str:
            if score >= 0.70:
                return "🔴 High Risk"
            elif score >= 0.30:
                return "🟡 Moderate Risk"
            else:
                return "🟢 Low Risk"

        def map_action(score: float) -> str:
            if score >= 0.70:
                return "Immediate 30-Day Critical Freeze & Senior Legal Notice"
            elif score >= 0.30:
                return "Formal Warning Notice & Daily Telemetry Tracking"
            else:
                return "Standard Automated Warning & Monitoring"

        scored_df["Risk_Tier"] = scored_df["Recidivism_Risk_Score"].apply(map_tier)
        scored_df["Recommended_Action"] = scored_df["Recidivism_Risk_Score"].apply(map_action)

        # Reorder and format key columns
        display_cols = [
            "homologated_name",
            "Category",
            "Recidivism_Risk_Score",
            "Risk_Score_Pct",
            "Risk_Tier",
            "Total_Price_Deficit",
            "Avg_Price_Deficit",
            "Max_Price_Deficit",
            "Total_Violations",
            "Active_Violation_Days",
            "Violation_Velocity",
            "Marketplaces_Audited",
            "Recommended_Action"
        ]

        scored_df = scored_df.rename(columns={
            "total_deficit": "Total_Price_Deficit",
            "avg_deficit": "Avg_Price_Deficit",
            "max_deficit": "Max_Price_Deficit",
            "violations": "Total_Violations",
            "active_days": "Active_Violation_Days",
            "velocity": "Violation_Velocity",
            "marketplaces": "Marketplaces_Audited"
        })

        return scored_df[display_cols].sort_values("Recidivism_Risk_Score", ascending=False)

    def aggregate_corporate_risk(self, scored_cohorts: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates cohort-level risk predictions up to corporate parent entities (100 resellers).
        """
        def determine_corporate_tier(scores: pd.Series) -> str:
            max_s = scores.max()
            if max_s >= 0.70:
                return "🔴 High Risk"
            elif max_s >= 0.30:
                return "🟡 Moderate Risk"
            else:
                return "🟢 Low Risk"

        def determine_corporate_action(tier: str) -> str:
            if "High" in tier:
                return "Critical Account Review & Cross-Category Supply Freeze"
            elif "Moderate" in tier:
                return "Targeted Category Probation & Senior Account Audit"
            else:
                return "Routine Compliance Auditing"

        corp_df = scored_cohorts.groupby("homologated_name").agg(
            Max_Risk_Score=("Recidivism_Risk_Score", "max"),
            Mean_Risk_Score=("Recidivism_Risk_Score", "mean"),
            Total_Corporate_Deficit=("Total_Price_Deficit", "sum"),
            Total_Corporate_Violations=("Total_Violations", "sum"),
            Categories_Audited=("Category", lambda x: ", ".join(sorted(x.unique()))),
            Primary_Risk_Category=("Category", lambda x: scored_cohorts.loc[x.index].sort_values("Recidivism_Risk_Score", ascending=False).iloc[0]["Category"])
        ).reset_index()

        corp_df["Max_Risk_Score"] = np.round(corp_df["Max_Risk_Score"], 4)
        corp_df["Mean_Risk_Score"] = np.round(corp_df["Mean_Risk_Score"], 4)
        corp_df["Overall_Corporate_Tier"] = corp_df["Max_Risk_Score"].apply(
            lambda s: "🔴 High Risk" if s >= 0.70 else ("🟡 Moderate Risk" if s >= 0.30 else "🟢 Low Risk")
        )
        corp_df["Corporate_Legal_Remedy"] = corp_df["Overall_Corporate_Tier"].apply(determine_corporate_action)

        return corp_df.sort_values(["Max_Risk_Score", "Total_Corporate_Deficit"], ascending=[False, False])

    def save_predictions(
        self,
        cohort_df: pd.DataFrame,
        corporate_df: pd.DataFrame,
        output_dir: Path = REPORTS_DIR,
        db_path: Optional[Path] = DATA_PATH / "map_project.db"
    ) -> None:
        """
        Exports scored cohort and corporate DataFrames to CSV and optionally SQLite.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        cohort_csv = output_dir / "recidivism_risk_cohorts.csv"
        corporate_csv = output_dir / "recidivism_risk_corporate.csv"

        cohort_df.to_csv(cohort_csv, index=False)
        corporate_df.to_csv(corporate_csv, index=False)
        print(f"[SUCCESS] Scored cohort risk saved to: {cohort_csv}")
        print(f"[SUCCESS] Corporate risk rollup saved to: {corporate_csv}")

        # Sync to SQLite if available
        if db_path and db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                cohort_df.to_sql("RECIDIVISM_RISK_COHORTS", con=conn, if_exists="replace", index=False)
                corporate_df.to_sql("RECIDIVISM_RISK_CORPORATE", con=conn, if_exists="replace", index=False)
                conn.close()
                print(f"[SUCCESS] Synced risk prediction tables to SQLite: {db_path.name}")
            except Exception as e:
                print(f"[WARNING] Could not sync to SQLite: {e}")


def run_recidivism_pipeline(
    violation_csv: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Tuple[RecidivismPredictor, pd.DataFrame, pd.DataFrame]:
    """
    Master pipeline runner for reseller recidivism risk prediction.
    """
    v_path = violation_csv or (DATA_PATH / "violation_table.csv")
    out_dir = output_dir or REPORTS_DIR

    print("\n" + "=" * 65)
    print(" [MACHINE LEARNING] RESELLER RECIDIVISM PREDICTIVE RISK ENGINE")
    print("=" * 65)
    print(f"[INFO] Ingesting surveillance violation telemetry: {v_path}")
    v_df = pd.read_csv(v_path)

    predictor = RecidivismPredictor()
    print("[INFO] Extracting temporal features (T1: Dec 21-28 -> T2: Dec 29-Jan 05)...")
    X, y = predictor.extract_temporal_features(v_df)

    print("[INFO] Training Champion (Random Forest) & Baseline (Logistic Regression)...")
    metrics = predictor.train(X, y)

    rf_m = metrics["random_forest"]
    lr_m = metrics["logistic_regression"]
    print(f"  • Random Forest (Champion)   -> ROC-AUC: {rf_m['roc_auc']:.4f} | Acc: {rf_m['accuracy']*100:.1f}% | F1: {rf_m['f1']:.4f}")
    print(f"  • Logistic Regression (Base) -> ROC-AUC: {lr_m['roc_auc']:.4f} | Acc: {lr_m['accuracy']*100:.1f}% | F1: {lr_m['f1']:.4f}")

    print("\n[INFO] Feature Importance Hierarchy (Drivers of Chronic Recidivism):")
    for feat, imp in list(predictor.feature_importances.items())[:6]:
        print(f"    - {feat:<22}: {imp*100:5.2f}%")

    print("\n[INFO] Scoring full 15-day surveillance cohort risk profile (279 cohorts)...")
    full_cohorts = predictor.extract_full_window_features(v_df)
    scored_cohorts = predictor.predict_cohort_risk(full_cohorts)
    corporate_risk = predictor.aggregate_corporate_risk(scored_cohorts)

    tier_dist = scored_cohorts["Risk_Tier"].value_counts().to_dict()
    print("\n[INFO] Reseller Risk Stratification Profile:")
    for tier, count in tier_dist.items():
        pct = (count / len(scored_cohorts)) * 100.0
        print(f"    {tier:<20}: {count:>3} cohorts ({pct:5.1f}%)")

    predictor.save_predictions(scored_cohorts, corporate_risk, output_dir=out_dir)
    return predictor, scored_cohorts, corporate_risk


if __name__ == "__main__":
    run_recidivism_pipeline()
