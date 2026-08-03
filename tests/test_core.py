from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.query_datetime import (
    ist_day_end_utc,
    ist_day_start_utc,
    to_query_end_datetime,
    to_query_start_datetime,
)
from app.core.rate_limit import RateLimiter
from app.core.timezone import APP_TIMEZONE, convert_datetime_fields


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


def test_convert_datetime_fields_handles_pydantic_models():
    class OrderStub(BaseModel):
        created_at: datetime
        name: str

    # 05:02 UTC → 10:32 IST
    utc_naive = datetime(2026, 8, 3, 5, 2, 57)
    converted = convert_datetime_fields(OrderStub(created_at=utc_naive, name="x"))
    assert isinstance(converted, dict)
    assert converted["name"] == "x"
    local = converted["created_at"]
    assert local.tzinfo is not None
    ist = local.astimezone(ZoneInfo(APP_TIMEZONE))
    assert ist.hour == 10 and ist.minute == 32


def test_convert_datetime_fields_handles_nested_pydantic_list():
    class ItemStub(BaseModel):
        created_at: datetime

    utc_naive = datetime(2026, 8, 3, 5, 2, 57, tzinfo=timezone.utc).replace(tzinfo=None)
    converted = convert_datetime_fields({"orders": [ItemStub(created_at=utc_naive)]})
    local = converted["orders"][0]["created_at"]
    ist = local.astimezone(ZoneInfo(APP_TIMEZONE))
    assert ist.hour == 10 and ist.minute == 32
