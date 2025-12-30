from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from app.modules.inventory.model import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    StockTransaction,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    LowStockAlert,
    StockTransactionType,
    PurchaseOrderStatus
)
from app.modules.inventory.schema import (
    IngredientCreate,
    IngredientUpdate,
    RecipeCreate,
    RecipeUpdate,
    RecipeIngredientCreate,
    StockTransactionCreate,
    SupplierCreate,
    SupplierUpdate,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderItemCreate
)


class InventoryService:
    """Service layer for Inventory Management operations"""
    
    # ==================== INGREDIENT OPERATIONS ====================
    
    @staticmethod
    async def create_ingredient(db: AsyncSession, ingredient_data: IngredientCreate) -> Ingredient:
        """Create a new ingredient"""
        # Convert tags list to dict format
        tags_dict = {"items": ingredient_data.tags} if ingredient_data.tags else None
        
        db_ingredient = Ingredient(
            restaurant_id=ingredient_data.restaurant_id,
            name=ingredient_data.name,
            description=ingredient_data.description,
            sku=ingredient_data.sku,
            barcode=ingredient_data.barcode,
            category=ingredient_data.category,
            sub_category=ingredient_data.sub_category,
            tags=tags_dict,
            unit_of_measure=ingredient_data.unit_of_measure,
            current_stock=ingredient_data.current_stock,
            minimum_stock=ingredient_data.minimum_stock,
            maximum_stock=ingredient_data.maximum_stock,
            reorder_level=ingredient_data.reorder_level,
            reorder_quantity=ingredient_data.reorder_quantity,
            cost_price=ingredient_data.cost_price,
            average_cost=ingredient_data.cost_price,
            storage_location=ingredient_data.storage_location,
            shelf_life_days=ingredient_data.shelf_life_days,
            primary_supplier_id=ingredient_data.primary_supplier_id,
            is_perishable=ingredient_data.is_perishable,
            track_batch=ingredient_data.track_batch,
            track_expiry=ingredient_data.track_expiry,
            low_stock_alert_enabled=ingredient_data.low_stock_alert_enabled,
            notes=ingredient_data.notes,
            created_by=ingredient_data.created_by
        )
        
        db.add(db_ingredient)
        await db.commit()
        await db.refresh(db_ingredient)
        
        # Check if low stock alert needed
        await InventoryService.check_low_stock_alert(db, db_ingredient)
        
        return db_ingredient
    
    @staticmethod
    async def get_ingredient_by_id(db: AsyncSession, ingredient_id: str) -> Optional[Ingredient]:
        """Get ingredient by ID"""
        result = await db.execute(
            select(Ingredient).where(Ingredient.id == ingredient_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_ingredients(
        db: AsyncSession,
        restaurant_id: str,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        low_stock_only: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Ingredient], int]:
        """Get ingredients with filters"""
        query = select(Ingredient).where(Ingredient.restaurant_id == restaurant_id)
        
        if category:
            query = query.where(Ingredient.category == category)
        
        if is_active is not None:
            query = query.where(Ingredient.is_active == is_active)
        
        if low_stock_only:
            query = query.where(Ingredient.current_stock <= Ingredient.minimum_stock)
        
        if search:
            query = query.where(
                or_(
                    Ingredient.name.ilike(f"%{search}%"),
                    Ingredient.sku.ilike(f"%{search}%"),
                    Ingredient.barcode.ilike(f"%{search}%")
                )
            )
        
        # Count total
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(Ingredient.name.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        
        return list(result.scalars().all()), total
    
    @staticmethod
    async def update_ingredient(
        db: AsyncSession,
        ingredient_id: str,
        ingredient_data: IngredientUpdate
    ) -> Optional[Ingredient]:
        """Update ingredient"""
        ingredient = await InventoryService.get_ingredient_by_id(db, ingredient_id)
        
        if not ingredient:
            return None
        
        update_data = ingredient_data.model_dump(exclude_unset=True)
        
        # Convert tags list to dict format
        if "tags" in update_data and update_data["tags"] is not None:
            update_data["tags"] = {"items": update_data["tags"]}
        
        for field, value in update_data.items():
            setattr(ingredient, field, value)
        
        await db.commit()
        await db.refresh(ingredient)
        
        # Check if low stock alert needed
        await InventoryService.check_low_stock_alert(db, ingredient)
        
        return ingredient
    
    @staticmethod
    async def delete_ingredient(db: AsyncSession, ingredient_id: str) -> bool:
        """Soft delete ingredient"""
        ingredient = await InventoryService.get_ingredient_by_id(db, ingredient_id)
        
        if not ingredient:
            return False
        
        ingredient.is_active = False
        await db.commit()
        
        return True
    
    # ==================== RECIPE OPERATIONS ====================
    
    @staticmethod
    async def create_recipe(db: AsyncSession, recipe_data: RecipeCreate) -> Recipe:
        """Create a recipe with ingredients"""
        # Create recipe
        db_recipe = Recipe(
            restaurant_id=recipe_data.restaurant_id,
            product_id=recipe_data.product_id,
            name=recipe_data.name,
            description=recipe_data.description,
            version=recipe_data.version,
            yield_quantity=recipe_data.yield_quantity,
            yield_unit=recipe_data.yield_unit,
            prep_time_minutes=recipe_data.prep_time_minutes,
            cook_time_minutes=recipe_data.cook_time_minutes,
            instructions=recipe_data.instructions,
            notes=recipe_data.notes,
            created_by=recipe_data.created_by
        )
        
        db.add(db_recipe)
        await db.flush()
        
        # Add recipe ingredients and calculate costs
        total_cost = 0
        
        for ing_data in recipe_data.ingredients:
            # Get ingredient to fetch current cost
            ingredient = await InventoryService.get_ingredient_by_id(db, ing_data.ingredient_id)
            
            if ingredient:
                cost_per_unit = ingredient.average_cost or ingredient.cost_price
                item_total_cost = int(float(ing_data.quantity) * cost_per_unit)
                
                db_recipe_ing = RecipeIngredient(
                    recipe_id=db_recipe.id,
                    ingredient_id=ing_data.ingredient_id,
                    quantity=ing_data.quantity,
                    unit=ing_data.unit,
                    cost_per_unit=cost_per_unit,
                    total_cost=item_total_cost,
                    preparation_note=ing_data.preparation_note,
                    is_optional=ing_data.is_optional,
                    display_order=ing_data.display_order
                )
                
                db.add(db_recipe_ing)
                total_cost += item_total_cost
        
        # Update recipe costs
        db_recipe.total_cost = total_cost
        db_recipe.cost_per_serving = int(total_cost / recipe_data.yield_quantity) if recipe_data.yield_quantity > 0 else total_cost
        
        await db.commit()
        await db.refresh(db_recipe)
        
        return db_recipe
    
    @staticmethod
    async def get_recipe_by_id(db: AsyncSession, recipe_id: str) -> Optional[Recipe]:
        """Get recipe by ID"""
        result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_recipe_by_product_id(db: AsyncSession, product_id: str) -> Optional[Recipe]:
        """Get recipe by product ID"""
        result = await db.execute(
            select(Recipe).where(and_(Recipe.product_id == product_id, Recipe.is_active == True))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_recipe_ingredients(db: AsyncSession, recipe_id: str) -> List[RecipeIngredient]:
        """Get ingredients for a recipe"""
        result = await db.execute(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .order_by(RecipeIngredient.display_order.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def deduct_stock_for_order(
        db: AsyncSession,
        restaurant_id: str,
        product_id: str,
        quantity: int,
        order_id: str,
        user_id: Optional[str] = None
    ) -> List[StockTransaction]:
        """Auto stock deduction when item is sold"""
        transactions = []
        
        # Get recipe for the product
        recipe = await InventoryService.get_recipe_by_product_id(db, product_id)
        
        if not recipe:
            return transactions
        
        # Get recipe ingredients
        recipe_ingredients = await InventoryService.get_recipe_ingredients(db, recipe.id)
        
        # Deduct stock for each ingredient
        for rec_ing in recipe_ingredients:
            if rec_ing.is_optional:
                continue
            
            ingredient = await InventoryService.get_ingredient_by_id(db, rec_ing.ingredient_id)
            
            if not ingredient:
                continue
            
            # Calculate quantity to deduct (recipe quantity * order quantity)
            deduct_qty = float(rec_ing.quantity) * quantity
            
            # Create stock transaction
            transaction = await InventoryService.create_stock_transaction(
                db,
                StockTransactionCreate(
                    restaurant_id=restaurant_id,
                    ingredient_id=ingredient.id,
                    transaction_type=StockTransactionType.SALE,
                    quantity=-deduct_qty,  # Negative for stock out
                    unit=rec_ing.unit,
                    unit_cost=ingredient.average_cost or ingredient.cost_price,
                    reference_type="order",
                    reference_id=order_id,
                    created_by=user_id
                )
            )
            
            transactions.append(transaction)
        
        return transactions
    
    # ==================== STOCK TRANSACTION OPERATIONS ====================
    
    @staticmethod
    async def generate_transaction_number(db: AsyncSession, transaction_type: StockTransactionType) -> str:
        """Generate unique transaction number"""
        prefix_map = {
            StockTransactionType.PURCHASE: "PUR",
            StockTransactionType.SALE: "SALE",
            StockTransactionType.ADJUSTMENT: "ADJ",
            StockTransactionType.WASTAGE: "WST",
            StockTransactionType.DAMAGE: "DMG",
            StockTransactionType.RETURN_TO_SUPPLIER: "RTS",
            StockTransactionType.TRANSFER_IN: "TIN",
            StockTransactionType.TRANSFER_OUT: "TOUT",
            StockTransactionType.INITIAL: "INIT"
        }
        
        prefix = prefix_map.get(transaction_type, "TXN")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # Get count for today to avoid duplicates
        count_result = await db.execute(
            select(func.count()).where(
                and_(
                    StockTransaction.transaction_number.like(f"{prefix}-{timestamp[:8]}%")
                )
            )
        )
        count = count_result.scalar_one()
        
        return f"{prefix}-{timestamp}-{count + 1:04d}"
    
    @staticmethod
    async def create_stock_transaction(
        db: AsyncSession,
        transaction_data: StockTransactionCreate
    ) -> StockTransaction:
        """Create stock transaction and update ingredient stock"""
        # Get ingredient
        ingredient = await InventoryService.get_ingredient_by_id(db, transaction_data.ingredient_id)
        
        if not ingredient:
            raise ValueError("Ingredient not found")
        
        # Generate transaction number
        transaction_number = await InventoryService.generate_transaction_number(
            db,
            transaction_data.transaction_type
        )
        
        # Calculate stock before and after
        stock_before = float(ingredient.current_stock)
        stock_after = stock_before + transaction_data.quantity
        
        # Prevent negative stock (optional, can be configured)
        if stock_after < 0:
            stock_after = 0
        
        # Calculate total cost
        total_cost = int(abs(transaction_data.quantity) * transaction_data.unit_cost)
        
        # Create transaction
        db_transaction = StockTransaction(
            restaurant_id=transaction_data.restaurant_id,
            ingredient_id=transaction_data.ingredient_id,
            transaction_type=transaction_data.transaction_type,
            transaction_number=transaction_number,
            quantity=transaction_data.quantity,
            unit=transaction_data.unit,
            stock_before=stock_before,
            stock_after=stock_after,
            unit_cost=transaction_data.unit_cost,
            total_cost=total_cost,
            reference_type=transaction_data.reference_type,
            reference_id=transaction_data.reference_id,
            supplier_id=transaction_data.supplier_id,
            batch_number=transaction_data.batch_number,
            expiry_date=transaction_data.expiry_date,
            reason=transaction_data.reason,
            requires_approval=transaction_data.requires_approval,
            is_approved=not transaction_data.requires_approval,
            notes=transaction_data.notes,
            created_by=transaction_data.created_by
        )
        
        db.add(db_transaction)
        
        # Update ingredient stock if approved
        if db_transaction.is_approved:
            ingredient.current_stock = stock_after
            
            # Update average cost for purchase transactions
            if transaction_data.transaction_type == StockTransactionType.PURCHASE and transaction_data.quantity > 0:
                old_value = float(stock_before) * ingredient.average_cost
                new_value = abs(transaction_data.quantity) * transaction_data.unit_cost
                total_value = old_value + new_value
                total_qty = stock_after
                
                if total_qty > 0:
                    ingredient.average_cost = int(total_value / total_qty)
                
                ingredient.last_purchase_price = transaction_data.unit_cost
        
        await db.commit()
        await db.refresh(db_transaction)
        
        # Check low stock alert
        await InventoryService.check_low_stock_alert(db, ingredient)
        
        return db_transaction
    
    @staticmethod
    async def get_stock_transactions(
        db: AsyncSession,
        restaurant_id: str,
        ingredient_id: Optional[str] = None,
        transaction_type: Optional[StockTransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[StockTransaction], int]:
        """Get stock transactions with filters"""
        query = select(StockTransaction).where(StockTransaction.restaurant_id == restaurant_id)
        
        if ingredient_id:
            query = query.where(StockTransaction.ingredient_id == ingredient_id)
        
        if transaction_type:
            query = query.where(StockTransaction.transaction_type == transaction_type)
        
        if start_date:
            query = query.where(StockTransaction.transaction_date >= start_date)
        
        if end_date:
            query = query.where(StockTransaction.transaction_date <= end_date)
        
        # Count total
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(StockTransaction.transaction_date.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        
        return list(result.scalars().all()), total
    
    # ==================== SUPPLIER OPERATIONS ====================
    
    @staticmethod
    async def create_supplier(db: AsyncSession, supplier_data: SupplierCreate) -> Supplier:
        """Create a new supplier"""
        # Convert supply_categories list to dict format
        categories_dict = {"items": supplier_data.supply_categories} if supplier_data.supply_categories else None
        
        db_supplier = Supplier(
            restaurant_id=supplier_data.restaurant_id,
            name=supplier_data.name,
            code=supplier_data.code,
            company_name=supplier_data.company_name,
            contact_person=supplier_data.contact_person,
            email=supplier_data.email,
            phone=supplier_data.phone,
            alternate_phone=supplier_data.alternate_phone,
            address_line1=supplier_data.address_line1,
            address_line2=supplier_data.address_line2,
            city=supplier_data.city,
            state=supplier_data.state,
            postal_code=supplier_data.postal_code,
            country=supplier_data.country,
            gstin=supplier_data.gstin,
            pan=supplier_data.pan,
            payment_terms_days=supplier_data.payment_terms_days,
            credit_limit=supplier_data.credit_limit,
            supply_categories=categories_dict,
            bank_name=supplier_data.bank_name,
            account_number=supplier_data.account_number,
            ifsc_code=supplier_data.ifsc_code,
            notes=supplier_data.notes,
            created_by=supplier_data.created_by
        )
        
        db.add(db_supplier)
        await db.commit()
        await db.refresh(db_supplier)
        
        return db_supplier
    
    @staticmethod
    async def get_supplier_by_id(db: AsyncSession, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID"""
        result = await db.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_suppliers(
        db: AsyncSession,
        restaurant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get suppliers with filters"""
        query = select(Supplier).where(Supplier.restaurant_id == restaurant_id)
        
        if status:
            query = query.where(Supplier.status == status)
        
        if search:
            query = query.where(
                or_(
                    Supplier.name.ilike(f"%{search}%"),
                    Supplier.code.ilike(f"%{search}%"),
                    Supplier.company_name.ilike(f"%{search}%")
                )
            )
        
        # Count total
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        
        return list(result.scalars().all()), total
    
    @staticmethod
    async def update_supplier(
        db: AsyncSession,
        supplier_id: str,
        supplier_data: SupplierUpdate
    ) -> Optional[Supplier]:
        """Update supplier"""
        supplier = await InventoryService.get_supplier_by_id(db, supplier_id)
        
        if not supplier:
            return None
        
        update_data = supplier_data.model_dump(exclude_unset=True)
        
        # Convert supply_categories list to dict format
        if "supply_categories" in update_data and update_data["supply_categories"] is not None:
            update_data["supply_categories"] = {"items": update_data["supply_categories"]}
        
        for field, value in update_data.items():
            setattr(supplier, field, value)
        
        await db.commit()
        await db.refresh(supplier)
        
        return supplier
    
    # ==================== PURCHASE ORDER OPERATIONS ====================
    
    @staticmethod
    async def generate_po_number(db: AsyncSession) -> str:
        """Generate unique PO number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # Get count for today
        count_result = await db.execute(
            select(func.count()).where(
                PurchaseOrder.po_number.like(f"PO-{timestamp[:8]}%")
            )
        )
        count = count_result.scalar_one()
        
        return f"PO-{timestamp}-{count + 1:04d}"
    
    @staticmethod
    async def create_purchase_order(db: AsyncSession, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create purchase order"""
        # Generate PO number
        po_number = await InventoryService.generate_po_number(db)
        
        # Create PO
        db_po = PurchaseOrder(
            restaurant_id=po_data.restaurant_id,
            supplier_id=po_data.supplier_id,
            po_number=po_number,
            expected_delivery_date=po_data.expected_delivery_date,
            delivery_address=po_data.delivery_address,
            shipping_method=po_data.shipping_method,
            shipping_charges=po_data.shipping_charges,
            other_charges=po_data.other_charges,
            payment_terms=po_data.payment_terms,
            terms_conditions=po_data.terms_conditions,
            requires_approval=po_data.requires_approval,
            notes=po_data.notes,
            created_by=po_data.created_by
        )
        
        db.add(db_po)
        await db.flush()
        
        # Add PO items and calculate totals
        subtotal = 0
        total_tax = 0
        total_discount = 0
        
        for item_data in po_data.items:
            # Calculate amounts
            line_total = int(item_data.quantity_ordered * item_data.unit_price)
            tax_amt = int(line_total * item_data.tax_percentage / 100)
            discount_amt = int(line_total * item_data.discount_percentage / 100)
            item_total = line_total + tax_amt - discount_amt
            
            db_po_item = PurchaseOrderItem(
                purchase_order_id=db_po.id,
                ingredient_id=item_data.ingredient_id,
                quantity_ordered=item_data.quantity_ordered,
                unit=item_data.unit,
                unit_price=item_data.unit_price,
                tax_percentage=item_data.tax_percentage,
                tax_amount=tax_amt,
                discount_percentage=item_data.discount_percentage,
                discount_amount=discount_amt,
                total_amount=item_total,
                notes=item_data.notes
            )
            
            db.add(db_po_item)
            
            subtotal += line_total
            total_tax += tax_amt
            total_discount += discount_amt
        
        # Update PO totals
        db_po.subtotal = subtotal
        db_po.tax_amount = total_tax
        db_po.discount_amount = total_discount
        db_po.total_amount = subtotal + total_tax - total_discount + po_data.shipping_charges + po_data.other_charges
        
        await db.commit()
        await db.refresh(db_po)
        
        return db_po
    
    @staticmethod
    async def receive_po_items(
        db: AsyncSession,
        po_id: str,
        items_received: List[dict],
        user_id: Optional[str] = None
    ) -> PurchaseOrder:
        """Receive items from purchase order and create stock transactions"""
        po = await InventoryService.get_po_by_id(db, po_id)
        
        if not po:
            raise ValueError("Purchase order not found")
        
        for item_data in items_received:
            po_item_id = item_data.get("po_item_id")
            qty_received = item_data.get("quantity_received", 0)
            batch_number = item_data.get("batch_number")
            expiry_date = item_data.get("expiry_date")
            
            # Get PO item
            result = await db.execute(
                select(PurchaseOrderItem).where(PurchaseOrderItem.id == po_item_id)
            )
            po_item = result.scalar_one_or_none()
            
            if not po_item or qty_received <= 0:
                continue
            
            # Update received quantity
            po_item.quantity_received += qty_received
            
            if po_item.quantity_received >= po_item.quantity_ordered:
                po_item.is_fully_received = True
            
            # Create stock transaction
            await InventoryService.create_stock_transaction(
                db,
                StockTransactionCreate(
                    restaurant_id=po.restaurant_id,
                    ingredient_id=po_item.ingredient_id,
                    transaction_type=StockTransactionType.PURCHASE,
                    quantity=qty_received,
                    unit=po_item.unit,
                    unit_cost=po_item.unit_price,
                    reference_type="purchase_order",
                    reference_id=po_id,
                    supplier_id=po.supplier_id,
                    batch_number=batch_number,
                    expiry_date=expiry_date,
                    created_by=user_id
                )
            )
        
        # Update PO status
        # Check if all items fully received
        items_result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
        )
        all_items = list(items_result.scalars().all())
        
        if all(item.is_fully_received for item in all_items):
            po.status = PurchaseOrderStatus.RECEIVED
            po.actual_delivery_date = datetime.utcnow()
        else:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
        
        await db.commit()
        await db.refresh(po)
        
        return po
    
    @staticmethod
    async def get_po_by_id(db: AsyncSession, po_id: str) -> Optional[PurchaseOrder]:
        """Get purchase order by ID"""
        result = await db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_po_items(db: AsyncSession, po_id: str) -> List[PurchaseOrderItem]:
        """Get items for a purchase order"""
        result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
        )
        return list(result.scalars().all())
    
    # ==================== LOW STOCK ALERT OPERATIONS ====================
    
    @staticmethod
    async def check_low_stock_alert(db: AsyncSession, ingredient: Ingredient) -> Optional[LowStockAlert]:
        """Check and create low stock alert if needed"""
        if not ingredient.low_stock_alert_enabled:
            return None
        
        # Check if stock is below minimum or reorder level
        if ingredient.current_stock <= ingredient.minimum_stock or ingredient.current_stock <= ingredient.reorder_level:
            # Check if alert already exists and not resolved
            result = await db.execute(
                select(LowStockAlert).where(
                    and_(
                        LowStockAlert.ingredient_id == ingredient.id,
                        LowStockAlert.is_resolved == False
                    )
                )
            )
            existing_alert = result.scalar_one_or_none()
            
            if not existing_alert:
                # Create new alert
                alert = LowStockAlert(
                    restaurant_id=ingredient.restaurant_id,
                    ingredient_id=ingredient.id,
                    current_stock=ingredient.current_stock,
                    minimum_stock=ingredient.minimum_stock,
                    reorder_level=ingredient.reorder_level,
                    unit=ingredient.unit_of_measure
                )
                
                db.add(alert)
                ingredient.low_stock_notified_at = datetime.utcnow()
                await db.commit()
                await db.refresh(alert)
                
                return alert
        
        return None
    
    @staticmethod
    async def get_low_stock_alerts(
        db: AsyncSession,
        restaurant_id: str,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LowStockAlert], int]:
        """Get low stock alerts"""
        query = select(LowStockAlert).where(LowStockAlert.restaurant_id == restaurant_id)
        
        if is_resolved is not None:
            query = query.where(LowStockAlert.is_resolved == is_resolved)
        
        # Count total
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(LowStockAlert.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        
        return list(result.scalars().all()), total
    
    @staticmethod
    async def resolve_low_stock_alert(
        db: AsyncSession,
        alert_id: str,
        action_taken: str,
        po_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[LowStockAlert]:
        """Resolve low stock alert"""
        result = await db.execute(
            select(LowStockAlert).where(LowStockAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        alert.action_taken = action_taken
        alert.purchase_order_id = po_id
        
        await db.commit()
        await db.refresh(alert)
        
        return alert
