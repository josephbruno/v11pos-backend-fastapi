"""
Billing Receipt Printing Service
Generates the final customer bill/receipt for a completed order
"""
from typing import List

from app.core.database import utc_now_naive
from app.modules.order.model import Order, OrderItem
from app.modules.restaurant.model import Restaurant


def _money(amount_paise: int) -> str:
    """Format an integer paise/cents amount as a 2-decimal string"""
    return f"{(amount_paise or 0) / 100:.2f}"


class ReceiptPrinter:
    """Service for generating the customer billing receipt"""

    @staticmethod
    def generate_receipt_text(order: Order, items: List[OrderItem], restaurant: Restaurant) -> str:
        """
        Generate plain text receipt for thermal printer / ESC-POS staging
        """
        lines = []
        width = 42  # Standard 80mm thermal printer width in characters

        lines.append(restaurant.name.upper().center(width))
        if restaurant.address:
            lines.append(restaurant.address.center(width))
        if restaurant.phone:
            lines.append(f"Ph: {restaurant.phone}".center(width))
        if restaurant.gstin:
            lines.append(f"GSTIN: {restaurant.gstin}".center(width))
        lines.append("=" * width)
        lines.append("")

        lines.append(f"Order #: {order.order_number}")
        if order.invoice_number:
            lines.append(f"Invoice #: {order.invoice_number}")
        lines.append(f"Type: {order.order_type.upper()}")
        if order.table_id:
            lines.append(f"Table: {order.table_id}")
        if order.guest_name:
            lines.append(f"Customer: {order.guest_name}")
        lines.append(f"Date: {utc_now_naive().strftime('%Y-%m-%d %I:%M %p')}")
        lines.append("-" * width)

        lines.append(f"{'Item':<22}{'Qty':>4}{'Amount':>16}")
        lines.append("-" * width)
        for item in items:
            name = item.product_name[:22]
            lines.append(f"{name:<22}{item.quantity:>4}{_money(item.line_total):>16}")
            if item.customization:
                lines.append(f"  NOTE: {item.customization}")
        lines.append("-" * width)

        lines.append(f"{'Subtotal':<26}{_money(order.subtotal):>16}")
        if order.discount_amount:
            lines.append(f"{'Discount':<26}{'-' + _money(order.discount_amount):>16}")
        if order.service_charge:
            lines.append(f"{'Service Charge':<26}{_money(order.service_charge):>16}")

        tax_details = order.tax_details or {}
        if tax_details.get("cgst_amount"):
            lines.append(f"{'CGST':<26}{_money(tax_details['cgst_amount']):>16}")
        if tax_details.get("sgst_amount"):
            lines.append(f"{'SGST':<26}{_money(tax_details['sgst_amount']):>16}")
        if tax_details.get("igst_amount"):
            lines.append(f"{'IGST':<26}{_money(tax_details['igst_amount']):>16}")
        if not tax_details and order.tax_amount:
            lines.append(f"{'Tax':<26}{_money(order.tax_amount):>16}")

        if order.rounding_amount:
            lines.append(f"{'Rounding':<26}{_money(order.rounding_amount):>16}")

        lines.append("=" * width)
        lines.append(f"{'TOTAL':<26}{_money(order.total_amount):>16}")
        lines.append("=" * width)
        lines.append("")

        if order.payment_method:
            lines.append(f"Payment: {order.payment_method.upper()}")
        lines.append(f"Paid: {_money(order.paid_amount)}")
        if order.due_amount:
            lines.append(f"Due: {_money(order.due_amount)}")

        lines.append("")
        lines.append("Thank you for visiting!".center(width))
        lines.append("")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def generate_receipt_html(order: Order, items: List[OrderItem], restaurant: Restaurant) -> str:
        """
        Generate HTML receipt for browser print (window.print()) fallback
        """
        tax_details = order.tax_details or {}

        item_rows = ""
        for item in items:
            note_html = f'<div class="note">{item.customization}</div>' if item.customization else ""
            item_rows += f"""
        <div class="item-row">
            <div class="item-name">{item.quantity}x {item.product_name}</div>
            <div class="item-amount">{_money(item.line_total)}</div>
        </div>
        {note_html}"""

        tax_rows = ""
        if tax_details.get("cgst_amount"):
            tax_rows += f'<div class="row"><span>CGST</span><span>{_money(tax_details["cgst_amount"])}</span></div>'
        if tax_details.get("sgst_amount"):
            tax_rows += f'<div class="row"><span>SGST</span><span>{_money(tax_details["sgst_amount"])}</span></div>'
        if tax_details.get("igst_amount"):
            tax_rows += f'<div class="row"><span>IGST</span><span>{_money(tax_details["igst_amount"])}</span></div>'
        if not tax_details and order.tax_amount:
            tax_rows += f'<div class="row"><span>Tax</span><span>{_money(order.tax_amount)}</span></div>'

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: 80mm auto; margin: 5mm; }}
        body {{ font-family: 'Courier New', monospace; font-size: 12pt; margin: 0; padding: 10px; width: 80mm; }}
        .header {{ text-align: center; font-weight: bold; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 10px; }}
        .header .store-name {{ font-size: 15pt; }}
        .section {{ margin: 8px 0; padding: 6px 0; border-bottom: 1px dashed #000; }}
        .item-row {{ display: flex; justify-content: space-between; margin: 4px 0; }}
        .note {{ margin-left: 10px; font-size: 10pt; font-style: italic; }}
        .row {{ display: flex; justify-content: space-between; }}
        .total-row {{ display: flex; justify-content: space-between; font-weight: bold; font-size: 13pt; border-top: 2px solid #000; padding-top: 6px; margin-top: 6px; }}
        .footer {{ text-align: center; font-size: 10pt; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="store-name">{restaurant.name.upper()}</div>
        {f'<div>{restaurant.address}</div>' if restaurant.address else ''}
        {f'<div>Ph: {restaurant.phone}</div>' if restaurant.phone else ''}
        {f'<div>GSTIN: {restaurant.gstin}</div>' if restaurant.gstin else ''}
    </div>
    <div class="section">
        <div class="row"><span>Order #</span><span>{order.order_number}</span></div>
        <div class="row"><span>Type</span><span>{order.order_type.upper()}</span></div>
        <div class="row"><span>Date</span><span>{utc_now_naive().strftime('%Y-%m-%d %I:%M %p')}</span></div>
    </div>
    <div class="section">
        {item_rows}
    </div>
    <div class="section">
        <div class="row"><span>Subtotal</span><span>{_money(order.subtotal)}</span></div>
        {f'<div class="row"><span>Discount</span><span>-{_money(order.discount_amount)}</span></div>' if order.discount_amount else ''}
        {f'<div class="row"><span>Service Charge</span><span>{_money(order.service_charge)}</span></div>' if order.service_charge else ''}
        {tax_rows}
    </div>
    <div class="total-row"><span>TOTAL</span><span>{_money(order.total_amount)}</span></div>
    <div class="section">
        {f'<div class="row"><span>Payment</span><span>{order.payment_method.upper()}</span></div>' if order.payment_method else ''}
        <div class="row"><span>Paid</span><span>{_money(order.paid_amount)}</span></div>
    </div>
    <div class="footer">Thank you for visiting!</div>
</body>
</html>
"""

    @staticmethod
    def generate_receipt_escpos(order: Order, items: List[OrderItem], restaurant: Restaurant) -> bytes:
        """
        Generate raw ESC/POS byte stream for direct thermal printing via the
        local print-bridge. Callers must base64-encode this before sending it
        as JSON to the bridge's /print endpoint.
        """
        ESC = b"\x1b"
        GS = b"\x1d"
        INIT = ESC + b"@"
        ALIGN_CENTER = ESC + b"a" + b"\x01"
        ALIGN_LEFT = ESC + b"a" + b"\x00"
        BOLD_ON = ESC + b"E" + b"\x01"
        BOLD_OFF = ESC + b"E" + b"\x00"
        CUT = GS + b"V" + b"\x42" + b"\x00"
        # Item list is indented off the paper edge; everything else keeps margin 0.
        ITEM_LIST_LEFT_MARGIN = 50  # dots (horizontal motion units)

        def left_margin(dots: int) -> bytes:
            """GS L nL nH - set left margin, must be sent at the start of a line"""
            return GS + b"L" + bytes([dots & 0xFF, (dots >> 8) & 0xFF])

        def line(text: str = "") -> bytes:
            return text.encode("ascii", errors="replace") + b"\n"

        buf = bytearray()
        buf += INIT
        buf += ALIGN_CENTER
        buf += BOLD_ON
        buf += line(restaurant.name.upper())
        buf += BOLD_OFF
        if restaurant.address:
            buf += line(restaurant.address)
        if restaurant.phone:
            buf += line(f"Ph: {restaurant.phone}")
        if restaurant.gstin:
            buf += line(f"GSTIN: {restaurant.gstin}")
        buf += line("=" * 32)

        buf += ALIGN_LEFT
        buf += line(f"Order #: {order.order_number}")
        buf += line(f"Date: {utc_now_naive().strftime('%Y-%m-%d %I:%M %p')}")
        buf += line("-" * 32)

        buf += left_margin(ITEM_LIST_LEFT_MARGIN)
        for item in items:
            buf += line(f"{item.quantity}x {item.product_name[:24]}")
            buf += line(f"{'':<24}{_money(item.line_total):>8}")
        buf += left_margin(0)

        buf += line("-" * 32)
        buf += line(f"{'Subtotal':<24}{_money(order.subtotal):>8}")
        if order.discount_amount:
            buf += line(f"{'Discount':<24}{'-' + _money(order.discount_amount):>8}")
        if order.service_charge:
            buf += line(f"{'Service Charge':<24}{_money(order.service_charge):>8}")
        if order.tax_amount:
            buf += line(f"{'Tax':<24}{_money(order.tax_amount):>8}")

        buf += BOLD_ON
        buf += line(f"{'TOTAL':<24}{_money(order.total_amount):>8}")
        buf += BOLD_OFF

        buf += ALIGN_CENTER
        buf += line("")
        buf += line("Thank you for visiting!")
        buf += line("")
        buf += line("")
        buf += CUT

        return bytes(buf)
