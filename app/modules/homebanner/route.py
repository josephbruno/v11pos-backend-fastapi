"""
Home banner API routes
"""
import json
from typing import Any, Optional, Tuple

from fastapi import APIRouter, Depends, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import error_response, success_response
from app.modules.homebanner.schema import HomeBannerCreate, HomeBannerResponse, HomeBannerUpdate
from app.modules.homebanner.service import DuplicateError, HomeBannerService
from app.modules.user.model import User
from app.services.storage_service import (
    delete_file,
    get_file_url,
    get_object_name_from_url,
    upload_file,
)


router = APIRouter(prefix="/homebanners", tags=["Homebanner"])


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


HOME_BANNER_CREATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "restaurant_id": {"type": "string"},
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "description": {"type": "string"},
            "mobile_image": {"type": "string", "format": "binary"},
            "desktop_image": {"type": "string", "format": "binary"},
            "redirect_url": {"type": "string"},
            "button_text": {"type": "string"},
            "active": {"type": "boolean"},
            "featured": {"type": "boolean"},
            "sort_order": {"type": "integer"},
        },
        "required": ["restaurant_id", "title"],
    }
)

HOME_BANNER_UPDATE_DOC = _multipart_request_body(
    {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "description": {"type": "string"},
            "mobile_image": {"type": "string", "format": "binary"},
            "desktop_image": {"type": "string", "format": "binary"},
            "redirect_url": {"type": "string"},
            "button_text": {"type": "string"},
            "active": {"type": "boolean"},
            "featured": {"type": "boolean"},
            "sort_order": {"type": "integer"},
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


@router.post("", status_code=status.HTTP_201_CREATED, openapi_extra=HOME_BANNER_CREATE_DOC)
async def create_home_banner(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new home banner"""
    try:
        data, uploads = await _parse_payload(request)
        data["mobile_image"] = await _upload_and_replace(None, uploads.get("mobile_image"), "homebanners/mobile") or data.get("mobile_image")
        data["desktop_image"] = await _upload_and_replace(None, uploads.get("desktop_image"), "homebanners/desktop") or data.get("desktop_image")

        banner = await HomeBannerService.create_banner(db, HomeBannerCreate(**data))
        return success_response(
            message="Home banner created successfully",
            data=HomeBannerResponse.model_validate(banner).model_dump(),
            timezone=getattr(current_user, "timezone", None),
            status_code=status.HTTP_201_CREATED,
        )
    except DuplicateError as e:
        return error_response(
            message="Failed to create home banner",
            error_code="DUPLICATE_ENTRY",
            error_details=str(e),
            field=e.field,
            status_code=status.HTTP_409_CONFLICT,
        )
    except ValueError as e:
        return error_response(
            message="Failed to create home banner",
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to create home banner",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/restaurant/{restaurant_id}")
async def get_home_banners(
    restaurant_id: str,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get home banners for a restaurant"""
    try:
        banners = await HomeBannerService.get_banners_by_restaurant(db, restaurant_id, active_only, skip, limit)
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


@router.get("/{banner_id}")
async def get_home_banner(
    banner_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get home banner by ID"""
    try:
        banner = await HomeBannerService.get_banner_by_id(db, banner_id)
        if not banner:
            return error_response(
                message="Home banner not found",
                error_code="NOT_FOUND",
                error_details=f"Home banner with ID {banner_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            message="Home banner retrieved successfully",
            data=HomeBannerResponse.model_validate(banner).model_dump(),
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve home banner",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/{banner_id}", openapi_extra=HOME_BANNER_UPDATE_DOC)
@router.patch("/{banner_id}", openapi_extra=HOME_BANNER_UPDATE_DOC)
@router.put("/{banner_id}", openapi_extra=HOME_BANNER_UPDATE_DOC)
async def update_home_banner(
    banner_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update home banner"""
    try:
        existing = await HomeBannerService.get_banner_by_id(db, banner_id)
        if not existing:
            return error_response(
                message="Home banner not found",
                error_code="NOT_FOUND",
                error_details=f"Home banner with ID {banner_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        data, uploads = await _parse_payload(request)
        if uploads.get("mobile_image"):
            data["mobile_image"] = await _upload_and_replace(existing.mobile_image, uploads.get("mobile_image"), "homebanners/mobile")
        if uploads.get("desktop_image"):
            data["desktop_image"] = await _upload_and_replace(existing.desktop_image, uploads.get("desktop_image"), "homebanners/desktop")

        banner = await HomeBannerService.update_banner(db, banner_id, HomeBannerUpdate(**data))
        return success_response(
            message="Home banner updated successfully",
            data=HomeBannerResponse.model_validate(banner).model_dump(),
            timezone=getattr(current_user, "timezone", None),
        )
    except DuplicateError as e:
        return error_response(
            message="Failed to update home banner",
            error_code="DUPLICATE_ENTRY",
            error_details=str(e),
            field=e.field,
            status_code=status.HTTP_409_CONFLICT,
        )
    except ValueError as e:
        return error_response(
            message="Failed to update home banner",
            error_code="VALIDATION_ERROR",
            error_details=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            message="Failed to update home banner",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.delete("/{banner_id}")
async def delete_home_banner(
    banner_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete home banner"""
    try:
        deleted = await HomeBannerService.delete_banner(db, banner_id)
        if not deleted:
            return error_response(
                message="Home banner not found",
                error_code="NOT_FOUND",
                error_details=f"Home banner with ID {banner_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            message="Home banner deleted successfully",
            data={"id": banner_id},
            timezone=getattr(current_user, "timezone", None),
        )
    except Exception as e:
        return error_response(
            message="Failed to delete home banner",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
