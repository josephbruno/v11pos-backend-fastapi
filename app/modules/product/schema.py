"""
Product catalog and inventory schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.modules.product.model import ModifierType


# Category Schemas

class CategoryBase(BaseModel):
    """Base category schema"""
    # Basic Information
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    # Parent-Child Hierarchy
    parent_id: Optional[str] = None
    level: int = 0
    
    # Display & Ordering
    active: bool = True
    sort_order: int = 0
    is_featured: bool = False
    
    # Media
    image: Optional[str] = None
    icon: Optional[str] = None
    banner_image: Optional[str] = None
    thumbnail: Optional[str] = None
    
    # Colors & Styling
    color: Optional[str] = Field(None, max_length=7)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)
    
    # Display Settings
    display_type: Optional[str] = Field(None, max_length=20)
    items_per_row: Optional[int] = None
    show_in_menu: bool = True
    show_in_homepage: bool = False
    show_in_pos: bool = True
    
    # Availability Settings
    available_for_delivery: bool = True
    available_for_takeaway: bool = True
    available_for_dine_in: bool = True
    
    # Time-based Availability
    available_from_time: Optional[str] = Field(None, max_length=10)
    available_to_time: Optional[str] = Field(None, max_length=10)
    available_days: Optional[dict] = None
    
    # Tax Settings
    tax_rate: Optional[float] = None
    tax_inclusive: bool = False
    
    # SEO & Marketing
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    meta_tags: Optional[dict] = None
    
    # Statistics & Analytics
    product_count: int = 0
    total_sales: int = 0
    view_count: int = 0
    order_count: int = 0
    
    # Commission & Pricing
    commission_percentage: Optional[float] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    
    # Discounts & Promotions
    discount_applicable: bool = True
    default_discount_percentage: Optional[float] = None
    
    # Attributes & Filters
    attributes: Optional[dict] = None
    tags: Optional[dict] = None
    dietary_info: Optional[dict] = None
    
    # Kitchen & Operations
    kitchen_station: Optional[str] = Field(None, max_length=50)
    preparation_area: Optional[str] = Field(None, max_length=50)
    avg_preparation_time: Optional[int] = None
    
    # Content & Notes
    long_description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    ingredients_note: Optional[str] = None
    allergen_info: Optional[str] = None
    
    # External Integration
    external_id: Optional[str] = Field(None, max_length=100)
    external_url: Optional[str] = Field(None, max_length=500)


class CategoryCreate(CategoryBase):
    """Schema for creating category"""
    restaurant_id: str


class CategoryUpdate(BaseModel):
    """Schema for updating category"""
    # Basic Information
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    
    # Parent-Child Hierarchy
    parent_id: Optional[str] = None
    level: Optional[int] = None
    
    # Display & Ordering
    active: Optional[bool] = None
    sort_order: Optional[int] = None
    is_featured: Optional[bool] = None
    
    # Media
    image: Optional[str] = None
    icon: Optional[str] = None
    banner_image: Optional[str] = None
    thumbnail: Optional[str] = None
    
    # Colors & Styling
    color: Optional[str] = Field(None, max_length=7)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)
    
    # Display Settings
    display_type: Optional[str] = Field(None, max_length=20)
    items_per_row: Optional[int] = None
    show_in_menu: Optional[bool] = None
    show_in_homepage: Optional[bool] = None
    show_in_pos: Optional[bool] = None
    
    # Availability Settings
    available_for_delivery: Optional[bool] = None
    available_for_takeaway: Optional[bool] = None
    available_for_dine_in: Optional[bool] = None
    
    # Time-based Availability
    available_from_time: Optional[str] = Field(None, max_length=10)
    available_to_time: Optional[str] = Field(None, max_length=10)
    available_days: Optional[dict] = None
    
    # Tax Settings
    tax_rate: Optional[float] = None
    tax_inclusive: Optional[bool] = None
    
    # SEO & Marketing
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    meta_tags: Optional[dict] = None
    
    # Statistics & Analytics
    product_count: Optional[int] = None
    total_sales: Optional[int] = None
    view_count: Optional[int] = None
    order_count: Optional[int] = None
    
    # Commission & Pricing
    commission_percentage: Optional[float] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    
    # Discounts & Promotions
    discount_applicable: Optional[bool] = None
    default_discount_percentage: Optional[float] = None
    
    # Attributes & Filters
    attributes: Optional[dict] = None
    tags: Optional[dict] = None
    dietary_info: Optional[dict] = None
    
    # Kitchen & Operations
    kitchen_station: Optional[str] = Field(None, max_length=50)
    preparation_area: Optional[str] = Field(None, max_length=50)
    avg_preparation_time: Optional[int] = None
    
    # Content & Notes
    long_description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    ingredients_note: Optional[str] = None
    allergen_info: Optional[str] = None
    
    # External Integration
    external_id: Optional[str] = Field(None, max_length=100)
    external_url: Optional[str] = Field(None, max_length=500)


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Product Schemas

class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: int = Field(..., ge=0)  # In paise/cents
    cost: int = Field(0, ge=0)
    category_id: str
    stock: int = Field(0, ge=0)
    min_stock: int = Field(5, ge=0)
    available: bool = True
    featured: bool = False
    image: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    department: str = 'kitchen'
    printer_tag: Optional[str] = None
    preparation_time: int = Field(15, ge=0)
    nutritional_info: Optional[dict] = None


class ProductCreate(ProductBase):
    """Schema for creating product"""
    restaurant_id: str


class ProductUpdate(BaseModel):
    """Schema for updating product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    cost: Optional[int] = Field(None, ge=0)
    category_id: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    available: Optional[bool] = None
    featured: Optional[bool] = None
    image: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    department: Optional[str] = None
    printer_tag: Optional[str] = None
    preparation_time: Optional[int] = Field(None, ge=0)
    nutritional_info: Optional[dict] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Modifier Schemas

