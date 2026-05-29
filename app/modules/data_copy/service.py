from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.data_copy.model import CopyLog, CopyStatus, CopyType, DataCopy
from app.modules.data_copy.schema import (
    CopyOptions,
    CopyStatistics,
    DataCopyCreate,
    DataCopyListResponse,
    DataCopyResponse,
)
from app.modules.product.model import (
    Category,
    ComboItem,
    ComboProduct,
    Modifier,
    ModifierOption,
    Product,
    ProductModifier,
)
from app.modules.restaurant.model import Restaurant
from app.services.storage_service import copy_file_url, copy_file_urls_in_value

logger = logging.getLogger(__name__)


class DataCopyService:
    """Service for copying restaurant data in Celery-backed background jobs."""

    CATEGORY_MEDIA_FIELDS = ("image", "icon", "banner_image", "thumbnail")
    PRODUCT_MEDIA_FIELDS = ("image", "thumbnail", "images", "gallery")
    MODIFIER_MEDIA_FIELDS = ("icon_url",)
    COMBO_MEDIA_FIELDS = ("image",)

    @staticmethod
    async def generate_copy_number() -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"CPY-{timestamp}-{random_suffix}"

    @staticmethod
    async def perform_copy(
        db: AsyncSession,
        copy_data: DataCopyCreate,
        current_user_id: str,
    ) -> List[DataCopyResponse]:
        """
        Create copy operation rows and enqueue one Celery task per destination.
        The actual data copy happens in the worker.
        """
        from app.modules.data_copy.tasks import run_data_copy

        source = await db.get(Restaurant, copy_data.source_restaurant_id)
        if not source:
            raise ValueError("Source restaurant not found")

        operations: List[DataCopy] = []
        for destination_id in copy_data.destination_restaurant_ids:
            if destination_id == copy_data.source_restaurant_id:
                raise ValueError("Destination restaurant cannot be the same as source restaurant")

            destination = await db.get(Restaurant, destination_id)
            if not destination:
                raise ValueError(f"Destination restaurant not found: {destination_id}")

            operation = await DataCopyService.create_copy_operation(
                db=db,
                source_restaurant_id=copy_data.source_restaurant_id,
                destination_restaurant_id=destination_id,
                copy_data=copy_data,
                current_user_id=current_user_id,
            )
            task = run_data_copy.delay(operation.id)
            operation.copy_metadata = {
                **(operation.copy_metadata or {}),
                "celery_task_id": task.id,
                "queued_at": datetime.utcnow().isoformat(),
            }
            operations.append(operation)

        await db.commit()
        for operation in operations:
            await db.refresh(operation)

        return [DataCopyService.to_response(operation) for operation in operations]

    @staticmethod
    async def create_copy_operation(
        db: AsyncSession,
        source_restaurant_id: str,
        destination_restaurant_id: str,
        copy_data: DataCopyCreate,
        current_user_id: str,
    ) -> DataCopy:
        copy_number = await DataCopyService.generate_copy_number()
        options = copy_data.options or CopyOptions()
        operation = DataCopy(
            source_restaurant_id=source_restaurant_id,
            destination_restaurant_id=destination_restaurant_id,
            copy_number=copy_number,
            copy_name=copy_data.copy_name or f"Copy from {source_restaurant_id}",
            copy_type=DataCopyService._enum_value(copy_data.copy_type),
            status=CopyStatus.PENDING.value,
            skip_duplicates=options.skip_duplicates,
            copy_images=options.copy_images,
            copy_prices=options.copy_prices,
            copy_stock=options.copy_stock,
            maintain_relationships=options.maintain_relationships,
            source_entity_ids=copy_data.source_entity_ids.model_dump(exclude_none=True)
            if copy_data.source_entity_ids
            else None,
            copied_by=current_user_id,
            notes=copy_data.notes,
            copy_metadata={
                "include_inactive": options.include_inactive,
                "include_unavailable": options.include_unavailable,
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(operation)
        await db.flush()
        await db.refresh(operation)
        return operation

    @staticmethod
    async def process_copy_operation(db: AsyncSession, copy_id: str) -> str:
        operation = await DataCopyService.get_copy_by_id(db, copy_id)
        if not operation:
            raise ValueError(f"Copy operation not found: {copy_id}")

        if operation.status == CopyStatus.COMPLETED.value:
            return operation.status

        try:
            operation.status = CopyStatus.PROCESSING.value
            operation.processing_started_at = datetime.utcnow()
            operation.error_message = None
            operation.error_details = None
            await db.commit()
            await db.refresh(operation)

            options = DataCopyService.options_from_operation(operation)
            entity_mapping: Dict[str, Dict[str, str]] = {
                "categories": {},
                "products": {},
                "modifiers": {},
                "modifier_options": {},
                "combos": {},
            }

            await DataCopyService.copy_categories_for_operation(db, operation, options, entity_mapping)
            await DataCopyService.copy_modifiers_for_operation(db, operation, options, entity_mapping)
            await DataCopyService.copy_products_for_operation(db, operation, options, entity_mapping)
            await DataCopyService.copy_product_modifier_links(db, operation, entity_mapping)
            await DataCopyService.copy_combos_for_operation(db, operation, options, entity_mapping)

            status = CopyStatus.COMPLETED.value
            if operation.items_failed:
                status = CopyStatus.PARTIAL.value if operation.items_copied else CopyStatus.FAILED.value

            operation.status = status
            operation.processing_completed_at = datetime.utcnow()
            operation.processing_time = int(
                (operation.processing_completed_at - operation.processing_started_at).total_seconds()
            )
            operation.total_items = operation.items_copied + operation.items_skipped + operation.items_failed
            operation.entity_mapping = entity_mapping
            operation.copy_summary = {
                "categories": operation.categories_copied,
                "products": operation.products_copied,
                "modifiers": operation.modifiers_copied,
                "combos": operation.combos_copied,
            }
            operation.updated_at = datetime.utcnow()
            await db.commit()
            return operation.status
        except Exception as exc:
            logger.exception("Data copy failed for %s", copy_id)
            operation.status = CopyStatus.FAILED.value
            operation.processing_completed_at = datetime.utcnow()
            if operation.processing_started_at:
                operation.processing_time = int(
                    (operation.processing_completed_at - operation.processing_started_at).total_seconds()
                )
            operation.error_message = str(exc)
            operation.error_details = {"error_type": type(exc).__name__}
            operation.updated_at = datetime.utcnow()
            await db.commit()
            raise

    @staticmethod
    async def copy_categories_for_operation(
        db: AsyncSession,
        operation: DataCopy,
        options: CopyOptions,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> None:
        copy_type = DataCopyService._normalized_value(operation.copy_type)
        if copy_type not in {
            CopyType.CATEGORY.value,
            CopyType.CATEGORY_PRODUCTS.value,
            CopyType.FULL_MENU.value,
        }:
            return

        category_ids = DataCopyService._selected_ids(operation, "category_ids")
        query = select(Category).where(
            Category.restaurant_id == operation.source_restaurant_id,
            Category.deleted_at.is_(None),
        )
        if category_ids:
            query = query.where(Category.id.in_(category_ids))
        if not options.include_inactive:
            query = query.where(Category.active.is_(True))
        query = query.order_by(Category.level.asc(), Category.sort_order.asc(), Category.created_at.asc())

        result = await db.execute(query)
        for source in result.scalars().all():
            destination_id, status = await DataCopyService.copy_category(
                db, source, operation, options, entity_mapping["categories"]
            )
            DataCopyService._increment(operation, "categories", status)
            if destination_id:
                entity_mapping["categories"][source.id] = destination_id

    @staticmethod
    async def copy_products_for_operation(
        db: AsyncSession,
        operation: DataCopy,
        options: CopyOptions,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> None:
        copy_type = DataCopyService._normalized_value(operation.copy_type)
        if copy_type not in {
            CopyType.PRODUCT.value,
            CopyType.CATEGORY_PRODUCTS.value,
            CopyType.FULL_MENU.value,
        }:
            return

        product_ids = DataCopyService._selected_ids(operation, "product_ids")
        query = select(Product).where(
            Product.restaurant_id == operation.source_restaurant_id,
            Product.deleted_at.is_(None),
        )
        if product_ids:
            query = query.where(Product.id.in_(product_ids))
        if not options.include_inactive:
            query = query.where(Product.is_published.is_(True))
        if not options.include_unavailable:
            query = query.where(Product.available.is_(True))
        query = query.order_by(Product.sort_order.asc(), Product.created_at.asc())

        result = await db.execute(query)
        for source in result.scalars().all():
            if source.category_id and source.category_id not in entity_mapping["categories"]:
                source_category = await db.get(Category, source.category_id)
                if source_category:
                    category_id, category_status = await DataCopyService.copy_category(
                        db,
                        source_category,
                        operation,
                        options,
                        entity_mapping["categories"],
                    )
                    DataCopyService._increment(operation, "categories", category_status)
                    if category_id:
                        entity_mapping["categories"][source.category_id] = category_id

            destination_id, status = await DataCopyService.copy_product(
                db, source, operation, options, entity_mapping["categories"]
            )
            DataCopyService._increment(operation, "products", status)
            if destination_id:
                entity_mapping["products"][source.id] = destination_id

    @staticmethod
    async def copy_modifiers_for_operation(
        db: AsyncSession,
        operation: DataCopy,
        options: CopyOptions,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> None:
        copy_type = DataCopyService._normalized_value(operation.copy_type)
        if copy_type not in {CopyType.MODIFIER.value, CopyType.FULL_MENU.value}:
            return

        modifier_ids = DataCopyService._selected_ids(operation, "modifier_ids")
        query = select(Modifier).where(Modifier.restaurant_id == operation.source_restaurant_id)
        if modifier_ids:
            query = query.where(Modifier.id.in_(modifier_ids))
        query = query.order_by(Modifier.created_at.asc())

        result = await db.execute(query)
        for source in result.scalars().all():
            destination_id, status = await DataCopyService.copy_modifier(
                db, source, operation, options, entity_mapping
            )
            DataCopyService._increment(operation, "modifiers", status)
            if destination_id:
                entity_mapping["modifiers"][source.id] = destination_id

    @staticmethod
    async def copy_combos_for_operation(
        db: AsyncSession,
        operation: DataCopy,
        options: CopyOptions,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> None:
        copy_type = DataCopyService._normalized_value(operation.copy_type)
        if copy_type not in {CopyType.COMBO.value, CopyType.FULL_MENU.value}:
            return

        combo_ids = DataCopyService._selected_ids(operation, "combo_ids")
        query = select(ComboProduct).where(ComboProduct.restaurant_id == operation.source_restaurant_id)
        if combo_ids:
            query = query.where(ComboProduct.id.in_(combo_ids))
        if not options.include_unavailable:
            query = query.where(ComboProduct.available.is_(True))
        query = query.order_by(ComboProduct.created_at.asc())

        result = await db.execute(query)
        for source in result.scalars().all():
            destination_id, status = await DataCopyService.copy_combo(
                db, source, operation, options, entity_mapping
            )
            DataCopyService._increment(operation, "combos", status)
            if destination_id:
                entity_mapping["combos"][source.id] = destination_id

    @staticmethod
    async def copy_category(
        db: AsyncSession,
        source: Category,
        operation: DataCopy,
        options: CopyOptions,
        category_mapping: Dict[str, str],
    ) -> Tuple[Optional[str], str]:
        existing_id = None
        if options.skip_duplicates:
            existing_id = await DataCopyService.find_duplicate(db, Category, source.name, operation.destination_restaurant_id)
        if existing_id:
            await DataCopyService.create_duplicate_log(db, operation.id, source.id, "category", source.name, existing_id)
            operation.duplicates_found += 1
            operation.duplicates_skipped += 1
            return existing_id if options.maintain_relationships else None, "skipped"

        try:
            overrides = {
                "id": str(uuid.uuid4()),
                "restaurant_id": operation.destination_restaurant_id,
                "parent_id": category_mapping.get(source.parent_id) if source.parent_id else None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "deleted_at": None,
            }
            data = DataCopyService.clone_column_data(source, Category, overrides)
            if options.copy_images:
                DataCopyService.copy_media_fields(data, DataCopyService.CATEGORY_MEDIA_FIELDS, "categories")
            else:
                DataCopyService.clear_fields(data, DataCopyService.CATEGORY_MEDIA_FIELDS)

            destination = Category(**data)
            db.add(destination)
            await db.flush()
            await DataCopyService.create_success_log(db, operation.id, source.id, "category", source.name, destination.id)
            return destination.id, "success"
        except Exception as exc:
            await DataCopyService.create_failure_log(db, operation.id, source.id, "category", source.name, exc)
            return None, "failed"

    @staticmethod
    async def copy_product(
        db: AsyncSession,
        source: Product,
        operation: DataCopy,
        options: CopyOptions,
        category_mapping: Dict[str, str],
    ) -> Tuple[Optional[str], str]:
        existing_id = None
        if options.skip_duplicates:
            existing_id = await DataCopyService.find_duplicate(db, Product, source.name, operation.destination_restaurant_id)
        if existing_id:
            await DataCopyService.create_duplicate_log(db, operation.id, source.id, "product", source.name, existing_id)
            operation.duplicates_found += 1
            operation.duplicates_skipped += 1
            return existing_id if operation.maintain_relationships else None, "skipped"

        new_category_id = category_mapping.get(source.category_id)
        if not new_category_id:
            existing_category_id = await DataCopyService.find_duplicate_category_by_source(
                db, source.category_id, operation.destination_restaurant_id
            )
            if existing_category_id:
                new_category_id = existing_category_id
                category_mapping[source.category_id] = existing_category_id
        if not new_category_id:
            await DataCopyService.create_skipped_log(
                db, operation.id, source.id, "product", source.name, "Category not copied"
            )
            return None, "skipped"

        try:
            overrides = {
                "id": str(uuid.uuid4()),
                "restaurant_id": operation.destination_restaurant_id,
                "category_id": new_category_id,
                "sku": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "published_at": None,
                "deleted_at": None,
            }
            data = DataCopyService.clone_column_data(source, Product, overrides)
            if not options.copy_prices:
                for field in ("price", "cost", "compare_at_price", "wholesale_price", "min_price", "max_price"):
                    if field in data:
                        data[field] = 0 if field in {"price", "cost"} else None
            if not options.copy_stock:
                for field in ("stock", "min_stock", "max_stock", "reorder_point", "reorder_quantity"):
                    if field in data:
                        data[field] = 0 if field in {"stock", "min_stock"} else None
            if options.copy_images:
                DataCopyService.copy_media_fields(data, DataCopyService.PRODUCT_MEDIA_FIELDS, "products")
            else:
                DataCopyService.clear_fields(data, DataCopyService.PRODUCT_MEDIA_FIELDS)

            destination = Product(**data)
            db.add(destination)
            await db.flush()
            await DataCopyService.create_success_log(db, operation.id, source.id, "product", source.name, destination.id)
            return destination.id, "success"
        except Exception as exc:
            await DataCopyService.create_failure_log(db, operation.id, source.id, "product", source.name, exc)
            return None, "failed"

    @staticmethod
    async def copy_modifier(
        db: AsyncSession,
        source: Modifier,
        operation: DataCopy,
        options: CopyOptions,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> Tuple[Optional[str], str]:
        existing_id = None
        if options.skip_duplicates:
            existing_id = await DataCopyService.find_duplicate(db, Modifier, source.name, operation.destination_restaurant_id)
        if existing_id:
            await DataCopyService.create_duplicate_log(db, operation.id, source.id, "modifier", source.name, existing_id)
            operation.duplicates_found += 1
            operation.duplicates_skipped += 1
            return existing_id if operation.maintain_relationships else None, "skipped"

        try:
            data = DataCopyService.clone_column_data(
                source,
                Modifier,
                {
                    "id": str(uuid.uuid4()),
                    "restaurant_id": operation.destination_restaurant_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            if options.copy_images:
                DataCopyService.copy_media_fields(data, DataCopyService.MODIFIER_MEDIA_FIELDS, "modifiers")
            else:
                DataCopyService.clear_fields(data, DataCopyService.MODIFIER_MEDIA_FIELDS)

            destination = Modifier(**data)
            db.add(destination)
            await db.flush()

            options_result = await db.execute(select(ModifierOption).where(ModifierOption.modifier_id == source.id))
            for source_option in options_result.scalars().all():
                option_data = DataCopyService.clone_column_data(
                    source_option,
                    ModifierOption,
                    {
                        "id": str(uuid.uuid4()),
                        "restaurant_id": operation.destination_restaurant_id,
                        "modifier_id": destination.id,
                        "price": source_option.price if options.copy_prices else 0,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )
                destination_option = ModifierOption(**option_data)
                db.add(destination_option)
                await db.flush()
                entity_mapping["modifier_options"][source_option.id] = destination_option.id

            await DataCopyService.create_success_log(db, operation.id, source.id, "modifier", source.name, destination.id)
            return destination.id, "success"
        except Exception as exc:
            await DataCopyService.create_failure_log(db, operation.id, source.id, "modifier", source.name, exc)
            return None, "failed"

    @staticmethod
    async def copy_product_modifier_links(
        db: AsyncSession,
        operation: DataCopy,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> None:
        if not operation.maintain_relationships:
            return
        if not entity_mapping["products"] or not entity_mapping["modifiers"]:
            return

        result = await db.execute(
            select(ProductModifier).where(
                ProductModifier.restaurant_id == operation.source_restaurant_id,
                ProductModifier.product_id.in_(entity_mapping["products"].keys()),
            )
        )
        for source_link in result.scalars().all():
            product_id = entity_mapping["products"].get(source_link.product_id)
            modifier_id = entity_mapping["modifiers"].get(source_link.modifier_id)
            if not product_id or not modifier_id:
                continue
            db.add(
                ProductModifier(
                    id=str(uuid.uuid4()),
                    restaurant_id=operation.destination_restaurant_id,
                    product_id=product_id,
                    modifier_id=modifier_id,
                    created_at=datetime.utcnow(),
                )
            )
        await db.flush()

    @staticmethod
    async def copy_combo(
        db: AsyncSession,
        source: ComboProduct,
        operation: DataCopy,
        options: CopyOptions,
        entity_mapping: Dict[str, Dict[str, str]],
    ) -> Tuple[Optional[str], str]:
        existing_id = None
        if options.skip_duplicates:
            existing_id = await DataCopyService.find_duplicate(db, ComboProduct, source.name, operation.destination_restaurant_id)
        if existing_id:
            await DataCopyService.create_duplicate_log(db, operation.id, source.id, "combo", source.name, existing_id)
            operation.duplicates_found += 1
            operation.duplicates_skipped += 1
            return existing_id if operation.maintain_relationships else None, "skipped"

        category_id = entity_mapping["categories"].get(source.category_id)
        if not category_id:
            await DataCopyService.create_skipped_log(
                db, operation.id, source.id, "combo", source.name, "Category not copied"
            )
            return None, "skipped"

        try:
            data = DataCopyService.clone_column_data(
                source,
                ComboProduct,
                {
                    "id": str(uuid.uuid4()),
                    "restaurant_id": operation.destination_restaurant_id,
                    "category_id": category_id,
                    "price": source.price if options.copy_prices else 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            if options.copy_images:
                DataCopyService.copy_media_fields(data, DataCopyService.COMBO_MEDIA_FIELDS, "combos")
            else:
                DataCopyService.clear_fields(data, DataCopyService.COMBO_MEDIA_FIELDS)

            destination = ComboProduct(**data)
            db.add(destination)
            await db.flush()

            result = await db.execute(select(ComboItem).where(ComboItem.combo_id == source.id))
            for source_item in result.scalars().all():
                product_id = entity_mapping["products"].get(source_item.product_id)
                if not product_id:
                    continue
                item_data = DataCopyService.clone_column_data(
                    source_item,
                    ComboItem,
                    {
                        "id": str(uuid.uuid4()),
                        "restaurant_id": operation.destination_restaurant_id,
                        "combo_id": destination.id,
                        "product_id": product_id,
                        "created_at": datetime.utcnow(),
                    },
                )
                db.add(ComboItem(**item_data))

            await db.flush()
            await DataCopyService.create_success_log(db, operation.id, source.id, "combo", source.name, destination.id)
            return destination.id, "success"
        except Exception as exc:
            await DataCopyService.create_failure_log(db, operation.id, source.id, "combo", source.name, exc)
            return None, "failed"

    @staticmethod
    def clone_column_data(source: Any, model: Type[Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        data = {}
        for column in model.__table__.columns:
            key = column.name
            if key in overrides:
                data[key] = overrides[key]
            elif hasattr(source, key):
                data[key] = getattr(source, key)
        return data

    @staticmethod
    def copy_media_fields(data: Dict[str, Any], fields: Iterable[str], folder: str) -> None:
        for field in fields:
            if field not in data:
                continue
            value = data.get(field)
            if field in {"images", "gallery"}:
                data[field] = copy_file_urls_in_value(value, folder)
            else:
                data[field] = copy_file_url(value, folder)

    @staticmethod
    def clear_fields(data: Dict[str, Any], fields: Iterable[str]) -> None:
        for field in fields:
            if field in data:
                data[field] = None

    @staticmethod
    async def find_duplicate(
        db: AsyncSession,
        model: Type[Any],
        name: str,
        restaurant_id: str,
    ) -> Optional[str]:
        conditions = [
            model.restaurant_id == restaurant_id,
            func.lower(model.name) == func.lower(name),
        ]
        if hasattr(model, "deleted_at"):
            conditions.append(model.deleted_at.is_(None))
        result = await db.execute(select(model.id).where(and_(*conditions)))
        return result.scalar_one_or_none()

    @staticmethod
    async def find_duplicate_category_by_source(
        db: AsyncSession,
        source_category_id: str,
        destination_restaurant_id: str,
    ) -> Optional[str]:
        source = await db.get(Category, source_category_id)
        if not source:
            return None
        return await DataCopyService.find_duplicate(db, Category, source.name, destination_restaurant_id)

    @staticmethod
    async def create_copy_log(
        db: AsyncSession,
        data_copy_id: str,
        source_entity_id: str,
        source_entity_type: str,
        source_entity_name: str,
        status: str,
        action_taken: str,
        destination_entity_id: Optional[str] = None,
        destination_entity_type: Optional[str] = None,
        is_duplicate: bool = False,
        duplicate_field: Optional[str] = None,
        duplicate_value: Optional[str] = None,
        existing_entity_id: Optional[str] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> CopyLog:
        copy_log = CopyLog(
            data_copy_id=data_copy_id,
            source_entity_id=source_entity_id,
            source_entity_type=source_entity_type,
            source_entity_name=source_entity_name,
            destination_entity_id=destination_entity_id,
            destination_entity_type=destination_entity_type,
            status=status,
            action_taken=action_taken,
            is_duplicate=is_duplicate,
            duplicate_field=duplicate_field,
            duplicate_value=duplicate_value,
            existing_entity_id=existing_entity_id,
            error_message=error_message,
            error_type=error_type,
            processed_at=datetime.utcnow(),
        )
        db.add(copy_log)
        return copy_log

    @staticmethod
    async def create_success_log(
        db: AsyncSession,
        data_copy_id: str,
        source_id: str,
        entity_type: str,
        entity_name: str,
        destination_id: str,
    ) -> None:
        await DataCopyService.create_copy_log(
            db,
            data_copy_id,
            source_id,
            entity_type,
            entity_name,
            "success",
            "copied",
            destination_id,
            entity_type,
        )

    @staticmethod
    async def create_duplicate_log(
        db: AsyncSession,
        data_copy_id: str,
        source_id: str,
        entity_type: str,
        entity_name: str,
        existing_id: str,
    ) -> None:
        await DataCopyService.create_copy_log(
            db,
            data_copy_id,
            source_id,
            entity_type,
            entity_name,
            "skipped",
            "skipped",
            is_duplicate=True,
            duplicate_field="name",
            duplicate_value=entity_name,
            existing_entity_id=existing_id,
        )

    @staticmethod
    async def create_skipped_log(
        db: AsyncSession,
        data_copy_id: str,
        source_id: str,
        entity_type: str,
        entity_name: str,
        reason: str,
    ) -> None:
        await DataCopyService.create_copy_log(
            db,
            data_copy_id,
            source_id,
            entity_type,
            entity_name,
            "skipped",
            "skipped",
            error_message=reason,
        )

    @staticmethod
    async def create_failure_log(
        db: AsyncSession,
        data_copy_id: str,
        source_id: str,
        entity_type: str,
        entity_name: str,
        exc: Exception,
    ) -> None:
        await DataCopyService.create_copy_log(
            db,
            data_copy_id,
            source_id,
            entity_type,
            entity_name,
            "failed",
            "failed",
            error_message=str(exc),
            error_type=type(exc).__name__,
        )

    @staticmethod
    def _increment(operation: DataCopy, entity_prefix: str, status: str) -> None:
        if status == "success":
            setattr(operation, f"{entity_prefix}_copied", getattr(operation, f"{entity_prefix}_copied") + 1)
            operation.items_copied += 1
        elif status == "skipped":
            setattr(operation, f"{entity_prefix}_skipped", getattr(operation, f"{entity_prefix}_skipped") + 1)
            operation.items_skipped += 1
        elif status == "failed":
            operation.items_failed += 1

    @staticmethod
    def options_from_operation(operation: DataCopy) -> CopyOptions:
        metadata = operation.copy_metadata or {}
        return CopyOptions(
            skip_duplicates=operation.skip_duplicates,
            copy_images=operation.copy_images,
            copy_prices=operation.copy_prices,
            copy_stock=operation.copy_stock,
            maintain_relationships=operation.maintain_relationships,
            include_inactive=bool(metadata.get("include_inactive", False)),
            include_unavailable=bool(metadata.get("include_unavailable", False)),
        )

    @staticmethod
    def _selected_ids(operation: DataCopy, key: str) -> List[str]:
        if not operation.source_entity_ids:
            return []
        value = operation.source_entity_ids.get(key)
        return value or []

    @staticmethod
    def _enum_value(value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)

    @staticmethod
    def _normalized_value(value: Any) -> str:
        raw = DataCopyService._enum_value(value)
        return raw.lower()

    @staticmethod
    def to_response(operation: DataCopy) -> DataCopyResponse:
        return DataCopyResponse(
            id=operation.id,
            source_restaurant_id=operation.source_restaurant_id,
            destination_restaurant_id=operation.destination_restaurant_id,
            copy_number=operation.copy_number,
            copy_name=operation.copy_name,
            copy_type=operation.copy_type,
            status=operation.status,
            processing_started_at=operation.processing_started_at,
            processing_completed_at=operation.processing_completed_at,
            processing_time=operation.processing_time,
            statistics=CopyStatistics(
                total_items=operation.total_items,
                items_copied=operation.items_copied,
                items_skipped=operation.items_skipped,
                items_failed=operation.items_failed,
                categories_copied=operation.categories_copied,
                categories_skipped=operation.categories_skipped,
                products_copied=operation.products_copied,
                products_skipped=operation.products_skipped,
                combos_copied=operation.combos_copied,
                combos_skipped=operation.combos_skipped,
                modifiers_copied=operation.modifiers_copied,
                modifiers_skipped=operation.modifiers_skipped,
                duplicates_found=operation.duplicates_found,
                duplicates_skipped=operation.duplicates_skipped,
            ),
            skip_duplicates=operation.skip_duplicates,
            copy_images=operation.copy_images,
            copy_prices=operation.copy_prices,
            copy_stock=operation.copy_stock,
            maintain_relationships=operation.maintain_relationships,
            error_message=operation.error_message,
            notes=operation.notes,
            copied_by=operation.copied_by,
            created_at=operation.created_at,
            updated_at=operation.updated_at,
        )

    @staticmethod
    async def get_copy_by_id(db: AsyncSession, copy_id: str) -> Optional[DataCopy]:
        result = await db.execute(
            select(DataCopy).where(DataCopy.id == copy_id, DataCopy.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_copies(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        source_restaurant_id: Optional[str] = None,
        destination_restaurant_id: Optional[str] = None,
        status: Optional[str] = None,
        copy_type: Optional[str] = None,
    ) -> DataCopyListResponse:
        query = select(DataCopy).where(DataCopy.deleted_at.is_(None))

        if source_restaurant_id:
            query = query.where(DataCopy.source_restaurant_id == source_restaurant_id)
        if destination_restaurant_id:
            query = query.where(DataCopy.destination_restaurant_id == destination_restaurant_id)
        if status:
            query = query.where(DataCopy.status == status)
        if copy_type:
            query = query.where(DataCopy.copy_type == copy_type)

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()

        result = await db.execute(
            query.order_by(DataCopy.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        copies = result.scalars().all()
        pages = (total + page_size - 1) // page_size

        return DataCopyListResponse(
            items=[DataCopyService.to_response(copy) for copy in copies],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
