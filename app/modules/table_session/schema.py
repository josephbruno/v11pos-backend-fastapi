from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.table_session.model import TableSessionStatus, TableTransferStatus


class TableSessionCreate(BaseModel):
    table_uuid: str = Field(..., description="Table ID from QR code")
    restaurant_uuid: str
    customer_uuid: str


class TableSessionResponse(BaseModel):
    id: str
    table_uuid: str
    restaurant_uuid: str
    customer_uuid: str
    active_order_uuid: Optional[str] = None
    status: str
    started_at: datetime
    closed_at: Optional[datetime] = None
    table_number: Optional[str] = None
    table_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TableTransferCreate(BaseModel):
    old_table_uuid: str
    new_table_uuid: str
    customer_uuid: str
    restaurant_uuid: str
    status: Optional[TableTransferStatus] = TableTransferStatus.PENDING_APPROVAL


class TableTransferResponse(BaseModel):
    id: str
    old_table_uuid: str
    new_table_uuid: str
    customer_uuid: str
    restaurant_uuid: str
    order_uuid: Optional[str] = None
    status: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    audit_log: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestBillPayload(BaseModel):
    table_uuid: str
    order_uuid: str
    customer_uuid: str
    restaurant_uuid: str


class BillItemSummary(BaseModel):
    id: str
    name: str
    quantity: int
    unit_price: int
    total_price: int


class BillSummaryResponse(BaseModel):
    order_uuid: str
    order_number: Optional[str] = None
    subtotal: int
    tax: int
    discount: int
    service_charge: int
    grand_total: int
    items: list[BillItemSummary]
    status: str


class TableValidateResponse(BaseModel):
    valid: bool
    table_uuid: str
    restaurant_uuid: str
    table_number: Optional[str] = None
    table_name: Optional[str] = None
    table_status: Optional[str] = None
    is_active: Optional[bool] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
