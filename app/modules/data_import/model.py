from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
import enum
from app.core.database import Base


class ImportType(str, enum.Enum):
    """Import type enumeration"""
    CATEGORY = "category"
    PRODUCT = "product"
    CATEGORY_PRODUCT = "category_product"
    CUSTOMER = "customer"
    STAFF = "staff"


class ImportStatus(str, enum.Enum):
    """Import status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ImportFileFormat(str, enum.Enum):
    """Import file format enumeration"""
    CSV = "csv"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"


class DataImport(Base):
    """Data import model - Track import operations"""
    
    __tablename__ = "data_imports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Import identification
    import_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    import_name: Mapped[str] = mapped_column(String(255), nullable=False)
    import_type: Mapped[str] = mapped_column(
        SQLEnum(ImportType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    
    # File information
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(
        SQLEnum(ImportFileFormat, native_enum=False, length=10),
        nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ImportStatus, native_enum=False, length=20),
        default=ImportStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Processing information
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    
    # Import statistics
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Duplicate handling
    duplicates_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Validation
    validation_errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_warnings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Import results
    import_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_warnings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skipped_rows: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    failed_rows: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Import settings
    update_existing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_duplicates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validate_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Mapping configuration
    column_mapping: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    import_options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # User tracking
    imported_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    import_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
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
        return f"<DataImport(id={self.id}, import_number={self.import_number}, type={self.import_type}, status={self.status})>"


class ImportLog(Base):
    """Import log model - Detailed row-level import logs"""
    
    __tablename__ = "import_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_import_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Row information
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    row_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # success, failed, skipped, updated
    action_taken: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # created, updated, skipped
    
    # Result
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # ID of created/updated entity
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Duplicate detection
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duplicate_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    existing_entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Validation
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_warnings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Processing info
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    log_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ImportLog(id={self.id}, row_number={self.row_number}, status={self.status})>"


class ImportTemplate(Base):
    """Import template model - Predefined import templates"""
    
    __tablename__ = "import_templates"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template information
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    import_type: Mapped[str] = mapped_column(
        SQLEnum(ImportType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    
    # File format
    file_format: Mapped[str] = mapped_column(
        SQLEnum(ImportFileFormat, native_enum=False, length=10),
        nullable=False
    )
    
    # Template structure
    required_columns: Mapped[dict] = mapped_column(JSON, nullable=False)
    optional_columns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    column_mapping: Mapped[dict] = mapped_column(JSON, nullable=False)
    sample_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Validation rules
    validation_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
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
        return f"<ImportTemplate(id={self.id}, name={self.template_name}, type={self.import_type})>"
