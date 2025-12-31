from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CopyTypeEnum(str, Enum):
    """Copy type enumeration"""
    CATEGORY = "category"
    PRODUCT = "product"
    COMBO = "combo"
    MODIFIER = "modifier"
    CATEGORY_PRODUCTS = "category_products"
    FULL_MENU = "full_menu"


class CopyStatusEnum(str, Enum):
    """Copy status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class CopyActionEnum(str, Enum):
    """Copy action enumeration"""
    COPIED = "copied"
    SKIPPED = "skipped"
    FAILED = "failed"


# ============== Copy Request Schemas ==============

class CopyEntityIds(BaseModel):
    """Source entity IDs for specific item copy"""
    category_ids: Optional[List[str]] = Field(None, description="Category IDs to copy")
    product_ids: Optional[List[str]] = Field(None, description="Product IDs to copy")
    combo_ids: Optional[List[str]] = Field(None, description="Combo IDs to copy")
    modifier_ids: Optional[List[str]] = Field(None, description="Modifier IDs to copy")


class CopyOptions(BaseModel):
    """Copy operation options"""
    skip_duplicates: bool = Field(True, description="Skip duplicate items")
    copy_images: bool = Field(True, description="Copy product images")
    copy_prices: bool = Field(True, description="Copy prices")
    copy_stock: bool = Field(False, description="Copy stock quantities")
    maintain_relationships: bool = Field(True, description="Maintain category-product relationships")
    include_inactive: bool = Field(False, description="Include inactive items")
    include_unavailable: bool = Field(False, description="Include unavailable items")


class DataCopyCreate(BaseModel):
    """Schema for creating data copy request"""
    source_restaurant_id: str = Field(..., description="Source restaurant ID")
    destination_restaurant_ids: List[str] = Field(..., min_length=1, description="Destination restaurant ID(s)")
    copy_type: CopyTypeEnum = Field(..., description="Type of copy operation")
    copy_name: Optional[str] = Field(None, description="Name for this copy operation")
    source_entity_ids: Optional[CopyEntityIds] = Field(None, description="Specific entity IDs to copy")
    options: Optional[CopyOptions] = Field(default_factory=CopyOptions, description="Copy options")
    notes: Optional[str] = Field(None, max_length=1000, description="Copy notes")
    
    @field_validator('destination_restaurant_ids')
    @classmethod
    def validate_destinations(cls, v):
        if not v:
            raise ValueError("At least one destination restaurant is required")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate destination restaurant IDs not allowed")
        return v


class DataCopyBulkCreate(BaseModel):
    """Schema for bulk copy to multiple restaurants"""
    source_restaurant_id: str = Field(..., description="Source restaurant ID")
    destination_restaurant_ids: List[str] = Field(..., min_length=1, description="Multiple destination restaurant IDs")
    copy_type: CopyTypeEnum = Field(..., description="Type of copy operation")
    copy_name_prefix: Optional[str] = Field("Bulk Copy", description="Prefix for copy names")
    source_entity_ids: Optional[CopyEntityIds] = Field(None, description="Specific entity IDs to copy")
    options: Optional[CopyOptions] = Field(default_factory=CopyOptions, description="Copy options")
    notes: Optional[str] = Field(None, max_length=1000, description="Copy notes")


class DataCopyFromTemplate(BaseModel):
    """Schema for copy using template"""
    template_id: str = Field(..., description="Copy template ID")
    source_restaurant_id: str = Field(..., description="Source restaurant ID")
    destination_restaurant_ids: List[str] = Field(..., min_length=1, description="Destination restaurant ID(s)")
    source_entity_ids: Optional[CopyEntityIds] = Field(None, description="Specific entity IDs to copy")
    notes: Optional[str] = Field(None, max_length=1000, description="Copy notes")


# ============== Copy Response Schemas ==============

class CopyStatistics(BaseModel):
    """Copy operation statistics"""
    total_items: int = Field(0, description="Total items to copy")
    items_copied: int = Field(0, description="Items successfully copied")
    items_skipped: int = Field(0, description="Items skipped")
    items_failed: int = Field(0, description="Items failed to copy")
    categories_copied: int = Field(0, description="Categories copied")
    categories_skipped: int = Field(0, description="Categories skipped")
    products_copied: int = Field(0, description="Products copied")
    products_skipped: int = Field(0, description="Products skipped")
    combos_copied: int = Field(0, description="Combos copied")
    combos_skipped: int = Field(0, description="Combos skipped")
    modifiers_copied: int = Field(0, description="Modifiers copied")
    modifiers_skipped: int = Field(0, description="Modifiers skipped")
    duplicates_found: int = Field(0, description="Duplicates found")
    duplicates_skipped: int = Field(0, description="Duplicates skipped")


class DataCopyResponse(BaseModel):
    """Schema for data copy response"""
    id: str
    source_restaurant_id: str
    destination_restaurant_id: str
    copy_number: str
    copy_name: str
    copy_type: str
    status: str
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_time: Optional[int]
    statistics: CopyStatistics
    skip_duplicates: bool
    copy_images: bool
    copy_prices: bool
    copy_stock: bool
    maintain_relationships: bool
    error_message: Optional[str]
    notes: Optional[str]
    copied_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DataCopyDetailResponse(DataCopyResponse):
    """Detailed data copy response with logs"""
    entity_mapping: Optional[Dict[str, Any]]
    copy_summary: Optional[Dict[str, Any]]
    skipped_items: Optional[Dict[str, Any]]
    failed_items: Optional[Dict[str, Any]]
    logs: Optional[List[Dict[str, Any]]]


class DataCopyListResponse(BaseModel):
    """List of data copy operations"""
    items: List[DataCopyResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Copy Log Schemas ==============

class CopyLogResponse(BaseModel):
    """Schema for copy log response"""
    id: str
    data_copy_id: str
    source_entity_id: str
    source_entity_type: str
    source_entity_name: str
    destination_entity_id: Optional[str]
    destination_entity_type: Optional[str]
    status: str
    action_taken: str
    is_duplicate: bool
    duplicate_field: Optional[str]
    duplicate_value: Optional[str]
    existing_entity_id: Optional[str]
    error_message: Optional[str]
    error_type: Optional[str]
    processed_at: datetime
    processing_time_ms: Optional[int]
    
    class Config:
        from_attributes = True


class CopyLogListResponse(BaseModel):
    """List of copy logs"""
    items: List[CopyLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Copy Template Schemas ==============

class CopyTemplateCreate(BaseModel):
    """Schema for creating copy template"""
    template_name: str = Field(..., min_length=1, max_length=255, description="Template name")
    template_description: Optional[str] = Field(None, max_length=1000, description="Template description")
    copy_type: CopyTypeEnum = Field(..., description="Type of copy operation")
    skip_duplicates: bool = Field(True, description="Skip duplicate items")
    copy_images: bool = Field(True, description="Copy product images")
    copy_prices: bool = Field(True, description="Copy prices")
    copy_stock: bool = Field(False, description="Copy stock quantities")
    maintain_relationships: bool = Field(True, description="Maintain category-product relationships")
    include_inactive: bool = Field(False, description="Include inactive items")
    include_unavailable: bool = Field(False, description="Include unavailable items")


class CopyTemplateUpdate(BaseModel):
    """Schema for updating copy template"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    template_description: Optional[str] = Field(None, max_length=1000, description="Template description")
    copy_type: Optional[CopyTypeEnum] = Field(None, description="Type of copy operation")
    skip_duplicates: Optional[bool] = Field(None, description="Skip duplicate items")
    copy_images: Optional[bool] = Field(None, description="Copy product images")
    copy_prices: Optional[bool] = Field(None, description="Copy prices")
    copy_stock: Optional[bool] = Field(None, description="Copy stock quantities")
    maintain_relationships: Optional[bool] = Field(None, description="Maintain category-product relationships")
    include_inactive: Optional[bool] = Field(None, description="Include inactive items")
    include_unavailable: Optional[bool] = Field(None, description="Include unavailable items")
    is_active: Optional[bool] = Field(None, description="Template active status")


