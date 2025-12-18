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
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    active: bool = True
    sort_order: int = 0
    image: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating category"""
    restaurant_id: str


class CategoryUpdate(BaseModel):
    """Schema for updating category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    active: Optional[bool] = None
    sort_order: Optional[int] = None
    image: Optional[str] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime
    
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
