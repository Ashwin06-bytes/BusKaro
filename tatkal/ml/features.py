"""
tatkal/ml/features.py
=====================
Extracts ML-ready feature dictionaries from live Django ORM objects for use
with ``predict_dynamic_surcharge()``.

This module is the *only* place that touches Django models inside the ML
package.  ``generate_data.py``, ``train_model.py`` and ``predict.py`` remain
pure-Python and Django-free.

Public API
----------
extract_features(schedule, tatkal_quota) -> dict[str, float | int]

    Returns a dictionary whose keys exactly match the ML model's training
    feature columns (in the same order defined in predict._FEATURE_ORDER).

    On any error the function logs a warning and returns None so the caller
    can fall back to the static 25% default.
"""

from __future__ import annotations

import datetime
import logging
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Festival calendar (current + next year for forward bookings)
# Expand this set each year or load from a DB table in a future iteration.
# ---------------------------------------------------------------------------
_FESTIVAL_DATES: frozenset[datetime.date] = frozenset([
    # Pongal / Makar Sankranti window
    datetime.date(2025, 1, 14),
    datetime.date(2025, 1, 15),
    datetime.date(2025, 1, 16),
    # Tamil New Year / Vishu
    datetime.date(2025, 4, 14),
    # Good Friday
    datetime.date(2025, 4, 18),
    # Eid al-Fitr (approx)
    datetime.date(2025, 3, 30),
    datetime.date(2025, 3, 31),
    # May Day
    datetime.date(2025, 5, 1),
    # Independence Day
    datetime.date(2025, 8, 15),
    # Ganesh Chaturthi
    datetime.date(2025, 8, 27),
    # Gandhi Jayanti
    datetime.date(2025, 10, 2),
    # Diwali window
    datetime.date(2025, 10, 20),
    datetime.date(2025, 10, 21),
    datetime.date(2025, 10, 22),
    # Christmas
    datetime.date(2025, 12, 24),
    datetime.date(2025, 12, 25),
    datetime.date(2025, 12, 26),
    # New Year
    datetime.date(2025, 12, 31),
    datetime.date(2026, 1, 1),
    # Pongal 2026
    datetime.date(2026, 1, 14),
    datetime.date(2026, 1, 15),
    # Tamil New Year 2026
    datetime.date(2026, 4, 14),
    # Independence Day 2026
    datetime.date(2026, 8, 15),
    # Diwali 2026 (approx)
    datetime.date(2026, 11, 8),
    datetime.date(2026, 11, 9),
    # Christmas 2026
    datetime.date(2026, 12, 24),
    datetime.date(2026, 12, 25),
    datetime.date(2026, 12, 26),
    datetime.date(2026, 12, 31),
    datetime.date(2027, 1, 1),
])

# ---------------------------------------------------------------------------
# Route popularity tier thresholds (bookings over last 90 days)
# Tier 1 = low-demand   :   0 – 9  bookings
# Tier 2 = mid-demand   :  10 – 49 bookings
# Tier 3 = high-demand  : 50+      bookings
# ---------------------------------------------------------------------------
_TIER_THRESHOLD_MID: int = 10
_TIER_THRESHOLD_HIGH: int = 50

# Look-back windows
_POPULARITY_LOOKBACK_DAYS: int = 90
_FILL_RATE_LOOKBACK_DAYS: int = 90


