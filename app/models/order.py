"""
Order related models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
import uuid

from app.database import Base
from app.enums import OrderType, OrderStatus, PaymentStatus, OrderPriority, KOTStatus


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_number = Column(String(20), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"))
    customer_name = Column(String(100), default='Guest')
    customer_phone = Column(String(20))
    customer_email = Column(String(255))
    table_number = Column(String(20))
    table_id = Column(String(36), ForeignKey("qr_tables.id", ondelete="SET NULL"))
    session_id = Column(String(36), ForeignKey("qr_sessions.id", ondelete="SET NULL"))
    order_type = Column(SQLEnum(OrderType), nullable=False, default=OrderType.DINE_IN, index=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.CONFIRMED, index=True)
    payment_status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    payment_method = Column(String(50))
    transaction_id = Column(String(100))
    subtotal = Column(Integer, nullable=False, default=0)  # Stored in cents
    tax_total = Column(Integer, nullable=False, default=0)  # Stored in cents
    service_charge = Column(Integer, nullable=False, default=0)  # Stored in cents
    discount = Column(Integer, nullable=False, default=0)  # Stored in cents
    discount_code = Column(String(50))
    loyalty_points_redeemed = Column(Integer, nullable=False, default=0)
    loyalty_points_earned = Column(Integer, nullable=False, default=0)
    tip = Column(Integer, nullable=False, default=0)  # Stored in cents
    total = Column(Integer, nullable=False, default=0)  # Stored in cents
    estimated_time = Column(Integer, nullable=False, default=15)
    priority = Column(SQLEnum(OrderPriority), nullable=False, default=OrderPriority.NORMAL)
    notes = Column(Text)
    delivery_address = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    accepted_at = Column(DateTime(timezone=True))
    preparing_at = Column(DateTime(timezone=True))
    ready_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    table = relationship("QRTable")
    session = relationship("QRSession", back_populates="orders")
    created_by_user = relationship("User", back_populates="created_orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tax_breakdown = relationship("OrderTax", back_populates="order", cascade="all, delete-orphan")
    kot_groups = relationship("KOTGroup", back_populates="order", cascade="all, delete-orphan")
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="order")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.order_number}', status='{self.status}', restaurant_id={self.restaurant_id})>"


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    combo_id = Column(String(36), ForeignKey("combo_products.id", ondelete="RESTRICT"))
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Integer, nullable=False)  # Stored in cents
    total_price = Column(Integer, nullable=False)  # Stored in cents
    special_instructions = Column(Text)
    department = Column(String(50), nullable=False, default='kitchen', index=True)
    printer_tag = Column(String(50))
    kot_status = Column(SQLEnum(KOTStatus), nullable=False, default=KOTStatus.PENDING, index=True)
    kot_printed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    combo = relationship("ComboProduct")
    modifiers = relationship("OrderItemModifier", back_populates="order_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product='{self.product_name}', qty={self.quantity})>"


class OrderItemModifier(Base):
    __tablename__ = "order_item_modifiers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    modifier_id = Column(String(36), ForeignKey("modifiers.id", ondelete="RESTRICT"), nullable=False)
    modifier_name = Column(String(100), nullable=False)
    option_id = Column(String(36), ForeignKey("modifier_options.id", ondelete="RESTRICT"))
    option_name = Column(String(100))
    price = Column(Integer, nullable=False, default=0)  # Stored in cents
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    order_item = relationship("OrderItem", back_populates="modifiers")
    modifier = relationship("Modifier")
    option = relationship("ModifierOption")
    
    def __repr__(self):
        return f"<OrderItemModifier(id={self.id}, modifier='{self.modifier_name}')>"


class KOTGroup(Base):
    __tablename__ = "kot_groups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(50), nullable=False, index=True)
    status = Column(SQLEnum(KOTStatus), nullable=False, default=KOTStatus.PENDING, index=True)
    item_count = Column(Integer, nullable=False, default=0)
    printed_at = Column(DateTime(timezone=True))
    print_count = Column(Integer, nullable=False, default=0)
    acknowledged_at = Column(DateTime(timezone=True))
    preparing_at = Column(DateTime(timezone=True))
    ready_at = Column(DateTime(timezone=True))
    served_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="kot_groups")
    
    def __repr__(self):
        return f"<KOTGroup(id={self.id}, department='{self.department}', status='{self.status}')>"


class OrderTax(Base):
    __tablename__ = "order_taxes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_rule_id = Column(String(36), ForeignKey("tax_rules.id", ondelete="RESTRICT"), nullable=False)
    tax_name = Column(String(100), nullable=False)
    tax_type = Column(String(50), nullable=False)
    percentage = Column(Integer, nullable=False)  # Stored as percentage * 100
    base_amount = Column(Integer, nullable=False)  # Stored in cents
    tax_amount = Column(Integer, nullable=False)  # Stored in cents
    is_compounded = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="tax_breakdown")
    tax_rule = relationship("TaxRule")
    
    def __repr__(self):
        return f"<OrderTax(id={self.id}, tax='{self.tax_name}', amount={self.tax_amount})>"


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    notes = Column(Text)
    changed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    order = relationship("Order", back_populates="status_history")
    changed_by_user = relationship("User")
    
    def __repr__(self):
        return f"<OrderStatusHistory(id={self.id}, order_id={self.order_id}, status='{self.status}')>"
