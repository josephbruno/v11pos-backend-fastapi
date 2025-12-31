from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import create_response
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

router = APIRouter(prefix="/api/v1/reports", tags=["Reports & Analytics"])


# Sales Reports

@router.post("/sales/generate", response_model=dict)
async def generate_sales_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate sales report (Daily/Monthly)
    
    - **Super Admin**: Can generate for specific restaurant or all restaurants
    - **Restaurant User**: Can only generate for their restaurant
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    # Validate restaurant access
    if user_role != "super_admin":
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
                generated_by=current_user.get("id")
            )
        else:
            report = await SalesReportService.generate_monthly_sales_report(
                db=db,
                from_date=request.from_date,
                to_date=request.to_date,
                restaurant_id=request.restaurant_id,
                generated_by=current_user.get("id")
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
        
        return create_response(
            success=True,
            message="Sales report generated successfully",
            data=SalesReportResponse.model_validate(report)
        )
    
    raise HTTPException(status_code=400, detail="Invalid report type")


@router.get("/sales/{report_id}", response_model=dict)
async def get_sales_report(
    report_id: str = Path(..., description="Sales report ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sales report by ID"""
    
    report = await SalesReportService.get_sales_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Sales report not found")
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if report.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return create_response(
        success=True,
        message="Sales report retrieved successfully",
        data=SalesReportResponse.model_validate(report)
    )


@router.get("/sales", response_model=dict)
async def list_sales_reports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List sales reports with pagination
    
    - **Super Admin**: Can view all reports or filter by restaurant
    - **Restaurant User**: Can only view their restaurant reports
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        restaurant_id = user_restaurant_id
    
    reports, total = await SalesReportService.list_sales_reports(
        db=db,
        restaurant_id=restaurant_id,
        report_type=report_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    
    return create_response(
        success=True,
        message="Sales reports retrieved successfully",
        data=SalesReportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=[SalesReportResponse.model_validate(r) for r in reports]
        )
    )


@router.patch("/sales/{report_id}", response_model=dict)
async def update_sales_report(
    report_id: str = Path(..., description="Sales report ID"),
    update_data: SalesReportUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update sales report"""
    
    # Check if report exists and user has access
    report = await SalesReportService.get_sales_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Sales report not found")
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if report.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Update
    updated_report = await SalesReportService.update_sales_report(db, report_id, update_data)
    
    return create_response(
        success=True,
        message="Sales report updated successfully",
        data=SalesReportResponse.model_validate(updated_report)
    )


@router.delete("/sales/{report_id}", response_model=dict)
async def delete_sales_report(
    report_id: str = Path(..., description="Sales report ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete sales report"""
    
    # Check if report exists and user has access
    report = await SalesReportService.get_sales_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Sales report not found")
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if report.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete
    success = await SalesReportService.delete_sales_report(db, report_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete sales report")
    
    return create_response(
        success=True,
        message="Sales report deleted successfully",
        data={"deleted": True}
    )


# Item-wise Sales Reports

@router.post("/items/generate", response_model=dict)
async def generate_item_wise_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate item-wise sales report
    
    - **Super Admin**: Can generate for specific restaurant or all restaurants
    - **Restaurant User**: Can only generate for their restaurant
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    reports = await ItemWiseSalesReportService.generate_item_wise_report(
        db=db,
        from_date=from_date,
        to_date=to_date,
        restaurant_id=restaurant_id
    )
    
    return create_response(
        success=True,
        message=f"Item-wise sales report generated for {len(reports)} items",
        data=[ItemWiseSalesReportResponse.model_validate(r) for r in reports]
    )


@router.get("/items", response_model=dict)
async def list_item_wise_reports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List item-wise sales reports
    
    - **Super Admin**: Can view all reports or filter by restaurant
    - **Restaurant User**: Can only view their restaurant reports
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        restaurant_id = user_restaurant_id
    
    reports, total = await ItemWiseSalesReportService.list_item_wise_reports(
        db=db,
        restaurant_id=restaurant_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    
    return create_response(
        success=True,
        message="Item-wise sales reports retrieved successfully",
        data=ItemWiseSalesReportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=[ItemWiseSalesReportResponse.model_validate(r) for r in reports]
        )
    )


# Category-wise Sales Reports

@router.post("/categories/generate", response_model=dict)
async def generate_category_wise_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate category-wise sales report
    
    - **Super Admin**: Can generate for specific restaurant or all restaurants
    - **Restaurant User**: Can only generate for their restaurant
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    reports = await CategoryWiseSalesReportService.generate_category_wise_report(
        db=db,
        from_date=from_date,
        to_date=to_date,
        restaurant_id=restaurant_id
    )
    
    return create_response(
        success=True,
        message=f"Category-wise sales report generated for {len(reports)} categories",
        data=[CategoryWiseSalesReportResponse.model_validate(r) for r in reports]
    )


@router.get("/categories", response_model=dict)
async def list_category_wise_reports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List category-wise sales reports
    
    - **Super Admin**: Can view all reports or filter by restaurant
    - **Restaurant User**: Can only view their restaurant reports
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        restaurant_id = user_restaurant_id
    
    reports, total = await CategoryWiseSalesReportService.list_category_wise_reports(
        db=db,
        restaurant_id=restaurant_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    
    return create_response(
        success=True,
        message="Category-wise sales reports retrieved successfully",
        data=CategoryWiseSalesReportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=[CategoryWiseSalesReportResponse.model_validate(r) for r in reports]
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
    current_user: dict = Depends(get_current_user)
):
    """
    Get payment mode report
    
    Shows breakdown of revenue by payment methods (Cash, Card, UPI, Wallet, etc.)
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement payment mode report service
    
    return create_response(
        success=True,
        message="Payment mode report retrieved successfully",
        data={"message": "Payment mode report - to be implemented"}
    )


@router.get("/tax-gst", response_model=dict)
async def get_tax_gst_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get tax (GST) report
    
    Shows breakdown of taxes: CGST, SGST, IGST, VAT, Service Tax
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement tax report service
    
    return create_response(
        success=True,
        message="Tax report retrieved successfully",
        data={"message": "Tax (GST) report - to be implemented"}
    )


@router.get("/discounts-offers", response_model=dict)
async def get_discounts_offers_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get discounts & offers report
    
    Shows breakdown by discount types: Coupons, Loyalty, Promotional, Staff
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement discount report service
    
    return create_response(
        success=True,
        message="Discounts & offers report retrieved successfully",
        data={"message": "Discounts & offers report - to be implemented"}
    )


@router.get("/cancelled-void", response_model=dict)
async def get_cancelled_void_report(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get cancelled/void orders report
    
    Shows cancelled orders, void orders, and refunds with reasons
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement cancelled/void report service
    
    return create_response(
        success=True,
        message="Cancelled/void orders report retrieved successfully",
        data={"message": "Cancelled/void orders report - to be implemented"}
    )


@router.get("/profit-cost", response_model=dict)
async def get_profit_cost_analysis(
    from_date: datetime = Query(..., description="From date"),
    to_date: datetime = Query(..., description="To date"),
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (super admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get profit & cost analysis report
    
    Shows revenue, costs, profit margins with category and item breakdown
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    # TODO: Implement profit/cost analysis service
    
    return create_response(
        success=True,
        message="Profit & cost analysis retrieved successfully",
        data={"message": "Profit & cost analysis - to be implemented"}
    )


# Super Admin Dashboard

@router.get("/dashboard/super-admin", response_model=dict)
async def get_super_admin_dashboard(
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get super admin dashboard with aggregated analytics across all restaurants
    
    **Super Admin Only**
    """
    
    # Check permissions
    user_role = current_user.get("role")
    
    if user_role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    # Set default date range if not provided
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    # TODO: Implement super admin dashboard aggregation
    
    return create_response(
        success=True,
        message="Super admin dashboard retrieved successfully",
        data={
            "message": "Super admin dashboard - to be implemented",
            "from_date": from_date,
            "to_date": to_date
        }
    )


@router.get("/dashboard/restaurant", response_model=dict)
async def get_restaurant_dashboard(
    restaurant_id: Optional[str] = Query(None, description="Restaurant ID (defaults to current user's restaurant)"),
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get restaurant dashboard with analytics for specific restaurant
    
    - **Super Admin**: Can view any restaurant
    - **Restaurant User**: Can only view their restaurant
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id and restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restaurant_id = user_restaurant_id
    
    if not restaurant_id:
        raise HTTPException(status_code=400, detail="Restaurant ID required")
    
    # Set default date range if not provided
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    # TODO: Implement restaurant dashboard
    
    return create_response(
        success=True,
        message="Restaurant dashboard retrieved successfully",
        data={
            "message": "Restaurant dashboard - to be implemented",
            "restaurant_id": restaurant_id,
            "from_date": from_date,
            "to_date": to_date
        }
    )
