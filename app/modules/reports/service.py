from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from app.modules.reports.model import (
    SalesReport, ItemWiseSalesReport, CategoryWiseSalesReport,
    ReportSchedule, ReportExport, ReportType, ReportStatus, ReportFormat
)
from app.modules.reports.schema import (
    SalesReportCreate, SalesReportUpdate,
    ItemWiseSalesReportCreate, CategoryWiseSalesReportCreate,
    ReportScheduleCreate, ReportScheduleUpdate,
    ReportExportCreate, ReportGenerateRequest,
    PaymentModeReportResponse, TaxReportResponse, DiscountOfferReportResponse,
    CancelledVoidReportResponse, ProfitCostAnalysisResponse
)
from app.modules.order.model import Order, OrderItem
from app.modules.product.model import Product, Category
from app.core.response import create_response


class SalesReportService:
    """Service for sales reports"""
    
    @staticmethod
    async def generate_daily_sales_report(
        db: AsyncSession,
        from_date: datetime,
        to_date: datetime,
        restaurant_id: Optional[str] = None,
        generated_by: Optional[str] = None
    ) -> SalesReport:
        """Generate daily sales report"""
        
        # Build base query
        query = select(Order).where(
            and_(
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.deleted_at.is_(None)
            )
        )
        
        # Filter by restaurant if specified
        if restaurant_id:
            query = query.where(Order.restaurant_id == restaurant_id)
        
        # Execute query
        result = await db.execute(query)
        orders = result.scalars().all()
        
        # Calculate metrics
        report_data = await SalesReportService._calculate_sales_metrics(db, orders, from_date, to_date, restaurant_id)
        
        # Create report
        report_number = f"SR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        report = SalesReport(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            report_number=report_number,
            report_type=ReportType.DAILY_SALES,
            report_name=f"Daily Sales Report - {from_date.strftime('%Y-%m-%d')}",
            report_date=datetime.utcnow(),
            from_date=from_date,
            to_date=to_date,
            period_type="day",
            period_value=from_date.strftime('%Y-%m-%d'),
            generated_by=generated_by,
            **report_data
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        return report
    
    @staticmethod
    async def generate_monthly_sales_report(
        db: AsyncSession,
        from_date: datetime,
        to_date: datetime,
        restaurant_id: Optional[str] = None,
        generated_by: Optional[str] = None
    ) -> SalesReport:
        """Generate monthly sales report"""
        
        # Build base query
        query = select(Order).where(
            and_(
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.deleted_at.is_(None)
            )
        )
        
        # Filter by restaurant if specified
        if restaurant_id:
            query = query.where(Order.restaurant_id == restaurant_id)
        
        # Execute query
        result = await db.execute(query)
        orders = result.scalars().all()
        
        # Calculate metrics
        report_data = await SalesReportService._calculate_sales_metrics(db, orders, from_date, to_date, restaurant_id)
        
        # Create report
        report_number = f"SR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        report = SalesReport(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            report_number=report_number,
            report_type=ReportType.MONTHLY_SALES,
            report_name=f"Monthly Sales Report - {from_date.strftime('%B %Y')}",
            report_date=datetime.utcnow(),
            from_date=from_date,
            to_date=to_date,
            period_type="month",
            period_value=from_date.strftime('%Y-%m'),
            generated_by=generated_by,
            **report_data
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        return report
    
    @staticmethod
    async def _calculate_sales_metrics(
        db: AsyncSession,
        orders: List[Order],
        from_date: datetime,
        to_date: datetime,
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate sales metrics from orders"""
        
        # Initialize counters
        metrics = {
            "total_sales": 0,
            "gross_sales": 0,
            "net_sales": 0,
            "total_orders": len(orders),
            "completed_orders": 0,
            "cancelled_orders": 0,
            "void_orders": 0,
            "dine_in_orders": 0,
            "takeaway_orders": 0,
            "delivery_orders": 0,
            "online_orders": 0,
            "dine_in_revenue": 0,
            "takeaway_revenue": 0,
            "delivery_revenue": 0,
            "online_revenue": 0,
            "total_tax": 0,
            "cgst_amount": 0,
            "sgst_amount": 0,
            "igst_amount": 0,
            "vat_amount": 0,
            "service_tax": 0,
            "total_discount": 0,
            "coupon_discount": 0,
            "loyalty_discount": 0,
            "promotional_discount": 0,
            "staff_discount": 0,
            "delivery_charges": 0,
            "service_charges": 0,
            "packaging_charges": 0,
            "convenience_fees": 0,
            "total_tips": 0,
            "rounding_amount": 0,
            "cash_payments": 0,
            "card_payments": 0,
            "upi_payments": 0,
            "wallet_payments": 0,
            "online_payments": 0,
            "credit_payments": 0,
            "total_refunds": 0,
            "refund_count": 0,
            "total_customers": 0,
            "new_customers": 0,
            "returning_customers": 0,
            "guest_customers": 0,
            "total_items_sold": 0,
            "unique_items_sold": 0,
            "complimentary_items": 0,
            "total_cost": 0,
            "gross_profit": 0,
            "is_consolidated": restaurant_id is None
        }
        
        # Track unique items
        unique_items = set()
        customer_ids = set()
        
        # Process each order
        for order in orders:
            # Order status
            if order.status == "completed":
                metrics["completed_orders"] += 1
            elif order.status == "cancelled":
                metrics["cancelled_orders"] += 1
            elif order.status == "void":
                metrics["void_orders"] += 1
            
            # Order type
            order_type = getattr(order, "order_type", None)
            if order_type == "dine_in":
                metrics["dine_in_orders"] += 1
                metrics["dine_in_revenue"] += order.total_amount or 0
            elif order_type == "takeaway":
                metrics["takeaway_orders"] += 1
                metrics["takeaway_revenue"] += order.total_amount or 0
            elif order_type == "delivery":
                metrics["delivery_orders"] += 1
                metrics["delivery_revenue"] += order.total_amount or 0
            elif order_type == "online":
                metrics["online_orders"] += 1
                metrics["online_revenue"] += order.total_amount or 0
            
            # Revenue
            if order.status == "completed":
                metrics["total_sales"] += order.total_amount or 0
                metrics["gross_sales"] += (order.subtotal_amount or 0)
                metrics["net_sales"] += order.final_amount or 0
            
            # Tax
            metrics["total_tax"] += order.tax_amount or 0
            metrics["cgst_amount"] += getattr(order, "cgst_amount", 0) or 0
            metrics["sgst_amount"] += getattr(order, "sgst_amount", 0) or 0
            metrics["igst_amount"] += getattr(order, "igst_amount", 0) or 0
            
            # Discounts
            metrics["total_discount"] += order.discount_amount or 0
            metrics["coupon_discount"] += getattr(order, "coupon_discount", 0) or 0
            metrics["loyalty_discount"] += getattr(order, "loyalty_discount", 0) or 0
            
            # Additional charges
            metrics["delivery_charges"] += getattr(order, "delivery_charges", 0) or 0
            metrics["service_charges"] += getattr(order, "service_charge", 0) or 0
            metrics["packaging_charges"] += getattr(order, "packaging_charges", 0) or 0
            
            # Tips
            metrics["total_tips"] += getattr(order, "tip_amount", 0) or 0
            metrics["rounding_amount"] += getattr(order, "rounding_amount", 0) or 0
            
            # Payment methods
            payment_method = getattr(order, "payment_method", None)
            payment_amount = order.paid_amount or 0
            
            if payment_method == "cash":
                metrics["cash_payments"] += payment_amount
            elif payment_method == "card":
                metrics["card_payments"] += payment_amount
            elif payment_method == "upi":
                metrics["upi_payments"] += payment_amount
            elif payment_method == "wallet":
                metrics["wallet_payments"] += payment_amount
            elif payment_method == "online":
                metrics["online_payments"] += payment_amount
            elif payment_method == "credit":
                metrics["credit_payments"] += payment_amount
            
            # Refunds
            if getattr(order, "is_refunded", False):
                metrics["refund_count"] += 1
                metrics["total_refunds"] += getattr(order, "refund_amount", 0) or 0
            
            # Customers
            customer_id = getattr(order, "customer_id", None)
            if customer_id:
                customer_ids.add(customer_id)
            else:
                metrics["guest_customers"] += 1
            
            # Items - need to fetch order items
            items_query = select(OrderItem).where(
                and_(
                    OrderItem.order_id == order.id,
                    OrderItem.deleted_at.is_(None)
                )
            )
            items_result = await db.execute(items_query)
            order_items = items_result.scalars().all()
            
            for item in order_items:
                metrics["total_items_sold"] += item.quantity or 0
                
                if item.product_id:
                    unique_items.add(item.product_id)
                
                if getattr(item, "is_complimentary", False):
                    metrics["complimentary_items"] += item.quantity or 0
                
                # Cost (if available)
                item_cost = getattr(item, "cost_price", 0) or 0
                metrics["total_cost"] += item_cost * (item.quantity or 0)
        
        # Calculate derived metrics
        metrics["unique_items_sold"] = len(unique_items)
        metrics["total_customers"] = len(customer_ids) + metrics["guest_customers"]
        metrics["gross_profit"] = metrics["gross_sales"] - metrics["total_cost"]
        
        if metrics["gross_sales"] > 0:
            metrics["profit_margin"] = round((metrics["gross_profit"] / metrics["gross_sales"]) * 100, 2)
        
        if metrics["total_orders"] > 0:
            metrics["average_order_value"] = metrics["total_sales"] // metrics["total_orders"]
            metrics["average_items_per_order"] = round(metrics["total_items_sold"] / metrics["total_orders"], 2)
        
        if metrics["total_customers"] > 0:
            metrics["average_customer_spend"] = metrics["total_sales"] // metrics["total_customers"]
        
        return metrics
    
    @staticmethod
    async def get_sales_report_by_id(db: AsyncSession, report_id: str) -> Optional[SalesReport]:
        """Get sales report by ID"""
        query = select(SalesReport).where(
            and_(
                SalesReport.id == report_id,
                SalesReport.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_sales_reports(
        db: AsyncSession,
        restaurant_id: Optional[str] = None,
        report_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[SalesReport], int]:
        """List sales reports with pagination"""
        
        # Build query
        query = select(SalesReport).where(SalesReport.deleted_at.is_(None))
        
        if restaurant_id:
            query = query.where(SalesReport.restaurant_id == restaurant_id)
        
        if report_type:
            query = query.where(SalesReport.report_type == report_type)
        
        if from_date:
            query = query.where(SalesReport.from_date >= from_date)
        
        if to_date:
            query = query.where(SalesReport.to_date <= to_date)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.order_by(desc(SalesReport.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return reports, total
    
    @staticmethod
    async def update_sales_report(
        db: AsyncSession,
        report_id: str,
        update_data: SalesReportUpdate
    ) -> Optional[SalesReport]:
        """Update sales report"""
        
        report = await SalesReportService.get_sales_report_by_id(db, report_id)
        if not report:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(report, field, value)
        
        await db.commit()
        await db.refresh(report)
        
        return report
    
    @staticmethod
    async def delete_sales_report(db: AsyncSession, report_id: str) -> bool:
        """Soft delete sales report"""
        
        report = await SalesReportService.get_sales_report_by_id(db, report_id)
        if not report:
            return False
        
        report.deleted_at = datetime.utcnow()
        await db.commit()
        
        return True


class ItemWiseSalesReportService:
    """Service for item-wise sales reports"""
    
    @staticmethod
    async def generate_item_wise_report(
        db: AsyncSession,
        from_date: datetime,
        to_date: datetime,
        restaurant_id: Optional[str] = None,
        sales_report_id: Optional[str] = None
    ) -> List[ItemWiseSalesReport]:
        """Generate item-wise sales report"""
        
        # Query order items
        query = select(OrderItem).join(Order).where(
            and_(
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.status == "completed",
                Order.deleted_at.is_(None),
                OrderItem.deleted_at.is_(None)
            )
        )
        
        if restaurant_id:
            query = query.where(Order.restaurant_id == restaurant_id)
        
        result = await db.execute(query)
        order_items = result.scalars().all()
        
        # Group by product
        product_data = {}
        
        for item in order_items:
            product_id = item.product_id
            if not product_id:
                continue
            
            if product_id not in product_data:
                product_data[product_id] = {
                    "items": [],
                    "product_name": item.product_name or "Unknown",
                    "category_id": None,
                    "category_name": None
                }
            
            product_data[product_id]["items"].append(item)
        
        # Create reports for each product
        reports = []
        
        for product_id, data in product_data.items():
            items = data["items"]
            
            # Calculate metrics
            quantity_sold = sum(item.quantity or 0 for item in items)
            total_revenue = sum(item.total_price or 0 for item in items)
            gross_revenue = sum(item.subtotal_price or 0 for item in items)
            total_discount = sum(item.discount_amount or 0 for item in items)
            total_tax = sum(item.tax_amount or 0 for item in items)
            net_revenue = total_revenue - total_discount
            
            # Cost and profit
            total_cost = sum((getattr(item, "cost_price", 0) or 0) * (item.quantity or 0) for item in items)
            gross_profit = gross_revenue - total_cost
            profit_margin = round((gross_profit / gross_revenue * 100), 2) if gross_revenue > 0 else 0
            
            # Pricing
            prices = [item.unit_price or 0 for item in items if item.unit_price]
            average_selling_price = sum(prices) // len(prices) if prices else 0
            min_selling_price = min(prices) if prices else None
            max_selling_price = max(prices) if prices else None
            
            # Order statistics
            order_count = len(set(item.order_id for item in items))
            average_quantity_per_order = round(quantity_sold / order_count, 2) if order_count > 0 else 0
            
            # Create report
            report = ItemWiseSalesReport(
                id=str(uuid.uuid4()),
                sales_report_id=sales_report_id,
                restaurant_id=restaurant_id,
                product_id=product_id,
                from_date=from_date,
                to_date=to_date,
                product_name=data["product_name"],
                category_id=data.get("category_id"),
                category_name=data.get("category_name"),
                quantity_sold=quantity_sold,
                total_revenue=total_revenue,
                gross_revenue=gross_revenue,
                net_revenue=net_revenue,
                average_selling_price=average_selling_price,
                min_selling_price=min_selling_price,
                max_selling_price=max_selling_price,
                total_cost=total_cost,
                average_cost=total_cost // quantity_sold if quantity_sold > 0 else 0,
                gross_profit=gross_profit,
                profit_margin=profit_margin,
                total_discount=total_discount,
                discount_count=sum(1 for item in items if (item.discount_amount or 0) > 0),
                total_tax=total_tax,
                order_count=order_count,
                average_quantity_per_order=average_quantity_per_order
            )
            
            db.add(report)
            reports.append(report)
        
        await db.commit()
        
        return reports
    
    @staticmethod
    async def list_item_wise_reports(
        db: AsyncSession,
        restaurant_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[ItemWiseSalesReport], int]:
        """List item-wise sales reports"""
        
        query = select(ItemWiseSalesReport).where(ItemWiseSalesReport.id.isnot(None))
        
        if restaurant_id:
            query = query.where(ItemWiseSalesReport.restaurant_id == restaurant_id)
        
        if from_date:
            query = query.where(ItemWiseSalesReport.from_date >= from_date)
        
        if to_date:
            query = query.where(ItemWiseSalesReport.to_date <= to_date)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Pagination
        query = query.order_by(desc(ItemWiseSalesReport.quantity_sold))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return reports, total


class CategoryWiseSalesReportService:
    """Service for category-wise sales reports"""
    
    @staticmethod
    async def generate_category_wise_report(
        db: AsyncSession,
        from_date: datetime,
        to_date: datetime,
        restaurant_id: Optional[str] = None,
        sales_report_id: Optional[str] = None
    ) -> List[CategoryWiseSalesReport]:
        """Generate category-wise sales report"""
        
        # Query order items with product and category info
        query = select(OrderItem, Product, Category).join(
            Order, OrderItem.order_id == Order.id
        ).outerjoin(
            Product, OrderItem.product_id == Product.id
        ).outerjoin(
            Category, Product.category_id == Category.id
        ).where(
            and_(
                Order.created_at >= from_date,
                Order.created_at <= to_date,
                Order.status == "completed",
                Order.deleted_at.is_(None),
                OrderItem.deleted_at.is_(None)
            )
        )
        
        if restaurant_id:
            query = query.where(Order.restaurant_id == restaurant_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Group by category
        category_data = {}
        
        for item, product, category in rows:
            if not category:
                continue
            
            category_id = category.id
            
            if category_id not in category_data:
                category_data[category_id] = {
                    "items": [],
                    "category_name": category.name,
                    "parent_category_id": getattr(category, "parent_id", None)
                }
            
            category_data[category_id]["items"].append(item)
        
        # Create reports
        reports = []
        
        for category_id, data in category_data.items():
            items = data["items"]
            
            # Calculate metrics
            total_items_sold = sum(item.quantity or 0 for item in items)
            unique_items_count = len(set(item.product_id for item in items if item.product_id))
            total_revenue = sum(item.total_price or 0 for item in items)
            gross_revenue = sum(item.subtotal_price or 0 for item in items)
            total_discount = sum(item.discount_amount or 0 for item in items)
            total_tax = sum(item.tax_amount or 0 for item in items)
            net_revenue = total_revenue - total_discount
            
            # Cost and profit
            total_cost = sum((getattr(item, "cost_price", 0) or 0) * (item.quantity or 0) for item in items)
            gross_profit = gross_revenue - total_cost
            profit_margin = round((gross_profit / gross_revenue * 100), 2) if gross_revenue > 0 else 0
            
            # Order statistics
            order_count = len(set(item.order_id for item in items))
            average_items_per_order = round(total_items_sold / order_count, 2) if order_count > 0 else 0
            
            # Create report
            report = CategoryWiseSalesReport(
                id=str(uuid.uuid4()),
                sales_report_id=sales_report_id,
                restaurant_id=restaurant_id,
                category_id=category_id,
                from_date=from_date,
                to_date=to_date,
                category_name=data["category_name"],
                parent_category_id=data.get("parent_category_id"),
                total_items_sold=total_items_sold,
                unique_items_count=unique_items_count,
                total_revenue=total_revenue,
                gross_revenue=gross_revenue,
                net_revenue=net_revenue,
                total_cost=total_cost,
                gross_profit=gross_profit,
                profit_margin=profit_margin,
                total_discount=total_discount,
                total_tax=total_tax,
                order_count=order_count,
                average_items_per_order=average_items_per_order
            )
            
            db.add(report)
            reports.append(report)
        
        await db.commit()
        
        return reports
    
    @staticmethod
    async def list_category_wise_reports(
        db: AsyncSession,
        restaurant_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[CategoryWiseSalesReport], int]:
        """List category-wise sales reports"""
        
        query = select(CategoryWiseSalesReport).where(CategoryWiseSalesReport.id.isnot(None))
        
        if restaurant_id:
            query = query.where(CategoryWiseSalesReport.restaurant_id == restaurant_id)
        
        if from_date:
            query = query.where(CategoryWiseSalesReport.from_date >= from_date)
        
        if to_date:
            query = query.where(CategoryWiseSalesReport.to_date <= to_date)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Pagination
        query = query.order_by(desc(CategoryWiseSalesReport.total_revenue))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return reports, total
