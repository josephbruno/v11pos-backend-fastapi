"""
Transactional email bodies for customer OTP (HTML + plain text).

Uses table-based layout and inline CSS for broad client support (Gmail, Outlook, Apple Mail).
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Optional


def _esc(value: Optional[str]) -> str:
    return html.escape(value or "", quote=True)


def _format_address(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    postal_code: Optional[str],
    country: Optional[str],
) -> str:
    parts = [p.strip() for p in [address or "", city or "", state or "", postal_code or "", country or ""] if p.strip()]
    return ", ".join(parts) if parts else ""


@dataclass
class RestaurantEmailContext:
    """Snapshot of restaurant fields for email rendering (no ORM in sync SMTP thread)."""

    name: str
    business_name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#1a1a2e"
    accent_color: str = "#4361ee"


def build_customer_otp_email(
    *,
    otp: str,
    restaurant: RestaurantEmailContext,
    expiry_minutes: int = 10,
) -> tuple[str, str, str]:
    """
    Returns (subject, text_plain, text_html).
    """
    display = (restaurant.business_name or restaurant.name).strip() or "Restaurant"
    subject = f"{display} — your sign-in code"

    addr_line = _format_address(
        restaurant.address, restaurant.city, restaurant.state, restaurant.postal_code, restaurant.country
    )
    safe_display = _esc(display)
    safe_otp = _esc(otp)
    safe_addr = _esc(addr_line) if addr_line else ""
    safe_phone = _esc(restaurant.phone) if restaurant.phone else ""
    safe_remail = _esc(restaurant.contact_email) if restaurant.contact_email else ""

    primary = restaurant.primary_color if _is_hex_color(restaurant.primary_color) else "#1a1a2e"
    accent = restaurant.accent_color if _is_hex_color(restaurant.accent_color) else "#4361ee"

    logo_block = ""
    if restaurant.logo_url and str(restaurant.logo_url).strip().lower().startswith("https://"):
        logo_block = (
            f'<img src="{_esc(restaurant.logo_url.strip())}" alt="" width="120" height="auto" '
            'style="max-width:120px;height:auto;display:block;margin:0 auto 16px;border:0;" />'
        )

    text_plain = (
        f"{display}\n\n"
        f"Your one-time sign-in code is: {otp}\n\n"
        f"This code expires in {expiry_minutes} minutes.\n\n"
        + (f"Location: {addr_line}\n" if addr_line else "")
        + (f"Phone: {restaurant.phone}\n" if restaurant.phone else "")
        + (f"Email: {restaurant.contact_email}\n" if restaurant.contact_email else "")
        + "\nIf you did not request this code, you can ignore this message.\n"
        "Do not share this code with anyone.\n"
    )

    # Preheader (hidden preview text for inbox clients)
    preheader = f"Use code {otp} to sign in. Expires in {expiry_minutes} minutes."

    detail_lines: list[str] = []
    if addr_line:
        detail_lines.append(
            f'<p style="margin:0 0 4px;font-size:14px;line-height:1.5;color:#475569;">{safe_addr}</p>'
        )
    if restaurant.phone:
        detail_lines.append(
            '<p style="margin:8px 0 0;font-size:14px;color:#475569;">'
            f'<strong style="color:#64748b;">Phone:</strong> {safe_phone}</p>'
        )
    if restaurant.contact_email:
        detail_lines.append(
            '<p style="margin:4px 0 0;font-size:14px;color:#475569;">'
            f'<strong style="color:#64748b;">Email:</strong> {safe_remail}</p>'
        )
    details_html = "".join(detail_lines)

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_display}</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;max-height:0;max-width:0;overflow:hidden;mso-hide:all;">{_esc(preheader)}</span>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f0f2f5;padding:24px 12px;">
  <tr>
    <td align="center">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
        <tr>
          <td style="height:4px;background:linear-gradient(90deg,{primary},{accent});"></td>
        </tr>
        <tr>
          <td style="padding:28px 28px 8px;text-align:center;">
            {logo_block}
            <p style="margin:0 0 4px;font-size:13px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#64748b;">Sign-in verification</p>
            <h1 style="margin:0;font-size:22px;line-height:1.3;font-weight:700;color:#0f172a;">{safe_display}</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 28px 24px;">
            <p style="margin:0 0 20px;font-size:15px;line-height:1.55;color:#334155;">Use the code below to continue to your account. This helps us keep your orders and profile secure.</p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
              <tr>
                <td align="center" style="padding:24px 16px;">
                  <p style="margin:0 0 8px;font-size:12px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#64748b;">Your code</p>
                  <p style="margin:0;font-size:36px;font-weight:700;letter-spacing:0.25em;font-family:ui-monospace,'Cascadia Code','SF Mono',Consolas,monospace;color:{primary};">{safe_otp}</p>
                </td>
              </tr>
            </table>
            <p style="margin:20px 0 0;font-size:14px;line-height:1.5;color:#64748b;">This code expires in <strong style="color:#0f172a;">{expiry_minutes} minutes</strong>. If it expires, request a new code from the app.</p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 28px 24px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-top:1px solid #e2e8f0;padding-top:20px;">
              <tr>
                <td>
                  <p style="margin:0 0 8px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#94a3b8;">Restaurant details</p>
                  <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#0f172a;">{safe_display}</p>
                  {details_html}
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 28px;background-color:#f8fafc;border-top:1px solid #e2e8f0;">
            <p style="margin:0;font-size:12px;line-height:1.6;color:#94a3b8;">If you did not try to sign in, you can ignore this email. Your account remains protected. Never share this code with anyone, including restaurant staff.</p>
          </td>
        </tr>
      </table>
      <p style="margin:16px 0 0;font-size:11px;color:#94a3b8;text-align:center;">This is an automated security message.</p>
    </td>
  </tr>
</table>
</body>
</html>"""

    return subject, text_plain, html_body


def _is_hex_color(value: str) -> bool:
    if not value or len(value) not in (4, 7):
        return False
    if not value.startswith("#"):
        return False
    body = value[1:]
    return all(c in "0123456789abcdefABCDEF" for c in body) and len(body) in (3, 6)


def restaurant_to_email_context(restaurant) -> RestaurantEmailContext:
    """Build context from a Restaurant ORM instance (sync-safe snapshot)."""
    name = getattr(restaurant, "name", None) or ""
    business = getattr(restaurant, "business_name", None) or name
    return RestaurantEmailContext(
        name=name or "Restaurant",
        business_name=business or name or "Restaurant",
        address=getattr(restaurant, "address", None),
        city=getattr(restaurant, "city", None),
        state=getattr(restaurant, "state", None),
        postal_code=getattr(restaurant, "postal_code", None),
        country=getattr(restaurant, "country", None),
        phone=getattr(restaurant, "phone", None),
        contact_email=getattr(restaurant, "email", None),
        logo_url=getattr(restaurant, "logo", None),
        primary_color=getattr(restaurant, "primary_color", None) or "#1a1a2e",
        accent_color=getattr(restaurant, "accent_color", None) or "#4361ee",
    )
