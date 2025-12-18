"""
Product catalog and inventory service layer
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
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


class CategoryService:
    """Service for category operations"""
    
    @staticmethod
    async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        category = Category(**category_data.model_dump())
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def get_category_by_id(db: AsyncSession, category_id: str) -> Optional[Category]:
        """Get category by ID"""
        result = await db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_categories_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """Get categories by restaurant"""
        query = select(Category).where(Category.restaurant_id == restaurant_id)
        
        if active_only:
            query = query.where(Category.active == True)
        
        query = query.order_by(Category.sort_order, Category.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
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
        
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def delete_category(db: AsyncSession, category_id: str) -> bool:
        """Delete category"""
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            return False
        
        await db.delete(category)
        await db.commit()
        return True


class ProductService:
    """Service for product operations"""
    
    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
        """Create a new product"""
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
    async def get_combo_items(db: AsyncSession, combo_id: str) -> List[ComboItem]:
        """Get items in a combo"""
        query = select(ComboItem).where(
            ComboItem.combo_id == combo_id
        ).order_by(ComboItem.sort_order)
        
        result = await db.execute(query)
        return list(result.scalars().all())
