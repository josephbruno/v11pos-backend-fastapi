"""
Product catalog and inventory models
"""
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
import uuid
import enum

from app.core.database import Base


class ModifierType(str, enum.Enum):
    """Modifier type enum"""
    SINGLE = "single"
    MULTIPLE = "multiple"


class Category(Base):
    """Product category model"""
    __tablename__ = "categories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"


class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    images: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    department: Mapped[str] = mapped_column(String(50), default='kitchen', nullable=False, index=True)
    printer_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preparation_time: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    nutritional_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, restaurant_id={self.restaurant_id})>"


class Modifier(Base):
    """Modifier model for product customization"""
    __tablename__ = "modifiers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[ModifierType] = mapped_column(
        SQLEnum(ModifierType),
        default=ModifierType.SINGLE,
        nullable=False,
        index=True
    )
    category: Mapped[str] = mapped_column(String(50), default='add-ons', nullable=False, index=True)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_selections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_selections: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Modifier(id={self.id}, name='{self.name}', type='{self.type}', restaurant_id={self.restaurant_id})>"


class ModifierOption(Base):
    """Modifier option model"""
    __tablename__ = "modifier_options"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    modifier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modifiers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # In paise/cents
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ModifierOption(id={self.id}, name='{self.name}', price={self.price})>"


class ProductModifier(Base):
    """Product-Modifier relationship"""
    __tablename__ = "product_modifiers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    modifier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modifiers.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ProductModifier(product_id={self.product_id}, modifier_id={self.modifier_id})>"


class ComboProduct(Base):
    """Combo/Bundle product model"""
    __tablename__ = "combo_products"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    max_quantity_per_order: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ComboProduct(id={self.id}, name='{self.name}', price={self.price}, restaurant_id={self.restaurant_id})>"


class ComboItem(Base):
    """Items in a combo product"""
    __tablename__ = "combo_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    combo_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("combo_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    choice_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    choices: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ComboItem(combo_id={self.combo_id}, product_id={self.product_id}, qty={self.quantity})>"


class InventoryTransaction(Base):
    """Inventory transaction log"""
    __tablename__ = "inventory_transactions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # purchase, sale, adjustment, waste
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    new_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In paise/cents
    total_cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # Order ID, Purchase ID, etc.
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<InventoryTransaction(id={self.id}, product_id={self.product_id}, type='{self.type}', qty={self.quantity})>"


# Translation Models for Multi-Language Support

class CategoryTranslation(Base):
    """Category translation model"""
    __tablename__ = "category_translations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # en, ta, hi, fr
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<CategoryTranslation(category_id={self.category_id}, lang='{self.language_code}', name='{self.name}')>"


class ProductTranslation(Base):
    """Product translation model"""
    __tablename__ = "product_translations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # en, ta, hi, fr
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ProductTranslation(product_id={self.product_id}, lang='{self.language_code}', name='{self.name}')>"


class ModifierTranslation(Base):
    """Modifier translation model"""
    __tablename__ = "modifier_translations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    modifier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modifiers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # en, ta, hi, fr
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ModifierTranslation(modifier_id={self.modifier_id}, lang='{self.language_code}', name='{self.name}')>"


class ModifierOptionTranslation(Base):
    """Modifier option translation model"""
    __tablename__ = "modifier_option_translations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    modifier_option_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modifier_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # en, ta, hi, fr
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ModifierOptionTranslation(option_id={self.modifier_option_id}, lang='{self.language_code}', name='{self.name}')>"


class ComboProductTranslation(Base):
    """Combo product translation model"""
    __tablename__ = "combo_product_translations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    combo_product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("combo_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # en, ta, hi, fr
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ComboProductTranslation(combo_id={self.combo_product_id}, lang='{self.language_code}', name='{self.name}')>"
