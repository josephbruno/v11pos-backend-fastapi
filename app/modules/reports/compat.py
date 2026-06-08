"""Frontend compatibility helpers for reports API contracts."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.order.model import Order
from app.modules.product.model import Product, Category
from app.modules.order.model import OrderItem
from app.modules.reports.model import SalesReport, ReportType
from app.modules.reports.service import SalesReportService
from app.modules.order.service import OrderService


class FrontendSalesGenerateRequest(BaseModel):
    """Body shape sent by v11pos-frontend apiServices.generateSalesReportNew."""

    restaurant_id: str
    period_type: str = Field(..., pattern="^(daily|monthly)$")
    report_date: Optional[str] = None
    report_month: Optional[int] = None
    report_year: Optional[int] = None


class FrontendItemGenerateRequest(BaseModel):
    restaurant_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def map_period_type_to_report_type(period_type: Optional[str]) -> Optional[str]:
    if not period_type:
        return None
    mapping = {
        "daily": ReportType.DAILY_SALES.value,
        "monthly": ReportType.MONTHLY_SALES.value,
    }
    return mapping.get(period_type.lower())


def legacy_pagination(skip: Optional[int], limit: Optional[int], page: int, page_size: int):
    if skip is not None or limit is not None:
        eff_skip = skip or 0
        eff_limit = limit or 30
        return eff_skip // eff_limit + 1 if eff_limit else 1, eff_limit, True
    return page, page_size, False


def serialize_sales_report_frontend(report: SalesReport | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(report, SalesReport):
        report_type = report.report_type.value if hasattr(report.report_type, "value") else str(report.report_type)
        from_date = report.from_date
        data = {
            "id": report.id,
            "restaurant_id": report.restaurant_id,
            "report_date": report.report_date.isoformat() if report.report_date else None,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": report.to_date.isoformat() if report.to_date else None,
            "total_orders": report.total_orders,
            "total_sales": report.total_sales,
            "total_tax": report.total_tax,
            "total_discount": report.total_discount,
            "net_sales": report.net_sales,
            "average_order_value": report.average_order_value,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "report_type": report_type,
        }
    else:
        data = dict(report)

    report_type = data.get("report_type", "")
    period_type = "monthly" if "monthly" in str(report_type) else "daily"
    from_date_raw = data.get("from_date")
    from_dt = None
    if from_date_raw:
        from_dt = from_date_raw if isinstance(from_date_raw, datetime) else datetime.fromisoformat(
            str(from_date_raw).replace("Z", "+00:00")
        )

    total_revenue = data.get("total_sales") or data.get("total_revenue") or 0
    net_revenue = data.get("net_sales") or data.get("net_revenue") or total_revenue
    aov = data.get("average_order_value") or data.get("avg_order_value") or 0

    return {
        "id": data.get("id", ""),
        "restaurant_id": data.get("restaurant_id"),
        "report_date": data.get("report_date"),
        "report_month": from_dt.month if from_dt else data.get("report_month"),
        "report_year": from_dt.year if from_dt else data.get("report_year"),
        "period_type": period_type,
        "total_orders": data.get("total_orders", 0),
        "total_revenue": total_revenue,
        "total_tax": data.get("total_tax", 0),
        "total_discount": data.get("total_discount", 0),
        "net_revenue": net_revenue,
        "avg_order_value": aov,
        "created_at": data.get("created_at") or datetime.utcnow().isoformat(),
    }


def serialize_item_report_frontend(item: Any) -> Dict[str, Any]:
    return {
        "id": item.id,
        "restaurant_id": item.restaurant_id,
        "product_id": getattr(item, "product_id", None),
        "product_name": getattr(item, "product_name", None),
        "category_name": getattr(item, "category_name", None),
        "quantity_sold": getattr(item, "quantity_sold", 0),
        "total_revenue": getattr(item, "total_revenue", 0),
        "total_cost": getattr(item, "total_cost", None),
        "profit": getattr(item, "gross_profit", None),
        "report_date": item.from_date.isoformat() if getattr(item, "from_date", None) else None,
        "created_at": item.created_at.isoformat() if getattr(item, "created_at", None) else None,
    }


def serialize_category_report_frontend(cat: Any) -> Dict[str, Any]:
    return {
        "id": cat.id,
        "restaurant_id": cat.restaurant_id,
        "category_id": getattr(cat, "category_id", None),
        "category_name": getattr(cat, "category_name", None),
        "total_revenue": getattr(cat, "total_revenue", 0),
        "quantity_sold": getattr(cat, "total_items_sold", 0),
        "report_date": cat.from_date.isoformat() if getattr(cat, "from_date", None) else None,
        "created_at": cat.created_at.isoformat() if getattr(cat, "created_at", None) else None,
    }


def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    last_day = monthrange(year, month)[1]
    start = datetime(year, month, 1)
    end = datetime(year, month, last_day, 23, 59, 59)
    return start, end


async def aggregate_live_monthly_sales(
    db: AsyncSession,
    restaurant_id: str,
    months: int = 12,
) -> List[Dict[str, Any]]:
    """Build monthly sales rows from live orders (no DB snapshot required)."""
    now = datetime.utcnow()
    rows: List[Dict[str, Any]] = []

    for i in range(months - 1, -1, -1):
        d = now - timedelta(days=30 * i)
        year, month = d.year, d.month
        from_date, to_date = _month_bounds(year, month)

        query = select(Order).where(
            and_(
                Order.restaurant_id == restaurant_id,
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        orders = list(result.scalars().all())
        metrics = await SalesReportService._calculate_sales_metrics(
            db, orders, from_date, to_date, restaurant_id
        )

        rows.append(
            serialize_sales_report_frontend(
                {
                    "id": f"live-{restaurant_id}-{year}-{month:02d}",
                    "restaurant_id": restaurant_id,
                    "report_date": from_date.isoformat(),
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                    "report_type": ReportType.MONTHLY_SALES.value,
                    "created_at": datetime.utcnow().isoformat(),
                    **metrics,
                }
            )
        )

    return rows


async def aggregate_live_daily_sales(
    db: AsyncSession,
    restaurant_id: str,
    days: int = 30,
) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    rows: List[Dict[str, Any]] = []

    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).date()
        from_date = datetime.combine(day, datetime.min.time())
        to_date = datetime.combine(day, datetime.max.time())

        query = select(Order).where(
            and_(
                Order.restaurant_id == restaurant_id,
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        orders = list(result.scalars().all())
        metrics = await SalesReportService._calculate_sales_metrics(
            db, orders, from_date, to_date, restaurant_id
        )

        rows.append(
            serialize_sales_report_frontend(
                {
                    "id": f"live-{restaurant_id}-{day.isoformat()}",
                    "restaurant_id": restaurant_id,
                    "report_date": from_date.isoformat(),
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                    "report_type": ReportType.DAILY_SALES.value,
                    "created_at": datetime.utcnow().isoformat(),
                    **metrics,
                }
            )
        )

    return rows


async def compute_live_item_reports(
    db: AsyncSession,
    restaurant_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)

    query = select(OrderItem).join(Order).where(
        and_(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= from_date,
            Order.created_at <= to_date,
            Order.status == "completed",
            Order.deleted_at.is_(None),
            OrderItem.deleted_at.is_(None),
        )
    )
    result = await db.execute(query)
    order_items = list(result.scalars().all())

    product_data: Dict[str, Dict[str, Any]] = {}
    for item in order_items:
        pid = item.product_id
        if not pid:
            continue
        if pid not in product_data:
            product_data[pid] = {"name": item.product_name or "Unknown", "items": []}
        product_data[pid]["items"].append(item)

    rows: List[Dict[str, Any]] = []
    for pid, data in product_data.items():
        items = data["items"]
        quantity_sold = sum(i.quantity or 0 for i in items)
        total_revenue = sum(i.total_price or 0 for i in items)
        rows.append(
            {
                "id": f"live-item-{restaurant_id}-{pid}",
                "restaurant_id": restaurant_id,
                "product_id": pid,
                "product_name": data["name"],
                "category_name": None,
                "quantity_sold": quantity_sold,
                "total_revenue": total_revenue,
                "total_cost": None,
                "profit": None,
                "report_date": from_date.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    rows.sort(key=lambda r: r["total_revenue"], reverse=True)
    return rows[:limit]


async def compute_live_category_reports(
    db: AsyncSession,
    restaurant_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)

    query = (
        select(OrderItem, Product, Category)
        .join(Order, OrderItem.order_id == Order.id)
        .outerjoin(Product, OrderItem.product_id == Product.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .where(
            and_(
                Order.restaurant_id == restaurant_id,
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.status == "completed",
                Order.deleted_at.is_(None),
                OrderItem.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(query)
    rows_raw = result.all()

    category_data: Dict[str, Dict[str, Any]] = {}
    for item, _product, category in rows_raw:
        cat_id = category.id if category else "uncategorized"
        cat_name = category.name if category else "Uncategorized"
        if cat_id not in category_data:
            category_data[cat_id] = {"name": cat_name, "items": []}
        category_data[cat_id]["items"].append(item)

    rows: List[Dict[str, Any]] = []
    for cat_id, data in category_data.items():
        items = data["items"]
        quantity_sold = sum(i.quantity or 0 for i in items)
        total_revenue = sum(i.total_price or 0 for i in items)
        rows.append(
            {
                "id": f"live-cat-{restaurant_id}-{cat_id}",
                "restaurant_id": restaurant_id,
                "category_id": None if cat_id == "uncategorized" else cat_id,
                "category_name": data["name"],
                "total_revenue": total_revenue,
                "quantity_sold": quantity_sold,
                "report_date": from_date.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    rows.sort(key=lambda r: r["total_revenue"], reverse=True)
    return rows[:limit]


def parse_frontend_generate_dates(
    req: FrontendSalesGenerateRequest,
) -> tuple[datetime, datetime, str, str]:
    if req.period_type == "daily":
        if req.report_date:
            day = datetime.fromisoformat(req.report_date.replace("Z", "")).date()
        else:
            day = datetime.utcnow().date()
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        report_type = ReportType.DAILY_SALES.value
        name = f"Daily Sales Report - {day.isoformat()}"
    else:
        year = req.report_year or datetime.utcnow().year
        month = req.report_month or datetime.utcnow().month
        start, end = _month_bounds(year, month)
        report_type = ReportType.MONTHLY_SALES.value
        name = f"Monthly Sales Report - {year}-{month:02d}"
    return start, end, report_type, name


def resolve_dashboard_dates(period: Optional[str]) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    mapping = {
        "today": 1,
        "7d": 7,
        "7days": 7,
        "30d": 30,
        "30days": 30,
        "90d": 90,
        "3months": 90,
        "12months": 365,
    }
    days = mapping.get((period or "30d").lower(), 30)
    return now - timedelta(days=days), now


async def build_restaurant_dashboard(
    db: AsyncSession,
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
) -> Dict[str, Any]:
    stats = await OrderService.get_order_statistics(
        db, restaurant_id=restaurant_id, start_date=from_date, end_date=to_date
    )
    monthly = await aggregate_live_monthly_sales(db, restaurant_id, months=6)
    items = await compute_live_item_reports(db, restaurant_id, from_date, to_date, limit=5)
    return {
        "restaurant_id": restaurant_id,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "order_statistics": stats,
        "revenue_trend": monthly,
        "top_products": items,
    }
