"""
User and Staff related models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base
from app.enums import UserRole, UserStatus, DayOfWeek


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for platform admins
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.STAFF, index=True)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE, index=True)
    avatar = Column(String(500))
    permissions = Column(JSON, nullable=False, default=list)
    join_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="users")
    shifts = relationship("ShiftSchedule", back_populates="user", cascade="all, delete-orphan")
    performance = relationship("StaffPerformance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    created_orders = relationship("Order", foreign_keys="[Order.created_by]", back_populates="created_by_user")
    assigned_customer_tags = relationship("CustomerTagMapping", foreign_keys="[CustomerTagMapping.assigned_by]", back_populates="assigned_by_user")
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}', restaurant_id={self.restaurant_id})>"


class ShiftSchedule(Base):
    __tablename__ = "shift_schedules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    day = Column(SQLEnum(DayOfWeek), nullable=False, index=True)
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)    # HH:MM format
    position = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="shifts")
    
    def __repr__(self):
        return f"<ShiftSchedule(user_id={self.user_id}, day='{self.day}', time='{self.start_time}-{self.end_time}')>"


class StaffPerformance(Base):
    __tablename__ = "staff_performance"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    orders_handled = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Integer, nullable=False, default=0)  # Stored in cents
    avg_order_value = Column(Integer, nullable=False, default=0)  # Stored in cents
    customer_rating = Column(Integer, nullable=False, default=0)  # Stored as rating * 100 (e.g., 4.50 = 450)
    punctuality_score = Column(Integer, nullable=False, default=100)
    last_calculated = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="performance")
    
    def __repr__(self):
        return f"<StaffPerformance(user_id={self.user_id}, orders={self.orders_handled})>"


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp = Column(String(6), nullable=False)  # 6-digit OTP
    is_used = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<PasswordResetToken(email={self.email}, is_used={self.is_used})>"
