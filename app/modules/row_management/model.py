"""
Row management models
"""
from datetime import datetime
from typing import Optional
import enum
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RowType(str, enum.Enum):
    CATEGORY = "category"
    PRODUCT = "product"
    COMBO_PRODUCT = "combo_product"
    SINGLE_BANNER = "single_banner"
    ADS_BANNER = "ads_banner"
    ADS_VIDEO = "ads_video"


class RowManagement(Base):
    """Homepage row management entity"""
    __tablename__ = "row_managements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    subtitle: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    row_type: Mapped[RowType] = mapped_column(SQLEnum(RowType), nullable=False, index=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    show_title: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    layout_style: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    items_per_view: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    auto_scroll: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    category_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    product_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    combo_product_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mobile_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    desktop_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    redirect_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    button_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    text_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<RowManagement(id={self.id}, name='{self.name}', type='{self.row_type}')>"
