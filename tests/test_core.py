from datetime import date

import pytest
from fastapi import HTTPException

from app.core.query_datetime import (
    ist_day_end_utc,
    ist_day_start_utc,
    to_query_end_datetime,
    to_query_start_datetime,
)
from app.core.rate_limit import RateLimiter


def test_ist_day_bounds_convert_to_utc_naive():
    day = date(2026, 6, 26)
    start = ist_day_start_utc(day)
    end = ist_day_end_utc(day)
    assert start.tzinfo is None
    assert end.tzinfo is None
    assert start < end
    # IST midnight 26 Jun = 25 Jun 18:30 UTC
    assert start.hour == 18 and start.day == 25


def test_query_date_only_uses_ist_day():
    start = to_query_start_datetime(date(2026, 6, 26))
    end = to_query_end_datetime(date(2026, 6, 26))
    assert start < end


def test_rate_limiter_blocks_after_max():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.check("127.0.0.1")
    limiter.check("127.0.0.1")
    with pytest.raises(HTTPException) as exc:
        limiter.check("127.0.0.1")
    assert exc.value.status_code == 429
