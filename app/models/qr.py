"""
QR ordering related models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
import uuid

from app.database import Base
from app.enums import QRSessionStatus


class QRTable(Base):
    __tablename__ = "qr_tables"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    table_number = Column(String(20), nullable=False, index=True)
    table_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False, default='Main Floor')
    capacity = Column(Integer, nullable=False, default=4)
    qr_token = Column(String(100), nullable=False, index=True)
    qr_code_url = Column(String(500), nullable=False)
    qr_code_image = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_occupied = Column(Boolean, nullable=False, default=False, index=True)
    current_session_id = Column(String(36), ForeignKey("qr_sessions.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="qr_tables")
    sessions = relationship("QRSession", back_populates="table", foreign_keys="[QRSession.table_id]")
    
    def __repr__(self):
        return f"<QRTable(id={self.id}, number='{self.table_number}', occupied={self.is_occupied}, restaurant_id={self.restaurant_id})>"


class QRSession(Base):
    __tablename__ = "qr_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    table_id = Column(String(36), ForeignKey("qr_tables.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"))
    customer_name = Column(String(100), default='Guest')
    customer_phone = Column(String(20))
    guest_count = Column(Integer, nullable=False, default=1)
    device_fingerprint = Column(String(255))
    status = Column(SQLEnum(QRSessionStatus), nullable=False, default=QRSessionStatus.ACTIVE, index=True)
    cart_items = Column(Integer, nullable=False, default=0)
    cart_total = Column(Integer, nullable=False, default=0)  # Stored in cents
    orders_placed = Column(Integer, nullable=False, default=0)
    total_spent = Column(Integer, nullable=False, default=0)  # Stored in cents
    start_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    end_time = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    table = relationship("QRTable", back_populates="sessions", foreign_keys=[table_id])
    customer = relationship("Customer", back_populates="qr_sessions")
    orders = relationship("Order", back_populates="session")
    
    def __repr__(self):
        return f"<QRSession(id={self.id}, table_id={self.table_id}, status='{self.status}', restaurant_id={self.restaurant_id})>"


class QRSettings(Base):
    __tablename__ = "qr_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    restaurant_name = Column(String(200), nullable=False)
    logo = Column(String(500))
    primary_color = Column(String(7), nullable=False, default='#00A19D')
    accent_color = Column(String(7), nullable=False, default='#FF6D00')
    enable_online_ordering = Column(Boolean, nullable=False, default=True)
    enable_payment_at_table = Column(Boolean, nullable=False, default=True)
    enable_online_payment = Column(Boolean, nullable=False, default=False)
    service_charge_percentage = Column(Integer, nullable=False, default=1000)  # Stored as percentage * 100
    auto_confirm_orders = Column(Boolean, nullable=False, default=False)
    order_timeout_minutes = Column(Integer, nullable=False, default=30)
    max_orders_per_session = Column(Integer, nullable=False, default=10)
    enable_customer_info = Column(Boolean, nullable=False, default=False)
    enable_special_instructions = Column(Boolean, nullable=False, default=True)
    enable_order_tracking = Column(Boolean, nullable=False, default=True)
    welcome_message = Column(Text)
    terms_and_conditions = Column(Text)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    contact_address = Column(Text)
    business_hours = Column(JSON)
    payment_gateways = Column(JSON, nullable=False, default=list)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<QRSettings(id={self.id}, restaurant='{self.restaurant_name}', restaurant_id={self.restaurant_id})>"
