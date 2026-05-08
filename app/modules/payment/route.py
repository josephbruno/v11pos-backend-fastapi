from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import error_response, success_response
from app.modules.payment.schema import OrderPaymentCreate, OrderPaymentResponse, OrderPaymentUpdate
from app.modules.payment.service import OrderPaymentService
from app.modules.user.model import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/orders/{order_id}", response_model=dict)
async def list_order_payments(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List all payment rows for an order (initial pending row plus any split legs)."""
    rows = await OrderPaymentService.list_for_order(db, order_id)
    return success_response(
        message="Order payments retrieved successfully",
        data=[OrderPaymentResponse.model_validate(r) for r in rows],
    )


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order_payment(
    payload: OrderPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an additional payment row (e.g. split tender).

    **Required body fields:** ``order_id``, ``restaurant_id``, ``amount``.
    """
    try:
        row = await OrderPaymentService.create_payment(db, payload, created_by=current_user.id)
        if not row:
            return error_response(
                message="Order not found or restaurant mismatch",
                error_code="NOT_FOUND",
                error_details="Invalid order_id for this restaurant_id",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Order payment created successfully",
            data=OrderPaymentResponse.model_validate(row),
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return error_response(
            message="Failed to create order payment",
            error_code="PAYMENT_CREATE_ERROR",
            error_details=str(e),
        )


@router.patch("/{payment_id}", response_model=dict)
async def update_order_payment(
    payment_id: str,
    payload: OrderPaymentUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Update gateway references, method, or status on a payment row."""
    row = await OrderPaymentService.update_payment(db, payment_id, payload)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return success_response(
        message="Order payment updated successfully",
        data=OrderPaymentResponse.model_validate(row),
    )
