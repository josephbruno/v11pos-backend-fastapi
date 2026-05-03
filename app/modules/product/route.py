"""
Product catalog and inventory API routes
"""
from fastapi import APIRouter, Depends, status, Request, UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Any
import json

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import success_response, error_response
from app.modules.user.model import User
from app.modules.product.schema import *
from app.modules.product.service import (
    CategoryService, ProductService, ModifierService,
    InventoryService, ComboProductService, DuplicateError
)
from app.services.storage_service import (
    upload_file,
    delete_file,
    get_file_url,
    get_object_name_from_url,
)


router = APIRouter(prefix="/products", tags=["Products"])

def _multipart_request_body(schema: dict) -> dict:
    return {
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": schema
                }
            }
        }
    }


CATEGORY_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "description": {"type": "string"},
            "image": {"type": "string", "format": "binary"},
        },
        "required": ["restaurant_id", "name", "slug"],
    }
)

CATEGORY_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "description": {"type": "string"},
            "image": {"type": "string", "format": "binary"},
        },
    }
)

PRODUCT_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "name": {"type": "string"},
            "price": {"type": "integer"},
            "category_id": {"type": "string"},
            "image": {"type": "string", "format": "binary"},
        },
        "required": ["restaurant_id", "name", "price", "category_id"],
    }
)

PRODUCT_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "integer"},
            "category_id": {"type": "string"},
            "image": {"type": "string", "format": "binary"},
        },
    }
)

COMBO_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "name": {"type": "string"},
            "price": {"type": "integer"},
            "category_id": {"type": "string"},
            "image": {"type": "string", "format": "binary"},
        },
        "required": ["restaurant_id", "name", "price", "category_id"],
    }
)

COMBO_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "description": {"type": "string"},
            "price": {"type": "integer"},
            "category_id": {"type": "string"},
            "available": {"type": "boolean"},
            "featured": {"type": "boolean"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "valid_from": {"type": "string", "format": "date-time"},
            "valid_until": {"type": "string", "format": "date-time"},
            "max_quantity_per_order": {"type": "integer"},
            "image": {"type": "string", "format": "binary"},
        },
    }
)

MODIFIER_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "name": {"type": "string"},
            "type": {"type": "string"},
            "icon": {"type": "string", "format": "binary"},
        },
        "required": ["restaurant_id", "name"],
    }
)

