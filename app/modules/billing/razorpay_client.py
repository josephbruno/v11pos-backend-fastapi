"""Thin wrapper around the Razorpay Python SDK."""

from __future__ import annotations

from typing import Any

import razorpay

from app.core.config import settings


class RazorpayNotConfiguredError(RuntimeError):
    pass


def get_razorpay_client() -> razorpay.Client:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RazorpayNotConfiguredError(
            "Razorpay credentials not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."
        )
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_plan(
    *,
    period: str,
    interval: int,
    item_name: str,
    amount_paise: int,
    currency: str = "INR",
    description: str | None = None,
) -> dict[str, Any]:
    client = get_razorpay_client()
    return client.plan.create(
        {
            "period": period,
            "interval": interval,
            "item": {
                "name": item_name,
                "amount": amount_paise,
                "currency": currency,
                "description": description or item_name,
            },
        }
    )


def create_razorpay_subscription(
    *,
    plan_id: str,
    total_count: int = 12,
    customer_notify: int = 1,
    notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    client = get_razorpay_client()
    payload: dict[str, Any] = {
        "plan_id": plan_id,
        "total_count": total_count,
        "customer_notify": customer_notify,
    }
    if notes:
        payload["notes"] = notes
    return client.subscription.create(payload)


def cancel_razorpay_subscription(subscription_id: str, cancel_at_cycle_end: bool = True) -> dict[str, Any]:
    client = get_razorpay_client()
    return client.subscription.cancel(subscription_id, {"cancel_at_cycle_end": 1 if cancel_at_cycle_end else 0})


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    client = get_razorpay_client()
    try:
        client.utility.verify_webhook_signature(
            body.decode("utf-8"),
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )
        return True
    except Exception:
        return False
