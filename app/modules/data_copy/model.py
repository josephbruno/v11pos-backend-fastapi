from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
import enum
from app.core.database import Base


class CopyType(str, enum.Enum):
    """Copy type enumeration"""
    CATEGORY = "category"
    PRODUCT = "product"
    COMBO = "combo"
    MODIFIER = "modifier"
    CATEGORY_PRODUCTS = "category_products"
    FULL_MENU = "full_menu"


class CopyStatus(str, enum.Enum):
    """Copy status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DataCopy(Base):
    """Data copy model - Track copy operations between restaurants"""
    
    __tablename__ = "data_copies"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Source and destination restaurants
    source_restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    destination_restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Copy identification
    copy_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    copy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    copy_type: Mapped[str] = mapped_column(
        SQLEnum(CopyType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(CopyStatus, native_enum=False, length=20),
        default=CopyStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Processing information
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    
    # Copy statistics
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_copied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Entity breakdown
    categories_copied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    categories_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    products_copied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    products_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    combos_copied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    combos_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    modifiers_copied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    modifiers_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Duplicate handling
    duplicates_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Copy options
    skip_duplicates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_images: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_prices: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintain_relationships: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Source entity IDs (for specific item copy)
    source_entity_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Entity mapping (source ID -> destination ID)
    entity_mapping: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Copy results
    copy_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skipped_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    failed_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # User tracking
    copied_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    copy_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<DataCopy(id={self.id}, copy_number={self.copy_number}, type={self.copy_type}, status={self.status})>"


class CopyLog(Base):
    """Copy log model - Detailed item-level copy logs"""
    
    __tablename__ = "copy_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_copy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_copies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Source entity
    source_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_entity_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Destination entity
    destination_entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    destination_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # success, failed, skipped
    action_taken: Mapped[str] = mapped_column(String(20), nullable=False)  # copied, skipped, failed
    
    # Duplicate detection
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duplicate_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    existing_entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Processing info
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    log_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<CopyLog(id={self.id}, entity={self.source_entity_name}, status={self.status})>"


class CopyTemplate(Base):
    """Copy template model - Predefined copy configurations"""
    
    __tablename__ = "copy_templates"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template information
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    copy_type: Mapped[str] = mapped_column(
        SQLEnum(CopyType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    
    # Copy settings
    skip_duplicates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_images: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_prices: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintain_relationships: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Filters
    include_inactive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    include_unavailable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Template settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # User tracking
    created_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Metadata
    template_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<CopyTemplate(id={self.id}, name={self.template_name}, type={self.copy_type})>"
