"""
Row management API routes
"""
import json
from typing import Any, Optional, Tuple

from fastapi import APIRouter, Depends, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import error_response, success_response
from app.modules.row_management.model import RowType
from app.modules.row_management.schema import (
    RowManagementCreate,
    RowManagementResponse,
    RowManagementUpdate,
)
from app.modules.row_management.service import DuplicateError, RowManagementService
from app.modules.user.model import User
from app.services.storage_service import (
    delete_file,
    get_file_url,
    get_object_name_from_url,
    upload_file,
)


router = APIRouter(prefix="/row-management", tags=["Row Management"])


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


ROW_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "name": {"type": "string"},
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "description": {"type": "string"},
            "row_type": {"type": "string"},
            "category_ids": {"type": "array", "items": {"type": "string"}},
            "product_ids": {"type": "array", "items": {"type": "string"}},
            "combo_product_ids": {"type": "array", "items": {"type": "string"}},
            "image": {"type": "string", "format": "binary"},
            "mobile_image": {"type": "string", "format": "binary"},
            "desktop_image": {"type": "string", "format": "binary"},
            "thumbnail_image": {"type": "string", "format": "binary"},
            "video_file": {"type": "string", "format": "binary"},
        },
        "required": ["restaurant_id", "name", "row_type"],
    }
)

ROW_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "description": {"type": "string"},
            "row_type": {"type": "string"},
            "category_ids": {"type": "array", "items": {"type": "string"}},
            "product_ids": {"type": "array", "items": {"type": "string"}},
            "combo_product_ids": {"type": "array", "items": {"type": "string"}},
            "image": {"type": "string", "format": "binary"},
            "mobile_image": {"type": "string", "format": "binary"},
            "desktop_image": {"type": "string", "format": "binary"},
            "thumbnail_image": {"type": "string", "format": "binary"},
            "video_file": {"type": "string", "format": "binary"},
        },
    }
)


async def _parse_payload(request: Request) -> Tuple[dict, dict[str, UploadFile]]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = await request.json()
        return data, {}

    form = await request.form()
    data: dict[str, Any] = {}
    uploads: dict[str, UploadFile] = {}

    for key, value in form.multi_items():
        if isinstance(value, (UploadFile, StarletteUploadFile)) or (
            hasattr(value, "filename") and hasattr(value, "file")
        ):
            uploads[key] = value
            continue

        if key in data:
            existing = data[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                data[key] = [existing, value]
        else:
            data[key] = value

    for key, value in data.items():
        if isinstance(value, str):
            try:
                data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass

    return data, uploads


async def _upload_and_replace(
    current_url: Optional[str],
    new_file: Optional[UploadFile],
    folder: str,
) -> Optional[str]:
    if not new_file:
        return current_url

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


@router.post("", status_code=status.HTTP_201_CREATED, openapi_extra=ROW_CREATE_DOC)
async def create_row_management(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new row management entry"""
    try:
        data, uploads = await _parse_payload(request)
        data["image"] = await _upload_and_replace(None, uploads.get("image"), "row-management/images") or data.get("image")
        data["mobile_image"] = await _upload_and_replace(None, uploads.get("mobile_image"), "row-management/mobile") or data.get("mobile_image")
        data["desktop_image"] = await _upload_and_replace(None, uploads.get("desktop_image"), "row-management/desktop") or data.get("desktop_image")
        data["thumbnail_image"] = await _upload_and_replace(None, uploads.get("thumbnail_image"), "row-management/thumbnails") or data.get("thumbnail_image")
        data["video_url"] = await _upload_and_replace(None, uploads.get("video_file"), "row-management/videos") or data.get("video_url")

        row = await RowManagementService.create_row(db, RowManagementCreate(**data))
        return success_response(
            message="Row management created successfully",
            data=RowManagementResponse.model_validate(row).model_dump(by_alias=True),
            timezone=getattr(current_user, "timezone", None),
            status_code=status.HTTP_201_CREATED,
        )
    except DuplicateError as e:
        return error_response(
            message="Failed to create row management",
            error_code="DUPLICATE_ENTRY",
            error_details=str(e),
            field=e.field,
            status_code=status.HTTP_409_CONFLICT,
        )
    except ValueError as e:
        return error_response(
            message="Failed to create row management",
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to create row management",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/restaurant/{restaurant_id}")
async def get_row_management_list(
    restaurant_id: str,
    row_type: Optional[RowType] = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get row management list for a restaurant (includes resolved category/product/combo payloads)."""
    try:
        rows = await RowManagementService.get_rows_by_restaurant_with_catalog(
            db, restaurant_id, row_type, active_only, skip, limit
        )
        return success_response(
            message="Row management retrieved successfully",
            data=[item.model_dump(by_alias=True) for item in rows],
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve row management",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/{row_id}")
async def get_row_management(
    row_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get row management by ID"""
    try:
        row = await RowManagementService.get_row_by_id(db, row_id)
        if not row:
            return error_response(
                message="Row management not found",
                error_code="NOT_FOUND",
                error_details=f"Row management with ID {row_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            message="Row management retrieved successfully",
            data=RowManagementResponse.model_validate(row).model_dump(by_alias=True),
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve row management",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/{row_id}", openapi_extra=ROW_UPDATE_DOC)
@router.patch("/{row_id}", openapi_extra=ROW_UPDATE_DOC)
@router.put("/{row_id}", openapi_extra=ROW_UPDATE_DOC)
async def update_row_management(
    row_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update row management"""
    try:
        existing = await RowManagementService.get_row_by_id(db, row_id)
        if not existing:
            return error_response(
                message="Row management not found",
                error_code="NOT_FOUND",
                error_details=f"Row management with ID {row_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        data, uploads = await _parse_payload(request)
        if uploads.get("image"):
            data["image"] = await _upload_and_replace(existing.image, uploads.get("image"), "row-management/images")
        if uploads.get("mobile_image"):
            data["mobile_image"] = await _upload_and_replace(existing.mobile_image, uploads.get("mobile_image"), "row-management/mobile")
        if uploads.get("desktop_image"):
            data["desktop_image"] = await _upload_and_replace(existing.desktop_image, uploads.get("desktop_image"), "row-management/desktop")
        if uploads.get("thumbnail_image"):
            data["thumbnail_image"] = await _upload_and_replace(existing.thumbnail_image, uploads.get("thumbnail_image"), "row-management/thumbnails")
        if uploads.get("video_file"):
            data["video_url"] = await _upload_and_replace(existing.video_url, uploads.get("video_file"), "row-management/videos")

        row = await RowManagementService.update_row(db, row_id, RowManagementUpdate(**data))
        return success_response(
            message="Row management updated successfully",
            data=RowManagementResponse.model_validate(row).model_dump(by_alias=True),
            timezone=getattr(current_user, "timezone", None),
        )
    except DuplicateError as e:
        return error_response(
            message="Failed to update row management",
            error_code="DUPLICATE_ENTRY",
            error_details=str(e),
            field=e.field,
            status_code=status.HTTP_409_CONFLICT,
        )
    except ValueError as e:
        return error_response(
            message="Failed to update row management",
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to update row management",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.delete("/{row_id}")
async def delete_row_management(
    row_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete row management"""
    try:
        deleted = await RowManagementService.delete_row(db, row_id)
        if not deleted:
            return error_response(
                message="Row management not found",
                error_code="NOT_FOUND",
                error_details=f"Row management with ID {row_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            message="Row management deleted successfully",
            data={"id": row_id},
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to delete row management",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
