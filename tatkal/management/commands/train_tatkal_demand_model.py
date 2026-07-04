"""
tatkal/management/commands/train_tatkal_demand_model.py
=======================================================
Django management command that orchestrates the full ML training pipeline:

    python manage.py train_tatkal_demand_model

Steps executed
--------------
1. Generate (or regenerate) the synthetic dataset → tatkal/ml/data.csv
2. Train LinearRegression and RandomForestRegressor on the dataset
3. Evaluate both models (MAE, RMSE, R²)
4. Automatically select the better-performing model (lowest RMSE)
5. Save the winner to tatkal/ml/demand_model.joblib

Options
-------
--regenerate-data   Force regeneration of data.csv even if it already exists.
                    Without this flag, existing data.csv is reused (faster).
--samples N         Number of synthetic samples to generate (default: 10000).
--seed N            Random seed for reproducibility (default: 42).

This command does NOT modify any Django model, migration, or view.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Generate synthetic training data and train the Tatkal demand "
        "prediction ML model.  Saves demand_model.joblib to tatkal/ml/."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--regenerate-data",
            action="store_true",
            default=False,
            help=(
                "Force regeneration of data.csv even if it already exists. "
                "Without this flag an existing data.csv is reused."
            ),
        )
        parser.add_argument(
            "--samples",
            type=int,
            default=10_000,
            metavar="N",
            help="Number of synthetic samples to generate (default: 10000).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            metavar="N",
            help="Random seed for reproducibility (default: 42).",
        )

    # ------------------------------------------------------------------
    def handle(self, *args, **options) -> None:
        regenerate: bool = options["regenerate_data"]
        n_samples: int = options["samples"]
        seed: int = options["seed"]

        # ---- Import ML modules here (not at top-level) to ensure that
        #      missing dependencies produce a clean error message rather
        #      than a traceback at Django startup.
        try:
            import numpy  # noqa: F401
            import pandas  # noqa: F401
            import joblib  # noqa: F401
            import sklearn  # noqa: F401
        except ImportError as exc:
            raise CommandError(
                f"Missing ML dependency: {exc}.\n"
                "Install requirements with:  pip install scikit-learn numpy pandas joblib"
            ) from exc

        from tatkal.ml.generate_data import DATA_PATH, generate_dataset
        from tatkal.ml.train_model import MODEL_PATH, train

        # ---- Step 1: Data generation -------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("\n-- Step 1: Dataset --"))

        if regenerate or not DATA_PATH.exists():
            action = "Regenerating" if DATA_PATH.exists() else "Generating"
            self.stdout.write(
                f"  {action} synthetic dataset "
                f"({n_samples:,} samples, seed={seed}) ..."
            )
            try:
                df = generate_dataset(
                    n_samples=n_samples,
                    random_seed=seed,
                    save_path=DATA_PATH,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] Dataset saved -> {DATA_PATH}  "
                        f"({len(df):,} rows)"
                    )
                )
            except Exception as exc:
                raise CommandError(f"Dataset generation failed: {exc}") from exc
        else:
            self.stdout.write(
                f"  Existing dataset found at {DATA_PATH}  "
                "(use --regenerate-data to force rebuild)"
            )

        # ---- Step 2: Training & evaluation --------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("\n-- Step 2: Training --"))
        self.stdout.write(
            "  Fitting LinearRegression and RandomForestRegressor ..."
        )

        try:
            best_model, best_name, metrics = train(
                data_path=DATA_PATH,
                model_path=MODEL_PATH,
            )
        except Exception as exc:
            raise CommandError(f"Model training failed: {exc}") from exc

        # ---- Step 3: Summary report ---------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("\n-- Step 3: Results --"))
        self.stdout.write(
            self.style.SUCCESS(f"  [OK] Selected model : {best_name}")
        )
        self.stdout.write(f"     MAE            : {metrics['mae']:.4f}")
        self.stdout.write(f"     RMSE           : {metrics['rmse']:.4f}")
        self.stdout.write(f"     R2             : {metrics['r2']:.4f}")
        self.stdout.write(
            self.style.SUCCESS(f"\n  [OK] Model artifact : {MODEL_PATH}")
        )
        self.stdout.write(
            "\nTo use the model, call:\n"
            "  from tatkal.ml.predict import predict_dynamic_surcharge\n"
            "  surcharge_pct, demand_score = predict_dynamic_surcharge(\n"
            "      minutes_to_departure=45,\n"
            "      day_of_week=5,\n"
            "      is_weekend=1,\n"
            "      is_festival=0,\n"
            "      route_popularity_tier=3,\n"
            "      seats_remaining_ratio=0.15,\n"
            "      historical_fill_rate=0.82,\n"
            "  )\n"
        )
