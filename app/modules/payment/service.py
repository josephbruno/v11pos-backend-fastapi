from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.order.model import Order, PaymentStatus
from app.modules.payment.model import OrderPayment
from app.modules.payment.schema import OrderPaymentCreate, OrderPaymentUpdate


class OrderPaymentService:
    @staticmethod
    async def create_pending_payment_for_order(
        db: AsyncSession,
        *,
        order_id: str,
        restaurant_id: str,
        amount: int,
        currency: str = "INR",
        created_by: Optional[str] = None,
    ) -> OrderPayment:
        row = OrderPayment(
            order_id=order_id,
            restaurant_id=restaurant_id,
            amount=amount,
            currency=currency,
            payment_status=PaymentStatus.PENDING,
            created_by=created_by,
        )
        db.add(row)
        await db.flush()
        await db.refresh(row)
        return row

    @staticmethod
    async def list_for_order(db: AsyncSession, order_id: str) -> List[OrderPayment]:
        result = await db.execute(
            select(OrderPayment)
            .where(OrderPayment.order_id == order_id)
            .order_by(OrderPayment.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, payment_id: str) -> Optional[OrderPayment]:
        return await db.get(OrderPayment, payment_id)

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        data: OrderPaymentCreate,
        created_by: Optional[str] = None,
    ) -> Optional[OrderPayment]:
        order = await db.get(Order, data.order_id)
        if not order or order.restaurant_id != data.restaurant_id:
            return None

        status = data.payment_status or PaymentStatus.PENDING
        row = OrderPayment(
            order_id=data.order_id,
            restaurant_id=data.restaurant_id,
            amount=data.amount,
            currency=data.currency,
            payment_status=status,
            payment_method=data.payment_method,
            gateway=data.gateway,
            gateway_transaction_id=data.gateway_transaction_id,
            payment_reference=data.payment_reference,
            notes=data.notes,
            extra_metadata=data.payment_metadata,
            created_by=created_by,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def update_payment(
        db: AsyncSession,
        payment_id: str,
        data: OrderPaymentUpdate,
    ) -> Optional[OrderPayment]:
        row = await db.get(OrderPayment, payment_id)
        if not row:
            return None

        patch = data.model_dump(exclude_unset=True)
        if "payment_metadata" in patch:
            row.extra_metadata = patch.pop("payment_metadata")
        for key, val in patch.items():
            setattr(row, key, val)

        await db.commit()
        await db.refresh(row)
        return row
