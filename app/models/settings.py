"""
Settings and Tax related models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
import uuid

from app.database import Base
from app.enums import TaxApplicableOn


class TaxRule(Base):
    __tablename__ = "tax_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    percentage = Column(Integer, nullable=False)  # Stored as percentage * 100
    applicable_on = Column(SQLEnum(TaxApplicableOn), nullable=False, default=TaxApplicableOn.ALL, index=True)
    categories = Column(JSON)
    min_amount = Column(Integer)  # Stored in cents
    max_amount = Column(Integer)  # Stored in cents
    is_compounded = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=0, index=True)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TaxRule(id={self.id}, name='{self.name}', percentage={self.percentage})>"


class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_name = Column(String(200), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    logo = Column(String(500))
    currency = Column(String(3), nullable=False, default='USD')
    timezone = Column(String(50), nullable=False, default='UTC')
    language = Column(String(5), nullable=False, default='en')
    tax_rate = Column(Integer, nullable=False, default=0)  # Stored as percentage * 100
    service_charge = Column(Integer, nullable=False, default=0)  # Stored as percentage * 100
    enable_tipping = Column(Boolean, nullable=False, default=True)
    default_tip_percentages = Column(JSON, nullable=False, default=list)
    print_kot_automatically = Column(Boolean, nullable=False, default=True)
    auto_print_receipt = Column(Boolean, nullable=False, default=False)
    email_notifications = Column(Boolean, nullable=False, default=True)
    sms_notifications = Column(Boolean, nullable=False, default=False)
    low_stock_alerts = Column(Boolean, nullable=False, default=True)
    business_hours = Column(JSON)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Settings(id={self.id}, restaurant='{self.restaurant_name}')>"
