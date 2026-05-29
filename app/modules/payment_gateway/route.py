from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import error_response, success_response
from app.modules.payment_gateway.model import PaymentGatewayProvider
from app.modules.payment_gateway.schema import (
    PaymentGatewayCreate,
    PaymentGatewayResponse,
    PaymentGatewayUpdate,
)
from app.modules.payment_gateway.service import PaymentGatewayService
from app.modules.user.model import User

router = APIRouter(prefix="/payment-gateways", tags=["payment-gateways"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_payment_gateway(
    payload: PaymentGatewayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create payment gateway credentials for a restaurant."""
    try:
        gateway = await PaymentGatewayService.create_gateway(db, payload, created_by=current_user.id)
        if not gateway:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with ID {payload.restaurant_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Payment gateway created successfully",
            data=PaymentGatewayResponse.from_model(gateway),
            status_code=status.HTTP_201_CREATED,
        )
    except IntegrityError:
        await db.rollback()
        return error_response(
            message="Payment gateway already exists",
            error_code="DUPLICATE_PAYMENT_GATEWAY",
            error_details="This restaurant already has credentials for this provider",
            status_code=status.HTTP_409_CONFLICT,
        )
    except Exception as exc:
        await db.rollback()
        return error_response(
            message="Failed to create payment gateway",
            error_code="PAYMENT_GATEWAY_CREATE_ERROR",
            error_details=str(exc),
        )


@router.get("/restaurant/{restaurant_id}", response_model=dict)
async def list_restaurant_payment_gateways(
    restaurant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    provider: PaymentGatewayProvider | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List payment gateways configured for a restaurant."""
    gateways, total = await PaymentGatewayService.list_by_restaurant(
        db,
        restaurant_id=restaurant_id,
        skip=skip,
        limit=limit,
        provider=provider,
        is_active=is_active,
    )
    return success_response(
        message="Payment gateways retrieved successfully",
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "payment_gateways": [PaymentGatewayResponse.from_model(g) for g in gateways],
        },
    )


@router.get("/{gateway_id}", response_model=dict)
async def get_payment_gateway(
    gateway_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get a payment gateway configuration by ID."""
    gateway = await PaymentGatewayService.get_by_id(db, gateway_id)
    if not gateway:
        return error_response(
            message="Payment gateway not found",
            error_code="NOT_FOUND",
            error_details=f"Payment gateway with ID {gateway_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(
        message="Payment gateway retrieved successfully",
        data=PaymentGatewayResponse.from_model(gateway),
    )


@router.put("/{gateway_id}", response_model=dict)
async def update_payment_gateway(
    gateway_id: str,
    payload: PaymentGatewayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update payment gateway credentials or configuration."""
    try:
        gateway = await PaymentGatewayService.update_gateway(
            db,
            gateway_id,
            payload,
            updated_by=current_user.id,
        )
        if not gateway:
            return error_response(
                message="Payment gateway not found",
                error_code="NOT_FOUND",
                error_details=f"Payment gateway with ID {gateway_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Payment gateway updated successfully",
            data=PaymentGatewayResponse.from_model(gateway),
        )
    except IntegrityError:
        await db.rollback()
        return error_response(
            message="Payment gateway already exists",
            error_code="DUPLICATE_PAYMENT_GATEWAY",
            error_details="This restaurant already has credentials for this provider",
            status_code=status.HTTP_409_CONFLICT,
        )
    except Exception as exc:
        await db.rollback()
        return error_response(
            message="Failed to update payment gateway",
            error_code="PAYMENT_GATEWAY_UPDATE_ERROR",
            error_details=str(exc),
        )


@router.patch("/{gateway_id}/default", response_model=dict)
async def set_default_payment_gateway(
    gateway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark one gateway as the default for its restaurant."""
    gateway = await PaymentGatewayService.set_default(db, gateway_id, updated_by=current_user.id)
    if not gateway:
        return error_response(
            message="Payment gateway not found",
            error_code="NOT_FOUND",
            error_details=f"Payment gateway with ID {gateway_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(
        message="Default payment gateway updated successfully",
        data=PaymentGatewayResponse.from_model(gateway),
    )


@router.delete("/{gateway_id}", response_model=dict)
async def delete_payment_gateway(
    gateway_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Delete a payment gateway configuration."""
    deleted = await PaymentGatewayService.delete_gateway(db, gateway_id)
    if not deleted:
        return error_response(
            message="Payment gateway not found",
            error_code="NOT_FOUND",
            error_details=f"Payment gateway with ID {gateway_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(
        message="Payment gateway deleted successfully",
        data={"deleted_payment_gateway_id": gateway_id},
    )
