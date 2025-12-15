"""
Product catalog models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base
from app.enums import ModifierType


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    active = Column(Boolean, nullable=False, default=True, index=True)
    sort_order = Column(Integer, nullable=False, default=0, index=True)
    image = Column(String(500))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="categories")
    products = relationship("Product", back_populates="category")
    combos = relationship("ComboProduct", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"


class Product(Base):
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(Integer, nullable=False)  # Stored in cents
    cost = Column(Integer, nullable=False, default=0)  # Stored in cents
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    stock = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, nullable=False, default=5)
    available = Column(Boolean, nullable=False, default=True, index=True)
    featured = Column(Boolean, nullable=False, default=False, index=True)
    image = Column(String(500))
    images = Column(JSON, default=list)
    tags = Column(JSON, nullable=False, default=list)
    department = Column(String(50), nullable=False, default='kitchen', index=True)
    printer_tag = Column(String(50))
    preparation_time = Column(Integer, nullable=False, default=15)
    nutritional_info = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="products")
    category = relationship("Category", back_populates="products")
    product_modifiers = relationship("ProductModifier", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    combo_items = relationship("ComboItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, restaurant_id={self.restaurant_id})>"


class Modifier(Base):
    __tablename__ = "modifiers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(ModifierType), nullable=False, default=ModifierType.SINGLE, index=True)
    category = Column(String(50), nullable=False, default='add-ons', index=True)
    required = Column(Boolean, nullable=False, default=False)
    min_selections = Column(Integer, nullable=False, default=0)
    max_selections = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    options = relationship("ModifierOption", back_populates="modifier", cascade="all, delete-orphan")
    product_modifiers = relationship("ProductModifier", back_populates="modifier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Modifier(id={self.id}, name='{self.name}', type='{self.type}', restaurant_id={self.restaurant_id})>"


class ModifierOption(Base):
    __tablename__ = "modifier_options"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    modifier_id = Column(String(36), ForeignKey("modifiers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False, default=0)  # Stored in cents
    available = Column(Boolean, nullable=False, default=True, index=True)
    sort_order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    modifier = relationship("Modifier", back_populates="options")
    
    def __repr__(self):
        return f"<ModifierOption(id={self.id}, name='{self.name}', price={self.price})>"


class ProductModifier(Base):
    __tablename__ = "product_modifiers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    modifier_id = Column(String(36), ForeignKey("modifiers.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="product_modifiers")
    modifier = relationship("Modifier", back_populates="product_modifiers")
    
    __table_args__ = (
        {'schema': None},
    )
    
    def __repr__(self):
        return f"<ProductModifier(product_id={self.product_id}, modifier_id={self.modifier_id})>"


class ComboProduct(Base):
    __tablename__ = "combo_products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(Integer, nullable=False)  # Stored in cents
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    image = Column(String(500))
    available = Column(Boolean, nullable=False, default=True, index=True)
    featured = Column(Boolean, nullable=False, default=False, index=True)
    tags = Column(JSON, nullable=False, default=list)
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    max_quantity_per_order = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="combos")
    items = relationship("ComboItem", back_populates="combo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ComboProduct(id={self.id}, name='{self.name}', price={self.price}, restaurant_id={self.restaurant_id})>"


class ComboItem(Base):
    __tablename__ = "combo_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    combo_id = Column(String(36), ForeignKey("combo_products.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    required = Column(Boolean, nullable=False, default=True)
    choice_group = Column(String(50))
    choices = Column(JSON)
    sort_order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    combo = relationship("ComboProduct", back_populates="items")
    product = relationship("Product", back_populates="combo_items")
    
    def __repr__(self):
        return f"<ComboItem(combo_id={self.combo_id}, product_id={self.product_id}, qty={self.quantity})>"
