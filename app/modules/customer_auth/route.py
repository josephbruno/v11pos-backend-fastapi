import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.response import error_response, success_response
from app.modules.customer.service import CustomerService
from app.modules.customer.schema import (
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerAddressUpdate,
    CustomerResponse,
    CustomerSelfProfileUpdate,
    CustomerUpdate,
)
from app.modules.order.model import OrderStatus
from app.modules.order.schema import OrderItemResponse, OrderResponse
from app.modules.order.service import OrderService
from app.modules.customer_auth.schema import (
    CustomerAuthTokenResponse,
    CustomerEmailOTPRequest,
    CustomerEmailOTPRequestResponse,
    CustomerEmailOTPVerify,
    CustomerGoogleLoginRequest,
    CustomerPhonePeInitRequest,
    CustomerRefreshTokenRequest,
    CustomerTablePaymentRequest,
)
from app.modules.customer_auth.payments import (
    CustomerPaymentError,
    init_phonepe_payment,
    phonepe_payment_status,
    record_table_payment,
)
from app.modules.customer_auth.service import CustomerAuthError, CustomerAuthService, send_customer_email_otp
from app.core.dependencies import get_current_customer
from app.modules.customer.model import Customer
from app.modules.table_session.schema import (
    RequestBillPayload,
    TableSessionCreate,
    TableSessionResponse,
    TableTransferCreate,
    TableTransferResponse,
)
from app.modules.table.service import TableService
from app.modules.table_session.service import (
    TableSessionError,
    TableSessionService,
    TableTransferService,
)


router = APIRouter(prefix="/customer-auth", tags=["Customer Authentication"])
_log = logging.getLogger(__name__)


async def _request_customer_otp(
    payload: CustomerEmailOTPRequest,
    request: Request,
    db: AsyncSession,
):
    customer, otp, expires_in = await CustomerAuthService.request_email_otp(
        db,
        str(payload.email).lower(),
        payload.restaurant_id,
        ip_address=_client_ip(request),
    )
    email_sent = await send_customer_email_otp(
        db, str(payload.email).lower(), otp, payload.restaurant_id
    )
    _log.info(
        "customer-auth request-otp done email=%s email_sent=%s customer_id=%s",
        str(payload.email).lower(),
        email_sent,
        customer.id,
    )

    data = CustomerEmailOTPRequestResponse(
        otp_sent=True,
        email_sent=email_sent,
        expires_in_seconds=expires_in,
        customer_id=customer.id,
        development_otp=(otp if settings.is_development else None),
    ).model_dump()
    return success_response(message="OTP sent", data=data)


