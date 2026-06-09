"""
Product catalog and inventory service layer
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import joinedload
from typing import Optional, List, Tuple, Dict
from datetime import datetime

from app.modules.product.model import (
    Category, Product, Modifier, ModifierOption, ProductModifier,
    ComboProduct, ComboItem, InventoryTransaction
)
from app.modules.product.schema import (
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    ModifierCreate, ModifierUpdate,
    ModifierOptionCreate, ModifierOptionUpdate,
    ComboProductCreate, ComboProductUpdate,
    ComboItemCreate,
    InventoryTransactionCreate,
    StockAdjustment
)



class DuplicateError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class CategoryService:
    """Service for category operations"""
    
    @staticmethod
    async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        # Check uniqueness: Name
        stmt = select(Category).where(
            Category.restaurant_id == category_data.restaurant_id,
            func.lower(Category.name) == func.lower(category_data.name),
            Category.deleted_at.is_(None)
        )
        if await db.scalar(stmt):
            raise DuplicateError("Category with this name already exists in this restaurant", field="name")
            
        # Check uniqueness: Slug
        stmt = select(Category).where(
            Category.restaurant_id == category_data.restaurant_id,
            Category.slug == category_data.slug,
            Category.deleted_at.is_(None)
        )
        if await db.scalar(stmt):
            raise DuplicateError("Category with this slug already exists in this restaurant", field="slug")

        category = Category(**category_data.model_dump())
        db.add(category)
        await db.commit()
        
        # Load with restaurant for name
        result = await db.execute(
            select(Category)
            .options(joinedload(Category.restaurant))
            .where(Category.id == category.id)
        )
        category = result.scalar_one()
        category.restaurant_name = category.restaurant.name
        
        return category
    
    @staticmethod
    async def get_category_by_id(db: AsyncSession, category_id: str) -> Optional[Category]:
        """Get category by ID"""
        result = await db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_categories_by_ids(
        db: AsyncSession,
        restaurant_id: str,
        category_ids: List[str],
    ) -> List[Category]:
        """Get non-deleted categories by IDs, scoped to a restaurant."""
        if not category_ids:
            return []
        result = await db.execute(
            select(Category)
            .options(joinedload(Category.restaurant))
            .where(
                Category.restaurant_id == restaurant_id,
                Category.id.in_(category_ids),
                Category.deleted_at.is_(None),
            )
        )
        categories = list(result.scalars().unique().all())
        for category in categories:
            if getattr(category, "restaurant", None) is not None:
                category.restaurant_name = category.restaurant.name
        return categories
    
    @staticmethod
    async def get_categories_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """Get categories by restaurant"""
        query = (
            select(Category)
            .options(joinedload(Category.restaurant))
            .where(
            Category.restaurant_id == restaurant_id,
            Category.deleted_at.is_(None)
            )
        )
        
        if active_only:
            query = query.where(Category.active == True)
        
        query = query.order_by(Category.sort_order, Category.name).offset(skip).limit(limit)
        result = await db.execute(query)
        categories = list(result.scalars().all())
        for category in categories:
            if getattr(category, "restaurant", None) is not None:
                category.restaurant_name = category.restaurant.name
        return categories
    
    @staticmethod
    async def update_category(
        db: AsyncSession,
        category_id: str,
        category_data: CategoryUpdate
    ) -> Optional[Category]:
        """Update category"""
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            return None
            
        # Check uniqueness if name is updated
        if category_data.name:
            stmt = select(Category).where(
                Category.restaurant_id == category.restaurant_id,
                Category.id != category_id,
                func.lower(Category.name) == func.lower(category_data.name),
                Category.deleted_at.is_(None)
            )
            if await db.scalar(stmt):
                 raise DuplicateError("Category with this name already exists in this restaurant", field="name")

        # Check uniqueness if slug is updated
        if category_data.slug:
            stmt = select(Category).where(
                Category.restaurant_id == category.restaurant_id,
                Category.id != category_id,
                Category.slug == category_data.slug,
                Category.deleted_at.is_(None)
            )
            if await db.scalar(stmt):
                 raise DuplicateError("Category with this slug already exists in this restaurant", field="slug")
        
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def delete_category(db: AsyncSession, category_id: str) -> bool:
        """Soft delete category"""
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            return False
        
        category.deleted_at = datetime.utcnow()
        await db.commit()
        return True


class ProductService:
    """Service for product operations"""

    @staticmethod
    def _product_scope_conditions(
        restaurant_id: str,
        *,
        category_id: Optional[str] = None,
        available_only: bool = False,
        featured_only: bool = False,
        search: Optional[str] = None,
    ):
        conditions = [
            Product.restaurant_id == restaurant_id,
            Product.deleted_at.is_(None),
        ]
        if category_id:
            conditions.append(Product.category_id == category_id)
        if available_only:
            conditions.append(Product.available == True)
        if featured_only:
            conditions.append(Product.featured == True)
        if search:
            conditions.append(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                )
            )
        return conditions

    @staticmethod
    async def _assert_product_unique(
        db: AsyncSession,
        restaurant_id: str,
        name: str,
        slug: str,
        exclude_product_id: Optional[str] = None,
    ) -> None:
        name_stmt = select(Product.id).where(
            Product.restaurant_id == restaurant_id,
            func.lower(Product.name) == func.lower(name.strip()),
            Product.deleted_at.is_(None),
        )
        if exclude_product_id:
            name_stmt = name_stmt.where(Product.id != exclude_product_id)
        if await db.scalar(name_stmt):
            raise DuplicateError(
                "Product with this name already exists in this restaurant",
                field="name",
            )

        slug_stmt = select(Product.id).where(
            Product.restaurant_id == restaurant_id,
            Product.slug == slug,
            Product.deleted_at.is_(None),
        )
        if exclude_product_id:
            slug_stmt = slug_stmt.where(Product.id != exclude_product_id)
        if await db.scalar(slug_stmt):
            raise DuplicateError(
                "Product with this slug already exists in this restaurant",
                field="slug",
            )

    @staticmethod
    async def get_products_paginated(
        db: AsyncSession,
        restaurant_id: str,
        *,
        category_id: Optional[str] = None,
        available_only: bool = False,
        featured_only: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 12,
        dedupe_by_name: bool = True,
    ) -> Tuple[List[Product], int]:
        """Get paginated products, optionally deduping same-name rows."""
        conditions = ProductService._product_scope_conditions(
            restaurant_id,
            category_id=category_id,
            available_only=available_only,
            featured_only=featured_only,
            search=search,
        )

        if dedupe_by_name:
            ranked_subq = (
                select(
                    Product.id.label("product_id"),
                    func.row_number()
                    .over(
                        partition_by=func.lower(Product.name),
                        order_by=(
                            Product.updated_at.desc(),
                            Product.created_at.desc(),
                            Product.id.desc(),
                        ),
                    )
                    .label("row_num"),
                )
                .where(and_(*conditions))
            ).subquery()

            deduped_ids = select(ranked_subq.c.product_id).where(
                ranked_subq.c.row_num == 1
            ).subquery()

            total_items = await db.scalar(
                select(func.count()).select_from(deduped_ids)
            ) or 0

            skip = max(page - 1, 0) * page_size
            result = await db.execute(
                select(Product)
                .join(deduped_ids, Product.id == deduped_ids.c.product_id)
                .order_by(Product.name)
                .offset(skip)
                .limit(page_size)
            )
            return list(result.scalars().all()), total_items

        base_query = select(Product).where(and_(*conditions))
        total_items = await db.scalar(
            select(func.count()).select_from(base_query.subquery())
        ) or 0

        skip = max(page - 1, 0) * page_size
        result = await db.execute(
            base_query.order_by(Product.name).offset(skip).limit(page_size)
        )
        return list(result.scalars().all()), total_items

    @staticmethod
    async def _reassign_product_references(
        db: AsyncSession,
        duplicate_id: str,
        keeper_id: str,
    ) -> None:
        """Point foreign keys from a duplicate product to the kept product."""
        params = {"keeper_id": keeper_id, "duplicate_id": duplicate_id}
        for table in (
            "order_items",
            "cart_items",
            "item_wise_sales_reports",
            "combo_items",
        ):
            await db.execute(
                text(
                    f"UPDATE {table} SET product_id = :keeper_id "
                    "WHERE product_id = :duplicate_id"
                ),
                params,
            )

        await db.execute(
            text(
                """
                UPDATE product_modifiers pm
                LEFT JOIN product_modifiers keeper_pm
                  ON keeper_pm.product_id = :keeper_id
                 AND keeper_pm.modifier_id = pm.modifier_id
                SET pm.product_id = :keeper_id
                WHERE pm.product_id = :duplicate_id
                  AND keeper_pm.id IS NULL
                """
            ),
            params,
        )
        await db.execute(
            text("DELETE FROM product_modifiers WHERE product_id = :duplicate_id"),
            params,
        )

    @staticmethod
    async def _find_duplicate_product_mappings(
        db: AsyncSession,
        restaurant_id: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        """Return (duplicate_id, keeper_id) pairs for same-name products."""
        restaurant_filter = ""
        params: Dict[str, str] = {}
        if restaurant_id:
            restaurant_filter = "AND restaurant_id = :restaurant_id"
            params["restaurant_id"] = restaurant_id

        result = await db.execute(
            text(
                f"""
                WITH ranked AS (
                    SELECT
                        id,
                        restaurant_id,
                        LOWER(name) AS name_key,
                        ROW_NUMBER() OVER (
                            PARTITION BY restaurant_id, LOWER(name)
                            ORDER BY updated_at DESC, created_at DESC, id DESC
                        ) AS row_num
                    FROM products
                    WHERE deleted_at IS NULL
                    {restaurant_filter}
                ),
                keepers AS (
                    SELECT restaurant_id, name_key, id AS keeper_id
                    FROM ranked
                    WHERE row_num = 1
                )
                SELECT r.id AS duplicate_id, k.keeper_id
                FROM ranked r
                JOIN keepers k
                  ON r.restaurant_id = k.restaurant_id
                 AND r.name_key = k.name_key
                WHERE r.row_num > 1
                """
            ),
            params,
        )
        return list(result.all())

    @staticmethod
    async def remove_duplicate_products(
        db: AsyncSession,
        restaurant_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """
        Delete duplicate products within the same restaurant (same name, case-insensitive).
        Keeps the most recently updated row and reassigns foreign keys first.
        """
        mappings = await ProductService._find_duplicate_product_mappings(
            db, restaurant_id=restaurant_id
        )
        duplicate_groups = len({keeper_id for _, keeper_id in mappings})

        if dry_run:
            return {
                "duplicate_groups": duplicate_groups,
                "products_to_delete": len(mappings),
                "deleted": 0,
            }

        deleted = 0
        for duplicate_id, keeper_id in mappings:
            await ProductService._reassign_product_references(
                db, duplicate_id, keeper_id
            )
            result = await db.execute(
                text("DELETE FROM products WHERE id = :duplicate_id"),
                {"duplicate_id": duplicate_id},
            )
            if result.rowcount:
                deleted += 1

        if deleted:
            await db.commit()

        return {
            "duplicate_groups": duplicate_groups,
            "products_to_delete": len(mappings),
            "deleted": deleted,
        }
    
    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
        """Create a new product"""
        await ProductService._assert_product_unique(
            db,
            product_data.restaurant_id,
            product_data.name,
            product_data.slug,
        )
        product = Product(**product_data.model_dump())
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product
    
    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        result = await db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_products_by_ids(
        db: AsyncSession,
        product_ids: List[str],
        restaurant_id: Optional[str] = None,
    ) -> List[Product]:
        """Get products by IDs (order not guaranteed). Optionally scope to a restaurant."""
        if not product_ids:
            return []
        q = select(Product).where(Product.id.in_(product_ids))
        if restaurant_id is not None:
            q = q.where(Product.restaurant_id == restaurant_id)
        result = await db.execute(q)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_products_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        category_id: Optional[str] = None,
        available_only: bool = False,
        featured_only: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Get products by restaurant with filters"""
        query = select(Product).where(Product.restaurant_id == restaurant_id)
        
        if category_id:
            query = query.where(Product.category_id == category_id)
        
        if available_only:
            query = query.where(Product.available == True)
        
        if featured_only:
            query = query.where(Product.featured == True)
        
        if search:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
            )
        
        query = query.order_by(Product.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_low_stock_products(
        db: AsyncSession,
        restaurant_id: str
    ) -> List[Product]:
        """Get products with low stock"""
        query = select(Product).where(
            and_(
                Product.restaurant_id == restaurant_id,
                Product.stock <= Product.min_stock
            )
        ).order_by(Product.stock)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_product(
        db: AsyncSession,
        product_id: str,
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """Update product"""
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            return None

        update_data = product_data.model_dump(exclude_unset=True)
        next_name = update_data.get("name", product.name)
        next_slug = update_data.get("slug", product.slug)
        await ProductService._assert_product_unique(
            db,
            product.restaurant_id,
            next_name,
            next_slug,
            exclude_product_id=product_id,
        )

        for field, value in update_data.items():
            setattr(product, field, value)
        
        await db.commit()
        await db.refresh(product)
        return product
    
    @staticmethod
    async def delete_product(db: AsyncSession, product_id: str) -> bool:
        """Delete product"""
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            return False
        
        await db.delete(product)
        await db.commit()
        return True


class ModifierService:
    """Service for modifier operations"""
    
    @staticmethod
    async def create_modifier(db: AsyncSession, modifier_data: ModifierCreate) -> Modifier:
        """Create a new modifier"""
        modifier = Modifier(**modifier_data.model_dump())
        db.add(modifier)
        await db.commit()
        await db.refresh(modifier)
        return modifier

    @staticmethod
    async def update_modifier(
        db: AsyncSession,
        modifier_id: str,
        modifier_data: ModifierUpdate
    ) -> Optional[Modifier]:
        """Update modifier"""
        result = await db.execute(select(Modifier).where(Modifier.id == modifier_id))
        modifier = result.scalar_one_or_none()
        if not modifier:
            return None

        update_data = modifier_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(modifier, field, value)

        await db.commit()
        await db.refresh(modifier)
        return modifier
    
    @staticmethod
    async def get_modifier_by_id(db: AsyncSession, modifier_id: str) -> Optional[Modifier]:
        """Get modifier by ID"""
        result = await db.execute(select(Modifier).where(Modifier.id == modifier_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_modifiers_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Modifier]:
        """Get modifiers by restaurant"""
        query = select(Modifier).where(Modifier.restaurant_id == restaurant_id)
        query = query.order_by(Modifier.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_modifier(db: AsyncSession, modifier_id: str) -> bool:
        """Delete modifier"""
        result = await db.execute(select(Modifier).where(Modifier.id == modifier_id))
        modifier = result.scalar_one_or_none()
        if not modifier:
            return False

        await db.delete(modifier)
        await db.commit()
        return True
    
    @staticmethod
    async def create_modifier_option(
        db: AsyncSession,
        option_data: ModifierOptionCreate
    ) -> ModifierOption:
        """Create a new modifier option"""
        option = ModifierOption(**option_data.model_dump())
        db.add(option)
        await db.commit()
        await db.refresh(option)
        return option
    
    @staticmethod
    async def get_modifier_options(
        db: AsyncSession,
        modifier_id: str
    ) -> List[ModifierOption]:
        """Get options for a modifier"""
        query = select(ModifierOption).where(
            ModifierOption.modifier_id == modifier_id
        ).order_by(ModifierOption.sort_order, ModifierOption.name)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_modifier_option_by_id(
        db: AsyncSession,
        option_id: str
    ) -> Optional[ModifierOption]:
        """Get modifier option by ID"""
        result = await db.execute(
            select(ModifierOption).where(ModifierOption.id == option_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_modifier_option(
        db: AsyncSession,
        option_id: str,
        option_data: ModifierOptionUpdate
    ) -> Optional[ModifierOption]:
        """Update a modifier option"""
        option = await ModifierService.get_modifier_option_by_id(db, option_id)
        if not option:
            return None

        update_data = option_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(option, field, value)

        await db.commit()
        await db.refresh(option)
        return option

    @staticmethod
    async def delete_modifier_option(
        db: AsyncSession,
        option_id: str
    ) -> bool:
        """Delete a modifier option"""
        option = await ModifierService.get_modifier_option_by_id(db, option_id)
        if not option:
            return False

        await db.delete(option)
        await db.commit()
        return True

    @staticmethod
    async def get_modifiers_with_options_by_restaurant(
        db: AsyncSession,
        restaurant_id: str
    ) -> List[Modifier]:
        """Get all modifiers with their options for a restaurant"""
        query = (
            select(Modifier)
            .options(joinedload(Modifier.options))
            .where(Modifier.restaurant_id == restaurant_id)
            .order_by(Modifier.name)
        )
        
        result = await db.execute(query)
        return list(result.unique().scalars().all())


class InventoryService:
    """Service for inventory operations"""
    
    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        transaction_data: InventoryTransactionCreate,
        user_id: Optional[str] = None
    ) -> InventoryTransaction:
        """Create inventory transaction and update stock"""
        # Get current product
        result = await db.execute(
            select(Product).where(Product.id == transaction_data.product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise ValueError("Product not found")
        
        # Calculate new stock
        previous_stock = product.stock
        new_stock = previous_stock + transaction_data.quantity
        
        if new_stock < 0:
            raise ValueError("Insufficient stock")
        
        # Calculate total cost
        total_cost = None
        if transaction_data.unit_cost:
            total_cost = transaction_data.unit_cost * abs(transaction_data.quantity)
        
        # Create transaction
        transaction = InventoryTransaction(
            restaurant_id=transaction_data.restaurant_id,
            product_id=transaction_data.product_id,
            type=transaction_data.type,
            quantity=transaction_data.quantity,
            previous_stock=previous_stock,
            new_stock=new_stock,
            unit_cost=transaction_data.unit_cost,
            total_cost=total_cost,
            reference_id=transaction_data.reference_id,
            reference_type=transaction_data.reference_type,
            notes=transaction_data.notes,
            performed_by=user_id or transaction_data.performed_by
        )
        
        # Update product stock
        product.stock = new_stock
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        restaurant_id: str,
        adjustment: StockAdjustment,
        user_id: Optional[str] = None
    ) -> InventoryTransaction:
        """Adjust product stock"""
        transaction_data = InventoryTransactionCreate(
            restaurant_id=restaurant_id,
            product_id=adjustment.product_id,
            type=adjustment.type,
            quantity=adjustment.quantity,
            notes=adjustment.notes,
            performed_by=user_id
        )
        
        return await InventoryService.create_transaction(db, transaction_data, user_id)
    
    @staticmethod
    async def get_product_transactions(
        db: AsyncSession,
        product_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """Get transactions for a product"""
        query = select(InventoryTransaction).where(
            InventoryTransaction.product_id == product_id
        ).order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_restaurant_transactions(
        db: AsyncSession,
        restaurant_id: str,
        transaction_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """Get transactions for a restaurant"""
        query = select(InventoryTransaction).where(
            InventoryTransaction.restaurant_id == restaurant_id
        )
        
        if transaction_type:
            query = query.where(InventoryTransaction.type == transaction_type)
        
        query = query.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


class ComboProductService:
    """Service for combo product operations"""
    
    @staticmethod
    async def create_combo(db: AsyncSession, combo_data: ComboProductCreate) -> ComboProduct:
        """Create a new combo product"""
        combo = ComboProduct(**combo_data.model_dump())
        db.add(combo)
        await db.commit()
        await db.refresh(combo)
        return combo
    
    @staticmethod
    async def get_combo_by_id(db: AsyncSession, combo_id: str) -> Optional[ComboProduct]:
        """Get combo by ID"""
        result = await db.execute(select(ComboProduct).where(ComboProduct.id == combo_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_combo(
        db: AsyncSession,
        combo_id: str,
        combo_data: ComboProductUpdate,
    ) -> Optional[ComboProduct]:
        """Update combo product (partial)."""
        result = await db.execute(select(ComboProduct).where(ComboProduct.id == combo_id))
        combo = result.scalar_one_or_none()
        if not combo:
            return None
        update_data = combo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(combo, field, value)
        await db.commit()
        await db.refresh(combo)
        return combo

    @staticmethod
    async def get_combos_by_ids(
        db: AsyncSession,
        restaurant_id: str,
        combo_ids: List[str],
    ) -> List[ComboProduct]:
        """Get combo products by IDs, scoped to a restaurant."""
        if not combo_ids:
            return []
        result = await db.execute(
            select(ComboProduct).where(
                ComboProduct.restaurant_id == restaurant_id,
                ComboProduct.id.in_(combo_ids),
            )
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_combos_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[ComboProduct]:
        """Get combo products by restaurant"""
        query = select(ComboProduct).where(ComboProduct.restaurant_id == restaurant_id)
        
        if available_only:
            query = query.where(ComboProduct.available == True)
        
        query = query.order_by(ComboProduct.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def add_combo_item(db: AsyncSession, item_data: ComboItemCreate) -> ComboItem:
        """Add item to combo"""
        item = ComboItem(**item_data.model_dump())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def add_combo_items(db: AsyncSession, items_data: List[ComboItemCreate]) -> List[ComboItem]:
        """Add multiple items to a combo (single transaction)."""
        if not items_data:
            return []
        items = [ComboItem(**item.model_dump()) for item in items_data]
        db.add_all(items)
        await db.commit()
        for item in items:
            await db.refresh(item)
        return items
    
    @staticmethod
    async def get_combo_items(db: AsyncSession, combo_id: str) -> List[ComboItem]:
        """Get items in a combo"""
        query = select(ComboItem).where(
            ComboItem.combo_id == combo_id
        ).order_by(ComboItem.sort_order)
        
        result = await db.execute(query)
        return list(result.scalars().all())
