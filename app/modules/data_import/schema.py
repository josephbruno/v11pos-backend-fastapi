from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ImportTypeEnum(str, Enum):
    """Import type enumeration"""
    CATEGORY = "category"
    PRODUCT = "product"
    CATEGORY_PRODUCT = "category_product"
    CUSTOMER = "customer"
    STAFF = "staff"


class ImportStatusEnum(str, Enum):
    """Import status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ImportFileFormatEnum(str, Enum):
    """Import file format enumeration"""
    CSV = "csv"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"


# Data Import Schemas

class DataImportBase(BaseModel):
    """Base data import schema"""
    import_name: str = Field(..., min_length=1, max_length=255)
    import_type: ImportTypeEnum
    update_existing: bool = False
    skip_duplicates: bool = True
    validate_only: bool = False
    notes: Optional[str] = None


class DataImportCreate(DataImportBase):
    """Schema for creating data import"""
    restaurant_id: str
    column_mapping: Optional[Dict[str, Any]] = None
    import_options: Optional[Dict[str, Any]] = None


class DataImportUpdate(BaseModel):
    """Schema for updating data import"""
    import_name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    remarks: Optional[str] = None


class DataImportResponse(DataImportBase):
    """Schema for data import response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    import_number: str
    file_name: str
    file_format: ImportFileFormatEnum
    file_path: str
    file_size: int
    file_url: Optional[str]
    status: ImportStatusEnum
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_time: Optional[int]
    total_rows: int
    rows_processed: int
    rows_imported: int
    rows_updated: int
    rows_skipped: int
    rows_failed: int
    duplicates_found: int
    duplicates_skipped: int
    duplicates_updated: int
    validation_errors_count: int
    validation_warnings_count: int
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    import_summary: Optional[Dict[str, Any]]
    validation_errors: Optional[Dict[str, Any]]
    validation_warnings: Optional[Dict[str, Any]]
    skipped_rows: Optional[Dict[str, Any]]
    failed_rows: Optional[Dict[str, Any]]
    column_mapping: Optional[Dict[str, Any]]
    import_options: Optional[Dict[str, Any]]
    imported_by: str
    remarks: Optional[str]
    import_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


# Import Log Schemas

class ImportLogResponse(BaseModel):
    """Schema for import log response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    data_import_id: str
    row_number: int
    row_data: Optional[Dict[str, Any]]
    status: str
    action_taken: Optional[str]
    entity_id: Optional[str]
    entity_type: Optional[str]
    error_message: Optional[str]
    error_type: Optional[str]
    is_duplicate: bool
    duplicate_field: Optional[str]
    duplicate_value: Optional[str]
    existing_entity_id: Optional[str]
    validation_errors: Optional[Dict[str, Any]]
    validation_warnings: Optional[Dict[str, Any]]
    processed_at: datetime
    processing_time_ms: Optional[int]


# Import Template Schemas

class ImportTemplateBase(BaseModel):
    """Base import template schema"""
    template_name: str = Field(..., min_length=1, max_length=255)
    template_description: Optional[str] = None
    import_type: ImportTypeEnum
    file_format: ImportFileFormatEnum


class ImportTemplateCreate(ImportTemplateBase):
    """Schema for creating import template"""
    required_columns: Dict[str, Any]
    optional_columns: Optional[Dict[str, Any]] = None
    column_mapping: Dict[str, Any]
    sample_data: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class ImportTemplateUpdate(BaseModel):
    """Schema for updating import template"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_description: Optional[str] = None
    required_columns: Optional[Dict[str, Any]] = None
    optional_columns: Optional[Dict[str, Any]] = None
    column_mapping: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ImportTemplateResponse(ImportTemplateBase):
    """Schema for import template response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    required_columns: Dict[str, Any]
    optional_columns: Optional[Dict[str, Any]]
    column_mapping: Dict[str, Any]
    sample_data: Optional[Dict[str, Any]]
    validation_rules: Optional[Dict[str, Any]]
    is_active: bool
    is_system_template: bool
    usage_count: int
    last_used_at: Optional[datetime]
    created_by: str
    template_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


# File Upload Schemas

class FileUploadRequest(BaseModel):
    """Schema for file upload request"""
    import_name: str = Field(..., min_length=1, max_length=255)
    import_type: ImportTypeEnum
    restaurant_id: str
    update_existing: bool = Field(default=False, description="Update existing records if duplicates found")
    skip_duplicates: bool = Field(default=True, description="Skip duplicate records")
    validate_only: bool = Field(default=False, description="Only validate without importing")
    notes: Optional[str] = None


class ValidationResult(BaseModel):
    """Schema for validation result"""
    is_valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []


class ImportStartRequest(BaseModel):
    """Schema for starting an import"""
    import_id: str
    update_existing: Optional[bool] = None
    skip_duplicates: Optional[bool] = None


class ImportProgressResponse(BaseModel):
    """Schema for import progress response"""
    import_id: str
    status: ImportStatusEnum
    progress_percentage: float
    rows_processed: int
    total_rows: int
    rows_imported: int
    rows_failed: int
    current_row: Optional[int]
    estimated_time_remaining: Optional[int]  # seconds


# Category Import Schemas

class CategoryImportRow(BaseModel):
    """Schema for category import row"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category: Optional[str] = None  # Parent category name
    display_order: Optional[int] = None
    is_active: bool = True
    image_url: Optional[str] = None
    
    # Tax
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    cgst_rate: Optional[float] = Field(None, ge=0, le=100)
    sgst_rate: Optional[float] = Field(None, ge=0, le=100)
    
    # Additional fields
    preparation_time: Optional[int] = None
    is_vegetarian: Optional[bool] = None
    is_non_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None


