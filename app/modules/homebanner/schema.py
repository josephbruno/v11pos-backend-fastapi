"""
Home banner schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HomeBannerBase(BaseModel):
    """Base home banner schema"""
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    mobile_image: Optional[str] = None
    desktop_image: Optional[str] = None
    redirect_url: Optional[str] = Field(None, max_length=500)
    button_text: Optional[str] = Field(None, max_length=100)
    active: bool = True
    featured: bool = False
    sort_order: int = 0
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_banner_variants(self):
        if not self.mobile_image and not self.desktop_image:
            raise ValueError("At least one of mobile_image or desktop_image is required")
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be greater than or equal to start_at")
        return self


class HomeBannerCreate(HomeBannerBase):
    """Schema for creating home banner"""
    restaurant_id: str


class HomeBannerUpdate(BaseModel):
    """Schema for updating home banner"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    mobile_image: Optional[str] = None
    desktop_image: Optional[str] = None
    redirect_url: Optional[str] = Field(None, max_length=500)
    button_text: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    featured: Optional[bool] = None
    sort_order: Optional[int] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be greater than or equal to start_at")
        return self


class HomeBannerResponse(HomeBannerBase):
    """Schema for home banner response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
