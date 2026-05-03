from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple, Any
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import success_response, error_response
from app.modules.table.schema import (
    TableCreate,
    TableUpdate,
    TableResponse,
    TableStatusUpdate
)
from app.modules.table.model import TableStatus
from app.modules.table.service import TableService
from app.modules.user.model import User
from app.services.storage_service import (
    upload_file,
    delete_file,
    get_file_url,
    get_object_name_from_url,
)


router = APIRouter(prefix="/tables", tags=["tables"])


def _multipart_request_body(schema: dict) -> dict:
    return {
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": schema,
                }
            }
        }
    }


TABLE_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "table_number": {"type": "string"},
            "table_name": {"type": "string"},
            "capacity": {"type": "integer"},
            "min_capacity": {"type": "integer"},
            "floor": {"type": "string"},
            "section": {"type": "string"},
            "position_x": {"type": "integer"},
            "position_y": {"type": "integer"},
            "image": {"type": "string", "format": "binary"},
            "qr_code": {"type": "string"},
            "status": {"type": "string"},
            "is_bookable": {"type": "boolean"},
            "is_outdoor": {"type": "boolean"},
            "is_accessible": {"type": "boolean"},
            "has_power_outlet": {"type": "boolean"},
            "minimum_spend": {"type": "integer"},
            "description": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["restaurant_id", "table_number", "capacity"],
    }
)

TABLE_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "table_number": {"type": "string"},
            "table_name": {"type": "string"},
            "capacity": {"type": "integer"},
            "min_capacity": {"type": "integer"},
            "floor": {"type": "string"},
            "section": {"type": "string"},
            "position_x": {"type": "integer"},
            "position_y": {"type": "integer"},
            "image": {"type": "string", "format": "binary"},
            "qr_code": {"type": "string"},
            "status": {"type": "string"},
            "is_active": {"type": "boolean"},
            "is_bookable": {"type": "boolean"},
            "is_outdoor": {"type": "boolean"},
            "is_accessible": {"type": "boolean"},
            "has_power_outlet": {"type": "boolean"},
            "minimum_spend": {"type": "integer"},
            "description": {"type": "string"},
            "notes": {"type": "string"},
        },
    }
)


async def _parse_payload(
    request: Request,
    file_field: Optional[str],
) -> Tuple[dict[str, Any], Optional[UploadFile]]:
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

    for key, value in list(data.items()):
        if isinstance(value, str):
            try:
                data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass

    data = {
        k: v
        for k, v in data.items()
        if not (isinstance(v, str) and v.strip() == "")
    }

    return data, upload


