"""
Cart API routes: staff or customer JWT (`get_cart_auth_context`).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CartAuthContext, get_cart_auth_context
from app.core.response import error_response, success_response
from app.modules.cart.schema import (
    CartComboProductSummary,
    CartItemAddRequest,
    CartItemResponse,
    CartItemUpdateRequest,
    CartProductSummary,
    CartResponse,
)
from app.modules.cart.service import CartService, CartValidationError


router = APIRouter(prefix="/carts", tags=["Cart"])


async def _build_cart_response(db: AsyncSession, cart) -> CartResponse:
    items_with_mods = await CartService.get_cart_items_with_modifier_options(db, cart.id)
    products_by_id, combos_by_id, category_names = await CartService.load_catalog_maps_for_cart_entries(
        db, items_with_mods
    )
    items: list[CartItemResponse] = []
    subtotal = 0
    total_qty = 0
    for entry in items_with_mods:
        item = entry.item
        total_price = (int(item.unit_price or 0) + int(item.modifiers_price or 0)) * int(item.quantity or 0)
        subtotal += total_price
        total_qty += int(item.quantity or 0)

        prod_summary: CartProductSummary | None = None
        combo_summary: CartComboProductSummary | None = None
        if item.product_id:
            p = products_by_id.get(item.product_id)
            if p:
                prod_summary = CartProductSummary(
                    id=p.id,
                    name=p.name,
                    slug=p.slug,
                    sku=p.sku,
                    description=p.description,
                    short_description=p.short_description,
                    price=int(p.price or 0),
                    image=p.image,
                    thumbnail=p.thumbnail,
                    category_id=p.category_id,
                    category_name=category_names.get(p.category_id),
                    available=bool(p.available),
                )
        elif item.combo_product_id:
            c = combos_by_id.get(item.combo_product_id)
            if c:
                combo_summary = CartComboProductSummary(
                    id=c.id,
                    name=c.name,
                    slug=c.slug,
                    description=c.description,
                    price=int(c.price or 0),
                    image=c.image,
                    category_id=c.category_id,
                    category_name=category_names.get(c.category_id),
                    available=bool(c.available),
                    featured=bool(c.featured),
                )

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
                product=prod_summary,
                combo_product=combo_summary,
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
    auth: CartAuthContext = Depends(get_cart_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get active cart for a customer (creates one if missing). Staff or customer Bearer token."""
    auth.enforce_customer_path_scope(restaurant_id, customer_id)
    try:
        cart = await CartService.get_or_create_active_cart(db, restaurant_id, customer_id)
        return success_response(
            message="Cart retrieved successfully",
            data=(await _build_cart_response(db, cart)).model_dump(),
            timezone=auth.response_timezone(),
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
    auth: CartAuthContext = Depends(get_cart_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Add an item to cart (product/combo with modifier options). Staff or customer Bearer token."""
    auth.enforce_customer_path_scope(payload.restaurant_id, payload.customer_id)
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
            timezone=auth.response_timezone(),
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
    auth: CartAuthContext = Depends(get_cart_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Update cart item quantity. Staff or customer Bearer token (customer: own cart only)."""
    try:
        from app.modules.cart.model import Cart, CartItem

        existing = await db.get(CartItem, item_id)
        if not existing:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        cart = await db.get(Cart, existing.cart_id)
        if not cart:
            return error_response(
                message="Cart not found",
                error_code="NOT_FOUND",
                error_details="Active cart not found for this item",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        auth.enforce_customer_cart_row(cart)

        item = await CartService.update_item_quantity(db, item_id, payload.quantity)
        if not item:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
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
            timezone=auth.response_timezone(),
        )
    except HTTPException:
        raise
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
    auth: CartAuthContext = Depends(get_cart_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Remove an item from cart (or decrement quantity). Staff or customer Bearer token (customer: own cart only)."""
    try:
        from app.modules.cart.model import Cart, CartItem

        item = await db.get(CartItem, item_id)
        if not item:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        cart_for_auth = await db.get(Cart, item.cart_id)
        if cart_for_auth:
            auth.enforce_customer_cart_row(cart_for_auth)

        ok = await CartService.remove_item(db, item_id, quantity=quantity)
        if not ok:
            return error_response(
                message="Cart item not found",
                error_code="NOT_FOUND",
                error_details=f"Cart item with ID {item_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        cart = await db.get(Cart, item.cart_id)
        if not cart:
            return success_response(
                message="Cart item removed successfully",
                data=None,
                timezone=auth.response_timezone(),
            )
        return success_response(
            message="Cart item removed successfully",
            data=(await _build_cart_response(db, cart)).model_dump(),
            timezone=auth.response_timezone(),
        )
    except HTTPException:
        raise
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
    auth: CartAuthContext = Depends(get_cart_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Clear (delete) the active cart for the customer. Staff or customer Bearer token."""
    auth.enforce_customer_path_scope(restaurant_id, customer_id)
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
            timezone=auth.response_timezone(),
        )
    except Exception as e:
        return error_response(
            message="Failed to clear cart",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