class ModifierOptionBase(BaseModel):
    """Base modifier option schema"""
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(0, ge=0)
    available: bool = True
    sort_order: int = 0


class ModifierOptionCreate(ModifierOptionBase):
    """Schema for creating modifier option"""
    restaurant_id: str
    modifier_id: str


class ModifierOptionUpdate(BaseModel):
    """Schema for updating modifier option"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[int] = Field(None, ge=0)
    available: Optional[bool] = None
    sort_order: Optional[int] = None


class ModifierOptionResponse(ModifierOptionBase):
    """Schema for modifier option response"""
    id: str
    restaurant_id: str
    modifier_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModifierBase(BaseModel):
    """Base modifier schema"""
    name: str = Field(..., min_length=1, max_length=100)
    type: ModifierType = ModifierType.SINGLE
    category: str = 'add-ons'
    required: bool = False
    min_selections: int = Field(0, ge=0)
    max_selections: Optional[int] = Field(None, ge=0)


class ModifierCreate(ModifierBase):
    """Schema for creating modifier"""
    restaurant_id: str


class ModifierUpdate(BaseModel):
    """Schema for updating modifier"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[ModifierType] = None
    category: Optional[str] = None
    required: Optional[bool] = None
    min_selections: Optional[int] = Field(None, ge=0)
    max_selections: Optional[int] = Field(None, ge=0)


class ModifierResponse(ModifierBase):
    """Schema for modifier response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Combo Product Schemas

class ComboItemBase(BaseModel):
    """Base combo item schema"""
    product_id: str
    quantity: int = Field(1, ge=1)
    required: bool = True
    choice_group: Optional[str] = None
    choices: Optional[List[str]] = None
    sort_order: int = 0


class ComboItemCreate(ComboItemBase):
    """Schema for creating combo item"""
    restaurant_id: str
    combo_id: str


class ComboItemResponse(ComboItemBase):
    """Schema for combo item response"""
    id: str
    restaurant_id: str
    combo_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ComboProductBase(BaseModel):
    """Base combo product schema"""
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: int = Field(..., ge=0)
    category_id: str
    image: Optional[str] = None
    available: bool = True
    featured: bool = False
    tags: Optional[List[str]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_quantity_per_order: int = Field(10, ge=1)


class ComboProductCreate(ComboProductBase):
    """Schema for creating combo product"""
    restaurant_id: str


class ComboProductUpdate(BaseModel):
    """Schema for updating combo product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    category_id: Optional[str] = None
    image: Optional[str] = None
    available: Optional[bool] = None
    featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_quantity_per_order: Optional[int] = Field(None, ge=1)


class ComboProductResponse(ComboProductBase):
    """Schema for combo product response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Inventory Transaction Schemas

class InventoryTransactionBase(BaseModel):
    """Base inventory transaction schema"""
    product_id: str
    type: str  # purchase, sale, adjustment, waste
    quantity: int
    unit_cost: Optional[int] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None


class InventoryTransactionCreate(InventoryTransactionBase):
    """Schema for creating inventory transaction"""
    restaurant_id: str
    performed_by: Optional[str] = None


class InventoryTransactionResponse(InventoryTransactionBase):
    """Schema for inventory transaction response"""
    id: str
    restaurant_id: str
    previous_stock: int
    new_stock: int
    total_cost: Optional[int]
    performed_by: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Stock Adjustment Schema

class StockAdjustment(BaseModel):
    """Schema for stock adjustment"""
    product_id: str
    quantity: int  # Can be positive or negative
    type: str = 'adjustment'  # adjustment, waste, damage, return
    notes: Optional[str] = None


# Translation Schemas

class TranslationBase(BaseModel):
    """Base translation schema"""
    language_code: str = Field(..., min_length=2, max_length=5)
    name: str = Field(..., min_length=1, max_length=255)


class CategoryTranslationCreate(TranslationBase):
    """Schema for creating category translation"""
    category_id: str
    description: Optional[str] = Field(None, max_length=500)


class ProductTranslationCreate(TranslationBase):
    """Schema for creating product translation"""
    product_id: str
    description: Optional[str] = Field(None, max_length=1000)


class ModifierTranslationCreate(TranslationBase):
    """Schema for creating modifier translation"""
    modifier_id: str


class ModifierOptionTranslationCreate(TranslationBase):
    """Schema for creating modifier option translation"""
    modifier_option_id: str


class ComboProductTranslationCreate(TranslationBase):
    """Schema for creating combo product translation"""
    combo_product_id: str
    description: Optional[str] = Field(None, max_length=1000)


class TranslationResponse(TranslationBase):
    """Schema for translation response"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
