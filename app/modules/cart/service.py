from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cart.model import (
    Cart,
    CartItem,
    CartItemModifierOption,
    CartItemType,
    CartStatus,
)
from app.modules.customer.model import Customer
from app.modules.order.model import Order
from app.modules.product.model import Category, ComboItem, ComboProduct, ModifierOption, Product
from app.modules.cart.schema import CartCheckoutRequest


class CartValidationError(ValueError):
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


def _signature_from_modifier_option_ids(modifier_option_ids: Iterable[str]) -> str:
    ids = [str(x).strip() for x in modifier_option_ids if str(x).strip()]
    ids = sorted(set(ids))
    return ",".join(ids)


@dataclass(frozen=True)
class CartItemWithModifiers:
    item: CartItem
    modifier_option_ids: List[str]


class CartService:
    @staticmethod
    async def get_or_create_active_cart(
        db: AsyncSession,
        restaurant_id: str,
        customer_id: str,
    ) -> Cart:
        # Ensure customer exists
        customer = await db.scalar(select(Customer).where(Customer.id == customer_id))
        if not customer:
            raise CartValidationError("Customer not found", field="customer_id")

        cart = await db.scalar(
            select(Cart).where(
                Cart.restaurant_id == restaurant_id,
                Cart.customer_id == customer_id,
                Cart.status == CartStatus.ACTIVE,
                Cart.is_active == True,
            )
        )
        if cart:
            return cart

        cart = Cart(restaurant_id=restaurant_id, customer_id=customer_id, status=CartStatus.ACTIVE, is_active=True)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
        return cart

    @staticmethod
    async def _load_modifier_options(
        db: AsyncSession,
        restaurant_id: str,
        modifier_option_ids: Iterable[str],
    ) -> List[ModifierOption]:
        ids = [x for x in {str(i).strip() for i in modifier_option_ids} if x]
        if not ids:
            return []

        result = await db.execute(
            select(ModifierOption).where(
                and_(
                    ModifierOption.restaurant_id == restaurant_id,
                    ModifierOption.id.in_(ids),
                    ModifierOption.available == True,
                )
            )
        )
        options = list(result.scalars().all())
        if len(options) != len(ids):
            raise CartValidationError("One or more modifier options are invalid", field="modifier_option_ids")
        return options

    @staticmethod
    async def add_item(
        db: AsyncSession,
        restaurant_id: str,
        customer_id: str,
        item_type: CartItemType,
        product_id: Optional[str],
        combo_product_id: Optional[str],
        quantity: int,
        modifier_option_ids: Iterable[str],
        notes: Optional[str] = None,
    ) -> CartItem:
        cart = await CartService.get_or_create_active_cart(db, restaurant_id, customer_id)

        modifier_signature = _signature_from_modifier_option_ids(modifier_option_ids)
        options = await CartService._load_modifier_options(db, restaurant_id, modifier_option_ids)
        modifiers_price = sum(int(o.price or 0) for o in options)

        unit_price = 0
        if item_type == CartItemType.PRODUCT:
            product = await db.scalar(
                select(Product).where(
                    Product.id == product_id,
                    Product.restaurant_id == restaurant_id,
                    Product.available == True,
                )
            )
            if not product:
                raise CartValidationError("Product not found", field="product_id")
            unit_price = int(product.price or 0)
        elif item_type == CartItemType.COMBO_PRODUCT:
            combo = await db.scalar(
                select(ComboProduct).where(
                    ComboProduct.id == combo_product_id,
                    ComboProduct.restaurant_id == restaurant_id,
                    ComboProduct.available == True,
                )
            )
            if not combo:
                raise CartValidationError("Combo product not found", field="combo_product_id")
            unit_price = int(combo.price or 0)
        else:
            raise CartValidationError("Invalid item_type", field="item_type")

        existing = await db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.item_type == item_type,
                CartItem.product_id == product_id,
                CartItem.combo_product_id == combo_product_id,
                CartItem.modifier_signature == modifier_signature,
            )
        )
        if existing:
            existing.quantity += quantity
            if notes is not None:
                existing.notes = notes
            await db.commit()
            await db.refresh(existing)
            return existing

        item = CartItem(
            cart_id=cart.id,
            restaurant_id=restaurant_id,
            item_type=item_type,
            product_id=product_id,
            combo_product_id=combo_product_id,
            quantity=quantity,
            unit_price=unit_price,
            modifiers_price=modifiers_price,
            notes=notes,
            modifier_signature=modifier_signature,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)

        if options:
            db.add_all(
                [
                    CartItemModifierOption(cart_item_id=item.id, modifier_option_id=o.id)
                    for o in options
                ]
            )
            await db.commit()

        await db.refresh(item)
        return item

    @staticmethod
    async def update_item_quantity(db: AsyncSession, item_id: str, quantity: int) -> Optional[CartItem]:
        item = await db.scalar(select(CartItem).where(CartItem.id == item_id))
        if not item:
            return None
        item.quantity = quantity
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def remove_item(db: AsyncSession, item_id: str, quantity: Optional[int] = None) -> bool:
        item = await db.scalar(select(CartItem).where(CartItem.id == item_id))
        if not item:
            return False

        if quantity is not None and quantity > 0 and item.quantity > quantity:
            item.quantity -= quantity
            await db.commit()
            return True

        await db.execute(delete(CartItem).where(CartItem.id == item_id))
        await db.commit()
        return True

    @staticmethod
    async def clear_cart(db: AsyncSession, restaurant_id: str, customer_id: str) -> bool:
        cart = await db.scalar(
            select(Cart).where(
                Cart.restaurant_id == restaurant_id,
                Cart.customer_id == customer_id,
                Cart.status == CartStatus.ACTIVE,
                Cart.is_active == True,
            )
        )
        if not cart:
            return False
        await db.execute(delete(Cart).where(Cart.id == cart.id))
        await db.commit()
        return True

    @staticmethod
    async def get_active_cart_with_items(
        db: AsyncSession,
        restaurant_id: str,
        customer_id: str,
    ) -> Optional[Cart]:
        return await db.scalar(
            select(Cart).where(
                Cart.restaurant_id == restaurant_id,
                Cart.customer_id == customer_id,
                Cart.status == CartStatus.ACTIVE,
                Cart.is_active == True,
            )
        )

    @staticmethod
    async def get_cart_items_with_modifier_options(db: AsyncSession, cart_id: str) -> List[CartItemWithModifiers]:
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.created_at.asc())
        )
        items = list(result.scalars().all())
        if not items:
            return []

        item_ids = [i.id for i in items]
        mo_result = await db.execute(
            select(CartItemModifierOption).where(CartItemModifierOption.cart_item_id.in_(item_ids))
        )
        links = list(mo_result.scalars().all())
        by_item: dict[str, List[str]] = {}
        for link in links:
            by_item.setdefault(link.cart_item_id, []).append(link.modifier_option_id)

        return [CartItemWithModifiers(item=i, modifier_option_ids=sorted(by_item.get(i.id, []))) for i in items]

    @staticmethod
    async def load_catalog_maps_for_cart_entries(
        db: AsyncSession,
        entries: List[CartItemWithModifiers],
    ) -> tuple[dict[str, Product], dict[str, ComboProduct], dict[str, str]]:
        """
        Batch-load products, combo products, and category names for cart line display.
        """
        product_ids = {e.item.product_id for e in entries if e.item.product_id}
        combo_ids = {e.item.combo_product_id for e in entries if e.item.combo_product_id}

        products: dict[str, Product] = {}
        if product_ids:
            res = await db.execute(select(Product).where(Product.id.in_(product_ids)))
            for row in res.scalars().unique().all():
                products[row.id] = row

        combos: dict[str, ComboProduct] = {}
        if combo_ids:
            res = await db.execute(select(ComboProduct).where(ComboProduct.id.in_(combo_ids)))
            for row in res.scalars().unique().all():
                combos[row.id] = row

        cat_ids: set[str] = set()
        for p in products.values():
            cat_ids.add(p.category_id)
        for c in combos.values():
            cat_ids.add(c.category_id)

        category_names: dict[str, str] = {}
        if cat_ids:
            res = await db.execute(select(Category).where(Category.id.in_(cat_ids)))
            for cat in res.scalars().all():
                category_names[cat.id] = cat.name

        return products, combos, category_names

    @staticmethod
    async def _first_combo_component_product_id(db: AsyncSession, combo_product_id: str) -> str:
        pid = await db.scalar(
            select(ComboItem.product_id)
            .where(ComboItem.combo_id == combo_product_id)
            .order_by(ComboItem.sort_order.asc(), ComboItem.id.asc())
            .limit(1)
        )
        if not pid:
            raise CartValidationError("Combo has no component products", field="combo_product_id")
        return pid

    @staticmethod
    async def checkout_active_cart(
        db: AsyncSession,
        restaurant_id: str,
        customer_id: str,
        checkout: CartCheckoutRequest,
        created_by: Optional[str] = None,
    ) -> Order:
        """
        Create an order from the customer's active cart, then mark the cart ordered.
        Uses one DB transaction (order insert + cart update).
        """
        from app.modules.order.schema import OrderCreate, OrderItemCreate
        from app.modules.order.service import OrderService

        cart = (
            await db.execute(
                select(Cart)
                .where(
                    Cart.restaurant_id == restaurant_id,
                    Cart.customer_id == customer_id,
                    Cart.status == CartStatus.ACTIVE,
                    Cart.is_active == True,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not cart:
            raise CartValidationError("No active cart", field="cart")

        entries = await CartService.get_cart_items_with_modifier_options(db, cart.id)
        if not entries:
            raise CartValidationError("Cart is empty", field="items")

        products_by_id, combos_by_id, _category_names = await CartService.load_catalog_maps_for_cart_entries(
            db, entries
        )

        order_items: list[OrderItemCreate] = []
        for entry in entries:
            options = await CartService._load_modifier_options(db, restaurant_id, entry.modifier_option_ids)
            modifiers_payload: dict = {
                "options": [{"id": o.id, "name": o.name, "price": int(o.price or 0)} for o in options]
            }

            if entry.item.item_type == CartItemType.PRODUCT:
                if not entry.item.product_id:
                    raise CartValidationError("Cart line missing product_id", field="product_id")
                product = products_by_id.get(entry.item.product_id)
                if not product or not product.available:
                    raise CartValidationError("A cart product is no longer available", field="product_id")
                order_items.append(
                    OrderItemCreate(
                        product_id=product.id,
                        product_name=product.name,
                        product_image=product.image,
                        quantity=int(entry.item.quantity or 0),
                        unit_price=int(entry.item.unit_price or 0),
                        modifiers=modifiers_payload,
                        modifiers_price=int(entry.item.modifiers_price or 0),
                        notes=entry.item.notes,
                    )
                )
            elif entry.item.item_type == CartItemType.COMBO_PRODUCT:
                if not entry.item.combo_product_id:
                    raise CartValidationError("Cart line missing combo_product_id", field="combo_product_id")
                combo = combos_by_id.get(entry.item.combo_product_id)
                if not combo or not combo.available:
                    raise CartValidationError("A cart combo is no longer available", field="combo_product_id")
                anchor_pid = await CartService._first_combo_component_product_id(db, combo.id)
                order_items.append(
                    OrderItemCreate(
                        product_id=anchor_pid,
                        product_name=combo.name,
                        product_image=combo.image,
                        quantity=int(entry.item.quantity or 0),
                        unit_price=int(entry.item.unit_price or 0),
                        modifiers=modifiers_payload,
                        modifiers_price=int(entry.item.modifiers_price or 0),
                        notes=entry.item.notes,
                        is_combo_item=True,
                        combo_id=combo.id,
                    )
                )
            else:
                raise CartValidationError("Unsupported cart line type", field="item_type")

        fields = checkout.model_dump()
        if not fields.get("source"):
            fields["source"] = "cart"
        order_data = OrderCreate(
            restaurant_id=restaurant_id,
            customer_id=customer_id,
            items=order_items,
            **fields,
        )

        order = await OrderService.create_order(db, order_data, created_by=created_by, commit=False)
        cart.status = CartStatus.ORDERED
        cart.is_active = False
        await db.commit()

        reloaded = await OrderService.get_order_by_id(db, order.id, include_items=True)
        return reloaded or order

