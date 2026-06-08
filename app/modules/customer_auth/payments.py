"""Customer-facing payment helpers (PhonePe init/status, table payment recording)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.customer.model import Customer
from app.modules.order.model import Order
from app.modules.order.service import OrderService

# Dev / stub PhonePe transaction store (replace with gateway integration in production)
_PHONEPE_TXNS: Dict[str, Dict[str, Any]] = {}


class CustomerPaymentError(Exception):
    def __init__(self, message: str, code: str = "PAYMENT_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


async def init_phonepe_payment(
    db: AsyncSession,
    customer: Customer,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    restaurant_id = str(payload.get("restaurant_id") or customer.restaurant_id)
    if restaurant_id != customer.restaurant_id:
        raise CustomerPaymentError("Restaurant mismatch", "FORBIDDEN", 403)

    amount = int(payload.get("amount") or 0)
    if amount <= 0:
        raise CustomerPaymentError("Invalid amount", "INVALID_AMOUNT", 400)

    merchant_txn_id = str(payload.get("merchant_transaction_id") or uuid.uuid4())
    redirect_url = str(payload.get("redirect_url") or "")

    _PHONEPE_TXNS[merchant_txn_id] = {
        "status": "PENDING",
        "amount": amount,
        "customer_id": customer.id,
        "restaurant_id": restaurant_id,
        "mobile_number": payload.get("mobile_number"),
        "created_at": datetime.utcnow().isoformat(),
    }

    # Development: bounce back to client checkout for status verification
    if settings.is_development and redirect_url:
        sep = "&" if "?" in redirect_url else "?"
        redirect_url = (
            f"{redirect_url}{sep}phonepe_return=1&merchantTransactionId={merchant_txn_id}"
        )

    return {
        "merchant_transaction_id": merchant_txn_id,
        "redirect_url": redirect_url,
        "payment_url": redirect_url,
        "instrumentResponse": {
            "type": "PAY_PAGE",
            "redirectInfo": {"url": redirect_url, "method": "GET"},
        },
    }


async def phonepe_payment_status(
    merchant_txn_id: str,
    customer: Customer,
) -> Optional[Dict[str, Any]]:
    rec = _PHONEPE_TXNS.get(merchant_txn_id)
    if not rec or rec.get("customer_id") != customer.id:
        return None
    if settings.is_development and rec.get("status") == "PENDING":
        rec["status"] = "COMPLETED"
    return {
        "status": rec.get("status", "PENDING"),
        "merchant_transaction_id": merchant_txn_id,
        "amount": rec.get("amount"),
    }


async def record_table_payment(
    db: AsyncSession,
    customer: Customer,
    order_id: str,
    payment_method: str,
    *,
    mark_paid: bool = False,
) -> Order:
    order = await OrderService.get_order_for_customer(
        db, order_id, customer.id, customer.restaurant_id
    )
    if not order:
        raise CustomerPaymentError("Order not found", "NOT_FOUND", 404)

    from app.modules.order.model import PaymentMethod, PaymentStatus
    from app.modules.order.schema import OrderUpdate

    method_map = {
        "cash": PaymentMethod.CASH,
        "card": PaymentMethod.CARD,
        "upi": PaymentMethod.UPI,
        "wallet": PaymentMethod.DIGITAL_WALLET,
        "phonepe": PaymentMethod.UPI,
    }
    normalized = method_map.get(payment_method.lower(), PaymentMethod.CASH)
    status = PaymentStatus.PAID if mark_paid else PaymentStatus.PENDING

    updated = await OrderService.update_order(
        db,
        order_id,
        OrderUpdate(
            payment_method=normalized,
            payment_status=status,
        ),
    )
    if not updated:
        raise CustomerPaymentError("Could not update payment", "UPDATE_FAILED", 500)
    return updated
