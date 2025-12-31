from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_superadmin
from app.modules.data_copy.schema import (
    DataCopyCreate, DataCopyResponse, DataCopyDetailResponse, DataCopyListResponse,
    CopyLogListResponse, DuplicateCheckRequest, DuplicateCheckResponse,
    CopyPreviewRequest, CopyPreviewResponse,
    CopyTemplateCreate, CopyTemplateUpdate, CopyTemplateResponse, CopyTemplateListResponse
)
from app.modules.data_copy.service import DataCopyService
from app.core.response import success_response, error_response

router = APIRouter(prefix="/api/v1/data-copy", tags=["Data Copy"])


@router.post("/copy", response_model=dict, status_code=status.HTTP_201_CREATED)
async def copy_data(
    copy_data: DataCopyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Copy data from source restaurant to destination restaurant(s)
    
    **Super Admin Only**
    
    - **source_restaurant_id**: Source restaurant ID
    - **destination_restaurant_ids**: List of destination restaurant IDs
    - **copy_type**: Type of data to copy (category, product, combo, modifier, category_products, full_menu)
    - **source_entity_ids**: Optional specific entity IDs to copy
    - **options**: Copy options (skip_duplicates, copy_images, etc.)
    
    Returns list of copy operations created for each destination restaurant.
    """
    try:
        results = await DataCopyService.perform_copy(
            db=db,
            copy_data=copy_data,
            current_user_id=current_user.id
        )
        
        return success_response(
            data={"copies": [r.model_dump() for r in results]},
            message=f"Successfully initiated copy to {len(results)} restaurant(s)",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        return error_response(
            message=f"Failed to copy data: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/copies", response_model=dict)
async def get_copies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_restaurant_id: Optional[str] = Query(None, description="Filter by source restaurant"),
    destination_restaurant_id: Optional[str] = Query(None, description="Filter by destination restaurant"),
    status: Optional[str] = Query(None, description="Filter by status"),
    copy_type: Optional[str] = Query(None, description="Filter by copy type"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Get list of copy operations with pagination
    
    **Super Admin Only**
    
    Query Parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **source_restaurant_id**: Filter by source restaurant
    - **destination_restaurant_id**: Filter by destination restaurant
    - **status**: Filter by status (pending, processing, completed, failed, partial)
    - **copy_type**: Filter by copy type
    """
    try:
        result = await DataCopyService.get_copies(
            db=db,
            page=page,
            page_size=page_size,
            source_restaurant_id=source_restaurant_id,
            destination_restaurant_id=destination_restaurant_id,
            status=status,
            copy_type=copy_type
        )
        
        return success_response(
            data=result.model_dump(),
            message="Copy operations retrieved successfully"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to retrieve copy operations: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/copies/{copy_id}", response_model=dict)
async def get_copy_detail(
    copy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Get detailed information about a specific copy operation
    
    **Super Admin Only**
    
    - **copy_id**: Copy operation ID
    
    Returns detailed copy information including logs and statistics.
    """
    try:
        data_copy = await DataCopyService.get_copy_by_id(db, copy_id)
        
        if not data_copy:
            return error_response(
                message="Copy operation not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        from app.modules.data_copy.schema import CopyStatistics
        
        response = DataCopyDetailResponse(
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
            updated_at=data_copy.updated_at,
            entity_mapping=data_copy.entity_mapping,
            copy_summary=data_copy.copy_summary,
            skipped_items=data_copy.skipped_items,
            failed_items=data_copy.failed_items,
            logs=None  # Can fetch logs separately if needed
        )
        
        return success_response(
            data=response.model_dump(),
            message="Copy operation details retrieved successfully"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to retrieve copy details: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/copies/{copy_id}/logs", response_model=dict)
async def get_copy_logs(
    copy_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by log status"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Get logs for a specific copy operation
    
    **Super Admin Only**
    
    - **copy_id**: Copy operation ID
    - **page**: Page number
    - **page_size**: Items per page
    - **status**: Filter by log status (success, failed, skipped)
    - **entity_type**: Filter by entity type (category, product, combo, modifier)
    """
    try:
        # Verify copy exists
        data_copy = await DataCopyService.get_copy_by_id(db, copy_id)
        if not data_copy:
            return error_response(
                message="Copy operation not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get logs
        from sqlalchemy import select, and_, func
        from app.modules.data_copy.model import CopyLog
        
        query = select(CopyLog).where(CopyLog.data_copy_id == copy_id)
        
        if status:
            query = query.where(CopyLog.status == status)
        if entity_type:
            query = query.where(CopyLog.source_entity_type == entity_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(CopyLog.processed_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Convert to response
        from app.modules.data_copy.schema import CopyLogResponse
        items = [
            CopyLogResponse(
                id=log.id,
                data_copy_id=log.data_copy_id,
                source_entity_id=log.source_entity_id,
                source_entity_type=log.source_entity_type,
                source_entity_name=log.source_entity_name,
                destination_entity_id=log.destination_entity_id,
                destination_entity_type=log.destination_entity_type,
                status=log.status,
                action_taken=log.action_taken,
                is_duplicate=log.is_duplicate,
                duplicate_field=log.duplicate_field,
                duplicate_value=log.duplicate_value,
                existing_entity_id=log.existing_entity_id,
                error_message=log.error_message,
                error_type=log.error_type,
                processed_at=log.processed_at,
                processing_time_ms=log.processing_time_ms
            )
            for log in logs
        ]
        
        pages = (total + page_size - 1) // page_size
        
        log_response = CopyLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
        
        return success_response(
            data=log_response.model_dump(),
            message="Copy logs retrieved successfully"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to retrieve copy logs: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/preview", response_model=dict)
async def preview_copy(
    preview_request: CopyPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Preview what will be copied before performing the operation
    
    **Super Admin Only**
    
    - **source_restaurant_id**: Source restaurant ID
    - **destination_restaurant_id**: Destination restaurant ID
    - **copy_type**: Type of data to copy
    - **source_entity_ids**: Optional specific entity IDs to preview
    - **options**: Copy options
    
    Returns preview of items to be copied, skipped, and any warnings.
    """
    try:
        # TODO: Implement preview logic
        return success_response(
            data={
                "preview": "Preview functionality coming soon",
                "message": "Preview will show items to be copied, duplicates, and dependencies"
            },
            message="Preview generated successfully"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to generate preview: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/check-duplicates", response_model=dict)
async def check_duplicates(
    duplicate_check: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Check for duplicates before copying
    
    **Super Admin Only**
    
    - **source_restaurant_id**: Source restaurant ID
    - **destination_restaurant_id**: Destination restaurant ID
    - **copy_type**: Type of data to check
    - **source_entity_ids**: Optional specific entity IDs to check
    
    Returns list of duplicate items that would be skipped.
    """
    try:
        # TODO: Implement duplicate check logic
        return success_response(
            data={
                "duplicates": "Duplicate check functionality coming soon",
                "message": "Check will show which items already exist in destination"
            },
            message="Duplicate check completed"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to check duplicates: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/statistics", response_model=dict)
async def get_copy_statistics(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin)
):
    """
    Get overall copy operation statistics
    
    **Super Admin Only**
    
    Query Parameters:
    - **restaurant_id**: Filter by restaurant (as source or destination)
    
    Returns aggregated statistics for copy operations.
    """
    try:
        from sqlalchemy import select, func, or_
        from app.modules.data_copy.model import DataCopy
        
        query = select(
            func.count(DataCopy.id).label("total_copies"),
            func.sum(DataCopy.items_copied).label("total_items_copied"),
            func.sum(DataCopy.items_skipped).label("total_items_skipped"),
            func.sum(DataCopy.categories_copied).label("total_categories_copied"),
            func.sum(DataCopy.products_copied).label("total_products_copied")
        ).where(DataCopy.deleted_at.is_(None))
        
        if restaurant_id:
            query = query.where(
                or_(
                    DataCopy.source_restaurant_id == restaurant_id,
                    DataCopy.destination_restaurant_id == restaurant_id
                )
            )
        
        result = await db.execute(query)
        stats = result.first()
        
        statistics = {
            "total_copies": stats.total_copies or 0,
            "total_items_copied": stats.total_items_copied or 0,
            "total_items_skipped": stats.total_items_skipped or 0,
            "total_categories_copied": stats.total_categories_copied or 0,
            "total_products_copied": stats.total_products_copied or 0
        }
        
        return success_response(
            data=statistics,
            message="Copy statistics retrieved successfully"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to retrieve statistics: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
