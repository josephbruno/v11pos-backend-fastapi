"""
Product catalog and inventory API routes
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import success_response, error_response
from app.modules.user.model import User
from app.modules.product.schema import *
from app.modules.product.service import (
    CategoryService, ProductService, ModifierService,
    InventoryService, ComboProductService
)


router = APIRouter(prefix="/products", tags=["Products"])


# Category Endpoints

@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category"""
    try:
        category = await CategoryService.create_category(db, category_data)
        return success_response(
            message="Category created successfully",
            data=CategoryResponse.model_validate(category).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to create category",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/categories/restaurant/{restaurant_id}")
async def get_categories(
    restaurant_id: str,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get categories for a restaurant"""
    try:
        categories = await CategoryService.get_categories_by_restaurant(
            db, restaurant_id, active_only, skip, limit
        )
        categories_data = [
            CategoryResponse.model_validate(c).model_dump()
            for c in categories
        ]
        return success_response(
            message="Categories retrieved successfully",
            data=categories_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve categories",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/categories/{category_id}")
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get category by ID"""
    try:
        category = await CategoryService.get_category_by_id(db, category_id)
        if not category:
            return error_response(
                message="Category not found",
                error_code="NOT_FOUND",
                error_details=f"Category with ID {category_id} not found"
            )
        
        return success_response(
            message="Category retrieved successfully",
            data=CategoryResponse.model_validate(category).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve category",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update category"""
    try:
        category = await CategoryService.update_category(db, category_id, category_data)
        if not category:
            return error_response(
                message="Category not found",
                error_code="NOT_FOUND",
                error_details=f"Category with ID {category_id} not found"
            )
        
        return success_response(
            message="Category updated successfully",
            data=CategoryResponse.model_validate(category).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to update category",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete category"""
    try:
        deleted = await CategoryService.delete_category(db, category_id)
        if not deleted:
            return error_response(
                message="Category not found",
                error_code="NOT_FOUND",
                error_details=f"Category with ID {category_id} not found"
            )
        
        return success_response(
            message="Category deleted successfully",
            data={"deleted_category_id": category_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to delete category",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Product Endpoints

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product"""
    try:
        product = await ProductService.create_product(db, product_data)
        return success_response(
            message="Product created successfully",
            data=ProductResponse.model_validate(product).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to create product",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/restaurant/{restaurant_id}")
async def get_products(
    restaurant_id: str,
    category_id: Optional[str] = None,
    available_only: bool = False,
    featured_only: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get products for a restaurant"""
    try:
        products = await ProductService.get_products_by_restaurant(
            db, restaurant_id, category_id, available_only,
            featured_only, search, skip, limit
        )
        products_data = [
            ProductResponse.model_validate(p).model_dump()
            for p in products
        ]
        return success_response(
            message="Products retrieved successfully",
            data=products_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve products",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/restaurant/{restaurant_id}/low-stock")
async def get_low_stock_products(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get products with low stock"""
    try:
        products = await ProductService.get_low_stock_products(db, restaurant_id)
        products_data = [
            ProductResponse.model_validate(p).model_dump()
            for p in products
        ]
        return success_response(
            message="Low stock products retrieved successfully",
            data=products_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve low stock products",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID"""
    try:
        product = await ProductService.get_product_by_id(db, product_id)
        if not product:
            return error_response(
                message="Product not found",
                error_code="NOT_FOUND",
                error_details=f"Product with ID {product_id} not found"
            )
        
        return success_response(
            message="Product retrieved successfully",
            data=ProductResponse.model_validate(product).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve product",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update product"""
    try:
        product = await ProductService.update_product(db, product_id, product_data)
        if not product:
            return error_response(
                message="Product not found",
                error_code="NOT_FOUND",
                error_details=f"Product with ID {product_id} not found"
            )
        
        return success_response(
            message="Product updated successfully",
            data=ProductResponse.model_validate(product).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to update product",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete product"""
    try:
        deleted = await ProductService.delete_product(db, product_id)
        if not deleted:
            return error_response(
                message="Product not found",
                error_code="NOT_FOUND",
                error_details=f"Product with ID {product_id} not found"
            )
        
        return success_response(
            message="Product deleted successfully",
            data={"deleted_product_id": product_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to delete product",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Inventory Endpoints

@router.post("/inventory/adjust", status_code=status.HTTP_201_CREATED)
async def adjust_stock(
    restaurant_id: str,
    adjustment: StockAdjustment,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Adjust product stock"""
    try:
        transaction = await InventoryService.adjust_stock(
            db, restaurant_id, adjustment, current_user.id
        )
        return success_response(
            message="Stock adjusted successfully",
            data=InventoryTransactionResponse.model_validate(transaction).model_dump()
        )
    except ValueError as e:
        return error_response(
            message="Stock adjustment failed",
            error_code="INVALID_OPERATION",
            error_details=str(e)
        )
    except Exception as e:
        return error_response(
            message="Failed to adjust stock",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/inventory/product/{product_id}/transactions")
async def get_product_transactions(
    product_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory transactions for a product"""
    try:
        transactions = await InventoryService.get_product_transactions(
            db, product_id, skip, limit
        )
        transactions_data = [
            InventoryTransactionResponse.model_validate(t).model_dump()
            for t in transactions
        ]
        return success_response(
            message="Transactions retrieved successfully",
            data=transactions_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve transactions",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/inventory/restaurant/{restaurant_id}/transactions")
async def get_restaurant_transactions(
    restaurant_id: str,
    transaction_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory transactions for a restaurant"""
    try:
        transactions = await InventoryService.get_restaurant_transactions(
            db, restaurant_id, transaction_type, skip, limit
        )
        transactions_data = [
            InventoryTransactionResponse.model_validate(t).model_dump()
            for t in transactions
        ]
        return success_response(
            message="Transactions retrieved successfully",
            data=transactions_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve transactions",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Modifier Endpoints

@router.post("/modifiers", status_code=status.HTTP_201_CREATED)
async def create_modifier(
    modifier_data: ModifierCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new modifier"""
    try:
        modifier = await ModifierService.create_modifier(db, modifier_data)
        return success_response(
            message="Modifier created successfully",
            data=ModifierResponse.model_validate(modifier).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to create modifier",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/modifiers/options", status_code=status.HTTP_201_CREATED)
async def create_modifier_option(
    option_data: ModifierOptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new modifier option"""
    try:
        option = await ModifierService.create_modifier_option(db, option_data)
        return success_response(
            message="Modifier option created successfully",
            data=ModifierOptionResponse.model_validate(option).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to create modifier option",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Combo Product Endpoints

@router.post("/combos", status_code=status.HTTP_201_CREATED)
async def create_combo(
    combo_data: ComboProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new combo product"""
    try:
        combo = await ComboProductService.create_combo(db, combo_data)
        return success_response(
            message="Combo product created successfully",
            data=ComboProductResponse.model_validate(combo).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to create combo product",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/combos/restaurant/{restaurant_id}")
async def get_combos(
    restaurant_id: str,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get combo products for a restaurant"""
    try:
        combos = await ComboProductService.get_combos_by_restaurant(
            db, restaurant_id, available_only, skip, limit
        )
        combos_data = [
            ComboProductResponse.model_validate(c).model_dump()
            for c in combos
        ]
        return success_response(
            message="Combo products retrieved successfully",
            data=combos_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve combo products",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )
