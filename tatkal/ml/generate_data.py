"""
tatkal/ml/generate_data.py
==========================
Generates a reproducible synthetic dataset for Tatkal demand prediction.

Feature Definitions
-------------------
minutes_to_departure   : int   [0, 480]
    Minutes remaining until bus departure at the time of the search.
    Lower values → higher urgency → higher expected demand.

day_of_week            : int   [0, 6]
    ISO weekday of the travel date (0 = Monday, 6 = Sunday).

is_weekend             : int   {0, 1}
    1 if day_of_week ∈ {5, 6} (Saturday or Sunday), else 0.

is_festival            : int   {0, 1}
    1 if the travel date falls on a known festival window.
    Simulated as ~12% of all samples (mirrors rough festival frequency).

route_popularity_tier  : int   {1, 2, 3}
    1 = Low-demand route (rural/off-peak corridor)
    2 = Medium-demand route (inter-city)
    3 = High-demand route (major city pairs, e.g. Chennai–Coimbatore)

seats_remaining_ratio  : float [0.0, 1.0]
    Fraction of seats still available: available_seats / total_seats.
    Lower → bus is filling up → higher demand.

historical_fill_rate   : float [0.0, 1.0]
    Average occupancy for this route/time-slot over the past 30 days.
    Higher → route is consistently popular.

Target
------
demand_score           : float [0.0, 10.0]
    Composite demand index.  Derived from the features with added noise
    so that a regression model can learn a non-trivial mapping.
    Formula (before clamping):
        score = 2.0
              + 3.0 × (1 - minutes_to_departure / 480)   # urgency
              + 1.5 × is_weekend
              + 2.0 × is_festival
              + (route_popularity_tier - 1) × 0.8        # tier bonus
              + 2.5 × historical_fill_rate
              + 1.5 × (1 - seats_remaining_ratio)         # scarcity
              + N(0, 0.6)                                  # noise
    Clamped to [0.0, 10.0].
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR: Path = Path(__file__).resolve().parent
DATA_PATH: Path = ML_DIR / "data.csv"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RANDOM_SEED: int = 42
N_SAMPLES: int = 10_000

FEATURE_COLUMNS: list[str] = [
    "minutes_to_departure",
    "day_of_week",
    "is_weekend",
    "is_festival",
    "route_popularity_tier",
    "seats_remaining_ratio",
    "historical_fill_rate",
]
TARGET_COLUMN: str = "demand_score"


def generate_dataset(
    n_samples: int = N_SAMPLES,
    random_seed: int = RANDOM_SEED,
    save_path: Path | None = DATA_PATH,
) -> pd.DataFrame:
    """
    Generate a reproducible synthetic Tatkal demand dataset.

    Parameters
    ----------
    n_samples : int
        Number of rows to generate.
    random_seed : int
        NumPy random seed for full reproducibility.
    save_path : Path or None
        If provided, the DataFrame is written to this CSV path.

    Returns
    -------
    pd.DataFrame
        DataFrame with FEATURE_COLUMNS + TARGET_COLUMN columns.
    """
    rng = np.random.default_rng(random_seed)

    # ---- Features ---------------------------------------------------------

    # Minutes to departure: skewed toward last-minute bookings
    minutes_to_departure: np.ndarray = rng.integers(0, 481, size=n_samples)

    # Day of week: uniformly distributed across 0–6
    day_of_week: np.ndarray = rng.integers(0, 7, size=n_samples)

    # Weekend flag derived from day_of_week
    is_weekend: np.ndarray = (day_of_week >= 5).astype(np.int8)

    # Festival flag: ~12% of trips fall on festival windows
    is_festival: np.ndarray = rng.choice(
        [0, 1], size=n_samples, p=[0.88, 0.12]
    ).astype(np.int8)

    # Route popularity tier: weighted toward mid-tier routes
    route_popularity_tier: np.ndarray = rng.choice(
        [1, 2, 3], size=n_samples, p=[0.30, 0.45, 0.25]
    )

    # Seats remaining ratio: beta-distributed (realistic fill patterns)
    seats_remaining_ratio: np.ndarray = rng.beta(a=2.0, b=1.5, size=n_samples)
    seats_remaining_ratio = np.clip(seats_remaining_ratio, 0.0, 1.0)

    # Historical fill rate: beta-distributed (route-level long-run average)
    historical_fill_rate: np.ndarray = rng.beta(a=3.0, b=2.0, size=n_samples)
    historical_fill_rate = np.clip(historical_fill_rate, 0.0, 1.0)

    # ---- Target -----------------------------------------------------------
    urgency_score: np.ndarray = 1.0 - (minutes_to_departure / 480.0)
    tier_bonus: np.ndarray = (route_popularity_tier - 1) * 0.8
    scarcity_score: np.ndarray = 1.0 - seats_remaining_ratio
    noise: np.ndarray = rng.normal(loc=0.0, scale=0.6, size=n_samples)

    raw_demand: np.ndarray = (
        2.0
        + 3.0 * urgency_score
        + 1.5 * is_weekend
        + 2.0 * is_festival
        + tier_bonus
        + 2.5 * historical_fill_rate
        + 1.5 * scarcity_score
        + noise
    )
    demand_score: np.ndarray = np.clip(raw_demand, 0.0, 10.0)

    # ---- Assemble DataFrame -----------------------------------------------
    df = pd.DataFrame(
        {
            "minutes_to_departure": minutes_to_departure,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_festival": is_festival,
            "route_popularity_tier": route_popularity_tier,
            "seats_remaining_ratio": seats_remaining_ratio.round(4),
            "historical_fill_rate": historical_fill_rate.round(4),
            "demand_score": demand_score.round(4),
        }
    )

    logger.info(
        "Generated synthetic dataset: %d rows, %d features.",
        len(df),
        len(FEATURE_COLUMNS),
    )
    logger.info(
        "demand_score stats → mean=%.3f  std=%.3f  min=%.3f  max=%.3f",
        df[TARGET_COLUMN].mean(),
        df[TARGET_COLUMN].std(),
        df[TARGET_COLUMN].min(),
        df[TARGET_COLUMN].max(),
    )

    if save_path is not None:
        os.makedirs(save_path.parent, exist_ok=True)
        df.to_csv(save_path, index=False)
        logger.info("Dataset saved → %s", save_path)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generate_dataset()
