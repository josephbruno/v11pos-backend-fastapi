"""Billing routes — Razorpay webhook (no JWT)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.modules.billing.razorpay_client import verify_webhook_signature
from app.modules.billing.service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/razorpay/webhook", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
):
    """Handle Razorpay subscription webhooks."""
    body = await request.body()
    if not x_razorpay_signature or not verify_webhook_signature(body, x_razorpay_signature):
        return error_response(
            message="Invalid webhook signature",
            error_code="INVALID_SIGNATURE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        event = json.loads(body.decode("utf-8"))
        await BillingService.handle_webhook(db, event)
        return success_response(message="Webhook processed")
    except Exception as exc:
        return error_response(
            message="Webhook processing failed",
            error_code="WEBHOOK_ERROR",
            error_details=str(exc),
        )
