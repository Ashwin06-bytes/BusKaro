"""
tatkal/ml/predict.py
====================
Public inference interface for the Tatkal demand prediction module.

Public API
----------
predict_dynamic_surcharge(
    minutes_to_departure,
    day_of_week,
    is_weekend,
    is_festival,
    route_popularity_tier,
    seats_remaining_ratio,
    historical_fill_rate,
    min_pct=10.0,
    max_pct=40.0,
) -> tuple[float, float | None]

Design decisions
----------------
* The model artifact (demand_model.joblib) is loaded **once** at the first
  call and cached in the module-level ``_MODEL`` variable.  Subsequent calls
  incur zero I/O overhead.

* Every exception is caught at the top of ``predict_dynamic_surcharge``.
  The function **never** raises.  On any failure it logs a warning and returns
  the safe default of (25.0, None) so the existing pricing flow is unaffected.

* The surcharge formula is:
      surcharge_pct = 10.0 + 3.0 × demand_score
  Clamped between min_pct (default 10%) and max_pct (default 40%).

* This module has **no Django imports** – it can be imported and tested
  without a running Django project.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR: Path = Path(__file__).resolve().parent
MODEL_PATH: Path = ML_DIR / "demand_model.joblib"

# ---------------------------------------------------------------------------
# Module-level model cache
# A threading.Lock ensures the model is loaded only once even under concurrent
# Django requests (e.g. from the aggregator ThreadPoolExecutor).
# ---------------------------------------------------------------------------
_MODEL: Optional[object] = None
_MODEL_LOCK: threading.Lock = threading.Lock()
_MODEL_LOAD_FAILED: bool = False  # latched True after a permanent load failure

# Exact feature order used during training — must not be reordered.
_FEATURE_ORDER: list[str] = [
    "minutes_to_departure",
    "day_of_week",
    "is_weekend",
    "is_festival",
    "route_popularity_tier",
    "seats_remaining_ratio",
    "historical_fill_rate",
]


def _load_model() -> Optional[object]:
    """
    Load (and cache) the persisted model from MODEL_PATH.

    Thread-safe via ``_MODEL_LOCK``.  After a permanent failure the flag
    ``_MODEL_LOAD_FAILED`` is latched so subsequent calls skip the I/O
    attempt entirely.

    Returns
    -------
    Loaded model object, or None on failure.
    """
    global _MODEL, _MODEL_LOAD_FAILED  # noqa: PLW0603

    # Fast path — already loaded
    if _MODEL is not None:
        return _MODEL

    # Permanent failure — skip retry
    if _MODEL_LOAD_FAILED:
        return None

    with _MODEL_LOCK:
        # Double-checked locking
        if _MODEL is not None:
            return _MODEL
        if _MODEL_LOAD_FAILED:
            return None

        if not MODEL_PATH.exists():
            logger.warning(
                "Tatkal demand model not found at %s. "
                "Run 'python manage.py train_tatkal_demand_model' to generate it. "
                "Falling back to default surcharge (25%%).",
                MODEL_PATH,
            )
            _MODEL_LOAD_FAILED = True
            return None

        try:
            import joblib  # deferred import – only needed at load time

            model = joblib.load(MODEL_PATH)
            _MODEL = model
            logger.info("Tatkal demand model loaded from %s", MODEL_PATH)
            return _MODEL
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to load Tatkal demand model from %s: %s. "
                "Falling back to default surcharge (25%%).",
                MODEL_PATH,
                exc,
            )
            _MODEL_LOAD_FAILED = True
            return None


def predict_dynamic_surcharge(
    minutes_to_departure: float,
    day_of_week: int,
    is_weekend: int,
    is_festival: int,
    route_popularity_tier: int,
    seats_remaining_ratio: float,
    historical_fill_rate: float,
    min_pct: float = 10.0,
    max_pct: float = 40.0,
) -> Tuple[float, Optional[float]]:
    """
    Predict the dynamic Tatkal surcharge percentage using the trained ML model.

    Parameters
    ----------
    minutes_to_departure  : Minutes remaining until bus departure.
                            Accepted range: [0, 480].
    day_of_week           : ISO weekday (0 = Monday … 6 = Sunday).
    is_weekend            : 1 if Saturday or Sunday, else 0.
    is_festival           : 1 if travel date is a festival window, else 0.
    route_popularity_tier : Route tier (1 = low, 2 = medium, 3 = high demand).
    seats_remaining_ratio : Fraction of seats still available [0.0, 1.0].
    historical_fill_rate  : Long-run average occupancy for this route [0.0, 1.0].
    min_pct               : Minimum surcharge percentage (floor). Default 10.0.
    max_pct               : Maximum surcharge percentage (ceiling). Default 40.0.

    Returns
    -------
    (surcharge_percentage, demand_score)
        surcharge_percentage : float – clamped surcharge in [min_pct, max_pct].
        demand_score         : float or None – raw model prediction [0, 10],
                               or None if the model is unavailable.

    Notes
    -----
    * This function **never raises**.  On any exception it returns (25.0, None).
    * The model is loaded lazily and cached for the lifetime of the process.
    * Surcharge formula:  surcharge_pct = 10.0 + 3.0 × demand_score
    """
    try:
        model = _load_model()

        if model is None:
            # Model unavailable – return safe default identical to existing
            # hardcoded behaviour so no pricing disruption occurs.
            return 25.0, None

        # ---- Build feature DataFrame (must match training column order and names)
        import pandas as pd
        feature_df = pd.DataFrame(
            [{
                "minutes_to_departure": float(minutes_to_departure),
                "day_of_week": int(day_of_week),
                "is_weekend": int(is_weekend),
                "is_festival": int(is_festival),
                "route_popularity_tier": int(route_popularity_tier),
                "seats_remaining_ratio": float(seats_remaining_ratio),
                "historical_fill_rate": float(historical_fill_rate),
            }],
            columns=_FEATURE_ORDER
        )

        # ---- Predict -------------------------------------------------------
        raw_score: float = float(model.predict(feature_df)[0])

        # Clamp raw score to the training range [0, 10] before applying formula
        demand_score: float = max(0.0, min(10.0, raw_score))

        # ---- Surcharge formula ---------------------------------------------
        # surcharge_pct = 10 + 3 × demand_score
        # Range: 10% (score=0) … 40% (score=10)
        surcharge_pct: float = 10.0 + 3.0 * demand_score
        surcharge_pct = max(min_pct, min(max_pct, surcharge_pct))

        logger.debug(
            "Tatkal ML → demand_score=%.3f  surcharge_pct=%.2f%%",
            demand_score,
            surcharge_pct,
        )

        return round(surcharge_pct, 2), round(demand_score, 4)

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "predict_dynamic_surcharge() raised an unexpected error: %s. "
            "Returning default surcharge (25%%).",
            exc,
        )
        return 25.0, None


# ---------------------------------------------------------------------------
# Convenience reset for unit testing (allows re-loading between tests)
# ---------------------------------------------------------------------------
def _reset_model_cache() -> None:
    """Reset the module-level model cache. Intended for use in tests only."""
    global _MODEL, _MODEL_LOAD_FAILED  # noqa: PLW0603
    _MODEL = None
    _MODEL_LOAD_FAILED = False
