"""
tatkal/ml/train_model.py
========================
Trains and evaluates two regression models on the synthetic Tatkal demand
dataset.  Selects and persists the better-performing model automatically.

Models evaluated
----------------
1. LinearRegression  – interpretable baseline
2. RandomForestRegressor – non-linear ensemble (typically wins)

Selection criterion: lowest RMSE on the held-out test set.

Usage (standalone, no Django required)
---------------------------------------
    python tatkal/ml/train_model.py

Output
------
    tatkal/ml/demand_model.joblib   – persisted best model
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from tatkal.ml.generate_data import (
    DATA_PATH,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    ML_DIR,
    generate_dataset,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_PATH: Path = ML_DIR / "demand_model.joblib"

# ---------------------------------------------------------------------------
# Hyper-parameters
# ---------------------------------------------------------------------------
TEST_SIZE: float = 0.20
RANDOM_SEED: int = 42
RF_N_ESTIMATORS: int = 100
RF_MAX_DEPTH: int = 12


def _evaluate(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """
    Compute MAE, RMSE and R² and log the results.

    Returns
    -------
    dict with keys 'mae', 'rmse', 'r2'.
    """
    mae: float = float(mean_absolute_error(y_true, y_pred))
    rmse: float = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2: float = float(r2_score(y_true, y_pred))

    logger.info(
        "[%s]  MAE=%.4f  RMSE=%.4f  R2=%.4f",
        model_name,
        mae,
        rmse,
        r2,
    )
    # Also print so the management command output is visible to operators
    sep = "-" * 40
    print(f"\n{sep}")
    print(f"  Model : {model_name}")
    print(f"  MAE   : {mae:.4f}")
    print(f"  RMSE  : {rmse:.4f}")
    print(f"  R2    : {r2:.4f}")
    print(sep)

    return {"mae": mae, "rmse": rmse, "r2": r2}


def load_or_generate_data(data_path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Load data.csv if it already exists, otherwise generate it first.

    Parameters
    ----------
    data_path : Path
        Expected location of the CSV file.

    Returns
    -------
    pd.DataFrame
    """
    if data_path.exists():
        logger.info("Loading existing dataset from %s", data_path)
        df = pd.read_csv(data_path)
    else:
        logger.info("data.csv not found – generating synthetic dataset …")
        df = generate_dataset(save_path=data_path)
    return df


def train(
    data_path: Path = DATA_PATH,
    model_path: Path = MODEL_PATH,
) -> Tuple[object, str, dict[str, float]]:
    """
    Full training pipeline.

    1. Load (or generate) dataset.
    2. Split into train / test.
    3. Fit LinearRegression and RandomForestRegressor.
    4. Evaluate both with MAE / RMSE / R².
    5. Pick the model with lowest RMSE.
    6. Persist the winner to *model_path*.

    Parameters
    ----------
    data_path  : Path to the CSV dataset.
    model_path : Destination for the persisted model artifact.

    Returns
    -------
    (best_model, best_model_name, metrics_dict)
    """
    # ---- Load data --------------------------------------------------------
    df: pd.DataFrame = load_or_generate_data(data_path)

    X: pd.DataFrame = df[FEATURE_COLUMNS]
    y: pd.Series = df[TARGET_COLUMN]

    logger.info(
        "Dataset loaded: %d rows | features: %s", len(df), FEATURE_COLUMNS
    )

    # ---- Train / test split -----------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED
    )
    logger.info(
        "Split → train=%d  test=%d", len(X_train), len(X_test)
    )

    # ---- Candidates -------------------------------------------------------
    candidates: dict[str, object] = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=RF_N_ESTIMATORS,
            max_depth=RF_MAX_DEPTH,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
    }

    results: dict[str, dict[str, float]] = {}

    for name, model in candidates.items():
        logger.info("Training %s …", name)
        model.fit(X_train, y_train)
        y_pred: np.ndarray = model.predict(X_test)
        metrics = _evaluate(name, y_test.to_numpy(), y_pred)
        results[name] = {"model": model, "metrics": metrics}

    # ---- Model selection (lowest RMSE) ------------------------------------
    best_name: str = min(
        results.keys(),
        key=lambda n: results[n]["metrics"]["rmse"],
    )
    best_model = results[best_name]["model"]
    best_metrics: dict[str, float] = results[best_name]["metrics"]

    print(f"\n[OK] Selected model: {best_name}")
    print(f"   MAE  = {best_metrics['mae']:.4f}")
    print(f"   RMSE = {best_metrics['rmse']:.4f}")
    print(f"   R2   = {best_metrics['r2']:.4f}\n")

    logger.info("Best model: %s (RMSE=%.4f)", best_name, best_metrics["rmse"])

    # ---- Persist ----------------------------------------------------------
    os.makedirs(model_path.parent, exist_ok=True)
    joblib.dump(best_model, model_path)
    logger.info("Model saved → %s", model_path)
    print(f"Model artifact saved -> {model_path}\n")

    return best_model, best_name, best_metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    train()
