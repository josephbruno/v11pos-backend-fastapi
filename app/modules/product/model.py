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
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Parent-Child Hierarchy (Subcategories)
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 = root, 1 = subcategory, etc.
    
    # Display & Ordering
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Media
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Icon/emoji for category
    banner_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Colors & Styling
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color code
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    text_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Display Settings
    display_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # grid, list, carousel
    items_per_row: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For grid display
    show_in_menu: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_in_homepage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_in_pos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Availability Settings
    available_for_delivery: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_for_takeaway: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_for_dine_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Time-based Availability
    available_from_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    available_to_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    available_days: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["monday", "tuesday", ...]
    
    # Tax Settings
    tax_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # SEO & Marketing
    seo_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Statistics & Analytics
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # In currency units
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Commission & Pricing
    commission_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)  # For marketplace
    min_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minimum product price
    max_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Maximum product price
    
    # Discounts & Promotions
    discount_applicable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_discount_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Attributes & Filters
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Custom attributes
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["vegetarian", "spicy", ...]
    dietary_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["vegan", "gluten-free", ...]
    
    # Kitchen & Operations
    kitchen_station: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # hot_kitchen, cold_station
    preparation_area: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avg_preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # minutes
    
    # Content & Notes
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ingredients_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergen_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # External Integration
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Third-party ID
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("app.modules.restaurant.model.Restaurant")
    
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
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True, unique=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compare_at_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Original price for discounts
    wholesale_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minimum selling price
    max_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Maximum selling price
    price_varies: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # For variants
    
    # Category & Organization
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    subcategory_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Inventory Management
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reorder_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reorder_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_backorder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # piece, kg, liter, etc.
    
    # Availability & Status
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_seasonal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Order Type Availability
    available_for_delivery: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_for_takeaway: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_for_dine_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_for_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Time-based Availability
    available_from_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    available_to_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    available_days: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    availability_schedule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Media & Display
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    images: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gallery: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Colors & Styling
    badge_text: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "New", "Hot", "Sale"
    badge_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    display_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Tags & Classification
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    collections: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    product_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # physical, digital, service
    
    # Kitchen & Operations
    department: Mapped[str] = mapped_column(String(50), default='kitchen', nullable=False, index=True)
    kitchen_station: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preparation_area: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    printer_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preparation_time: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    cooking_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Dietary & Allergen Information
    nutritional_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dietary_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["vegan", "gluten-free"]
    allergen_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # mild, medium, hot, extra-hot
    
    # Tax & Compliance
    tax_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tax_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # For GST India
    
    # Discounts & Promotions
    discount_applicable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    discount_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    discount_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discount_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    discount_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Ordering Rules
    min_order_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_order_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_increment: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Variants & Customization
    has_variants: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    variant_options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["size", "color"]
    requires_customization: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    customization_options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Weight & Dimensions
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)  # in grams
    weight_unit: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    length: Mapped[Optional[float]] = mapped_column(nullable=True)
    width: Mapped[Optional[float]] = mapped_column(nullable=True)
    height: Mapped[Optional[float]] = mapped_column(nullable=True)
    dimension_unit: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # SEO & Marketing
    seo_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Analytics & Performance
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_average: Mapped[Optional[float]] = mapped_column(nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Sorting & Display
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    display_priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Loyalty & Rewards
    loyalty_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reward_applicable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Commission & Marketplace
    commission_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    commission_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # percentage, fixed
    
    # Additional Attributes
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # External Integration
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    supplier_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Notes & Internal
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
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
