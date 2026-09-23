"""
Receipt printer configuration models

Stores per-restaurant printer registrations pointing at a local print-bridge
service (e.g. a machine near the till running printer-service). The frontend
reads this config and POSTs print jobs directly to `printer_url`, so the
backend never talks to the printer itself - it is only the config store.
"""
from datetime import datetime
from typing import Optional
import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utc_now_naive


class PrinterPurpose(str, enum.Enum):
    """What this printer is used for"""
    BILL = "bill"
    KOT = "kot"


class ReceiptPrinter(Base):
    """Local print-bridge registration for a restaurant"""
    __tablename__ = "receipt_printers"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "purpose", name="uq_receipt_printers_restaurant_purpose"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    purpose: Mapped[str] = mapped_column(
        SQLEnum(PrinterPurpose, native_enum=False, length=20),
        default=PrinterPurpose.BILL,
        nullable=False,
        index=True,
    )

    # OS/spooler queue name on the machine running the print-bridge
    printer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Local print-bridge base URL, e.g. http://127.0.0.1:9100
    printer_url: Mapped[str] = mapped_column(String(500), nullable=False)
    # Shared secret sent as the x-print-token header
    printer_token: Mapped[str] = mapped_column(String(255), nullable=False)
    # "printerType" value expected by the local print-bridge (e.g. ZEBRA, TSC,
    # ESCPOS) - the bridge is an existing external service, this must match
    # whatever it already accepts.
    printer_type: Mapped[str] = mapped_column(String(20), default="ZEBRA", nullable=False)
    # Which receipt content format to send as "data": text, html, or escpos
    data_format: Mapped[str] = mapped_column(String(10), default="text", nullable=False)

    paper_size: Mapped[str] = mapped_column(String(10), default="80mm", nullable=False)
    auto_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    print_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    logo_on_receipt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ReceiptPrinter(id={self.id}, restaurant_id={self.restaurant_id}, purpose={self.purpose}, printer_name='{self.printer_name}')>"
