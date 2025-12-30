from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
import uuid
import enum
from app.core.database import Base


class TableStatus(str, enum.Enum):
    """Table status enumeration"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class Table(Base):
    """Table database model - Linked to specific restaurant"""
    
    __tablename__ = "tables"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic information
    table_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    table_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    min_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Location and layout
    floor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For floor plan layout
    position_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For floor plan layout
    
    # Visual
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL to table/section image
    qr_code: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL to QR code for table
    
    # Status and availability
    status: Mapped[str] = mapped_column(
        SQLEnum(TableStatus, native_enum=False, length=20),
        default=TableStatus.AVAILABLE,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_bookable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Can be reserved online
    
    # Additional features
    is_outdoor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Wheelchair accessible
    has_power_outlet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Pricing (for special tables like VIP)
    minimum_spend: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minimum order amount
    
    # Notes and description
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Table(id={self.id}, restaurant_id={self.restaurant_id}, table_number={self.table_number}, capacity={self.capacity}, status={self.status})>"
