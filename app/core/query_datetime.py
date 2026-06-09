"""Helpers for parsing date/datetime query parameters."""

from datetime import date, datetime, time, timezone, timedelta
from typing import Annotated, Any, Optional, Union

from pydantic import BeforeValidator

IST = timezone(timedelta(hours=5, minutes=30))


def parse_query_date(value: Any) -> Optional[Union[date, datetime]]:
    """Accept YYYY-MM-DD or ISO-8601 datetime query values."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("Invalid date or datetime")

    raw = value.strip()
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        return date.fromisoformat(raw)
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


QueryDateInput = Annotated[
    Optional[Union[date, datetime]],
    BeforeValidator(parse_query_date),
]


def _as_utc_naive(dt: datetime) -> datetime:
    """Normalize aware/naive datetimes to UTC naive for utcnow() DB columns."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def to_query_start_datetime(value: Optional[Union[date, datetime]]) -> Optional[datetime]:
    """Convert a query date/datetime to the start of the range in UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=IST)
        return _as_utc_naive(value)
    return _as_utc_naive(datetime.combine(value, time.min, tzinfo=IST))


def ist_today() -> date:
    """Current calendar date in Asia/Kolkata."""
    return datetime.now(IST).date()


def ist_day_start_utc(day: date) -> datetime:
    """IST midnight for the given day, as UTC naive."""
    return _as_utc_naive(datetime.combine(day, time.min, tzinfo=IST))


def ist_day_end_utc(day: date) -> datetime:
    """IST end-of-day for the given day, as UTC naive."""
    return _as_utc_naive(datetime.combine(day, time.max, tzinfo=IST))


def to_query_end_datetime(value: Optional[Union[date, datetime]]) -> Optional[datetime]:
    """Convert a query date/datetime to the end of the range in UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            if value.time() == time.min:
                return _as_utc_naive(datetime.combine(value.date(), time.max, tzinfo=IST))
            value = value.replace(tzinfo=IST)
        return _as_utc_naive(value)
    return _as_utc_naive(datetime.combine(value, time.max, tzinfo=IST))
