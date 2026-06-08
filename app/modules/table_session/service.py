from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.order.model import Order, OrderStatus, PaymentStatus
from app.modules.order.schema import OrderUpdate
from app.modules.order.service import OrderService
from app.modules.table.model import Table, TableStatus
from app.modules.table.service import TableService
from app.modules.table_session.model import (
    TableSession,
    TableSessionStatus,
    TableTransfer,
    TableTransferStatus,
)
from app.modules.table_session.schema import (
    TableSessionCreate,
    TableTransferCreate,
    TableValidateResponse,
)


class TableSessionError(Exception):
    def __init__(self, message: str, code: str = "TABLE_SESSION_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


TERMINAL_ORDER_STATUSES = {
    OrderStatus.COMPLETED.value,
    OrderStatus.CANCELLED.value,
    OrderStatus.REFUNDED.value,
}
NON_EDITABLE_ORDER_STATUSES = TERMINAL_ORDER_STATUSES | {
    OrderStatus.PENDING_APPROVAL.value,
}
TERMINAL_PAYMENT_STATUSES = {PaymentStatus.PAID.value, PaymentStatus.REFUNDED.value}


class TableSessionService:
    @staticmethod
    def _session_to_dict(session: TableSession, table: Optional[Table] = None) -> dict:
        return {
            "id": session.id,
            "table_uuid": session.table_id,
            "restaurant_uuid": session.restaurant_id,
            "customer_uuid": session.customer_id,
            "active_order_uuid": session.active_order_id,
            "status": session.status.upper() if session.status else "ACTIVE",
            "started_at": session.started_at,
            "closed_at": session.closed_at,
            "table_number": table.table_number if table else None,
            "table_name": table.table_name if table else None,
        }

    @staticmethod
    def _transfer_to_dict(transfer: TableTransfer) -> dict:
        return {
            "id": transfer.id,
            "old_table_uuid": transfer.old_table_id,
            "new_table_uuid": transfer.new_table_id,
            "customer_uuid": transfer.customer_id,
            "restaurant_uuid": transfer.restaurant_id,
            "order_uuid": transfer.order_id,
            "status": transfer.status.upper().replace("_", "_"),
            "resolved_by": transfer.resolved_by,
            "resolved_at": transfer.resolved_at,
            "audit_log": transfer.audit_log,
            "created_at": transfer.created_at,
        }

    @staticmethod
    async def validate_table(
        db: AsyncSession,
        table_uuid: str,
        restaurant_id: Optional[str] = None,
    ) -> TableValidateResponse:
        table = await TableService.get_table_by_id(db, table_uuid)
        if not table:
            return TableValidateResponse(
                valid=False,
                table_uuid=table_uuid,
                restaurant_uuid=restaurant_id or "",
                error_code="INVALID_TABLE",
                message="Invalid table QR code.",
            )
        if restaurant_id and table.restaurant_id != restaurant_id:
            return TableValidateResponse(
                valid=False,
                table_uuid=table_uuid,
                restaurant_uuid=restaurant_id,
                error_code="RESTAURANT_MISMATCH",
                message="Table does not belong to this restaurant.",
            )
        if not table.is_active:
            return TableValidateResponse(
                valid=False,
                table_uuid=table_uuid,
                restaurant_uuid=table.restaurant_id,
                error_code="TABLE_INACTIVE",
                message="This table is not available for ordering.",
            )
        if table.status in (TableStatus.MAINTENANCE.value, TableStatus.MAINTENANCE):
            return TableValidateResponse(
                valid=False,
                table_uuid=table_uuid,
                restaurant_uuid=table.restaurant_id,
                error_code="TABLE_MAINTENANCE",
                message="This table is under maintenance.",
            )
        return TableValidateResponse(
            valid=True,
            table_uuid=table.id,
            restaurant_uuid=table.restaurant_id,
            table_number=table.table_number,
            table_name=table.table_name,
            table_status=table.status,
            is_active=table.is_active,
        )

    @staticmethod
    async def get_active_session_for_customer(
        db: AsyncSession,
        customer_id: str,
        restaurant_id: str,
    ) -> Optional[TableSession]:
        result = await db.execute(
            select(TableSession).where(
                and_(
                    TableSession.customer_id == customer_id,
                    TableSession.restaurant_id == restaurant_id,
                    TableSession.status == TableSessionStatus.ACTIVE.value,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_by_id(db: AsyncSession, session_id: str) -> Optional[TableSession]:
        result = await db.execute(select(TableSession).where(TableSession.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_restore_session(
        db: AsyncSession,
        payload: TableSessionCreate,
    ) -> Tuple[TableSession, Table]:
        validation = await TableSessionService.validate_table(
            db, payload.table_uuid, payload.restaurant_uuid
        )
        if not validation.valid:
            raise TableSessionError(
                validation.message or "Invalid table",
                code=validation.error_code or "INVALID_TABLE",
                status_code=404,
            )

        existing = await TableSessionService.get_active_session_for_customer(
            db, payload.customer_uuid, payload.restaurant_uuid
        )
        table = await TableService.get_table_by_id(db, payload.table_uuid)
        if not table:
            raise TableSessionError("Table not found", code="INVALID_TABLE", status_code=404)

        if existing:
            if existing.table_id != payload.table_uuid:
                raise TableSessionError(
                    "Customer already has an active session on another table",
                    code="ACTIVE_SESSION_MISMATCH",
                    status_code=409,
                )
            return existing, table

        session = TableSession(
            restaurant_id=payload.restaurant_uuid,
            table_id=payload.table_uuid,
            customer_id=payload.customer_uuid,
            status=TableSessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        if str(table.status) == TableStatus.AVAILABLE.value:
            await TableService.update_table_status(db, table.id, TableStatus.OCCUPIED)
        await db.commit()
        await db.refresh(session)
        return session, table

    @staticmethod
    async def close_session(
        db: AsyncSession,
        session_id: str,
        customer_id: str,
        restaurant_id: str,
    ) -> bool:
        session = await TableSessionService.get_session_by_id(db, session_id)
        if not session or session.customer_id != customer_id or session.restaurant_id != restaurant_id:
            return False
        session.status = TableSessionStatus.CLOSED.value
        session.closed_at = datetime.utcnow()
        await db.commit()
        return True

    @staticmethod
    async def set_active_order(
        db: AsyncSession,
        customer_id: str,
        restaurant_id: str,
        table_id: str,
        order_id: str,
    ) -> Optional[TableSession]:
        session = await TableSessionService.get_active_session_for_customer(
            db, customer_id, restaurant_id
        )
        if not session or session.table_id != table_id:
            return None
        session.active_order_id = order_id
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_active_order_for_table(
        db: AsyncSession,
        customer_id: str,
        restaurant_id: str,
        table_id: str,
    ) -> Optional[Order]:
        result = await db.execute(
            select(Order)
            .where(
                and_(
                    Order.customer_id == customer_id,
                    Order.restaurant_id == restaurant_id,
                    Order.table_id == table_id,
                )
            )
            .order_by(Order.updated_at.desc())
        )
        orders = result.scalars().all()
        for order in orders:
            if order.status in TERMINAL_ORDER_STATUSES:
                continue
            if order.payment_status in TERMINAL_PAYMENT_STATUSES:
                continue
            return order
        return None

    @staticmethod
    def is_order_editable(order: Order) -> bool:
        if order.payment_status in TERMINAL_PAYMENT_STATUSES:
            return False
        status = order.status.value if hasattr(order.status, "value") else str(order.status)
        if status in NON_EDITABLE_ORDER_STATUSES:
            return False
        return True

    @staticmethod
    def is_qr_table_order(order: Order) -> bool:
        return (order.source or "").lower() == "qr_table" and bool(order.table_id)

    @staticmethod
    async def request_bill(
        db: AsyncSession,
        order_id: str,
        customer_id: str,
        restaurant_id: str,
        table_id: str,
    ) -> Order:
        order = await OrderService.get_order_for_customer(db, order_id, customer_id, restaurant_id)
        if not order:
            raise TableSessionError("Order not found", code="ORDER_NOT_FOUND", status_code=404)
        if order.table_id != table_id:
            raise TableSessionError("Order is not linked to this table", code="TABLE_MISMATCH", status_code=400)
        if not TableSessionService.is_order_editable(order):
            raise TableSessionError("Order cannot be modified", code="ORDER_LOCKED", status_code=400)

        updated = await OrderService.update_order(
            db,
            order_id,
            OrderUpdate(
                status=OrderStatus.ON_HOLD,
                staff_notes=(order.staff_notes or "") + "\n[BILL_REQUESTED]",
            ),
        )
        if not updated:
            raise TableSessionError("Failed to update order", code="UPDATE_FAILED", status_code=500)
        reloaded = await OrderService.get_order_for_customer(
            db, order_id, customer_id, restaurant_id
        )
        return reloaded or updated

    @staticmethod
    def build_bill_summary(order: Order) -> dict:
        items = order.items or []
        subtotal = sum(int(i.total_price or 0) for i in items)
        tax = int(order.tax_amount or 0)
        discount = int(order.discount_amount or 0)
        service_charge = int(order.service_charge or 0)
        grand_total = int(order.total_amount or 0)
        status = order.status.value if hasattr(order.status, "value") else str(order.status)
        if "BILL_REQUESTED" in (order.staff_notes or ""):
            status = "bill_requested"
        return {
            "order_uuid": order.id,
            "order_number": order.order_number,
            "subtotal": subtotal,
            "tax": tax,
            "discount": discount,
            "service_charge": service_charge,
            "grand_total": grand_total,
            "items": [
                {
                    "id": i.id,
                    "name": i.product_name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total_price": i.total_price,
                }
                for i in items
            ],
            "status": status.upper(),
        }


class TableTransferService:
    @staticmethod
    async def get_transfer_by_id(db: AsyncSession, transfer_id: str) -> Optional[TableTransfer]:
        result = await db.execute(select(TableTransfer).where(TableTransfer.id == transfer_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_transfer(
        db: AsyncSession,
        payload: TableTransferCreate,
    ) -> TableTransfer:
        if payload.old_table_uuid == payload.new_table_uuid:
            raise TableSessionError("Cannot transfer to the same table", code="SAME_TABLE", status_code=400)

        old_table = await TableService.get_table_by_id(db, payload.old_table_uuid)
        new_table = await TableService.get_table_by_id(db, payload.new_table_uuid)
        if not old_table or not new_table:
            raise TableSessionError("Invalid table", code="INVALID_TABLE", status_code=404)
        if old_table.restaurant_id != payload.restaurant_uuid or new_table.restaurant_id != payload.restaurant_uuid:
            raise TableSessionError("Restaurant mismatch", code="RESTAURANT_MISMATCH", status_code=400)

        session = await TableSessionService.get_active_session_for_customer(
            db, payload.customer_uuid, payload.restaurant_uuid
        )
        if not session or session.table_id != payload.old_table_uuid:
            raise TableSessionError("No active session on source table", code="NO_SESSION", status_code=400)

        active_order = await TableSessionService.get_active_order_for_table(
            db, payload.customer_uuid, payload.restaurant_uuid, payload.old_table_uuid
        )

        transfer = TableTransfer(
            restaurant_id=payload.restaurant_uuid,
            customer_id=payload.customer_uuid,
            old_table_id=payload.old_table_uuid,
            new_table_id=payload.new_table_uuid,
            order_id=active_order.id if active_order else session.active_order_id,
            status=TableTransferStatus.PENDING_APPROVAL.value,
        )
        db.add(transfer)
        await db.commit()
        await db.refresh(transfer)
        return transfer

    @staticmethod
    async def resolve_transfer(
        db: AsyncSession,
        transfer_id: str,
        approve: bool,
        resolved_by: str,
    ) -> Optional[TableTransfer]:
        transfer = await TableTransferService.get_transfer_by_id(db, transfer_id)
        if not transfer:
            return None
        if transfer.status != TableTransferStatus.PENDING_APPROVAL.value:
            raise TableSessionError("Transfer already resolved", code="ALREADY_RESOLVED", status_code=400)

        transfer.status = (
            TableTransferStatus.APPROVED.value if approve else TableTransferStatus.REJECTED.value
        )
        transfer.resolved_by = resolved_by
        transfer.resolved_at = datetime.utcnow()
        transfer.audit_log = {
            "action": "approved" if approve else "rejected",
            "resolved_by": resolved_by,
            "resolved_at": transfer.resolved_at.isoformat(),
        }

        if approve:
            session = await TableSessionService.get_active_session_for_customer(
                db, transfer.customer_id, transfer.restaurant_id
            )
            if session and session.table_id == transfer.old_table_id:
                session.table_id = transfer.new_table_id
                session.status = TableSessionStatus.ACTIVE.value

            if transfer.order_id:
                order = await OrderService.get_order_by_id(db, transfer.order_id)
                if order:
                    await OrderService.update_order(
                        db,
                        order.id,
                        OrderUpdate(table_id=transfer.new_table_id),
                    )

            await TableService.update_table_status(db, transfer.old_table_id, TableStatus.AVAILABLE)
            await TableService.update_table_status(db, transfer.new_table_id, TableStatus.OCCUPIED)  # noqa: E501

        await db.commit()
        await db.refresh(transfer)
        return transfer

    @staticmethod
    async def list_pending_transfers(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[list[TableTransfer], int]:
        query = select(TableTransfer).where(
            and_(
                TableTransfer.restaurant_id == restaurant_id,
                TableTransfer.status == TableTransferStatus.PENDING_APPROVAL.value,
            )
        )
        count_result = await db.execute(select(TableTransfer.id).where(query.whereclause))
        total = len(count_result.scalars().all())
        result = await db.execute(
            query.order_by(TableTransfer.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total


class QrTableOrderService:
    """Staff approval for new QR table orders (not item appends)."""

    @staticmethod
    async def list_pending_orders(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[list[Order], int]:
        base = and_(
            Order.restaurant_id == restaurant_id,
            Order.status == OrderStatus.PENDING_APPROVAL.value,
            Order.source == "qr_table",
            Order.table_id.isnot(None),
        )
        count_result = await db.execute(select(func.count()).select_from(Order).where(base))
        total = int(count_result.scalar() or 0)
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(base)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def _get_pending_qr_order(db: AsyncSession, order_id: str) -> Optional[Order]:
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.id == order_id,
                Order.status == OrderStatus.PENDING_APPROVAL.value,
                Order.source == "qr_table",
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def approve_order(
        db: AsyncSession,
        order_id: str,
        resolved_by: str,
    ) -> Optional[Order]:
        order = await QrTableOrderService._get_pending_qr_order(db, order_id)
        if not order:
            return None

        note = f"\n[QR_ORDER_APPROVED by {resolved_by}]"
        updated = await OrderService.update_order(
            db,
            order_id,
            OrderUpdate(
                status=OrderStatus.PENDING,
                staff_notes=(order.staff_notes or "") + note,
            ),
        )
        return updated

    @staticmethod
    async def reject_order(
        db: AsyncSession,
        order_id: str,
        resolved_by: str,
    ) -> Optional[Order]:
        order = await QrTableOrderService._get_pending_qr_order(db, order_id)
        if not order:
            return None

        note = f"\n[QR_ORDER_REJECTED by {resolved_by}]"
        updated = await OrderService.update_order(
            db,
            order_id,
            OrderUpdate(
                status=OrderStatus.CANCELLED,
                staff_notes=(order.staff_notes or "") + note,
            ),
        )

        if order.customer_id and order.table_id:
            session = await TableSessionService.get_active_session_for_customer(
                db, order.customer_id, order.restaurant_id
            )
            if session and session.active_order_id == order_id:
                session.active_order_id = None
                await db.commit()

        return updated
