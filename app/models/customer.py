"""
Customer and Loyalty related models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
import uuid

from app.database import Base
from app.enums import LoyaltyOperation


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255))
    address = Column(Text)
    loyalty_points = Column(Integer, nullable=False, default=0)
    total_spent = Column(Integer, nullable=False, default=0)  # Stored in cents
    visit_count = Column(Integer, nullable=False, default=0)
    last_visit = Column(DateTime(timezone=True), index=True)
    notes = Column(Text)
    is_blacklisted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="customers")
    tag_mappings = relationship("CustomerTagMapping", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="customer", cascade="all, delete-orphan")
    qr_sessions = relationship("QRSession", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', phone='{self.phone}', restaurant_id={self.restaurant_id})>"


class CustomerTag(Base):
    __tablename__ = "customer_tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), nullable=False, default='#00A19D')
    benefits = Column(JSON, nullable=False, default=list)
    discount_percentage = Column(Integer, nullable=False, default=0)  # Stored as percentage * 100 (e.g., 10.50% = 1050)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer_mappings = relationship("CustomerTagMapping", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomerTag(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"


class CustomerTagMapping(Base):
    __tablename__ = "customer_tag_mapping"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(String(36), ForeignKey("customer_tags.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    customer = relationship("Customer", back_populates="tag_mappings")
    tag = relationship("CustomerTag", back_populates="customer_mappings")
    assigned_by_user = relationship("User", back_populates="assigned_customer_tags")
    
    def __repr__(self):
        return f"<CustomerTagMapping(customer_id={self.customer_id}, tag_id={self.tag_id})>"


class LoyaltyRule(Base):
    __tablename__ = "loyalty_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    earn_rate = Column(Integer, nullable=False, default=100)  # Stored as rate * 100 (e.g., 1.00 = 100)
    redeem_rate = Column(Integer, nullable=False, default=100)
    min_redeem_points = Column(Integer, nullable=False, default=100)
    max_redeem_percentage = Column(Integer, nullable=False, default=50)
    expiry_days = Column(Integer)
    active = Column(Boolean, nullable=False, default=True, index=True)
    priority = Column(Integer, nullable=False, default=0, index=True)
    applicable_tags = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<LoyaltyRule(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"


class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="SET NULL"))
    points = Column(Integer, nullable=False)
    operation = Column(SQLEnum(LoyaltyOperation), nullable=False, index=True)
    reason = Column(String(255))
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="loyalty_transactions")
    order = relationship("Order", back_populates="loyalty_transactions")
    created_by_user = relationship("User")
    
    def __repr__(self):
        return f"<LoyaltyTransaction(id={self.id}, customer_id={self.customer_id}, points={self.points})>"