class CategoryImportData(BaseModel):
    """Schema for category import data"""
    categories: List[CategoryImportRow]


# Product Import Schemas

class ProductImportRow(BaseModel):
    """Schema for product import row"""
    name: str = Field(..., min_length=1, max_length=200)
    category_name: str = Field(..., description="Category name (must exist or be imported)")
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    
    # Pricing
    price: int = Field(..., ge=0, description="Price in paise/cents")
    cost_price: Optional[int] = Field(None, ge=0)
    
    # Inventory
    track_inventory: bool = True
    current_stock: Optional[int] = Field(None, ge=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    
    # Tax
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    cgst_rate: Optional[float] = Field(None, ge=0, le=100)
    sgst_rate: Optional[float] = Field(None, ge=0, le=100)
    is_tax_inclusive: bool = False
    
    # Status
    is_active: bool = True
    is_available: bool = True
    
    # Additional fields
    preparation_time: Optional[int] = None
    calories: Optional[int] = None
    spice_level: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    is_non_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    is_featured: Optional[bool] = None
    
    # Display
    display_order: Optional[int] = None
    image_url: Optional[str] = None


class ProductImportData(BaseModel):
    """Schema for product import data"""
    products: List[ProductImportRow]


class CategoryProductImportRow(BaseModel):
    """Schema for combined category and product import"""
    category_name: str
    category_description: Optional[str] = None
    product_name: str
    product_description: Optional[str] = None
    product_sku: Optional[str] = None
    price: int
    cost_price: Optional[int] = None
    is_active: bool = True
    tax_rate: Optional[float] = None


# List responses

class DataImportListResponse(BaseModel):
    """Schema for paginated data import list"""
    total: int
    page: int
    page_size: int
    data: List[DataImportResponse]


class ImportLogListResponse(BaseModel):
    """Schema for paginated import log list"""
    total: int
    page: int
    page_size: int
    data: List[ImportLogResponse]


class ImportTemplateListResponse(BaseModel):
    """Schema for paginated import template list"""
    total: int
    page: int
    page_size: int
    data: List[ImportTemplateResponse]


# Sample data generation

class GenerateSampleRequest(BaseModel):
    """Schema for generating sample data"""
    import_type: ImportTypeEnum
    file_format: ImportFileFormatEnum = ImportFileFormatEnum.EXCEL
    include_sample_data: bool = True
    row_count: int = Field(default=10, ge=1, le=100)


class BulkImportRequest(BaseModel):
    """Schema for bulk import request"""
    restaurant_id: str
    import_type: ImportTypeEnum
    data: Dict[str, Any]
    update_existing: bool = False
    skip_duplicates: bool = True
