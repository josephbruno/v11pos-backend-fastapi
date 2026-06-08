"""Unit tests for cashier billing and reports API compatibility helpers."""

from datetime import datetime

from app.modules.order.schema import OrderStatusUpdate, OrderPaymentUpdate, OrderCancelRequest
from app.modules.order.model import OrderStatus, PaymentStatus
from app.modules.reports.compat import (
    FrontendSalesGenerateRequest,
    map_period_type_to_report_type,
    legacy_pagination,
    serialize_sales_report_frontend,
    serialize_category_report_frontend,
    parse_frontend_generate_dates,
    resolve_dashboard_dates,
)


def test_delivered_status_maps_to_completed():
    update = OrderStatusUpdate(status="delivered")
    assert update.status == OrderStatus.COMPLETED


def test_payment_update_allows_missing_paid_amount():
    payload = OrderPaymentUpdate(payment_status=PaymentStatus.PAID)
    assert payload.paid_amount is None
    assert payload.payment_method is None


def test_cancel_request_body_schema():
    body = OrderCancelRequest(reason="Customer changed mind")
    assert body.reason == "Customer changed mind"


def test_period_type_alias():
    assert map_period_type_to_report_type("monthly") == "monthly_sales"
    assert map_period_type_to_report_type("daily") == "daily_sales"


def test_legacy_pagination_from_skip_limit():
    page, page_size, legacy = legacy_pagination(skip=30, limit=10, page=1, page_size=20)
    assert legacy is True
    assert page == 4
    assert page_size == 10


def test_serialize_sales_report_frontend_from_dict():
    row = serialize_sales_report_frontend(
        {
            "id": "abc",
            "restaurant_id": "r1",
            "report_type": "monthly_sales",
            "from_date": "2025-06-01T00:00:00",
            "total_sales": 50000,
            "net_sales": 48000,
            "total_orders": 12,
            "total_tax": 2000,
            "total_discount": 1000,
            "average_order_value": 4000,
            "created_at": "2025-06-08T00:00:00",
        }
    )
    assert row["total_revenue"] == 50000
    assert row["period_type"] == "monthly"
    assert row["report_month"] == 6
    assert row["report_year"] == 2025
    assert row["avg_order_value"] == 4000


def test_serialize_category_quantity_sold_alias():
    class Cat:
        id = "c1"
        restaurant_id = "r1"
        category_id = "cat1"
        category_name = "Beverages"
        total_revenue = 9000
        total_items_sold = 42
        from_date = datetime(2025, 6, 1)
        created_at = datetime(2025, 6, 8)

    out = serialize_category_report_frontend(Cat())
    assert out["quantity_sold"] == 42
    assert out["total_revenue"] == 9000


def test_parse_frontend_monthly_generate_dates():
    req = FrontendSalesGenerateRequest(
        restaurant_id="r1",
        period_type="monthly",
        report_month=3,
        report_year=2025,
    )
    start, end, report_type, name = parse_frontend_generate_dates(req)
    assert report_type == "monthly_sales"
    assert start.month == 3
    assert end.day == 31
    assert "March" in name or "2025" in name


def test_resolve_dashboard_dates():
    start, end = resolve_dashboard_dates("12months")
    assert (end - start).days >= 364


if __name__ == "__main__":
    tests = [
        test_delivered_status_maps_to_completed,
        test_payment_update_allows_missing_paid_amount,
        test_cancel_request_body_schema,
        test_period_type_alias,
        test_legacy_pagination_from_skip_limit,
        test_serialize_sales_report_frontend_from_dict,
        test_serialize_category_quantity_sold_alias,
        test_parse_frontend_monthly_generate_dates,
        test_resolve_dashboard_dates,
    ]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print(f"All {len(tests)} tests passed")
