"""
Row management service layer
"""
from datetime import datetime
from typing import List, Optional, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.model import Category, ComboProduct, Product
from app.modules.product.schema import CategoryResponse, ComboProductResponse, ProductResponse
from app.modules.product.service import CategoryService, ComboProductService, ProductService
from app.modules.row_management.model import RowManagement, RowType
from app.modules.row_management.schema import (
    RowManagementCreate,
    RowManagementOpenFetchResponse,
    RowManagementResponse,
    RowManagementUpdate,
)

T = TypeVar("T")


def _entities_in_id_order(entities: List[T], id_order: List[str]) -> List[T]:
    """Preserve list order from id_order; skip IDs with no matching entity."""
    by_id = {getattr(e, "id"): e for e in entities}
    return [by_id[i] for i in id_order if i in by_id]


class DuplicateError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class RowManagementService:
    """Service for row management operations"""

    @staticmethod
    async def _validate_reference_ids(
        db: AsyncSession,
        restaurant_id: str,
        row_type: RowType,
        category_ids: Optional[list[str]],
        product_ids: Optional[list[str]],
        combo_product_ids: Optional[list[str]],
    ) -> None:
        if row_type == RowType.CATEGORY and category_ids:
            result = await db.execute(
                select(Category.id).where(
                    Category.restaurant_id == restaurant_id,
                    Category.id.in_(category_ids),
                    Category.deleted_at.is_(None),
                )
            )
            found_ids = {item[0] for item in result.all()}
            missing = sorted(set(category_ids) - found_ids)
            if missing:
                raise ValueError(f"Invalid category_ids: {', '.join(missing)}")

        if row_type == RowType.PRODUCT and product_ids:
            result = await db.execute(
                select(Product.id).where(
                    Product.restaurant_id == restaurant_id,
                    Product.id.in_(product_ids),
                )
            )
            found_ids = {item[0] for item in result.all()}
            missing = sorted(set(product_ids) - found_ids)
            if missing:
                raise ValueError(f"Invalid product_ids: {', '.join(missing)}")

        if row_type == RowType.COMBO_PRODUCT and combo_product_ids:
            result = await db.execute(
                select(ComboProduct.id).where(
                    ComboProduct.restaurant_id == restaurant_id,
                    ComboProduct.id.in_(combo_product_ids),
                )
            )
            found_ids = {item[0] for item in result.all()}
            missing = sorted(set(combo_product_ids) - found_ids)
            if missing:
                raise ValueError(f"Invalid combo_product_ids: {', '.join(missing)}")

    @staticmethod
    async def create_row(db: AsyncSession, row_data: RowManagementCreate) -> RowManagement:
        stmt = select(RowManagement).where(
            RowManagement.restaurant_id == row_data.restaurant_id,
            func.lower(RowManagement.name) == func.lower(row_data.name),
            RowManagement.deleted_at.is_(None),
        )
        if await db.scalar(stmt):
            raise DuplicateError("Row management with this name already exists in this restaurant", field="name")

        await RowManagementService._validate_reference_ids(
            db,
            row_data.restaurant_id,
            row_data.row_type,
            row_data.category_ids,
            row_data.product_ids,
            row_data.combo_product_ids,
        )

        row = RowManagement(**row_data.model_dump())
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def get_row_by_id(db: AsyncSession, row_id: str) -> Optional[RowManagement]:
        result = await db.execute(
            select(RowManagement).where(
                RowManagement.id == row_id,
                RowManagement.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_rows_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        row_type: Optional[RowType] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RowManagement]:
        query = select(RowManagement).where(
            RowManagement.restaurant_id == restaurant_id,
            RowManagement.deleted_at.is_(None),
        )
        if row_type:
            query = query.where(RowManagement.row_type == row_type)
        if active_only:
            query = query.where(RowManagement.active == True)

        query = query.order_by(RowManagement.sort_order, RowManagement.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_rows_by_restaurant_with_catalog(
        db: AsyncSession,
        restaurant_id: str,
        row_type: Optional[RowType] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RowManagementOpenFetchResponse]:
        """
        Same as get_rows_by_restaurant, plus category_items / product_items / combo_product_items
        populated from *_ids (order matches the stored ID lists; missing IDs are skipped).
        """
        rows = await RowManagementService.get_rows_by_restaurant(
            db, restaurant_id, row_type, active_only, skip, limit
        )
        cat_ids: list[str] = []
        prod_ids: list[str] = []
        combo_ids: list[str] = []
        for row in rows:
            if row.category_ids:
                cat_ids.extend(row.category_ids)
            if row.product_ids:
                prod_ids.extend(row.product_ids)
            if row.combo_product_ids:
                combo_ids.extend(row.combo_product_ids)

        uniq_cat = list(dict.fromkeys(cat_ids))
        uniq_prod = list(dict.fromkeys(prod_ids))
        uniq_combo = list(dict.fromkeys(combo_ids))

        categories = await CategoryService.get_categories_by_ids(db, restaurant_id, uniq_cat)
        products = await ProductService.get_products_by_ids(db, uniq_prod, restaurant_id=restaurant_id)
        combos = await ComboProductService.get_combos_by_ids(db, restaurant_id, uniq_combo)

        out: list[RowManagementOpenFetchResponse] = []
        for row in rows:
            base_kw = RowManagementResponse.model_validate(row).model_dump()
            cat_order = row.category_ids or []
            prod_order = row.product_ids or []
            combo_order = row.combo_product_ids or []

            cat_entities = _entities_in_id_order(categories, cat_order) if cat_order else []
            prod_entities = _entities_in_id_order(products, prod_order) if prod_order else []
            combo_entities = _entities_in_id_order(combos, combo_order) if combo_order else []

            out.append(
                RowManagementOpenFetchResponse(
                    **base_kw,
                    category_items=[CategoryResponse.model_validate(c) for c in cat_entities]
                    if cat_entities
                    else None,
                    product_items=[ProductResponse.model_validate(p) for p in prod_entities]
                    if prod_entities
                    else None,
                    combo_product_items=[ComboProductResponse.model_validate(c) for c in combo_entities]
                    if combo_entities
                    else None,
                )
            )
        return out

    @staticmethod
    async def update_row(
        db: AsyncSession,
        row_id: str,
        row_data: RowManagementUpdate,
    ) -> Optional[RowManagement]:
        row = await RowManagementService.get_row_by_id(db, row_id)
        if not row:
            return None

        if row_data.name:
            stmt = select(RowManagement).where(
                RowManagement.restaurant_id == row.restaurant_id,
                RowManagement.id != row_id,
                func.lower(RowManagement.name) == func.lower(row_data.name),
                RowManagement.deleted_at.is_(None),
            )
            if await db.scalar(stmt):
                raise DuplicateError("Row management with this name already exists in this restaurant", field="name")

        update_data = row_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(row, field, value)

        await RowManagementService._validate_reference_ids(
            db,
            row.restaurant_id,
            row.row_type,
            row.category_ids,
            row.product_ids,
            row.combo_product_ids,
        )

        if row.start_at and row.end_at and row.end_at < row.start_at:
            raise ValueError("end_at must be greater than or equal to start_at")
        if row.row_type == RowType.CATEGORY and not row.category_ids:
            raise ValueError("category_ids is required for category row type")
        if row.row_type == RowType.PRODUCT and not row.product_ids:
            raise ValueError("product_ids is required for product row type")
        if row.row_type == RowType.COMBO_PRODUCT and not row.combo_product_ids:
            raise ValueError("combo_product_ids is required for combo_product row type")
        if row.row_type in {RowType.SINGLE_BANNER, RowType.ADS_BANNER} and not any(
            [row.image, row.mobile_image, row.desktop_image]
        ):
            raise ValueError("At least one banner image is required for banner row types")
        if row.row_type == RowType.ADS_VIDEO and not row.video_url:
            raise ValueError("video_url is required for ads_video row type")

        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def delete_row(db: AsyncSession, row_id: str) -> bool:
        row = await RowManagementService.get_row_by_id(db, row_id)
        if not row:
            return False

        row.deleted_at = datetime.utcnow()
        await db.commit()
        return True
