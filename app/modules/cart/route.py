"""
Cart API routes (staff-authenticated, customer-scoped).
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import error_response, success_response
from app.modules.cart.schema import (
    CartItemAddRequest,
    CartItemResponse,
    CartItemUpdateRequest,
    CartResponse,
)
from app.modules.cart.service import CartService, CartValidationError
from app.modules.user.model import User


router = APIRouter(prefix="/carts", tags=["Cart"])


async def _build_cart_response(db: AsyncSession, cart) -> CartResponse:
    items_with_mods = await CartService.get_cart_items_with_modifier_options(db, cart.id)
    items: list[CartItemResponse] = []
    subtotal = 0
    total_qty = 0
    for entry in items_with_mods:
        item = entry.item
        total_price = (int(item.unit_price or 0) + int(item.modifiers_price or 0)) * int(item.quantity or 0)
        subtotal += total_price
        total_qty += int(item.quantity or 0)
        items.append(
            CartItemResponse(
                id=item.id,
                cart_id=item.cart_id,
                restaurant_id=item.restaurant_id,
                item_type=item.item_type,
                product_id=item.product_id,
                combo_product_id=item.combo_product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                modifiers_price=item.modifiers_price,
                total_price=total_price,
                modifier_option_ids=entry.modifier_option_ids,
                notes=item.notes,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    return CartResponse(
        id=cart.id,
        restaurant_id=cart.restaurant_id,
        customer_id=cart.customer_id,
        status=cart.status,
        is_active=cart.is_active,
        subtotal=subtotal,
        total_quantity=total_qty,
        items=items,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.get("/restaurant/{restaurant_id}/customer/{customer_id}")
async def get_active_cart(
    restaurant_id: str,
    customer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active cart for a customer (creates one if missing)."""
    try:
        cart = await CartService.get_or_create_active_cart(db, restaurant_id, customer_id)
        return success_response(
            message="Cart retrieved successfully",
            data=(await _build_cart_response(db, cart)).model_dump(),
            timezone=getattr(current_user, "timezone", None),
        )
    except CartValidationError as e:
        return error_response(
            message=str(e),
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            field=getattr(e, "field", None),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve cart",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    payload: CartItemAddRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an item to cart (product/combo with modifier options)."""
    try:
        await CartService.add_item(
            db=db,
            restaurant_id=payload.restaurant_id,
            customer_id=payload.customer_id,
            item_type=payload.item_type,
            product_id=payload.product_id,
            combo_product_id=payload.combo_product_id,
            quantity=payload.quantity,
            modifier_option_ids=payload.modifier_option_ids,
            notes=payload.notes,
        )
        cart = await CartService.get_or_create_active_cart(db, payload.restaurant_id, payload.customer_id)
        return success_response(
            message="Item added to cart successfully",
            data=(await _build_cart_response(db, cart)).model_dump(),
            timezone=getattr(current_user, "timezone", None),
            status_code=status.HTTP_201_CREATED,
        )
    except CartValidationError as e:
        return error_response(
            message=str(e),
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            field=getattr(e, "field", None),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to add item to cart",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.patch("/items/{item_id}")
async def update_cart_item(
    item_id: str,
    payload: CartItemUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update cart item quantity."""
    try:
        item = await CartService.update_item_quantity(db, item_id, payload.quantity)
        if not item:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        from app.modules.cart.model import Cart

        cart = await db.get(Cart, item.cart_id)
        if not cart:
            return error_response(
                message="Cart not found",
                error_code="NOT_FOUND",
                error_details="Active cart not found for this item",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Cart item updated successfully",
            data=(await _build_cart_response(db, cart)).model_dump(),
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to update cart item",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: str,
    quantity: int | None = Query(None, ge=1, description="If provided, decrement by quantity"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an item from cart (or decrement quantity)."""
    try:
        # Load item first so we can return updated cart
        from app.modules.cart.model import CartItem  # local import to avoid circulars

        item = await db.get(CartItem, item_id)
        if not item:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        ok = await CartService.remove_item(db, item_id, quantity=quantity)
        if not ok:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        from app.modules.cart.model import Cart
        cart = await db.get(Cart, item.cart_id)
        if not cart:
            return success_response(
                message="Cart item removed successfully",
                data=None,
                timezone=getattr(current_user, "timezone", None),
            )
        return success_response(
            message="Cart item removed successfully",
            data=(await _build_cart_response(db, cart)).model_dump(),
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to remove cart item",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.delete("/restaurant/{restaurant_id}/customer/{customer_id}")
async def clear_cart(
    restaurant_id: str,
    customer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear (delete) the active cart for the customer."""
    try:
        ok = await CartService.clear_cart(db, restaurant_id, customer_id)
        if not ok:
            return error_response(
                message="Cart not found",
                error_code="NOT_FOUND",
                error_details="Active cart not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Cart cleared successfully",
            data={"restaurant_id": restaurant_id, "customer_id": customer_id},
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to clear cart",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
