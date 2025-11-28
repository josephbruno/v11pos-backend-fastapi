"""
Product schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    active: bool = True
    sort_order: int = 0
    image: Optional[str] = Field(None, max_length=500)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    active: Optional[bool] = None
    sort_order: Optional[int] = None
    image: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: int = Field(..., gt=0, description="Price in cents")
    cost: int = Field(default=0, ge=0, description="Cost in cents")
    category_id: uuid.UUID
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=5, ge=0)
    available: bool = True
    featured: bool = False
    image: Optional[str] = Field(None, max_length=500)
    images: List[str] = []
    tags: List[str] = []
    department: str = Field(default="kitchen", max_length=50)
    printer_tag: Optional[str] = Field(None, max_length=50)
    preparation_time: int = Field(default=15, ge=0)
    nutritional_info: Optional[dict] = None


class ProductCreate(ProductBase):
    slug: str = Field(..., min_length=1, max_length=200)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[int] = Field(None, gt=0)
    cost: Optional[int] = Field(None, ge=0)
    category_id: Optional[uuid.UUID] = None
    stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    available: Optional[bool] = None
    featured: Optional[bool] = None
    image: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    department: Optional[str] = None
    printer_tag: Optional[str] = None
    preparation_time: Optional[int] = None
    nutritional_info: Optional[dict] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    
    # Computed field for display price (cents to dollars)
    @property
    def price_display(self) -> float:
        return self.price / 100
    
    @property
    def cost_display(self) -> float:
        return self.cost / 100
    
    @property
    def margin_percentage(self) -> float:
        if self.price > 0:
            return ((self.price - self.cost) / self.price) * 100
        return 0
    
    class Config:
        from_attributes = True


class ModifierOptionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(default=0, ge=0, description="Price in cents")
    available: bool = True
    sort_order: int = 0


class ModifierOptionCreate(ModifierOptionBase):
    """Schema for creating modifier option - modifier_id comes from path parameter"""
    pass


class ModifierOptionResponse(ModifierOptionBase):
    id: uuid.UUID
    modifier_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModifierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="single or multiple")
    category: str = Field(default="add-ons", max_length=50)
    required: bool = False
    min_selections: int = Field(default=0, ge=0)
    max_selections: Optional[int] = Field(None, ge=0)


class ModifierCreate(ModifierBase):
    pass


class ModifierResponse(ModifierBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    options: List[ModifierOptionResponse] = []
    
    class Config:
        from_attributes = True


# Combo Product Schemas
class ComboItemBase(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)
    required: bool = True
    choice_group: Optional[str] = Field(None, max_length=50)
    choices: Optional[List[str]] = None
    sort_order: int = 0


class ComboItemCreate(ComboItemBase):
    pass


class ComboItemResponse(ComboItemBase):
    id: str
    combo_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ComboProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: int = Field(..., gt=0, description="Price in cents")
    category_id: str
    image: Optional[str] = Field(None, max_length=500)
    available: bool = True
    featured: bool = False
    tags: List[str] = []
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_quantity_per_order: int = Field(default=10, ge=1)


class ComboProductCreate(ComboProductBase):
    items: List[ComboItemCreate] = Field(..., min_length=1)


class ComboProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[int] = Field(None, gt=0)
    category_id: Optional[str] = None
    image: Optional[str] = None
    available: Optional[bool] = None
    featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_quantity_per_order: Optional[int] = Field(None, ge=1)


class ComboProductResponse(ComboProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    items: List[ComboItemResponse] = []
    
    @property
    def price_display(self) -> float:
        return self.price / 100
    
    class Config:
        from_attributes = True
