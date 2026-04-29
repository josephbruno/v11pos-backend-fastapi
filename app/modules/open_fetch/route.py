"""
Read-only "open fetch" endpoints for UI screens.

These endpoints intentionally reuse existing services/schemas and do not change
the current product/homebanner/row-management workflows.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import error_response, success_response
from app.modules.homebanner.schema import HomeBannerResponse
from app.modules.homebanner.service import HomeBannerService
from app.modules.product.schema import (
    CategoryResponse,
    ComboProductResponse,
    ModifierResponse,
    ProductResponse,
)
from app.modules.product.service import (
    CategoryService,
    ComboProductService,
    ModifierService,
    ProductService,
)
from app.modules.row_management.model import RowType
from app.modules.row_management.schema import RowManagementResponse
from app.modules.row_management.service import RowManagementService
from app.modules.user.model import User


router = APIRouter(prefix="/open", tags=["Open Fetch"])


@router.get("/categories/restaurant/{restaurant_id}")
async def fetch_categories(
    restaurant_id: str,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch categories with pagination."""
    try:
        categories = await CategoryService.get_categories_by_restaurant(
            db, restaurant_id, active_only, skip, limit
        )
        return success_response(
            message="Categories retrieved successfully",
            data=[CategoryResponse.model_validate(item).model_dump() for item in categories],
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve categories",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/products/restaurant/{restaurant_id}")
async def fetch_products(
    restaurant_id: str,
    category_id: Optional[str] = None,
    available_only: bool = False,
    featured_only: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Fetch products with pagination."""
    try:
        products = await ProductService.get_products_by_restaurant(
            db, restaurant_id, category_id, available_only, featured_only, search, skip, limit
        )
        return success_response(
            message="Products retrieved successfully",
            data=[ProductResponse.model_validate(item).model_dump() for item in products],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve products",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/combos/restaurant/{restaurant_id}")
async def fetch_combo_products(
    restaurant_id: str,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Fetch combo products with pagination."""
    try:
        combos = await ComboProductService.get_combos_by_restaurant(
            db, restaurant_id, available_only, skip, limit
        )
        return success_response(
            message="Combo products retrieved successfully",
            data=[ComboProductResponse.model_validate(item).model_dump() for item in combos],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve combo products",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/modifiers/restaurant/{restaurant_id}")
async def fetch_modifiers(
    restaurant_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch modifiers with pagination."""
    try:
        modifiers = await ModifierService.get_modifiers_by_restaurant(db, restaurant_id, skip, limit)
        return success_response(
            message="Modifiers retrieved successfully",
            data=[ModifierResponse.model_validate(item).model_dump() for item in modifiers],
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve modifiers",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/homebanners/restaurant/{restaurant_id}")
async def fetch_homebanners(
    restaurant_id: str,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch home banners with pagination."""
    try:
        banners = await HomeBannerService.get_banners_by_restaurant(
            db, restaurant_id, active_only, skip, limit
        )
        return success_response(
            message="Home banners retrieved successfully",
            data=[HomeBannerResponse.model_validate(item).model_dump() for item in banners],
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve home banners",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/row-management/restaurant/{restaurant_id}")
async def fetch_row_management(
    restaurant_id: str,
    row_type: Optional[RowType] = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch row management rows with pagination."""
    try:
        rows = await RowManagementService.get_rows_by_restaurant(
            db, restaurant_id, row_type, active_only, skip, limit
        )
        return success_response(
            message="Row management retrieved successfully",
            data=[RowManagementResponse.model_validate(item).model_dump(by_alias=True) for item in rows],
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve row management",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )

