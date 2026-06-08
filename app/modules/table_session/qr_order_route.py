from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import error_response, success_response
from app.modules.order.schema import OrderItemResponse, OrderResponse
from app.modules.table_session.service import QrTableOrderService
from app.modules.user.model import User

router = APIRouter(prefix="/qr-table-orders", tags=["QR Table Orders"])


def _order_payload(order) -> dict:
    resp = OrderResponse.model_validate(order)
    resp.items = [OrderItemResponse.model_validate(i) for i in (order.items or [])]
    return resp.model_dump()


@router.get("/restaurant/{restaurant_id}/pending", response_model=None)
async def list_pending_qr_orders(
    restaurant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staff: QR table orders awaiting waiter/cashier approval before kitchen."""
    orders, total = await QrTableOrderService.list_pending_orders(
        db, restaurant_id, skip=skip, limit=limit
    )
    return success_response(
        message="Pending QR table orders retrieved",
        data={
            "orders": [_order_payload(o) for o in orders],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    )


@router.patch("/{order_id}/approve", response_model=None)
async def approve_qr_table_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await QrTableOrderService.approve_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    from app.modules.order.service import OrderService

    full = await OrderService.get_order_by_id(db, order_id, include_items=True)
    return success_response(
        message="QR table order approved",
        data={"order": _order_payload(full or order)},
    )


@router.patch("/{order_id}/reject", response_model=None)
async def reject_qr_table_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await QrTableOrderService.reject_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    from app.modules.order.service import OrderService

    full = await OrderService.get_order_by_id(db, order_id, include_items=True)
    return success_response(
        message="QR table order rejected",
        data={"order": _order_payload(full or order)},
    )