class CopyTemplateResponse(BaseModel):
    """Schema for copy template response"""
    id: str
    template_name: str
    template_description: Optional[str]
    copy_type: str
    skip_duplicates: bool
    copy_images: bool
    copy_prices: bool
    copy_stock: bool
    maintain_relationships: bool
    include_inactive: bool
    include_unavailable: bool
    is_active: bool
    is_system_template: bool
    usage_count: int
    last_used_at: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CopyTemplateListResponse(BaseModel):
    """List of copy templates"""
    items: List[CopyTemplateResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Duplicate Check Schemas ==============

class DuplicateCheckRequest(BaseModel):
    """Schema for checking duplicates before copy"""
    source_restaurant_id: str = Field(..., description="Source restaurant ID")
    destination_restaurant_id: str = Field(..., description="Destination restaurant ID")
    copy_type: CopyTypeEnum = Field(..., description="Type of copy operation")
    source_entity_ids: Optional[CopyEntityIds] = Field(None, description="Specific entity IDs to check")


class DuplicateItem(BaseModel):
    """Duplicate item details"""
    source_id: str
    source_name: str
    entity_type: str
    existing_id: str
    existing_name: str
    duplicate_field: str


class DuplicateCheckResponse(BaseModel):
    """Duplicate check response"""
    has_duplicates: bool
    duplicate_count: int
    total_items: int
    items_to_copy: int
    items_to_skip: int
    duplicates: List[DuplicateItem]


# ============== Copy Preview Schemas ==============

class CopyPreviewRequest(BaseModel):
    """Schema for previewing copy operation"""
    source_restaurant_id: str = Field(..., description="Source restaurant ID")
    destination_restaurant_id: str = Field(..., description="Destination restaurant ID")
    copy_type: CopyTypeEnum = Field(..., description="Type of copy operation")
    source_entity_ids: Optional[CopyEntityIds] = Field(None, description="Specific entity IDs to preview")
    options: Optional[CopyOptions] = Field(default_factory=CopyOptions, description="Copy options")


class PreviewItem(BaseModel):
    """Preview item details"""
    entity_id: str
    entity_type: str
    entity_name: str
    will_copy: bool
    reason: Optional[str]
    is_duplicate: bool
    has_dependencies: bool
    dependencies: List[str] = []


class CopyPreviewResponse(BaseModel):
    """Copy preview response"""
    source_restaurant_id: str
    destination_restaurant_id: str
    copy_type: str
    total_items: int
    items_to_copy: int
    items_to_skip: int
    estimated_time_seconds: int
    preview_items: List[PreviewItem]
    warnings: List[str] = []
