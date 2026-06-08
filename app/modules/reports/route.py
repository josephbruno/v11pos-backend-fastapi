from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any, Dict
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import success_response, error_response
from app.modules.reports.schema import (
    SalesReportCreate, SalesReportUpdate, SalesReportResponse,
    SalesReportListResponse, ItemWiseSalesReportResponse,
    ItemWiseSalesReportListResponse, CategoryWiseSalesReportResponse,
    CategoryWiseSalesReportListResponse, ReportGenerateRequest,
    PaymentModeReportResponse, TaxReportResponse, DiscountOfferReportResponse,
    CancelledVoidReportResponse, ProfitCostAnalysisResponse,
    ReportScheduleCreate, ReportScheduleUpdate, ReportScheduleResponse,
    ReportScheduleListResponse, ReportExportResponse, ReportExportListResponse
)
from app.modules.reports.service import (
    SalesReportService, ItemWiseSalesReportService, CategoryWiseSalesReportService
)
from app.modules.reports.model import ReportType
from app.modules.user.model import User
from app.modules.reports.compat import (
    FrontendSalesGenerateRequest,
    FrontendItemGenerateRequest,
    map_period_type_to_report_type,
    legacy_pagination,
    serialize_sales_report_frontend,
    serialize_item_report_frontend,
    serialize_category_report_frontend,
    aggregate_live_monthly_sales,
    aggregate_live_daily_sales,
    compute_live_item_reports,
    compute_live_category_reports,
    parse_frontend_generate_dates,
    resolve_dashboard_dates,
    build_restaurant_dashboard,
)

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


def _user_attr(user: User, key: str):
    """Read user fields from ORM model (get_current_user returns User)."""
    return getattr(user, key, None)


def _is_super_admin(user: User) -> bool:
    role = _user_attr(user, "role")
    return bool(_user_attr(user, "is_superadmin")) or role in ("super_admin", "superadmin")


# Sales Reports