async def _verify_customer_otp(payload: CustomerEmailOTPVerify, db: AsyncSession):
    customer = await CustomerAuthService.verify_email_otp(
        db,
        str(payload.email).lower(),
        payload.restaurant_id,
        payload.otp,
    )
    customer_full = await CustomerService.get_customer_by_id(db, customer.id)
    customer_out = customer_full or customer
    tokens = CustomerAuthService.issue_tokens(customer_out)
    resp = CustomerAuthTokenResponse(
        customer=CustomerResponse.model_validate(customer_out),
        **tokens,
    )
    return success_response(
        message="OTP verified successfully",
        data=resp.model_dump(),
    )


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/send-otp", response_model=None)
async def send_otp(
    payload: CustomerEmailOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1 — Customer authentication: send a one-time code to the customer's email.

    Next call **POST /customer-auth/verify-otp** with the same email and the OTP.
    """
    try:
        return await _request_customer_otp(payload, request, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to send OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/verify-otp", response_model=None)
async def verify_otp(
    payload: CustomerEmailOTPVerify,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 — Customer authentication: verify the OTP.

    On success, **data** includes **customer** (full profile) and JWT **access_token** / **refresh_token**.
    """
    try:
        return await _verify_customer_otp(payload, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to verify OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/email/request-otp", response_model=None)
async def request_email_otp(
    payload: CustomerEmailOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Same as **POST /customer-auth/send-otp** (kept for backward compatibility)."""
    try:
        return await _request_customer_otp(payload, request, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to request OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/email/verify-otp", response_model=None)
async def verify_email_otp(
    payload: CustomerEmailOTPVerify,
    db: AsyncSession = Depends(get_db),
):
    """Same as **POST /customer-auth/verify-otp** (kept for backward compatibility)."""
    try:
        return await _verify_customer_otp(payload, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to verify OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/refresh", response_model=None)
async def refresh_customer_access_token(
    payload: CustomerRefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await CustomerAuthService.refresh_access_token(db, payload.refresh_token)
        return success_response(message="Token refreshed successfully", data=data)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Token refresh failed", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/google/login", response_model=None)
async def customer_google_login(
    payload: CustomerGoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Customer login using Google (client-provided email/name).

    On success, **data** includes **customer** (full profile) and JWT **access_token** / **refresh_token**.
    """
    try:
        customer = await CustomerAuthService.login_with_google(
            db,
            str(payload.email).lower(),
            payload.restaurant_id,
            provided_name=payload.name,
        )
        customer_full = await CustomerService.get_customer_by_id(db, customer.id)
        customer_out = customer_full or customer
        tokens = CustomerAuthService.issue_tokens(customer_out)
        resp = CustomerAuthTokenResponse(
            customer=CustomerResponse.model_validate(customer_out),
            **tokens,
        )
        return success_response(message="Login successful", data=resp.model_dump())
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(
            message="Google login failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/me", response_model=None)
async def get_current_customer_profile(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    customer_with_addresses = await CustomerService.get_customer_by_id(db, customer.id)
    return success_response(
        message="Customer profile retrieved successfully",
        data=CustomerResponse.model_validate(customer_with_addresses or customer).model_dump(),
    )


@router.patch("/me", response_model=None)
async def update_current_customer_profile(
    payload: CustomerSelfProfileUpdate,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """
    Update profile and legacy address fields on the customer record.
    Does not change **email** (used for OTP login). Use saved addresses under **/me/addresses** for multiple delivery addresses.
    """
    data = payload.model_dump(exclude_unset=True)
    if not data:
        refreshed = await CustomerService.get_customer_by_id(db, customer.id)
        return success_response(
            message="No changes applied",
            data=CustomerResponse.model_validate(refreshed or customer).model_dump(),
        )
    try:
        updated = await CustomerService.update_customer(
            db, customer.id, CustomerUpdate(**data)
        )
    except ValueError as e:
        return error_response(
            message=str(e),
            error_code="DUPLICATE_EMAIL",
            error_details=str(e),
            status_code=status.HTTP_409_CONFLICT,
        )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return success_response(
        message="Profile updated successfully",
        data=CustomerResponse.model_validate(updated).model_dump(),
    )


@router.get("/me/addresses", response_model=None)
async def list_my_addresses(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
    include_inactive: bool = Query(False, description="Include inactive addresses"),
):
    addresses = await CustomerService.list_customer_addresses(
        db, customer.id, include_inactive=include_inactive
    )
    return success_response(
        message="Addresses retrieved successfully",
        data=[CustomerAddressResponse.model_validate(a) for a in addresses],
    )


@router.post("/me/addresses", response_model=None, status_code=status.HTTP_201_CREATED)
async def add_my_address(
    payload: CustomerAddressCreate,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    address = await CustomerService.add_customer_address(db, customer.id, payload)
    return success_response(
        message="Address added successfully",
        data=CustomerAddressResponse.model_validate(address).model_dump(),
    )


@router.put("/me/addresses/{address_id}", response_model=None)
async def update_my_address(
    address_id: str,
    payload: CustomerAddressUpdate,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    address = await CustomerService.update_customer_address(db, customer.id, address_id, payload)
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return success_response(
        message="Address updated successfully",
        data=CustomerAddressResponse.model_validate(address).model_dump(),
    )


@router.delete("/me/addresses/{address_id}", response_model=None)
async def delete_my_address(
    address_id: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    ok = await CustomerService.delete_customer_address(db, customer.id, address_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return success_response(message="Address deleted successfully", data={"id": address_id})


@router.get("/me/orders", response_model=None)
async def list_my_orders(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    order_status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
):
    """
    Orders where **customer_id** matches the logged-in customer (same restaurant as the JWT).
    """
    orders, total = await OrderService.get_orders_for_customer(
        db,
        customer_id=customer.id,
        restaurant_id=customer.restaurant_id,
        skip=skip,
        limit=limit,
        status=order_status,
    )
    out: list[OrderResponse] = []
    for order in orders:
        or_resp = OrderResponse.model_validate(order)
        or_resp.items = [OrderItemResponse.model_validate(i) for i in (order.items or [])]
        out.append(or_resp)
    return success_response(
        message="Orders retrieved successfully",
        data={"orders": [o.model_dump() for o in out], "total": total, "skip": skip, "limit": limit},
    )


@router.get("/me/orders/{order_id}", response_model=None)
async def get_my_order(
    order_id: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    order = await OrderService.get_order_for_customer(
        db, order_id, customer.id, customer.restaurant_id
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order_response = OrderResponse.model_validate(order)
    order_response.items = [OrderItemResponse.model_validate(i) for i in (order.items or [])]
    return success_response(
        message="Order retrieved successfully",
        data=order_response.model_dump(),
    )


@router.post("/table-sessions", response_model=None)
async def create_table_session(
    payload: TableSessionCreate,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    if payload.customer_uuid != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer mismatch")
    if payload.restaurant_uuid != customer.restaurant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant mismatch")
    try:
        session, table = await TableSessionService.create_or_restore_session(db, payload)
        active_order = await TableSessionService.get_active_order_for_table(
            db, customer.id, customer.restaurant_id, session.table_id
        )
        if active_order and not session.active_order_id:
            session.active_order_id = active_order.id
            await db.commit()
            await db.refresh(session)
        resp = TableSessionResponse(
            id=session.id,
            table_uuid=session.table_id,
            restaurant_uuid=session.restaurant_id,
            customer_uuid=session.customer_id,
            active_order_uuid=session.active_order_id,
            status=session.status.upper(),
            started_at=session.started_at,
            closed_at=session.closed_at,
            table_number=table.table_number,
            table_name=table.table_name,
        )
        return success_response(message="Table session started", data={"session": resp.model_dump()})
    except TableSessionError as e:
        return error_response(message=e.message, error_code=e.code, status_code=e.status_code)


@router.get("/table-sessions/active", response_model=None)
async def get_active_table_session(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    session = await TableSessionService.get_active_session_for_customer(
        db, customer.id, customer.restaurant_id
    )
    if not session:
        return success_response(message="No active session", data={"session": None})
    table = await TableService.get_table_by_id(db, session.table_id)
    resp = TableSessionResponse(
        id=session.id,
        table_uuid=session.table_id,
        restaurant_uuid=session.restaurant_id,
        customer_uuid=session.customer_id,
        active_order_uuid=session.active_order_id,
        status=session.status.upper(),
        started_at=session.started_at,
        closed_at=session.closed_at,
        table_number=table.table_number if table else None,
        table_name=table.table_name if table else None,
    )
    return success_response(message="Active session retrieved", data={"session": resp.model_dump()})


@router.delete("/table-sessions/active", response_model=None)
async def close_active_table_session(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    session = await TableSessionService.get_active_session_for_customer(
        db, customer.id, customer.restaurant_id
    )
    if not session:
        return success_response(message="No active session", data={"closed": False})
    ok = await TableSessionService.close_session(db, session.id, customer.id, customer.restaurant_id)
    return success_response(message="Session closed", data={"closed": ok})


@router.post("/table-transfers", response_model=None)
async def request_table_transfer(
    payload: TableTransferCreate,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    if payload.customer_uuid != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer mismatch")
    if payload.restaurant_uuid != customer.restaurant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant mismatch")
    try:
        transfer = await TableTransferService.create_transfer(db, payload)
        resp = TableTransferResponse(
            id=transfer.id,
            old_table_uuid=transfer.old_table_id,
            new_table_uuid=transfer.new_table_id,
            customer_uuid=transfer.customer_id,
            restaurant_uuid=transfer.restaurant_id,
            order_uuid=transfer.order_id,
            status=transfer.status.upper(),
            resolved_by=transfer.resolved_by,
            resolved_at=transfer.resolved_at,
            audit_log=transfer.audit_log,
            created_at=transfer.created_at,
        )
        return success_response(message="Transfer requested", data={"transfer": resp.model_dump()})
    except TableSessionError as e:
        return error_response(message=e.message, error_code=e.code, status_code=e.status_code)


@router.get("/table-transfers/{transfer_id}", response_model=None)
async def get_table_transfer_status(
    transfer_id: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    transfer = await TableTransferService.get_transfer_by_id(db, transfer_id)
    if not transfer or transfer.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    resp = TableTransferResponse(
        id=transfer.id,
        old_table_uuid=transfer.old_table_id,
        new_table_uuid=transfer.new_table_id,
        customer_uuid=transfer.customer_id,
        restaurant_uuid=transfer.restaurant_id,
        order_uuid=transfer.order_id,
        status=transfer.status.upper(),
        resolved_by=transfer.resolved_by,
        resolved_at=transfer.resolved_at,
        audit_log=transfer.audit_log,
        created_at=transfer.created_at,
    )
    return success_response(message="Transfer retrieved", data={"transfer": resp.model_dump()})


@router.post("/orders/{order_id}/request-bill", response_model=None)
async def request_order_bill(
    order_id: str,
    payload: RequestBillPayload,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    if payload.customer_uuid != customer.id or payload.order_uuid != order_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Order mismatch")
    try:
        order = await TableSessionService.request_bill(
            db, order_id, customer.id, customer.restaurant_id, payload.table_uuid
        )
        bill = TableSessionService.build_bill_summary(order)
        return success_response(message="Bill requested", data={"bill": bill})
    except TableSessionError as e:
        return error_response(message=e.message, error_code=e.code, status_code=e.status_code)


@router.get("/orders/{order_id}/bill", response_model=None)
async def get_order_bill(
    order_id: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    order = await OrderService.get_order_for_customer(
        db, order_id, customer.id, customer.restaurant_id
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    bill = TableSessionService.build_bill_summary(order)
    return success_response(message="Bill summary retrieved", data={"bill": bill})


@router.post("/payments/phonepe/init", response_model=None)
async def customer_phonepe_init(
    payload: CustomerPhonePeInitRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await init_phonepe_payment(db, customer, payload.model_dump())
        return success_response(message="PhonePe payment initiated", data=data)
    except CustomerPaymentError as e:
        return error_response(message=e.message, error_code=e.code, status_code=e.status_code)


@router.get("/payments/phonepe/status/{merchant_transaction_id}", response_model=None)
async def customer_phonepe_status(
    merchant_transaction_id: str,
    customer: Customer = Depends(get_current_customer),
):
    data = await phonepe_payment_status(merchant_transaction_id, customer)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return success_response(message="PhonePe payment status", data=data)


@router.post("/orders/{order_id}/table-payment", response_model=None)
async def customer_table_payment(
    order_id: str,
    payload: CustomerTablePaymentRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    try:
        order = await record_table_payment(
            db,
            customer,
            order_id,
            payload.payment_method,
            mark_paid=payload.mark_paid,
        )
        return success_response(
            message="Payment method recorded",
            data={"order_id": order.id, "payment_status": order.payment_status, "payment_method": order.payment_method},
        )
    except CustomerPaymentError as e:
        return error_response(message=e.message, error_code=e.code, status_code=e.status_code)