async def _upload_and_replace(
    current_url: Optional[str],
    new_file: Optional[UploadFile],
    folder: str,
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
                pass

    return new_url


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, openapi_extra=TABLE_CREATE_DOC)
async def create_table(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new table for a restaurant.

    Accepts **application/json** or **multipart/form-data**. For multipart, send
    fields as form data and an optional **image** file; the stored image URL is
    written to **image** on the table. With JSON, **image** may be a URL string.

    - **restaurant_id**: Restaurant ID (required)
    - **table_number**: Table number/identifier (required)
    - **table_name**: Optional name for the table
    - **capacity**: Maximum seating capacity (required)
    - **min_capacity**: Minimum capacity for booking
    - **floor**: Floor location
    - **section**: Section within restaurant (e.g., "Patio", "Main Hall")
    - **position_x/position_y**: Coordinates for floor plan layout
    - **image**: File (multipart) or image URL string (JSON)
    - **qr_code**: URL to QR code for contactless ordering
    - **status**: Current status (available, occupied, reserved, cleaning, maintenance)
    - **is_bookable**: Can customers book this table online
    - **is_outdoor**: Is this an outdoor table
    - **is_accessible**: Wheelchair accessible
    - **has_power_outlet**: Has power outlets for devices
    - **minimum_spend**: Minimum order amount for special tables
    - **description**: Table description
    - **notes**: Internal notes
    """
    try:
        data, image_file = await _parse_payload(request, file_field="image")
        if image_file:
            image_url = await _upload_and_replace(None, image_file, folder="tables")
            data["image"] = image_url

        table_data = TableCreate(**data)

        existing_table = await TableService.get_table_by_number(
            db,
            table_data.restaurant_id,
            table_data.table_number,
        )

        if existing_table:
            return error_response(
                message=f"Table number '{table_data.table_number}' already exists for this restaurant",
                error_code="DUPLICATE_TABLE_NUMBER",
                status_code=status.HTTP_409_CONFLICT,
            )

        table = await TableService.create_table(db, table_data)
        return success_response(
            data=TableResponse.model_validate(table),
            message="Table created successfully",
        )
    except ValueError as e:
        return error_response(
            message="Failed to create table",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except ValidationError as e:
        return error_response(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except Exception as e:
        return error_response(
            message="Failed to create table",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/{table_id}", response_model=dict)
async def get_table(
    table_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get table by ID"""
    table = await TableService.get_table_by_id(db, table_id)
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    
    return success_response(
        data=TableResponse.model_validate(table),
        message="Table retrieved successfully"
    )


@router.get("/restaurant/{restaurant_id}", response_model=dict)
async def get_restaurant_tables(
    restaurant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[TableStatus] = Query(None, description="Filter by table status"),
    floor: Optional[str] = Query(None, description="Filter by floor"),
    section: Optional[str] = Query(None, description="Filter by section"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_bookable: Optional[bool] = Query(None, description="Filter by bookable status"),
    min_capacity: Optional[int] = Query(None, ge=1, description="Minimum capacity required"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of tables for a restaurant with optional filtering
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return (max 100)
    - **status**: Filter by table status
    - **floor**: Filter by floor
    - **section**: Filter by section
    - **is_active**: Filter by active status
    - **is_bookable**: Filter by bookable status
    - **min_capacity**: Filter by minimum capacity
    """
    tables, total = await TableService.get_tables(
        db,
        restaurant_id=restaurant_id,
        skip=skip,
        limit=limit,
        status=status,
        floor=floor,
        section=section,
        is_active=is_active,
        is_bookable=is_bookable,
        min_capacity=min_capacity
    )
    
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "tables": [TableResponse.model_validate(t) for t in tables]
        },
        message="Tables retrieved successfully"
    )


@router.get("/restaurant/{restaurant_id}/available", response_model=dict)
async def get_available_tables(
    restaurant_id: str,
    capacity: Optional[int] = Query(None, ge=1, description="Minimum capacity required"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available tables for a restaurant
    
    - **restaurant_id**: Restaurant ID
    - **capacity**: Minimum capacity required (optional)
    """
    tables = await TableService.get_available_tables(
        db,
        restaurant_id=restaurant_id,
        capacity=capacity
    )
    
    return success_response(
        data={
            "total": len(tables),
            "tables": [TableResponse.model_validate(t) for t in tables]
        },
        message="Available tables retrieved successfully"
    )


@router.get("/restaurant/{restaurant_id}/statistics", response_model=dict)
async def get_table_statistics(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get table statistics for a restaurant
    
    Returns counts of total, available, occupied, and reserved tables,
    along with total capacity and occupancy rate.
    """
    stats = await TableService.get_table_statistics(db, restaurant_id)
    
    return success_response(
        data=stats,
        message="Table statistics retrieved successfully"
    )


@router.put("/{table_id}", response_model=dict, openapi_extra=TABLE_UPDATE_DOC)
async def update_table(
    table_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update table information (JSON or multipart/form-data with optional image)."""
    try:
        existing = await TableService.get_table_by_id(db, table_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found",
            )

        data, image_file = await _parse_payload(request, file_field="image")
        image_url = await _upload_and_replace(
            existing.image,
            image_file,
            folder="tables",
        )
        if image_url:
            data["image"] = image_url

        table_data = TableUpdate(**data)
        table = await TableService.update_table(db, table_id, table_data)

        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found",
            )

        return success_response(
            data=TableResponse.model_validate(table),
            message="Table updated successfully",
        )
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(
            message="Failed to update table",
            error_code="INVALID_FILE",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except ValidationError as e:
        return error_response(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except Exception as e:
        return error_response(
            message="Failed to update table",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.patch("/{table_id}/status", response_model=dict)
async def update_table_status(
    table_id: str,
    status_data: TableStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update table status only
    
    - **status**: New status (available, occupied, reserved, cleaning, maintenance)
    """
    table = await TableService.update_table_status(db, table_id, status_data.status)
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    
    return success_response(
        data=TableResponse.model_validate(table),
        message=f"Table status updated to {status_data.status.value}"
    )


@router.post("/bulk/status", response_model=dict)
async def bulk_update_table_status(
    table_ids: List[str],
    status: TableStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update status for multiple tables
    
    - **table_ids**: List of table IDs to update
    - **status**: New status to apply to all tables
    """
    count = await TableService.bulk_update_status(db, table_ids, status)
    
    return success_response(
        data={"updated_count": count},
        message=f"Updated status for {count} tables"
    )


@router.delete("/{table_id}", response_model=dict)
async def delete_table(
    table_id: str,
    permanent: bool = Query(False, description="Permanently delete table"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete table (soft delete by default, set permanent=true for hard delete)
    
    - **table_id**: Table ID
    - **permanent**: If true, permanently delete the table from database
    """
    if permanent:
        success = await TableService.permanently_delete_table(db, table_id)
    else:
        success = await TableService.delete_table(db, table_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    
    return success_response(
        data={"id": table_id},
        message="Table deleted successfully"
    )
