"""
Helper fxns or the BI usage pipeline
"""

from datetime import date, datetime, timedelta, timezone

ACTIVITY_EVENTS_MAX_RETENTION_DAYS = 28

def get_dates_to_fetch(
        lookback_days: int,
        today: date | None = None,
        last_loaded_date: date | None = None
) -> list[date]:
    """return ascending list of UTC dates to query activity events for"""
    if today is None:
        today = datetime.now(timezone.utc).date()

    lookback_days = max(1, min(lookback_days, ACTIVITY_EVENTS_MAX_RETENTION_DAYS))

    window_start = today - timedelta(days=lookback_days)
    window_end = today - timedelta(days=1)

    if last_loaded_date is not None and last_loaded_date >= window_start:
        window_start = last_loaded_date

    days: list[date] = []
    current = window_start
    while current <= window_end:
        days.append(current)
        current += timedelta(days=1)
    return days

def limit_backfill(dates: list[date], max_days_per_run: int | None) -> list[date]:
    """cap a fetch window to the oldest ``max_days_per_run`` dates"""
    if not max_days_per_run or max_days_per_run<=0:
        return dates
    return dates[:max_days_per_run]

def day_bounds(day: date) -> tuple[str, str]:
    """return ``(start, end)`` ISO-8601 UTC strings spanning the future"""
    iso = day.isoformat()
    return f"{iso}T00:00:00", f"{iso}T23:59:59"

