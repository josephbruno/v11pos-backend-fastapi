"""
Row management schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.product.schema import CategoryResponse, ComboProductResponse, ProductResponse
from app.modules.row_management.model import RowType


class RowManagementBase(BaseModel):
    """Base row management schema"""
    name: str = Field(..., min_length=1, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    row_type: RowType

    active: bool = True
    show_title: bool = True
    sort_order: int = 0
    layout_style: Optional[str] = Field(None, max_length=30)
    items_per_view: Optional[int] = Field(None, ge=1)
    auto_scroll: bool = False

    category_ids: Optional[list[str]] = None
    product_ids: Optional[list[str]] = None
    combo_product_ids: Optional[list[str]] = None

    image: Optional[str] = None
    mobile_image: Optional[str] = None
    desktop_image: Optional[str] = None
    video_url: Optional[str] = Field(None, max_length=500)
    thumbnail_image: Optional[str] = None

    redirect_url: Optional[str] = Field(None, max_length=500)
    button_text: Optional[str] = Field(None, max_length=100)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    extra_data: Optional[dict] = Field(
        None,
        serialization_alias="metadata",
    )

    @model_validator(mode="after")
    def validate_row_type_payload(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be greater than or equal to start_at")

        if self.row_type == RowType.CATEGORY and not self.category_ids:
            raise ValueError("category_ids is required for category row type")
        if self.row_type == RowType.PRODUCT and not self.product_ids:
            raise ValueError("product_ids is required for product row type")
        if self.row_type == RowType.COMBO_PRODUCT and not self.combo_product_ids:
            raise ValueError("combo_product_ids is required for combo_product row type")
        if self.row_type in {RowType.SINGLE_BANNER, RowType.ADS_BANNER}:
            if not any([self.image, self.mobile_image, self.desktop_image]):
                raise ValueError("At least one banner image is required for banner row types")
        if self.row_type == RowType.ADS_VIDEO and not self.video_url:
            raise ValueError("video_url is required for ads_video row type")

        return self


class RowManagementCreate(RowManagementBase):
    """Schema for creating row management"""
    restaurant_id: str
    extra_data: Optional[dict] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata",
    )


class RowManagementUpdate(BaseModel):
    """Schema for updating row management"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    row_type: Optional[RowType] = None

    active: Optional[bool] = None
    show_title: Optional[bool] = None
    sort_order: Optional[int] = None
    layout_style: Optional[str] = Field(None, max_length=30)
    items_per_view: Optional[int] = Field(None, ge=1)
    auto_scroll: Optional[bool] = None

    category_ids: Optional[list[str]] = None
    product_ids: Optional[list[str]] = None
    combo_product_ids: Optional[list[str]] = None

    image: Optional[str] = None
    mobile_image: Optional[str] = None
    desktop_image: Optional[str] = None
    video_url: Optional[str] = Field(None, max_length=500)
    thumbnail_image: Optional[str] = None

    redirect_url: Optional[str] = Field(None, max_length=500)
    button_text: Optional[str] = Field(None, max_length=100)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    extra_data: Optional[dict] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata",
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be greater than or equal to start_at")
        return self


class RowManagementResponse(RowManagementBase):
    """Schema for row management response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RowManagementOpenFetchResponse(RowManagementResponse):
    """Row payload for public/open APIs: includes resolved catalog entities for configured IDs."""

    category_items: Optional[list[CategoryResponse]] = None
    product_items: Optional[list[ProductResponse]] = None
    combo_product_items: Optional[list[ComboProductResponse]] = None

    model_config = ConfigDict(from_attributes=True)
