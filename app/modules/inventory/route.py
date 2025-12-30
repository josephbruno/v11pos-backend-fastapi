from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import success_response, error_response
from app.modules.inventory.schema import (
    IngredientCreate,
    IngredientUpdate,
    IngredientResponse,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeIngredientResponse,
    StockTransactionCreate,
    StockTransactionResponse,
    StockAdjustmentRequest,
    WastageEntry,
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderItemResponse,
    ReceiveItemsRequest,
    LowStockAlertResponse
)
from app.modules.inventory.model import StockTransactionType, PurchaseOrderStatus
from app.modules.inventory.service import InventoryService
from app.modules.user.model import User


router = APIRouter(prefix="/inventory", tags=["inventory-management"])


# ==================== INGREDIENT ENDPOINTS ====================

@router.post("/ingredients", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    ingredient_data: IngredientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new ingredient/raw material
    
    - **name**: Ingredient name (required)
    - **unit_of_measure**: Unit (kg, g, l, ml, pc, etc.)
    - **current_stock**: Initial stock quantity
    - **minimum_stock**: Low stock alert threshold
    - **reorder_level**: Trigger purchase order creation
    - **cost_price**: Cost per unit (in paise/cents)
    - **category**: Classification (vegetables, dairy, meat, etc.)
    - **is_perishable**: Track expiry dates
    - **track_batch**: Enable batch/lot tracking
    """
    try:
        ingredient = await InventoryService.create_ingredient(db, ingredient_data)
        return success_response(
            data=IngredientResponse.model_validate(ingredient),
            message="Ingredient created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create ingredient",
            error=str(e)
        )


@router.get("/ingredients/{ingredient_id}", response_model=dict)
async def get_ingredient(
    ingredient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ingredient by ID"""
    ingredient = await InventoryService.get_ingredient_by_id(db, ingredient_id)
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    
    return success_response(
        data=IngredientResponse.model_validate(ingredient),
        message="Ingredient retrieved successfully"
    )


@router.get("/ingredients/restaurant/{restaurant_id}", response_model=dict)
async def get_ingredients(
    restaurant_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    search: Optional[str] = Query(None, description="Search by name, SKU, or barcode"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get ingredients for a restaurant
    
    Supports filtering by:
    - Category
    - Active status
    - Low stock (below minimum threshold)
    - Search (name, SKU, barcode)
    """
    ingredients, total = await InventoryService.get_ingredients(
        db,
        restaurant_id=restaurant_id,
        category=category,
        is_active=is_active,
        low_stock_only=low_stock_only,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "ingredients": [IngredientResponse.model_validate(ing) for ing in ingredients]
        },
        message="Ingredients retrieved successfully"
    )


@router.put("/ingredients/{ingredient_id}", response_model=dict)
async def update_ingredient(
    ingredient_id: str,
    ingredient_data: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ingredient"""
    ingredient = await InventoryService.update_ingredient(db, ingredient_id, ingredient_data)
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    
    return success_response(
        data=IngredientResponse.model_validate(ingredient),
        message="Ingredient updated successfully"
    )


@router.delete("/ingredients/{ingredient_id}", response_model=dict)
async def delete_ingredient(
    ingredient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate ingredient (soft delete)"""
    success = await InventoryService.delete_ingredient(db, ingredient_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    
    return success_response(
        data={"id": ingredient_id},
        message="Ingredient deactivated successfully"
    )


# ==================== RECIPE ENDPOINTS ====================

@router.post("/recipes", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create recipe mapping (menu item → ingredients)
    
    Links a menu item to its ingredients with quantities.
    Automatically calculates recipe cost and cost per serving.
    
    Example:
    ```json
    {
      "product_id": "product-uuid",
      "name": "Chicken Burger",
      "yield_quantity": 1,
      "ingredients": [
        {
          "ingredient_id": "ing-uuid-1",
          "quantity": 150,
          "unit": "g",
          "preparation_note": "Grilled"
        },
        {
          "ingredient_id": "ing-uuid-2",
          "quantity": 2,
          "unit": "pc"
        }
      ]
    }
    ```
    """
    try:
        recipe = await InventoryService.create_recipe(db, recipe_data)
        
        # Load ingredients
        ingredients = await InventoryService.get_recipe_ingredients(db, recipe.id)
        recipe_response = RecipeResponse.model_validate(recipe)
        recipe_response.ingredients = [RecipeIngredientResponse.model_validate(ing) for ing in ingredients]
        
        return success_response(
            data=recipe_response,
            message="Recipe created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create recipe",
            error=str(e)
        )


@router.get("/recipes/{recipe_id}", response_model=dict)
async def get_recipe(
    recipe_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recipe by ID with ingredients"""
    recipe = await InventoryService.get_recipe_by_id(db, recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Load ingredients
    ingredients = await InventoryService.get_recipe_ingredients(db, recipe_id)
    recipe_response = RecipeResponse.model_validate(recipe)
    recipe_response.ingredients = [RecipeIngredientResponse.model_validate(ing) for ing in ingredients]
    
    return success_response(
        data=recipe_response,
        message="Recipe retrieved successfully"
    )


@router.get("/recipes/product/{product_id}", response_model=dict)
async def get_recipe_by_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recipe for a product/menu item"""
    recipe = await InventoryService.get_recipe_by_product_id(db, product_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found for this product"
        )
    
    # Load ingredients
    ingredients = await InventoryService.get_recipe_ingredients(db, recipe.id)
    recipe_response = RecipeResponse.model_validate(recipe)
    recipe_response.ingredients = [RecipeIngredientResponse.model_validate(ing) for ing in ingredients]
    
    return success_response(
        data=recipe_response,
        message="Recipe retrieved successfully"
    )


# ==================== STOCK TRANSACTION ENDPOINTS ====================

@router.post("/stock/transactions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_stock_transaction(
    transaction_data: StockTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create stock transaction (Stock In/Out)
    
    Transaction types:
    - **purchase**: Stock purchased from supplier
    - **sale**: Auto deduction on sale (created automatically)
    - **adjustment**: Manual stock adjustment
    - **wastage**: Wastage entry
    - **damage**: Damage entry
    - **return_to_supplier**: Return to supplier
    - **transfer_in/out**: Inter-location transfer
    - **initial**: Initial stock entry
    
    Positive quantity = Stock IN
    Negative quantity = Stock OUT
    """
    try:
        transaction = await InventoryService.create_stock_transaction(db, transaction_data)
        return success_response(
            data=StockTransactionResponse.model_validate(transaction),
            message="Stock transaction created successfully"
        )
    except ValueError as e:
        return error_response(
            message=str(e),
            error="Validation error"
        )
    except Exception as e:
        return error_response(
            message="Failed to create stock transaction",
            error=str(e)
        )


@router.post("/stock/adjustment", response_model=dict)
async def adjust_stock(
    adjustment: StockAdjustmentRequest,
    restaurant_id: str = Query(..., description="Restaurant ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manual stock adjustment
    
    Use for correcting stock discrepancies, physical counts, etc.
    """
    try:
        # Get ingredient to fetch unit
        ingredient = await InventoryService.get_ingredient_by_id(db, adjustment.ingredient_id)
        
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found"
            )
        
        transaction = await InventoryService.create_stock_transaction(
            db,
            StockTransactionCreate(
                restaurant_id=restaurant_id,
                ingredient_id=adjustment.ingredient_id,
                transaction_type=StockTransactionType.ADJUSTMENT,
                quantity=adjustment.adjustment_quantity,
                unit=ingredient.unit_of_measure,
                unit_cost=ingredient.average_cost or ingredient.cost_price,
                reason=adjustment.reason,
                notes=adjustment.notes,
                created_by=current_user.id
            )
        )
        
        return success_response(
            data=StockTransactionResponse.model_validate(transaction),
            message="Stock adjusted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="Failed to adjust stock",
            error=str(e)
        )


@router.post("/stock/wastage", response_model=dict)
async def record_wastage(
    wastage: WastageEntry,
    restaurant_id: str = Query(..., description="Restaurant ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record wastage entry
    
    Track spoiled, expired, or wasted ingredients.
    Automatically deducts from stock.
    """
    try:
        ingredient = await InventoryService.get_ingredient_by_id(db, wastage.ingredient_id)
        
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found"
            )
        
        transaction = await InventoryService.create_stock_transaction(
            db,
            StockTransactionCreate(
                restaurant_id=restaurant_id,
                ingredient_id=wastage.ingredient_id,
                transaction_type=StockTransactionType.WASTAGE,
                quantity=-abs(wastage.quantity),  # Always negative
                unit=ingredient.unit_of_measure,
                unit_cost=ingredient.average_cost or ingredient.cost_price,
                reason=wastage.reason,
                notes=wastage.notes,
                created_by=current_user.id
            )
        )
        
        return success_response(
            data=StockTransactionResponse.model_validate(transaction),
            message="Wastage recorded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="Failed to record wastage",
            error=str(e)
        )


@router.post("/stock/damage", response_model=dict)
async def record_damage(
    damage: WastageEntry,  # Same structure as wastage
    restaurant_id: str = Query(..., description="Restaurant ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record damage entry (broken, damaged items)"""
    try:
        ingredient = await InventoryService.get_ingredient_by_id(db, damage.ingredient_id)
        
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found"
            )
        
        transaction = await InventoryService.create_stock_transaction(
            db,
            StockTransactionCreate(
                restaurant_id=restaurant_id,
                ingredient_id=damage.ingredient_id,
                transaction_type=StockTransactionType.DAMAGE,
                quantity=-abs(damage.quantity),
                unit=ingredient.unit_of_measure,
                unit_cost=ingredient.average_cost or ingredient.cost_price,
                reason=damage.reason,
                notes=damage.notes,
                created_by=current_user.id
            )
        )
        
        return success_response(
            data=StockTransactionResponse.model_validate(transaction),
            message="Damage recorded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="Failed to record damage",
            error=str(e)
        )


@router.get("/stock/transactions/restaurant/{restaurant_id}", response_model=dict)
async def get_stock_transactions(
    restaurant_id: str,
    ingredient_id: Optional[str] = Query(None, description="Filter by ingredient"),
    transaction_type: Optional[StockTransactionType] = Query(None, description="Filter by type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get stock transactions with filters
    
    Track all stock movements for audit and analysis.
    """
    transactions, total = await InventoryService.get_stock_transactions(
        db,
        restaurant_id=restaurant_id,
        ingredient_id=ingredient_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "transactions": [StockTransactionResponse.model_validate(txn) for txn in transactions]
        },
        message="Transactions retrieved successfully"
    )


# ==================== SUPPLIER ENDPOINTS ====================

@router.post("/suppliers", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new supplier
    
    Store supplier information for purchase management.
    - Contact details
    - Payment terms
    - Credit limit
    - Bank details
    """
    try:
        supplier = await InventoryService.create_supplier(db, supplier_data)
        return success_response(
            data=SupplierResponse.model_validate(supplier),
            message="Supplier created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create supplier",
            error=str(e)
        )


@router.get("/suppliers/{supplier_id}", response_model=dict)
async def get_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get supplier by ID"""
    supplier = await InventoryService.get_supplier_by_id(db, supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    return success_response(
        data=SupplierResponse.model_validate(supplier),
        message="Supplier retrieved successfully"
    )


@router.get("/suppliers/restaurant/{restaurant_id}", response_model=dict)
async def get_suppliers(
    restaurant_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get suppliers for a restaurant"""
    suppliers, total = await InventoryService.get_suppliers(
        db,
        restaurant_id=restaurant_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "suppliers": [SupplierResponse.model_validate(sup) for sup in suppliers]
        },
        message="Suppliers retrieved successfully"
    )


@router.put("/suppliers/{supplier_id}", response_model=dict)
async def update_supplier(
    supplier_id: str,
    supplier_data: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update supplier"""
    supplier = await InventoryService.update_supplier(db, supplier_id, supplier_data)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    return success_response(
        data=SupplierResponse.model_validate(supplier),
        message="Supplier updated successfully"
    )


# ==================== PURCHASE ORDER ENDPOINTS ====================

@router.post("/purchase-orders", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create purchase order
    
    Generate PO to order ingredients from suppliers.
    Automatically calculates totals including tax, discount, and shipping.
    
    Example:
    ```json
    {
      "supplier_id": "supplier-uuid",
      "items": [
        {
          "ingredient_id": "ing-uuid",
          "quantity_ordered": 50,
          "unit": "kg",
          "unit_price": 15000,
          "tax_percentage": 5.0
        }
      ],
      "shipping_charges": 50000
    }
    ```
    """
    try:
        po = await InventoryService.create_purchase_order(db, po_data)
        
        # Load items
        items = await InventoryService.get_po_items(db, po.id)
        po_response = PurchaseOrderResponse.model_validate(po)
        po_response.items = [PurchaseOrderItemResponse.model_validate(item) for item in items]
        
        return success_response(
            data=po_response,
            message="Purchase order created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create purchase order",
            error=str(e)
        )


@router.get("/purchase-orders/{po_id}", response_model=dict)
async def get_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get purchase order by ID with items"""
    po = await InventoryService.get_po_by_id(db, po_id)
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # Load items
    items = await InventoryService.get_po_items(db, po_id)
    po_response = PurchaseOrderResponse.model_validate(po)
    po_response.items = [PurchaseOrderItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=po_response,
        message="Purchase order retrieved successfully"
    )


@router.post("/purchase-orders/{po_id}/receive", response_model=dict)
async def receive_purchase_order_items(
    po_id: str,
    receive_data: ReceiveItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Receive items from purchase order
    
    Creates stock transactions and updates ingredient stock.
    Supports partial receiving and batch tracking.
    
    Example:
    ```json
    {
      "items": [
        {
          "po_item_id": "item-uuid",
          "quantity_received": 45,
          "batch_number": "BATCH-2023-001",
          "expiry_date": "2024-12-31"
        }
      ]
    }
    ```
    """
    try:
        po = await InventoryService.receive_po_items(
            db,
            po_id,
            receive_data.items,
            current_user.id
        )
        
        # Load items
        items = await InventoryService.get_po_items(db, po_id)
        po_response = PurchaseOrderResponse.model_validate(po)
        po_response.items = [PurchaseOrderItemResponse.model_validate(item) for item in items]
        
        return success_response(
            data=po_response,
            message="Items received successfully"
        )
    except ValueError as e:
        return error_response(
            message=str(e),
            error="Validation error"
        )
    except Exception as e:
        return error_response(
            message="Failed to receive items",
            error=str(e)
        )


@router.patch("/purchase-orders/{po_id}/status", response_model=dict)
async def update_purchase_order_status(
    po_id: str,
    status: PurchaseOrderStatus = Query(..., description="New status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update purchase order status"""
    try:
        po = await InventoryService.get_po_by_id(db, po_id)
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        po.status = status
        
        # Update dates based on status
        if status == PurchaseOrderStatus.APPROVED:
            po.approved_by = current_user.id
            po.approved_at = datetime.utcnow()
        elif status == PurchaseOrderStatus.RECEIVED:
            po.actual_delivery_date = datetime.utcnow()
        
        await db.commit()
        await db.refresh(po)
        
        return success_response(
            data=PurchaseOrderResponse.model_validate(po),
            message=f"Purchase order status updated to {status}"
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="Failed to update status",
            error=str(e)
        )


# ==================== LOW STOCK ALERT ENDPOINTS ====================

@router.get("/alerts/low-stock/restaurant/{restaurant_id}", response_model=dict)
async def get_low_stock_alerts(
    restaurant_id: str,
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get low stock alerts
    
    Automatically generated when ingredient stock falls below minimum or reorder level.
    Shows current stock vs minimum required.
    """
    alerts, total = await InventoryService.get_low_stock_alerts(
        db,
        restaurant_id=restaurant_id,
        is_resolved=is_resolved,
        skip=skip,
        limit=limit
    )
    
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "alerts": [LowStockAlertResponse.model_validate(alert) for alert in alerts]
        },
        message="Low stock alerts retrieved successfully"
    )


@router.post("/alerts/low-stock/{alert_id}/resolve", response_model=dict)
async def resolve_low_stock_alert(
    alert_id: str,
    action_taken: str = Query(..., description="Action taken to resolve"),
    po_id: Optional[str] = Query(None, description="Purchase order ID if created"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resolve low stock alert
    
    Mark alert as resolved with action taken.
    Link to purchase order if created.
    """
    try:
        alert = await InventoryService.resolve_low_stock_alert(
            db,
            alert_id,
            action_taken,
            po_id,
            current_user.id
        )
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return success_response(
            data=LowStockAlertResponse.model_validate(alert),
            message="Alert resolved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="Failed to resolve alert",
            error=str(e)
        )


# ==================== AUTO DEDUCTION ENDPOINT ====================

@router.post("/stock/auto-deduct", response_model=dict)
async def auto_deduct_stock_for_order(
    restaurant_id: str = Query(..., description="Restaurant ID"),
    product_id: str = Query(..., description="Product/Menu item ID"),
    quantity: int = Query(..., description="Quantity sold", ge=1),
    order_id: str = Query(..., description="Order ID for reference"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Auto stock deduction on sale
    
    **AUTOMATICALLY CALLED WHEN ORDER IS CREATED**
    
    Based on recipe mapping, deducts ingredient stock automatically.
    Creates stock transactions for each ingredient used.
    
    Example: When 2 burgers are sold, it automatically deducts:
    - 300g chicken (2x 150g per burger)
    - 4 buns (2x 2 per burger)
    - etc.
    """
    try:
        transactions = await InventoryService.deduct_stock_for_order(
            db,
            restaurant_id=restaurant_id,
            product_id=product_id,
            quantity=quantity,
            order_id=order_id,
            user_id=current_user.id
        )
        
        if not transactions:
            return success_response(
                data={
                    "transactions_created": 0,
                    "message": "No recipe found for this product or no ingredients to deduct"
                },
                message="No stock deduction performed"
            )
        
        return success_response(
            data={
                "transactions_created": len(transactions),
                "transactions": [StockTransactionResponse.model_validate(txn) for txn in transactions]
            },
            message=f"Stock deducted for {quantity} unit(s) of product"
        )
    except Exception as e:
        return error_response(
            message="Failed to deduct stock",
            error=str(e)
        )

