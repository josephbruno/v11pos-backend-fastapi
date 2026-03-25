from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
import logging
from app.modules.data_copy.model import DataCopy, CopyLog, CopyTemplate, CopyType, CopyStatus
from app.modules.data_copy.schema import (
    DataCopyCreate, CopyOptions, CopyEntityIds,
    DataCopyResponse, DataCopyDetailResponse, DataCopyListResponse,
    CopyLogResponse, CopyLogListResponse,
    CopyTemplateCreate, CopyTemplateUpdate, CopyTemplateResponse, CopyTemplateListResponse,
    DuplicateCheckRequest, DuplicateCheckResponse, DuplicateItem,
    CopyPreviewRequest, CopyPreviewResponse, PreviewItem,
    CopyStatistics
)
from app.modules.product.model import Category, Product
from app.modules.restaurant.model import Restaurant

logger = logging.getLogger(__name__)


class DataCopyService:
    """Service for copying data between restaurants"""
    
    @staticmethod
    async def generate_copy_number() -> str:
        """Generate unique copy number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"CPY-{timestamp}-{random_suffix}"
    
    @staticmethod
    async def create_copy_operation(
        db: AsyncSession,
        source_restaurant_id: str,
        destination_restaurant_id: str,
        copy_data: DataCopyCreate,
        current_user_id: str
    ) -> DataCopy:
        """Create a new copy operation record"""
        copy_number = await DataCopyService.generate_copy_number()
        copy_name = copy_data.copy_name or f"Copy from Restaurant {source_restaurant_id}"
        
        data_copy = DataCopy(
            source_restaurant_id=source_restaurant_id,
            destination_restaurant_id=destination_restaurant_id,
            copy_number=copy_number,
            copy_name=copy_name,
            copy_type=copy_data.copy_type.value,
            status=CopyStatus.PENDING.value,
            skip_duplicates=copy_data.options.skip_duplicates if copy_data.options else True,
            copy_images=copy_data.options.copy_images if copy_data.options else True,
            copy_prices=copy_data.options.copy_prices if copy_data.options else True,
            copy_stock=copy_data.options.copy_stock if copy_data.options else False,
            maintain_relationships=copy_data.options.maintain_relationships if copy_data.options else True,
            source_entity_ids=copy_data.source_entity_ids.model_dump() if copy_data.source_entity_ids else None,
            copied_by=current_user_id,
            notes=copy_data.notes
        )
        
        db.add(data_copy)
        await db.commit()
        await db.refresh(data_copy)
        
        return data_copy
    
    @staticmethod
    async def check_duplicate_category(
        db: AsyncSession,
        category_name: str,
        destination_restaurant_id: str
    ) -> Optional[str]:
        """Check if category already exists in destination restaurant"""
        query = select(Category.id).where(
            and_(
                Category.restaurant_id == destination_restaurant_id,
                func.lower(Category.name) == func.lower(category_name),
                Category.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        return existing
    
    @staticmethod
    async def check_duplicate_product(
        db: AsyncSession,
        product_name: str,
        destination_restaurant_id: str
    ) -> Optional[str]:
        """Check if product already exists in destination restaurant"""
        query = select(Product.id).where(
            and_(
                Product.restaurant_id == destination_restaurant_id,
                func.lower(Product.name) == func.lower(product_name),
                Product.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        return existing
    
    @staticmethod
    async def copy_category(
        db: AsyncSession,
        source_category: Category,
        destination_restaurant_id: str,
        data_copy_id: str,
        options: CopyOptions
    ) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Copy a single category to destination restaurant
        Returns: (new_category_id, status, error_message)
        """
        try:
            # Check for duplicates
            existing_id = await DataCopyService.check_duplicate_category(
                db, source_category.name, destination_restaurant_id
            )
            
            if existing_id:
                # Log as duplicate
                await DataCopyService.create_copy_log(
                    db=db,
                    data_copy_id=data_copy_id,
                    source_entity_id=source_category.id,
                    source_entity_type="category",
                    source_entity_name=source_category.name,
                    status="skipped",
                    action_taken="skipped",
                    is_duplicate=True,
                    duplicate_field="name",
                    duplicate_value=source_category.name,
                    existing_entity_id=existing_id
                )
                return None, "skipped", "Duplicate category"
            
            # Create new category
            new_category = Category(
                id=str(uuid.uuid4()),
                restaurant_id=destination_restaurant_id,
                name=source_category.name,
                description=source_category.description,
                image=source_category.image if options.copy_images else None,
                is_active=source_category.is_active,
                display_order=source_category.display_order,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_category)
            
            # Log success
            await DataCopyService.create_copy_log(
                db=db,
                data_copy_id=data_copy_id,
                source_entity_id=source_category.id,
                source_entity_type="category",
                source_entity_name=source_category.name,
                destination_entity_id=new_category.id,
                destination_entity_type="category",
                status="success",
                action_taken="copied"
            )
            
            return new_category.id, "success", None
            
        except Exception as e:
            logger.error(f"Error copying category {source_category.id}: {str(e)}")
            
            # Log failure
            await DataCopyService.create_copy_log(
                db=db,
                data_copy_id=data_copy_id,
                source_entity_id=source_category.id,
                source_entity_type="category",
                source_entity_name=source_category.name,
                status="failed",
                action_taken="failed",
                error_message=str(e),
                error_type=type(e).__name__
            )
            
            return None, "failed", str(e)
    
    @staticmethod
    async def copy_product(
        db: AsyncSession,
        source_product: Product,
        destination_restaurant_id: str,
        data_copy_id: str,
        options: CopyOptions,
        category_mapping: Dict[str, str]
    ) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Copy a single product to destination restaurant
        Returns: (new_product_id, status, error_message)
        """
        try:
            # Check for duplicates
            existing_id = await DataCopyService.check_duplicate_product(
                db, source_product.name, destination_restaurant_id
            )
            
            if existing_id:
                # Log as duplicate
                await DataCopyService.create_copy_log(
                    db=db,
                    data_copy_id=data_copy_id,
                    source_entity_id=source_product.id,
                    source_entity_type="product",
                    source_entity_name=source_product.name,
                    status="skipped",
                    action_taken="skipped",
                    is_duplicate=True,
                    duplicate_field="name",
                    duplicate_value=source_product.name,
                    existing_entity_id=existing_id
                )
                return None, "skipped", "Duplicate product"
            
            # Map category ID if maintaining relationships
            new_category_id = None
            if options.maintain_relationships and source_product.category_id:
                new_category_id = category_mapping.get(source_product.category_id)
                if not new_category_id:
                    # Category not copied, skip product
                    await DataCopyService.create_copy_log(
                        db=db,
                        data_copy_id=data_copy_id,
                        source_entity_id=source_product.id,
                        source_entity_type="product",
                        source_entity_name=source_product.name,
                        status="skipped",
                        action_taken="skipped",
                        error_message="Category not found in destination"
                    )
                    return None, "skipped", "Category not copied"
            
            # Create new product
            new_product = Product(
                id=str(uuid.uuid4()),
                restaurant_id=destination_restaurant_id,
                category_id=new_category_id,
                name=source_product.name,
                description=source_product.description,
                image=source_product.image if options.copy_images else None,
                price=source_product.price if options.copy_prices else 0,
                cost_price=source_product.cost_price if options.copy_prices else 0,
                discount_price=source_product.discount_price if options.copy_prices else None,
                sku=source_product.sku,
                barcode=source_product.barcode,
                stock_quantity=source_product.stock_quantity if options.copy_stock else 0,
                low_stock_threshold=source_product.low_stock_threshold,
                track_inventory=source_product.track_inventory,
                is_active=source_product.is_active,
                is_available=source_product.is_available,
                is_featured=source_product.is_featured,
                tax_rate=source_product.tax_rate,
                preparation_time=source_product.preparation_time,
                calories=source_product.calories,
                is_vegetarian=source_product.is_vegetarian,
                is_vegan=source_product.is_vegan,
                is_gluten_free=source_product.is_gluten_free,
                allergen_info=source_product.allergen_info,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_product)
            
            # Log success
            await DataCopyService.create_copy_log(
                db=db,
                data_copy_id=data_copy_id,
                source_entity_id=source_product.id,
                source_entity_type="product",
                source_entity_name=source_product.name,
                destination_entity_id=new_product.id,
                destination_entity_type="product",
                status="success",
                action_taken="copied"
            )
            
            return new_product.id, "success", None
            
        except Exception as e:
            logger.error(f"Error copying product {source_product.id}: {str(e)}")
            
            # Log failure
            await DataCopyService.create_copy_log(
                db=db,
                data_copy_id=data_copy_id,
                source_entity_id=source_product.id,
                source_entity_type="product",
                source_entity_name=source_product.name,
                status="failed",
                action_taken="failed",
                error_message=str(e),
                error_type=type(e).__name__
            )
            
            return None, "failed", str(e)
    
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
        error_type: Optional[str] = None
    ) -> CopyLog:
        """Create a copy log entry"""
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
            processed_at=datetime.utcnow()
        )
        
        db.add(copy_log)
        return copy_log
    
    @staticmethod
    async def perform_copy(
        db: AsyncSession,
        copy_data: DataCopyCreate,
        current_user_id: str
    ) -> List[DataCopyResponse]:
        """Perform the actual copy operation for all destination restaurants"""
        results = []
        
        for destination_id in copy_data.destination_restaurant_ids:
            try:
                # Create copy operation record
                data_copy = await DataCopyService.create_copy_operation(
                    db=db,
                    source_restaurant_id=copy_data.source_restaurant_id,
                    destination_restaurant_id=destination_id,
                    copy_data=copy_data,
                    current_user_id=current_user_id
                )
                
                # Update status to processing
                data_copy.status = CopyStatus.PROCESSING.value
                data_copy.processing_started_at = datetime.utcnow()
                await db.commit()
                
                # Initialize counters
                categories_copied = 0
                categories_skipped = 0
                products_copied = 0
                products_skipped = 0
                category_mapping: Dict[str, str] = {}
                
                options = copy_data.options or CopyOptions()
                
                # Copy categories
                if copy_data.copy_type in [CopyType.CATEGORY, CopyType.CATEGORY_PRODUCTS, CopyType.FULL_MENU]:
                    category_ids = []
                    if copy_data.source_entity_ids and copy_data.source_entity_ids.category_ids:
                        category_ids = copy_data.source_entity_ids.category_ids
                    else:
                        # Get all categories from source restaurant
                        query = select(Category).where(
                            and_(
                                Category.restaurant_id == copy_data.source_restaurant_id,
                                Category.deleted_at.is_(None)
                            )
                        )
                        if not options.include_inactive:
                            query = query.where(Category.is_active == True)
                        
                        result = await db.execute(query)
                        categories = result.scalars().all()
                        category_ids = [c.id for c in categories]
                    
                    # Copy each category
                    for cat_id in category_ids:
                        category_query = select(Category).where(Category.id == cat_id)
                        cat_result = await db.execute(category_query)
                        category = cat_result.scalar_one_or_none()
                        
                        if category:
                            new_id, status, error = await DataCopyService.copy_category(
                                db=db,
                                source_category=category,
                                destination_restaurant_id=destination_id,
                                data_copy_id=data_copy.id,
                                options=options
                            )
                            
                            if status == "success" and new_id:
                                categories_copied += 1
                                category_mapping[cat_id] = new_id
                            elif status == "skipped":
                                categories_skipped += 1
                
                # Copy products
                if copy_data.copy_type in [CopyType.PRODUCT, CopyType.CATEGORY_PRODUCTS, CopyType.FULL_MENU]:
                    product_ids = []
                    if copy_data.source_entity_ids and copy_data.source_entity_ids.product_ids:
                        product_ids = copy_data.source_entity_ids.product_ids
                    else:
                        # Get all products from source restaurant
                        query = select(Product).where(
                            and_(
                                Product.restaurant_id == copy_data.source_restaurant_id,
                                Product.deleted_at.is_(None)
                            )
                        )
                        if not options.include_inactive:
                            query = query.where(Product.is_active == True)
                        if not options.include_unavailable:
                            query = query.where(Product.is_available == True)
                        
                        result = await db.execute(query)
                        products = result.scalars().all()
                        product_ids = [p.id for p in products]
                    
                    # Copy each product
                    for prod_id in product_ids:
                        product_query = select(Product).where(Product.id == prod_id)
                        prod_result = await db.execute(product_query)
                        product = prod_result.scalar_one_or_none()
                        
                        if product:
                            new_id, status, error = await DataCopyService.copy_product(
                                db=db,
                                source_product=product,
                                destination_restaurant_id=destination_id,
                                data_copy_id=data_copy.id,
                                options=options,
                                category_mapping=category_mapping
                            )
                            
                            if status == "success":
                                products_copied += 1
                            elif status == "skipped":
                                products_skipped += 1
                
                # Update copy operation with results
                data_copy.status = CopyStatus.COMPLETED.value
                data_copy.processing_completed_at = datetime.utcnow()
                data_copy.processing_time = int(
                    (data_copy.processing_completed_at - data_copy.processing_started_at).total_seconds()
                )
                data_copy.categories_copied = categories_copied
                data_copy.categories_skipped = categories_skipped
                data_copy.products_copied = products_copied
                data_copy.products_skipped = products_skipped
                data_copy.items_copied = categories_copied + products_copied
                data_copy.items_skipped = categories_skipped + products_skipped
                data_copy.total_items = data_copy.items_copied + data_copy.items_skipped
                data_copy.entity_mapping = category_mapping
                
                await db.commit()
                await db.refresh(data_copy)
                
                # Convert to response
                response = DataCopyResponse(
                    id=data_copy.id,
                    source_restaurant_id=data_copy.source_restaurant_id,
                    destination_restaurant_id=data_copy.destination_restaurant_id,
                    copy_number=data_copy.copy_number,
                    copy_name=data_copy.copy_name,
                    copy_type=data_copy.copy_type,
                    status=data_copy.status,
                    processing_started_at=data_copy.processing_started_at,
                    processing_completed_at=data_copy.processing_completed_at,
                    processing_time=data_copy.processing_time,
                    statistics=CopyStatistics(
                        total_items=data_copy.total_items,
                        items_copied=data_copy.items_copied,
                        items_skipped=data_copy.items_skipped,
                        items_failed=data_copy.items_failed,
                        categories_copied=data_copy.categories_copied,
                        categories_skipped=data_copy.categories_skipped,
                        products_copied=data_copy.products_copied,
                        products_skipped=data_copy.products_skipped,
                        combos_copied=data_copy.combos_copied,
                        combos_skipped=data_copy.combos_skipped,
                        modifiers_copied=data_copy.modifiers_copied,
                        modifiers_skipped=data_copy.modifiers_skipped,
                        duplicates_found=data_copy.duplicates_found,
                        duplicates_skipped=data_copy.duplicates_skipped
                    ),
                    skip_duplicates=data_copy.skip_duplicates,
                    copy_images=data_copy.copy_images,
                    copy_prices=data_copy.copy_prices,
                    copy_stock=data_copy.copy_stock,
                    maintain_relationships=data_copy.maintain_relationships,
                    error_message=data_copy.error_message,
                    notes=data_copy.notes,
                    copied_by=data_copy.copied_by,
                    created_at=data_copy.created_at,
                    updated_at=data_copy.updated_at
                )
                
                results.append(response)
                
            except Exception as e:
                logger.error(f"Error copying to restaurant {destination_id}: {str(e)}")
                # Continue with next destination
                continue
        
        return results
    
    @staticmethod
    async def get_copy_by_id(db: AsyncSession, copy_id: str) -> Optional[DataCopy]:
        """Get copy operation by ID"""
        query = select(DataCopy).where(
            and_(
                DataCopy.id == copy_id,
                DataCopy.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_copies(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        source_restaurant_id: Optional[str] = None,
        destination_restaurant_id: Optional[str] = None,
        status: Optional[str] = None,
        copy_type: Optional[str] = None
    ) -> DataCopyListResponse:
        """Get list of copy operations with pagination"""
        query = select(DataCopy).where(DataCopy.deleted_at.is_(None))
        
        if source_restaurant_id:
            query = query.where(DataCopy.source_restaurant_id == source_restaurant_id)
        if destination_restaurant_id:
            query = query.where(DataCopy.destination_restaurant_id == destination_restaurant_id)
        if status:
            query = query.where(DataCopy.status == status)
        if copy_type:
            query = query.where(DataCopy.copy_type == copy_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(DataCopy.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        copies = result.scalars().all()
        
        # Convert to response
        items = []
        for copy in copies:
            items.append(
                DataCopyResponse(
                    id=copy.id,
                    source_restaurant_id=copy.source_restaurant_id,
                    destination_restaurant_id=copy.destination_restaurant_id,
                    copy_number=copy.copy_number,
                    copy_name=copy.copy_name,
                    copy_type=copy.copy_type,
                    status=copy.status,
                    processing_started_at=copy.processing_started_at,
                    processing_completed_at=copy.processing_completed_at,
                    processing_time=copy.processing_time,
                    statistics=CopyStatistics(
                        total_items=copy.total_items,
                        items_copied=copy.items_copied,
                        items_skipped=copy.items_skipped,
                        items_failed=copy.items_failed,
                        categories_copied=copy.categories_copied,
                        categories_skipped=copy.categories_skipped,
                        products_copied=copy.products_copied,
                        products_skipped=copy.products_skipped,
                        combos_copied=copy.combos_copied,
                        combos_skipped=copy.combos_skipped,
                        modifiers_copied=copy.modifiers_copied,
                        modifiers_skipped=copy.modifiers_skipped,
                        duplicates_found=copy.duplicates_found,
                        duplicates_skipped=copy.duplicates_skipped
                    ),
                    skip_duplicates=copy.skip_duplicates,
                    copy_images=copy.copy_images,
                    copy_prices=copy.copy_prices,
                    copy_stock=copy.copy_stock,
                    maintain_relationships=copy.maintain_relationships,
                    error_message=copy.error_message,
                    notes=copy.notes,
                    copied_by=copy.copied_by,
                    created_at=copy.created_at,
                    updated_at=copy.updated_at
                )
            )
        
        pages = (total + page_size - 1) // page_size
        
        return DataCopyListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