@router.post("/sales/generate", response_model=dict)
async def generate_sales_report(
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate sales report (Daily/Monthly)
    
    - **Super Admin**: Can generate for specific restaurant or all restaurants
    - **Restaurant User**: Can only generate for their restaurant
  Accepts native ``ReportGenerateRequest`` or frontend ``period_type`` body.
    """
    if "period_type" in body and "report_type" not in body:
        fe_req = FrontendSalesGenerateRequest(**body)
        from_date, to_date, report_type, report_name = parse_frontend_generate_dates(fe_req)
        request = ReportGenerateRequest(
            restaurant_id=fe_req.restaurant_id,
            report_type=report_type,
            report_name=report_name,
            from_date=from_date,
            to_date=to_date,
        )
    else:
        request = ReportGenerateRequest(**body)

    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    # Validate restaurant access
    if not _is_super_admin(current_user):
        if request.restaurant_id and request.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied to this restaurant")
        request.restaurant_id = user_restaurant_id
    
    # Generate appropriate report type
    if request.report_type in ["daily_sales", "monthly_sales"]:
        if request.report_type == "daily_sales":
            report = await SalesReportService.generate_daily_sales_report(
                db=db,
                from_date=request.from_date,
                to_date=request.to_date,
                restaurant_id=request.restaurant_id,
                generated_by=_user_attr(current_user, "id")
            )
        else:
            report = await SalesReportService.generate_monthly_sales_report(
                db=db,
                from_date=request.from_date,
                to_date=request.to_date,
                restaurant_id=request.restaurant_id,
                generated_by=_user_attr(current_user, "id")
            )
        
        # Generate breakdowns if requested
        if request.include_item_breakdown:
            await ItemWiseSalesReportService.generate_item_wise_report(
                db=db,
                from_date=request.from_date,
                to_date=request.to_date,
                restaurant_id=request.restaurant_id,
                sales_report_id=report.id
            )
        
        if request.include_category_breakdown:
            await CategoryWiseSalesReportService.generate_category_wise_report(
                db=db,
                from_date=request.from_date,
                to_date=request.to_date,
                restaurant_id=request.restaurant_id,
                sales_report_id=report.id
            )
        
        return success_response(
            message="Sales report generated successfully",
            data=serialize_sales_report_frontend(report),
        )
    
    raise HTTPException(status_code=400, detail="Invalid report type")


@router.get("/sales/{report_id}", response_model=dict)
async def get_sales_report(
    report_id: str = Path(..., description="Sales report ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales report by ID"""
    
    report = await SalesReportService.get_sales_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Sales report not found")
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if report.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return success_response(
        message="Sales report retrieved successfully",
        data=SalesReportResponse.model_validate(report)
    )


@router.get("/sales", response_model=dict)
async def list_sales_reports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    period_type: Optional[str] = Query(None, description="Frontend alias: daily|monthly"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    skip: Optional[int] = Query(None, ge=0, description="Legacy offset"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Legacy page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List sales reports with pagination
    
    - **Super Admin**: Can view all reports or filter by restaurant
    - **Restaurant User**: Can only view their restaurant reports
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        restaurant_id = user_restaurant_id

    page, page_size, legacy_format = legacy_pagination(skip, limit, page, page_size)
    effective_report_type = report_type or map_period_type_to_report_type(period_type)

    reports, total = await SalesReportService.list_sales_reports(
        db=db,
        restaurant_id=restaurant_id,
        report_type=effective_report_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )

    if not reports and restaurant_id and (period_type or legacy_format):
        months = limit or page_size or 12
        if (period_type or "").lower() == "daily":
            live_rows = await aggregate_live_daily_sales(db, restaurant_id, days=months)
        else:
            live_rows = await aggregate_live_monthly_sales(db, restaurant_id, months=months)
        if legacy_format:
            return success_response(
                message="Sales reports retrieved successfully",
                data=live_rows,
            )
        return success_response(
            message="Sales reports retrieved successfully",
            data=SalesReportListResponse(
                total=len(live_rows),
                page=page,
                page_size=page_size,
                data=live_rows,
            ),
        )

    serialized = [serialize_sales_report_frontend(r) for r in reports]

    if legacy_format:
        return success_response(
            message="Sales reports retrieved successfully",
            data=serialized,
        )

    return success_response(
        message="Sales reports retrieved successfully",
        data=SalesReportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=serialized,
        )
    )


@router.patch("/sales/{report_id}", response_model=dict)
async def update_sales_report(
    report_id: str = Path(..., description="Sales report ID"),
    update_data: SalesReportUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update sales report"""
    
    # Check if report exists and user has access
    report = await SalesReportService.get_sales_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Sales report not found")
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if report.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Update
    updated_report = await SalesReportService.update_sales_report(db, report_id, update_data)
    
    return success_response(
        message="Sales report updated successfully",
        data=SalesReportResponse.model_validate(updated_report)
    )


@router.delete("/sales/{report_id}", response_model=dict)
async def delete_sales_report(
    report_id: str = Path(..., description="Sales report ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete sales report"""
    
    # Check if report exists and user has access
    report = await SalesReportService.get_sales_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Sales report not found")
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if report.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete
    success = await SalesReportService.delete_sales_report(db, report_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete sales report")
    
    return success_response(
        message="Sales report deleted successfully",
        data={"deleted": True}
    )


# Item-wise Sales Reports

@router.post("/items/generate", response_model=dict)
async def generate_item_wise_report(
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    body: Optional[FrontendItemGenerateRequest] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate item-wise sales report
    
    - **Super Admin**: Can generate for specific restaurant or all restaurants
    - **Restaurant User**: Can only generate for their restaurant
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id

    if body:
        restaurant_id = body.restaurant_id or restaurant_id
        if body.start_date:
            from_date = datetime.fromisoformat(body.start_date.replace("Z", ""))
        if body.end_date:
            to_date = datetime.fromisoformat(body.end_date.replace("Z", ""))

    if not from_date or not to_date:
        to_date = to_date or datetime.utcnow()
        from_date = from_date or (to_date - timedelta(days=30))
    
    reports = await ItemWiseSalesReportService.generate_item_wise_report(
        db=db,
        from_date=from_date,
        to_date=to_date,
        restaurant_id=restaurant_id
    )
    
    return success_response(
        message=f"Item-wise sales report generated for {len(reports)} items",
        data=[serialize_item_report_frontend(r) for r in reports]
    )


@router.get("/items", response_model=dict)
async def list_item_wise_reports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    skip: Optional[int] = Query(None, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List item-wise sales reports
    
    - **Super Admin**: Can view all reports or filter by restaurant
    - **Restaurant User**: Can only view their restaurant reports
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        restaurant_id = user_restaurant_id

    page, page_size, legacy_format = legacy_pagination(skip, limit, page, page_size)

    reports, total = await ItemWiseSalesReportService.list_item_wise_reports(
        db=db,
        restaurant_id=restaurant_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )

    if not reports and restaurant_id:
        live = await compute_live_item_reports(
            db, restaurant_id, from_date, to_date, limit=page_size
        )
        if legacy_format:
            return success_response(
                message="Item-wise sales reports retrieved successfully",
                data=live,
            )
        return success_response(
            message="Item-wise sales reports retrieved successfully",
            data=ItemWiseSalesReportListResponse(
                total=len(live), page=page, page_size=page_size, data=live
            ),
        )

    serialized = [serialize_item_report_frontend(r) for r in reports]
    if legacy_format:
        return success_response(
            message="Item-wise sales reports retrieved successfully",
            data=serialized,
        )

    return success_response(
        message="Item-wise sales reports retrieved successfully",
        data=ItemWiseSalesReportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=serialized,
        )
    )


# Category-wise Sales Reports

@router.post("/categories/generate", response_model=dict)
async def generate_category_wise_report(
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    body: Optional[FrontendItemGenerateRequest] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate category-wise sales report
    
    - **Super Admin**: Can generate for specific restaurant or all restaurants
    - **Restaurant User**: Can only generate for their restaurant
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id

    if body:
        restaurant_id = body.restaurant_id or restaurant_id
        if body.start_date:
            from_date = datetime.fromisoformat(body.start_date.replace("Z", ""))
        if body.end_date:
            to_date = datetime.fromisoformat(body.end_date.replace("Z", ""))

    if not from_date or not to_date:
        to_date = to_date or datetime.utcnow()
        from_date = from_date or (to_date - timedelta(days=30))
    
    reports = await CategoryWiseSalesReportService.generate_category_wise_report(
        db=db,
        from_date=from_date,
        to_date=to_date,
        restaurant_id=restaurant_id
    )
    
    return success_response(
        message=f"Category-wise sales report generated for {len(reports)} categories",
        data=[serialize_category_report_frontend(r) for r in reports]
    )


@router.get("/categories", response_model=dict)
async def list_category_wise_reports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    skip: Optional[int] = Query(None, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List category-wise sales reports
    
    - **Super Admin**: Can view all reports or filter by restaurant
    - **Restaurant User**: Can only view their restaurant reports
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        restaurant_id = user_restaurant_id

    page, page_size, legacy_format = legacy_pagination(skip, limit, page, page_size)

    reports, total = await CategoryWiseSalesReportService.list_category_wise_reports(
        db=db,
        restaurant_id=restaurant_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )

    if not reports and restaurant_id:
        live = await compute_live_category_reports(
            db, restaurant_id, from_date, to_date, limit=page_size
        )
        if legacy_format:
            return success_response(
                message="Category-wise sales reports retrieved successfully",
                data=live,
            )
        return success_response(
            message="Category-wise sales reports retrieved successfully",
            data=CategoryWiseSalesReportListResponse(
                total=len(live), page=page, page_size=page_size, data=live
            ),
        )

    serialized = [serialize_category_report_frontend(r) for r in reports]
    if legacy_format:
        return success_response(
            message="Category-wise sales reports retrieved successfully",
            data=serialized,
        )

    return success_response(
        message="Category-wise sales reports retrieved successfully",
        data=CategoryWiseSalesReportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=serialized,
        )
    )


# Specialized Reports (Payment Mode, Tax, Discounts, etc.)
# These endpoints can be added similarly with dedicated service methods

@router.get("/payment-mode", response_model=dict)
async def get_payment_mode_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment mode report
    
    Shows breakdown of revenue by payment methods (Cash, Card, UPI, Wallet, etc.)
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement payment mode report service
    
    return success_response(
        message="Payment mode report retrieved successfully",
        data={"message": "Payment mode report - to be implemented"}
    )


@router.get("/tax-gst", response_model=dict)
async def get_tax_gst_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tax (GST) report
    
    Shows breakdown of taxes: CGST, SGST, IGST, VAT, Service Tax
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement tax report service
    
    return success_response(
        message="Tax report retrieved successfully",
        data={"message": "Tax (GST) report - to be implemented"}
    )


@router.get("/discounts-offers", response_model=dict)
async def get_discounts_offers_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get discounts & offers report
    
    Shows breakdown by discount types: Coupons, Loyalty, Promotional, Staff
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement discount report service
    
    return success_response(
        message="Discounts & offers report retrieved successfully",
        data={"message": "Discounts & offers report - to be implemented"}
    )


@router.get("/cancelled-void", response_model=dict)
async def get_cancelled_void_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cancelled/void orders report
    
    Shows cancelled orders, void orders, and refunds with reasons
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement cancelled/void report service
    
    return success_response(
        message="Cancelled/void orders report retrieved successfully",
        data={"message": "Cancelled/void orders report - to be implemented"}
    )


@router.get("/profit-cost", response_model=dict)
async def get_profit_cost_analysis(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get profit & cost analysis report
    
    Shows revenue, costs, profit margins with category and item breakdown
    """
    
    # Check permissions
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement profit/cost analysis service
    
    return success_response(
        message="Profit & cost analysis retrieved successfully",
        data={"message": "Profit & cost analysis - to be implemented"}
    )


# Super Admin Dashboard

@router.get("/dashboard/super-admin", response_model=dict)
async def get_super_admin_dashboard(
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get super admin dashboard with aggregated analytics across all restaurants
    
    **Super Admin Only**
    """
    
    if not _is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    # Set default date range if not provided
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    # TODO: Implement super admin dashboard aggregation
    
    return success_response(
        message="Super admin dashboard retrieved successfully",
        data={
            "message": "Super admin dashboard - to be implemented",
            "from_date": from_date,
            "to_date": to_date
        }
    )


@router.get("/dashboard/restaurant/{restaurant_id}", response_model=dict)
async def get_restaurant_dashboard_by_path(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    period: Optional[str] = Query(None, description="Period alias: today, 7d, 30d, 12months"),
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Frontend-compatible dashboard path used by apiServices.getDashboardStats."""
    return await _restaurant_dashboard_impl(
        db, current_user, restaurant_id, period, from_date, to_date
    )


@router.get("/dashboard/restaurant", response_model=dict)
async def get_restaurant_dashboard(
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (defaults to current user's restaurant)"),
    period: Optional[str] = Query(None, description="Period alias: today, 7d, 30d, 12months"),
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get restaurant dashboard with analytics for specific restaurant
    
    - **Super Admin**: Can view any restaurant
    - **Restaurant User**: Can only view their restaurant
    """
    return await _restaurant_dashboard_impl(
        db, current_user, restaurant_id, period, from_date, to_date
    )


async def _restaurant_dashboard_impl(
    db: AsyncSession,
    current_user: User,
    restaurant_id: Optional[str],
    period: Optional[str],
    from_date: Optional[datetime],
    to_date: Optional[datetime],
):
    user_restaurant_id = _user_attr(current_user, "restaurant_id")
    
    if not _is_super_admin(current_user):
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id

    if not restaurant_id:
        raise HTTPException(status_code=400, detail="Restaurant ID required")

    if not from_date or not to_date:
        from_date, to_date = resolve_dashboard_dates(period)

    payload = await build_restaurant_dashboard(db, restaurant_id, from_date, to_date)
    return success_response(
        message="Restaurant dashboard retrieved successfully",
        data=payload,
    )