def extract_features(
    schedule,  # inventory.models.Schedule instance
    tatkal_quota,  # tatkal.models.TatkalQuota instance (may be None)
) -> Optional[dict]:
    """
    Compute the seven ML input features for a given internal Schedule.

    Parameters
    ----------
    schedule      : inventory.models.Schedule instance (already loaded).
    tatkal_quota  : tatkal.models.TatkalQuota instance (may be None; not
                    currently used in feature computation but reserved for
                    future quota-level signals).

    Returns
    -------
    dict with keys matching _FEATURE_ORDER, or None on any failure.

    Notes
    -----
    * All DB calls are scoped to ``schedule.route`` or ``schedule`` itself —
      there are no unbounded table scans.
    * The function never raises; callers should check for None.
    """
    try:
        journey_date: datetime.date = schedule.journey_date
        departure_time: datetime.time = schedule.departure_time

        # ── 1. minutes_to_departure ─────────────────────────────────────────
        dep_dt = timezone.make_aware(
            datetime.datetime.combine(journey_date, departure_time)
        )
        now = timezone.now()
        minutes_to_departure: float = max(
            0.0,
            (dep_dt - now).total_seconds() / 60.0,
        )

        # ── 2. day_of_week ──────────────────────────────────────────────────
        day_of_week: int = journey_date.weekday()  # 0=Mon … 6=Sun

        # ── 3. is_weekend ───────────────────────────────────────────────────
        is_weekend: int = 1 if day_of_week >= 5 else 0

        # ── 4. is_festival ──────────────────────────────────────────────────
        is_festival: int = 1 if journey_date in _FESTIVAL_DATES else 0

        # ── 5. route_popularity_tier ────────────────────────────────────────
        #
        # Count Bookings (CONFIRMED or PENDING — excluding CANCELLED) that
        # used a Schedule on the same Route in the last 90 days.
        # We use only a count — one aggregate query, no N+1 risk.
        from bookings.models import Booking  # local import — avoids circular
        lookback_date = (now - datetime.timedelta(days=_POPULARITY_LOOKBACK_DAYS)).date()
        booking_count: int = Booking.objects.filter(
            schedule__route=schedule.route,
            created_at__date__gte=lookback_date,
        ).exclude(status='CANCELLED').count()

        if booking_count >= _TIER_THRESHOLD_HIGH:
            route_popularity_tier = 3
        elif booking_count >= _TIER_THRESHOLD_MID:
            route_popularity_tier = 2
        else:
            route_popularity_tier = 1

        # ── 6. seats_remaining_ratio ────────────────────────────────────────
        #
        # Count AVAILABLE seats in SeatInventory for this exact schedule,
        # divided by the bus's declared total_seats.
        from inventory.models import SeatInventory  # local import
        available_seats: int = SeatInventory.objects.filter(
            schedule=schedule,
            status='AVAILABLE',
        ).count()
        total_seats: int = max(1, schedule.bus.total_seats)  # guard /0
        seats_remaining_ratio: float = round(available_seats / total_seats, 4)

        # ── 7. historical_fill_rate ─────────────────────────────────────────
        #
        # For COMPLETED schedules on the same Route and same weekday in the
        # last 90 days, compute the average occupancy:
        #   fill_rate = avg(booked_seats / total_seats)
        #
        # "booked_seats" = SeatInventory rows with status='BOOKED' per schedule.
        # We do this with two aggregate queries (one count per completed schedule
        # is expensive at scale, so we use a single annotated aggregate).
        from django.db.models import Count, Q
        from inventory.models import Schedule as ScheduleModel  # local import

        cutoff_date = (now - datetime.timedelta(days=_FILL_RATE_LOOKBACK_DAYS)).date()
        completed_schedules = list(
            ScheduleModel.objects.filter(
                route=schedule.route,
                status='COMPLETED',
                journey_date__gte=cutoff_date,
                journey_date__weekday=day_of_week,  # same weekday only
            ).annotate(
                booked_count=Count(
                    'inventory',
                    filter=Q(inventory__status='BOOKED'),
                )
            ).select_related('bus')  # avoids N+1 when reading bus.total_seats
        )

        if completed_schedules:
            # Compute weighted average: sum(booked) / sum(total_seats)
            total_booked: int = sum(s.booked_count for s in completed_schedules)
            total_capacity: int = sum(
                max(1, s.bus.total_seats) for s in completed_schedules
            )
            historical_fill_rate: float = round(
                min(1.0, total_booked / total_capacity), 4
            )
        else:
            # No historical data: assume moderate fill rate as neutral prior
            historical_fill_rate = 0.5

        features = {
            "minutes_to_departure": minutes_to_departure,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_festival": is_festival,
            "route_popularity_tier": route_popularity_tier,
            "seats_remaining_ratio": seats_remaining_ratio,
            "historical_fill_rate": historical_fill_rate,
        }

        logger.debug(
            "Tatkal features for schedule %s: %s",
            schedule.id,
            features,
        )
        return features

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "extract_features() failed for schedule_id=%s: %s. "
            "Falling back to static 25%% surcharge.",
            getattr(schedule, "id", "unknown"),
            exc,
        )
        return None
