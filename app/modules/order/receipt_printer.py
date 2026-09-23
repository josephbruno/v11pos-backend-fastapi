"""
Billing Receipt Printing Service
Generates the final customer bill/receipt for a completed order
"""
from typing import List

from app.core.timezone import get_ist_now
from app.modules.order.model import Order, OrderItem
from app.modules.restaurant.model import Restaurant


def _inr(amount: float) -> str:
    """
    Format an order/item amount as an INR string, e.g. 'Rs. 108.00'.

    Order/OrderItem money columns are documented as paise, but the POS
    terminal actually writes rupee values straight through - see
    OrderPanel.tsx's buildOrderItems() (unit_price: item.priceRs, no *100)
    and every formatInr() in the frontend, none of which divide by 100
    either. Match that existing convention here instead of the docstring:
    treat these columns as rupees, not paise.
    """
    return f"Rs. {(amount or 0):.2f}"


def _pretax(total: float, tax: float) -> float:
    """
    Strip the tax portion baked into a total/subtotal, for display.

    OrderService.calculate_item_total() folds each item's tax_amount into
    its own total_price, and order.subtotal is the sum of those totals -
    so both already include tax. Printing that as "Subtotal" then "Tax"
    then "TOTAL" (same as Subtotal) makes it look like tax was shown but
    never actually added. Subtracting the tax back out here, for display
    only, restores the expected Subtotal -> + Tax -> = Total reading
    without touching the underlying order-calculation logic used
    elsewhere in the app.
    """
    return max(0.0, (total or 0) - (tax or 0))


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
        lines.append(f"Date: {get_ist_now().strftime('%Y-%m-%d %I:%M %p')}")
        lines.append("-" * width)

        lines.append(f"{'Item':<20}{'Qty':>4}{'Amount':>18}")
        lines.append("-" * width)
        for item in items:
            name = item.product_name[:20]
            amount = _pretax(item.total_price, item.tax_amount)
            lines.append(f"{name:<20}{item.quantity:>4}{_inr(amount):>18}")
            if item.customization:
                lines.append(f"  NOTE: {item.customization}")
        lines.append("-" * width)

        lines.append(f"{'Subtotal':<24}{_inr(_pretax(order.subtotal, order.tax_amount)):>18}")
        if order.discount_amount:
            lines.append(f"{'Discount':<24}{'-' + _inr(order.discount_amount):>18}")
        if order.service_charge:
            lines.append(f"{'Service Charge':<24}{_inr(order.service_charge):>18}")

        tax_details = order.tax_details or {}
        if tax_details.get("cgst_amount"):
            lines.append(f"{'CGST':<24}{_inr(tax_details['cgst_amount']):>18}")
        if tax_details.get("sgst_amount"):
            lines.append(f"{'SGST':<24}{_inr(tax_details['sgst_amount']):>18}")
        if tax_details.get("igst_amount"):
            lines.append(f"{'IGST':<24}{_inr(tax_details['igst_amount']):>18}")
        if not tax_details and order.tax_amount:
            lines.append(f"{'Tax':<24}{_inr(order.tax_amount):>18}")

        if order.rounding_amount:
            lines.append(f"{'Rounding':<24}{_inr(order.rounding_amount):>18}")

        lines.append("=" * width)
        lines.append(f"{'TOTAL':<24}{_inr(order.total_amount):>18}")
        lines.append("=" * width)
        lines.append("")

        if order.payment_method:
            lines.append(f"Payment: {order.payment_method.upper()}")
        lines.append(f"Paid: {_inr(order.paid_amount)}")
        if order.due_amount:
            lines.append(f"Due: {_inr(order.due_amount)}")

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
            amount = _pretax(item.total_price, item.tax_amount)
            item_rows += f"""
        <div class="item-row">
            <div class="item-name">{item.product_name} x{item.quantity}</div>
            <div class="item-amount">{_inr(amount)}</div>
        </div>
        {note_html}"""

        tax_rows = ""
        if tax_details.get("cgst_amount"):
            tax_rows += f'<div class="row"><span>CGST</span><span>{_inr(tax_details["cgst_amount"])}</span></div>'
        if tax_details.get("sgst_amount"):
            tax_rows += f'<div class="row"><span>SGST</span><span>{_inr(tax_details["sgst_amount"])}</span></div>'
        if tax_details.get("igst_amount"):
            tax_rows += f'<div class="row"><span>IGST</span><span>{_inr(tax_details["igst_amount"])}</span></div>'
        if not tax_details and order.tax_amount:
            tax_rows += f'<div class="row"><span>Tax</span><span>{_inr(order.tax_amount)}</span></div>'

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
        <div class="row"><span>Date</span><span>{get_ist_now().strftime('%Y-%m-%d %I:%M %p')}</span></div>
    </div>
    <div class="section">
        {item_rows}
    </div>
    <div class="section">
        <div class="row"><span>Subtotal</span><span>{_inr(_pretax(order.subtotal, order.tax_amount))}</span></div>
        {f'<div class="row"><span>Discount</span><span>-{_inr(order.discount_amount)}</span></div>' if order.discount_amount else ''}
        {f'<div class="row"><span>Service Charge</span><span>{_inr(order.service_charge)}</span></div>' if order.service_charge else ''}
        {tax_rows}
    </div>
    <div class="total-row"><span>TOTAL</span><span>{_inr(order.total_amount)}</span></div>
    <div class="section">
        {f'<div class="row"><span>Payment</span><span>{order.payment_method.upper()}</span></div>' if order.payment_method else ''}
        <div class="row"><span>Paid</span><span>{_inr(order.paid_amount)}</span></div>
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

        # 42 characters is the standard column count for 78-80mm thermal
        # paper at default Font A (matches generate_receipt_text's width) -
        # keep this in sync with the sample preview in Settings.tsx.
        LINE_WIDTH = 42
        AMOUNT_WIDTH = 14  # fits "Rs. 999999.99"
        LABEL_WIDTH = LINE_WIDTH - AMOUNT_WIDTH  # 28
        ITEM_INDENT = "  "  # small text indent, not a hardware margin

        def line(text: str = "") -> bytes:
            return text.encode("ascii", errors="replace") + b"\n"

        def kv(label: str, value: float, negative: bool = False) -> bytes:
            amount = ("-" if negative else "") + _inr(value)
            return line(f"{label:<{LABEL_WIDTH}}{amount:>{AMOUNT_WIDTH}}")

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
        buf += line("=" * LINE_WIDTH)

        buf += ALIGN_LEFT
        buf += line(f"Order #: {order.order_number}")
        buf += line(f"Date: {get_ist_now().strftime('%Y-%m-%d %I:%M %p')}")
        buf += line("-" * LINE_WIDTH)

        name_width = LABEL_WIDTH - len(ITEM_INDENT)
        for item in items:
            # Truncate the product name only, so the " xN" quantity suffix
            # is never cut off for long names.
            qty_suffix = f" x{item.quantity}"
            name = item.product_name[: name_width - len(qty_suffix)] + qty_suffix
            amount = _pretax(item.total_price, item.tax_amount)
            # Routed through kv() - same label/amount column math as the
            # totals below it, so the two sections can never drift apart.
            buf += kv(f"{ITEM_INDENT}{name}", amount)

        buf += line("-" * LINE_WIDTH)
        buf += kv("Subtotal", _pretax(order.subtotal, order.tax_amount))
        if order.discount_amount:
            buf += kv("Discount", order.discount_amount, negative=True)
        if order.service_charge:
            buf += kv("Service Charge", order.service_charge)
        if order.tax_amount:
            buf += kv("Tax", order.tax_amount)

        # Not bold: on some thermal printers, emphasized/bold mode renders at
        # a different per-character pixel width than normal text, which
        # would silently break this row's column alignment against the
        # normal-weight rows above it even though the character math matches.
        buf += kv("TOTAL", order.total_amount)

        buf += ALIGN_CENTER
        buf += line("")
        buf += line("Thank you for visiting!")
        buf += line("")
        buf += line("")
        buf += CUT

        return bytes(buf)
