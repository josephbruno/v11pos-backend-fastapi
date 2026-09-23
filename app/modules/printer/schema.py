"""
Receipt printer configuration schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.printer.model import PrinterPurpose


class ReceiptPrinterBase(BaseModel):
    """Base receipt printer schema"""
    purpose: PrinterPurpose = PrinterPurpose.BILL
    printer_name: str = Field(..., min_length=1, max_length=100)
    printer_url: str = Field(..., min_length=1, max_length=500)
    printer_token: str = Field(..., min_length=1, max_length=255)
    printer_type: str = Field(default="ZEBRA", max_length=20)
    data_format: str = Field(default="text", max_length=10)
    paper_size: str = Field(default="80mm", max_length=10)
    auto_print: bool = False
    print_copies: int = Field(default=1, ge=1, le=10)
    logo_on_receipt: bool = True
    is_active: bool = True


class ReceiptPrinterCreate(ReceiptPrinterBase):
    """Schema for creating/upserting a receipt printer"""
    restaurant_id: str


class ReceiptPrinterUpdate(BaseModel):
    """Schema for updating a receipt printer"""
    printer_name: Optional[str] = Field(None, min_length=1, max_length=100)
    printer_url: Optional[str] = Field(None, min_length=1, max_length=500)
    printer_token: Optional[str] = Field(None, min_length=1, max_length=255)
    printer_type: Optional[str] = Field(None, max_length=20)
    data_format: Optional[str] = Field(None, max_length=10)
    paper_size: Optional[str] = Field(None, max_length=10)
    auto_print: Optional[bool] = None
    print_copies: Optional[int] = Field(None, ge=1, le=10)
    logo_on_receipt: Optional[bool] = None
    is_active: Optional[bool] = None


class ReceiptPrinterResponse(BaseModel):
    """Masked schema for listing/admin display - never exposes the raw token"""
    id: str
    restaurant_id: str
    purpose: PrinterPurpose
    printer_name: str
    printer_url: str
    has_token: bool
    printer_type: str
    data_format: str
    paper_size: str
    auto_print: bool
    print_copies: int
    logo_on_receipt: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, printer) -> "ReceiptPrinterResponse":
        return cls(
            id=printer.id,
            restaurant_id=printer.restaurant_id,
            purpose=printer.purpose,
            printer_name=printer.printer_name,
            printer_url=printer.printer_url,
            has_token=bool(printer.printer_token),
            printer_type=printer.printer_type,
            data_format=printer.data_format,
            paper_size=printer.paper_size,
            auto_print=printer.auto_print,
            print_copies=printer.print_copies,
            logo_on_receipt=printer.logo_on_receipt,
            is_active=printer.is_active,
            created_at=printer.created_at,
            updated_at=printer.updated_at,
        )


class ReceiptPrinterActiveResponse(ReceiptPrinterBase):
    """Unmasked schema returned only when the frontend needs to call the bridge directly"""
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
