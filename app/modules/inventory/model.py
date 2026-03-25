from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
import enum
from app.core.database import Base


class UnitOfMeasure(str, enum.Enum):
    """Unit of measurement enumeration"""
    KILOGRAM = "kg"
    GRAM = "g"
    LITER = "l"
    MILLILITER = "ml"
    PIECE = "pc"
    DOZEN = "dozen"
    BOTTLE = "bottle"
    CAN = "can"
    BAG = "bag"
    BOX = "box"
    PACKET = "packet"
    POUND = "lb"
    OUNCE = "oz"
    CUP = "cup"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"


class StockTransactionType(str, enum.Enum):
    """Stock transaction type enumeration"""
    PURCHASE = "purchase"           # Stock purchased from supplier
    SALE = "sale"                   # Auto deduction on sale
    ADJUSTMENT = "adjustment"       # Manual adjustment
    WASTAGE = "wastage"            # Wastage entry
    DAMAGE = "damage"              # Damage entry
    RETURN_TO_SUPPLIER = "return_to_supplier"
    TRANSFER_IN = "transfer_in"    # Transfer from another location
    TRANSFER_OUT = "transfer_out"  # Transfer to another location
    INITIAL = "initial"            # Initial stock entry


class SupplierStatus(str, enum.Enum):
    """Supplier status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class Ingredient(Base):
    """Ingredient/Raw Material Master"""
    
    __tablename__ = "ingredients"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # Stock Keeping Unit
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Category and Classification
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of tags
    
    # Unit of Measurement
    unit_of_measure: Mapped[str] = mapped_column(
        SQLEnum(UnitOfMeasure, native_enum=False, length=20),
        nullable=False
    )
    
    # Stock Information
    current_stock: Mapped[float] = mapped_column(Numeric(15, 3), default=0.0, nullable=False, index=True)
    minimum_stock: Mapped[float] = mapped_column(Numeric(15, 3), default=0.0, nullable=False)  # Low stock alert threshold
    maximum_stock: Mapped[Optional[float]] = mapped_column(Numeric(15, 3), nullable=True)
    reorder_level: Mapped[float] = mapped_column(Numeric(15, 3), default=0.0, nullable=False)  # Trigger purchase when reached
    reorder_quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 3), nullable=True)  # Suggested order quantity
    
    # Pricing (in paise/cents)
    cost_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Per unit
    average_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Weighted average
    last_purchase_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Storage Information
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Supplier Information
    primary_supplier_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Tracking
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    track_batch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Track by batch/lot
    track_expiry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Track expiry dates
    
    # Low Stock Alert
    low_stock_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    low_stock_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Ingredient(id={self.id}, name={self.name}, current_stock={self.current_stock}, unit={self.unit_of_measure})>"


class Recipe(Base):
    """Recipe Mapping - Links menu items to ingredients"""
    
    __tablename__ = "recipes"
    
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
    
    # Recipe Information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    
    # Yield Information
    yield_quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0, nullable=False)  # How many servings
    yield_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Costing
    total_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # In paise/cents
    cost_per_serving: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Preparation
    prep_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, name={self.name}, product_id={self.product_id})>"


class RecipeIngredient(Base):
    """Recipe Ingredients - Links recipes to ingredients with quantities"""
    
    __tablename__ = "recipe_ingredients"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipe_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Quantity Information
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)  # Quantity required
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # Unit (should match ingredient's unit)
    
    # Costing
    cost_per_unit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # At time of recipe creation
    total_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # quantity * cost_per_unit
    
    # Optional fields
    preparation_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<RecipeIngredient(recipe_id={self.recipe_id}, ingredient_id={self.ingredient_id}, quantity={self.quantity})>"


class StockTransaction(Base):
    """Stock In/Out tracking with auto deduction"""
    
    __tablename__ = "stock_transactions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Transaction Information
    transaction_type: Mapped[str] = mapped_column(
        SQLEnum(StockTransactionType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    transaction_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Quantity
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)  # Positive for IN, can be negative
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Before/After Stock
    stock_before: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    stock_after: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    
    # Costing
    unit_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Cost per unit (paise/cents)
    total_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # quantity * unit_cost
    
    # Reference Information
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # order_id, po_id, etc.
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Supplier (for purchase transactions)
    supplier_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Batch/Lot tracking
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Wastage/Damage specific
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Approval tracking
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<StockTransaction(id={self.id}, type={self.transaction_type}, ingredient_id={self.ingredient_id}, quantity={self.quantity})>"


class Supplier(Base):
    """Supplier Master for purchase management"""
    
    __tablename__ = "suppliers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Contact Information
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    
    # Business Information
    gstin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Tax ID
    pan: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Payment Terms
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Net days
    credit_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In paise/cents
    current_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Outstanding amount
    
    # Categories
    supply_categories: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of categories
    
    # Rating and Performance
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)  # 0-5 rating
    total_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_purchase_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(SupplierStatus, native_enum=False, length=20),
        default=SupplierStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Bank Details
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name={self.name}, status={self.status})>"


class PurchaseOrder(Base):
    """Purchase Order management"""
    
    __tablename__ = "purchase_orders"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Order Information
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    po_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(PurchaseOrderStatus, native_enum=False, length=30),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Financial
    subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shipping_charges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    other_charges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Delivery Information
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Terms and Conditions
    payment_terms: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    terms_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Approval
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, status={self.status}, total={self.total_amount})>"


class PurchaseOrderItem(Base):
    """Purchase Order Items"""
    
    __tablename__ = "purchase_order_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Order Details
    quantity_ordered: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Numeric(15, 3), default=0.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Pricing
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    tax_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Receiving
    is_fully_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderItem(po_id={self.purchase_order_id}, ingredient_id={self.ingredient_id}, qty={self.quantity_ordered})>"


class LowStockAlert(Base):
    """Low Stock Alert tracking"""
    
    __tablename__ = "low_stock_alerts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Alert Information
    current_stock: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    minimum_stock: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    reorder_level: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Status
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Action Taken
    action_taken: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    purchase_order_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<LowStockAlert(id={self.id}, ingredient_id={self.ingredient_id}, current={self.current_stock}, min={self.minimum_stock})>"