MODIFIER_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string"},
            "icon": {"type": "string", "format": "binary"},
        },
    }
)
async def _parse_payload(
    request: Request,
    file_field: Optional[str]
) -> Tuple[dict, Optional[UploadFile]]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = await request.json()
        return data, None

    form = await request.form()
    data: dict[str, Any] = {}
    upload: Optional[UploadFile] = None

    for key, value in form.multi_items():
        if isinstance(value, (UploadFile, StarletteUploadFile)) or (
            hasattr(value, "filename") and hasattr(value, "file")
        ):
            if file_field and key == file_field:
                upload = value
            continue
        if key in data:
            existing = data[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                data[key] = [existing, value]
        else:
            data[key] = value

    # Parse JSON strings for complex data types
    for key, value in data.items():
        if isinstance(value, str):
            try:
                # Try to parse as JSON
                parsed = json.loads(value)
                data[key] = parsed
            except (json.JSONDecodeError, TypeError):
                # Keep as string if not valid JSON
                pass

    return data, upload


async def _upload_and_replace(
    current_url: Optional[str],
    new_file: Optional[UploadFile],
    folder: str
) -> Optional[str]:
    if not new_file:
        return None

    object_name = await upload_file(new_file, folder=folder)
    new_url = get_file_url(object_name)

    if current_url:
        old_object_name = get_object_name_from_url(current_url)
        if old_object_name:
            try:
                delete_file(old_object_name)
            except Exception:
                # Best-effort cleanup; do not block the update on delete errors
                pass

    return new_url

# Category Endpoints

@router.post("/categories", status_code=status.HTTP_201_CREATED, openapi_extra=CATEGORY_CREATE_DOC)
async def create_category(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category"""
    try:
        data, image_file = await _parse_payload(request, file_field="image")
        if image_file:
            image_url = await _upload_and_replace(None, image_file, folder="categories")
            data["image"] = image_url

        category_data = CategoryCreate(**data)
        category = await CategoryService.create_category(db, category_data)
        # Use current_user.timezone for automatic datetime conversion
        return success_response(
            message="Category created successfully",
            data=CategoryResponse.model_validate(category).model_dump(),
            timezone=getattr(current_user, 'timezone', None)
        )
    except DuplicateError as e:
        return error_response(
            message="Failed to create category",
            error_code="DUPLICATE_ENTRY",
            error_details=str(e),
            field=e.field,
            status_code=status.HTTP_409_CONFLICT
        )
    except ValueError as e:
        return error_response(
            message="Failed to create category",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
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
    current_user: User = Depends(get_current_active_user),
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
        # Use current_user.timezone for automatic datetime conversion
        return success_response(
            message="Categories retrieved successfully",
            data=categories_data,
            timezone=getattr(current_user, 'timezone', None)
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
    current_user: User = Depends(get_current_active_user),
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
        
        # Use current_user.timezone for automatic datetime conversion
        return success_response(
            message="Category retrieved successfully",
            data=CategoryResponse.model_validate(category).model_dump(),
            timezone=getattr(current_user, 'timezone', None)
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve category",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )

@router.post("/categories/{category_id}", openapi_extra=CATEGORY_UPDATE_DOC)
@router.patch("/categories/{category_id}", openapi_extra=CATEGORY_UPDATE_DOC)
@router.put("/categories/{category_id}", openapi_extra=CATEGORY_UPDATE_DOC)
async def update_category(
    category_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update category"""
    try:
        existing = await CategoryService.get_category_by_id(db, category_id)
        if not existing:
            return error_response(
                message="Category not found",
                error_code="NOT_FOUND",
                error_details=f"Category with ID {category_id} not found"
            )

        data, image_file = await _parse_payload(request, file_field="image")
        image_url = await _upload_and_replace(
            existing.image,
            image_file,
            folder="categories"
        )
        if image_url:
            data["image"] = image_url

        category_data = CategoryUpdate(**data)
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
    except DuplicateError as e:
        return error_response(
            message="Failed to update category",
            error_code="DUPLICATE_ENTRY",
            error_details=str(e),
            field=e.field,
            status_code=status.HTTP_409_CONFLICT
        )
    except ValueError as e:
        return error_response(
            message="Failed to update category",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
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

@router.post("", status_code=status.HTTP_201_CREATED, openapi_extra=PRODUCT_CREATE_DOC)
async def create_product(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product"""
    try:
        data, image_file = await _parse_payload(request, file_field="image")
        if image_file:
            image_url = await _upload_and_replace(None, image_file, folder="products")
            data["image"] = image_url

        product_data = ProductCreate(**data)
        product = await ProductService.create_product(db, product_data)
        return success_response(
            message="Product created successfully",
            data=ProductResponse.model_validate(product).model_dump()
        )
    except ValueError as e:
        return error_response(
            message="Failed to create product",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
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


@router.put("/{product_id}", openapi_extra=PRODUCT_UPDATE_DOC)
async def update_product(
    product_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update product"""
    try:
        existing = await ProductService.get_product_by_id(db, product_id)
        if not existing:
            return error_response(
                message="Product not found",
                error_code="NOT_FOUND",
                error_details=f"Product with ID {product_id} not found"
            )

        data, image_file = await _parse_payload(request, file_field="image")
        image_url = await _upload_and_replace(
            existing.image,
            image_file,
            folder="products"
        )
        if image_url:
            data["image"] = image_url

        product_data = ProductUpdate(**data)
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
    except ValueError as e:
        return error_response(
            message="Failed to update product",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
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

@router.get("/modifiers/restaurant/{restaurant_id}")
async def get_modifiers(
    restaurant_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get modifiers for a restaurant"""
    try:
        modifiers = await ModifierService.get_modifiers_by_restaurant(
            db, restaurant_id, skip, limit
        )
        modifiers_data = [
            ModifierResponse.model_validate(m).model_dump()
            for m in modifiers
        ]
        return success_response(
            message="Modifiers retrieved successfully",
            data=modifiers_data,
            timezone=getattr(current_user, "timezone", None)
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve modifiers",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )

@router.post("/modifiers", status_code=status.HTTP_201_CREATED, openapi_extra=MODIFIER_CREATE_DOC)
async def create_modifier(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new modifier"""
    try:
        data, icon_file = await _parse_payload(request, file_field="icon")
        if icon_file:
            icon_url = await _upload_and_replace(None, icon_file, folder="modifiers")
            data["icon_url"] = icon_url

        modifier_data = ModifierCreate(**data)
        modifier = await ModifierService.create_modifier(db, modifier_data)
        return success_response(
            message="Modifier created successfully",
            data=ModifierResponse.model_validate(modifier).model_dump()
        )
    except ValueError as e:
        return error_response(
            message="Failed to create modifier",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message="Failed to create modifier",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/modifiers/{modifier_id}", openapi_extra=MODIFIER_UPDATE_DOC)
async def update_modifier(
    modifier_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update modifier"""
    try:
        existing = await ModifierService.get_modifier_by_id(db, modifier_id)
        if not existing:
            return error_response(
                message="Modifier not found",
                error_code="NOT_FOUND",
                error_details=f"Modifier with ID {modifier_id} not found"
            )

        data, icon_file = await _parse_payload(request, file_field="icon")
        icon_url = await _upload_and_replace(
            existing.icon_url,
            icon_file,
            folder="modifiers"
        )
        if icon_url:
            data["icon_url"] = icon_url

        modifier_data = ModifierUpdate(**data)
        modifier = await ModifierService.update_modifier(db, modifier_id, modifier_data)
        if not modifier:
            return error_response(
                message="Modifier not found",
                error_code="NOT_FOUND",
                error_details=f"Modifier with ID {modifier_id} not found"
            )

        return success_response(
            message="Modifier updated successfully",
            data=ModifierResponse.model_validate(modifier).model_dump()
        )
    except ValueError as e:
        return error_response(
            message="Failed to update modifier",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message="Failed to update modifier",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.delete("/modifiers/{modifier_id}")
async def delete_modifier(
    modifier_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete modifier"""
    try:
        deleted = await ModifierService.delete_modifier(db, modifier_id)
        if not deleted:
            return error_response(
                message="Modifier not found",
                error_code="NOT_FOUND",
                error_details=f"Modifier with ID {modifier_id} not found"
            )

        return success_response(
            message="Modifier deleted successfully",
            data={"deleted_modifier_id": modifier_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to delete modifier",
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


@router.get("/modifiers/{modifier_id}/options")
async def get_modifier_options(
    modifier_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get options for a modifier"""
    try:
        options = await ModifierService.get_modifier_options(db, modifier_id)
        return success_response(
            message="Modifier options retrieved successfully",
            data=[ModifierOptionResponse.model_validate(o).model_dump() for o in options],
            timezone=getattr(current_user, "timezone", None)
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve modifier options",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/modifiers/options/{option_id}")
async def update_modifier_option(
    option_id: str,
    option_data: ModifierOptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a modifier option"""
    try:
        option = await ModifierService.update_modifier_option(db, option_id, option_data)
        if not option:
            return error_response(
                message="Modifier option not found",
                error_code="NOT_FOUND",
                error_details=f"Modifier option with ID {option_id} not found"
            )

        return success_response(
            message="Modifier option updated successfully",
            data=ModifierOptionResponse.model_validate(option).model_dump(),
            timezone=getattr(current_user, "timezone", None)
        )
    except Exception as e:
        return error_response(
            message="Failed to update modifier option",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.delete("/modifiers/options/{option_id}")
async def delete_modifier_option(
    option_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a modifier option"""
    try:
        deleted = await ModifierService.delete_modifier_option(db, option_id)
        if not deleted:
            return error_response(
                message="Modifier option not found",
                error_code="NOT_FOUND",
                error_details=f"Modifier option with ID {option_id} not found"
            )

        return success_response(
            message="Modifier option deleted successfully",
            data={"deleted_option_id": option_id},
            timezone=getattr(current_user, "timezone", None)
        )
    except Exception as e:
        return error_response(
            message="Failed to delete modifier option",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/modifiers/restaurant/{restaurant_id}/hierarchical")
async def get_hierarchical_modifiers(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get modifiers with nested options for a restaurant"""
    try:
        modifiers = await ModifierService.get_modifiers_with_options_by_restaurant(
            db, restaurant_id
        )
        return success_response(
            message="Hierarchical modifiers retrieved successfully",
            data=[ModifierWithOptionsResponse.model_validate(m).model_dump() for m in modifiers],
            timezone=getattr(current_user, "timezone", None)
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve hierarchical modifiers",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Combo Product Endpoints

@router.post("/combos", status_code=status.HTTP_201_CREATED, openapi_extra=COMBO_CREATE_DOC)
async def create_combo(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new combo product"""
    try:
        data, image_file = await _parse_payload(request, file_field="image")
        if image_file:
            image_url = await _upload_and_replace(None, image_file, folder="combos")
            data["image"] = image_url

        combo_data = ComboProductCreate(**data)
        combo = await ComboProductService.create_combo(db, combo_data)
        return success_response(
            message="Combo product created successfully",
            data=ComboProductResponse.model_validate(combo).model_dump()
        )
    except ValueError as e:
        return error_response(
            message="Failed to create combo product",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message="Failed to create combo product",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/combos/{combo_id}", openapi_extra=COMBO_UPDATE_DOC)
async def update_combo(
    combo_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing combo product"""
    try:
        existing = await ComboProductService.get_combo_by_id(db, combo_id)
        if not existing:
            return error_response(
                message="Combo product not found",
                error_code="NOT_FOUND",
                error_details=f"Combo product with ID {combo_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        data, image_file = await _parse_payload(request, file_field="image")
        image_url = await _upload_and_replace(
            existing.image,
            image_file,
            folder="combos",
        )
        if image_url:
            data["image"] = image_url

        combo_data = ComboProductUpdate(**data)
        combo = await ComboProductService.update_combo(db, combo_id, combo_data)
        if not combo:
            return error_response(
                message="Combo product not found",
                error_code="NOT_FOUND",
                error_details=f"Combo product with ID {combo_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            message="Combo product updated successfully",
            data=ComboProductResponse.model_validate(combo).model_dump(),
        )
    except ValueError as e:
        return error_response(
            message="Failed to update combo product",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to update combo product",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
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


@router.post("/combos/{combo_id}/items", status_code=status.HTTP_201_CREATED)
async def add_combo_items(
    combo_id: str,
    payload: ComboItemsBulkCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add items to an existing combo product"""
    try:
        combo = await ComboProductService.get_combo_by_id(db, combo_id)
        if not combo:
            return error_response(
                message="Combo product not found",
                error_code="NOT_FOUND",
                error_details=f"Combo product with ID {combo_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate all referenced products exist and belong to the same restaurant
        referenced_product_ids: set[str] = set()
        for item in payload.items:
            referenced_product_ids.add(item.product_id)
            if item.choices:
                referenced_product_ids.update(item.choices)

        products = await ProductService.get_products_by_ids(db, list(referenced_product_ids))
        products_by_id = {p.id: p for p in products}

        missing_ids = sorted(pid for pid in referenced_product_ids if pid not in products_by_id)
        if missing_ids:
            return error_response(
                message="One or more products not found",
                error_code="NOT_FOUND",
                error_details={"missing_product_ids": missing_ids},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        invalid_restaurant_ids = sorted(
            pid for pid, p in products_by_id.items() if p.restaurant_id != combo.restaurant_id
        )
        if invalid_restaurant_ids:
            return error_response(
                message="One or more products belong to a different restaurant",
                error_code="VALIDATION_ERROR",
                error_details={"invalid_product_ids": invalid_restaurant_ids},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        items_data = [
            ComboItemCreate(
                restaurant_id=combo.restaurant_id,
                combo_id=combo_id,
                **item.model_dump(),
            )
            for item in payload.items
        ]
        items = await ComboProductService.add_combo_items(db, items_data)

        return success_response(
            message="Combo items added successfully",
            data=[ComboItemResponse.model_validate(i).model_dump() for i in items],
        )
    except Exception as e:
        return error_response(
            message="Failed to add combo items",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/combos/{combo_id}/items")
async def get_combo_items(
    combo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get items for a combo product"""
    try:
        combo = await ComboProductService.get_combo_by_id(db, combo_id)
        if not combo:
            return error_response(
                message="Combo product not found",
                error_code="NOT_FOUND",
                error_details=f"Combo product with ID {combo_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        items = await ComboProductService.get_combo_items(db, combo_id)
        return success_response(
            message="Combo items retrieved successfully",
            data=[ComboItemResponse.model_validate(i).model_dump() for i in items],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve combo items",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
