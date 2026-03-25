"""
KOT (Kitchen Order Ticket) Printing Service
Handles printing of kitchen order tickets for different stations
"""
from typing import Optional, List, Dict
from datetime import datetime
from app.modules.kds.model import KitchenDisplay, KitchenDisplayItem, KitchenStation
from app.modules.order.model import Order


class KOTPrinter:
    """Service for generating and printing Kitchen Order Tickets"""
    
    @staticmethod
    def generate_kot_text(
        display: KitchenDisplay,
        items: List[KitchenDisplayItem],
        station: KitchenStation
    ) -> str:
        """
        Generate plain text KOT format for printing
        
        Returns formatted text ready for thermal printer or PDF generation
        """
        lines = []
        width = 42  # Standard thermal printer width in characters
        
        # Header
        lines.append("=" * width)
        lines.append("KITCHEN ORDER TICKET".center(width))
        lines.append("=" * width)
        lines.append("")
        
        # Station Information
        lines.append(f"Station: {station.name.upper()}")
        lines.append(f"Type: {station.station_type.upper()}")
        lines.append("-" * width)
        lines.append("")
        
        # Order Information
        lines.append(f"Order #: {display.order_number}")
        lines.append(f"Order Type: {display.order_type.upper()}")
        
        if display.table_number:
            lines.append(f"Table: {display.table_number}")
        
        if display.customer_name:
            lines.append(f"Customer: {display.customer_name}")
        
        lines.append(f"Time: {display.received_at.strftime('%I:%M %p')}")
        
        if display.is_rush:
            lines.append("")
            lines.append("*** RUSH ORDER ***".center(width))
        
        if display.priority > 0:
            lines.append(f"Priority: {display.priority}")
        
        lines.append("")
        lines.append("=" * width)
        lines.append("ITEMS".center(width))
        lines.append("=" * width)
        lines.append("")
        
        # Items
        for item in items:
            # Item quantity and name
            item_line = f"{item.quantity}x {item.product_name}"
            lines.append(item_line)
            
            # Modifiers
            if item.modifiers and item.modifiers.get("items"):
                for modifier in item.modifiers.get("items", []):
                    if isinstance(modifier, dict):
                        mod_name = modifier.get("name", "")
                        mod_qty = modifier.get("quantity", 1)
                        lines.append(f"  + {mod_qty}x {mod_name}")
                    else:
                        lines.append(f"  + {modifier}")
            
            # Customization
            if item.customization:
                lines.append(f"  NOTE: {item.customization}")
            
            # Special notes
            if item.notes:
                lines.append(f"  ** {item.notes}")
            
            # Complimentary flag
            if item.is_complimentary:
                lines.append("  [COMPLIMENTARY]")
            
            # Attention flag
            if item.requires_attention:
                lines.append("  *** ATTENTION REQUIRED ***")
            
            lines.append("")
        
        lines.append("-" * width)
        lines.append(f"Total Items: {len(items)}")
        lines.append("")
        
        # Special Instructions
        if display.special_instructions:
            lines.append("SPECIAL INSTRUCTIONS:")
            lines.append(display.special_instructions)
            lines.append("")
        
        if display.kitchen_notes:
            lines.append("KITCHEN NOTES:")
            lines.append(display.kitchen_notes)
            lines.append("")
        
        # Timing
        if display.estimated_prep_time:
            lines.append(f"Est. Prep Time: {display.estimated_prep_time} min")
        
        if display.due_time:
            lines.append(f"Due By: {display.due_time.strftime('%I:%M %p')}")
        
        lines.append("")
        lines.append("=" * width)
        lines.append(f"Printed: {datetime.utcnow().strftime('%Y-%m-%d %I:%M %p')}")
        lines.append("=" * width)
        
        # Footer spacing for cut
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_kot_html(
        display: KitchenDisplay,
        items: List[KitchenDisplayItem],
        station: KitchenStation
    ) -> str:
        """
        Generate HTML format KOT for web printing or PDF generation
        """
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: 80mm auto;
            margin: 5mm;
        }
        body {
            font-family: 'Courier New', monospace;
            font-size: 12pt;
            margin: 0;
            padding: 10px;
            width: 80mm;
        }
        .header {
            text-align: center;
            font-weight: bold;
            font-size: 14pt;
            border-top: 2px solid #000;
            border-bottom: 2px solid #000;
            padding: 5px 0;
            margin-bottom: 10px;
        }
        .section {
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 1px dashed #000;
        }
        .label {
            font-weight: bold;
        }
        .rush {
            text-align: center;
            font-weight: bold;
            font-size: 14pt;
            background: #000;
            color: #fff;
            padding: 5px;
            margin: 10px 0;
        }
        .item {
            margin: 8px 0;
            padding: 5px 0;
        }
        .item-name {
            font-weight: bold;
            font-size: 13pt;
        }
        .modifier {
            margin-left: 15px;
            font-size: 11pt;
        }
        .note {
            margin-left: 15px;
            font-style: italic;
            font-size: 11pt;
        }
        .complimentary {
            font-weight: bold;
            margin-left: 15px;
        }
        .footer {
            text-align: center;
            font-size: 10pt;
            border-top: 2px solid #000;
            padding-top: 5px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
"""
        
        # Header
        html += f"""
    <div class="header">
        KITCHEN ORDER TICKET<br>
        {station.name.upper()}
    </div>
"""
        
        # Order Info
        html += f"""
    <div class="section">
        <div><span class="label">Order #:</span> {display.order_number}</div>
        <div><span class="label">Type:</span> {display.order_type.upper()}</div>
"""
        
        if display.table_number:
            html += f"""        <div><span class="label">Table:</span> {display.table_number}</div>\n"""
        
        if display.customer_name:
            html += f"""        <div><span class="label">Customer:</span> {display.customer_name}</div>\n"""
        
        html += f"""        <div><span class="label">Time:</span> {display.received_at.strftime('%I:%M %p')}</div>\n"""
        html += """    </div>\n"""
        
        # Rush Order
        if display.is_rush:
            html += """    <div class="rush">*** RUSH ORDER ***</div>\n"""
        
        # Items
        html += """    <div class="section">\n"""
        html += """        <div style="text-align: center; font-weight: bold; margin-bottom: 10px;">ITEMS</div>\n"""
        
        for item in items:
            html += f"""        <div class="item">\n"""
            html += f"""            <div class="item-name">{item.quantity}x {item.product_name}</div>\n"""
            
            # Modifiers
            if item.modifiers and item.modifiers.get("items"):
                for modifier in item.modifiers.get("items", []):
                    if isinstance(modifier, dict):
                        mod_name = modifier.get("name", "")
                        mod_qty = modifier.get("quantity", 1)
                        html += f"""            <div class="modifier">+ {mod_qty}x {mod_name}</div>\n"""
                    else:
                        html += f"""            <div class="modifier">+ {modifier}</div>\n"""
            
            # Customization
            if item.customization:
                html += f"""            <div class="note">NOTE: {item.customization}</div>\n"""
            
            # Notes
            if item.notes:
                html += f"""            <div class="note">** {item.notes}</div>\n"""
            
            # Complimentary
            if item.is_complimentary:
                html += """            <div class="complimentary">[COMPLIMENTARY]</div>\n"""
            
            html += """        </div>\n"""
        
        html += f"""        <div style="margin-top: 10px;"><span class="label">Total Items:</span> {len(items)}</div>\n"""
        html += """    </div>\n"""
        
        # Special Instructions
        if display.special_instructions or display.kitchen_notes:
            html += """    <div class="section">\n"""
            if display.special_instructions:
                html += f"""        <div><span class="label">SPECIAL INSTRUCTIONS:</span></div>\n"""
                html += f"""        <div>{display.special_instructions}</div>\n"""
            if display.kitchen_notes:
                html += f"""        <div><span class="label">KITCHEN NOTES:</span></div>\n"""
                html += f"""        <div>{display.kitchen_notes}</div>\n"""
            html += """    </div>\n"""
        
        # Timing
        if display.estimated_prep_time or display.due_time:
            html += """    <div class="section">\n"""
            if display.estimated_prep_time:
                html += f"""        <div><span class="label">Est. Prep Time:</span> {display.estimated_prep_time} min</div>\n"""
            if display.due_time:
                html += f"""        <div><span class="label">Due By:</span> {display.due_time.strftime('%I:%M %p')}</div>\n"""
            html += """    </div>\n"""
        
        # Footer
        html += f"""
    <div class="footer">
        Printed: {datetime.utcnow().strftime('%Y-%m-%d %I:%M %p')}
    </div>
</body>
</html>
"""
        
        return html
    
    @staticmethod
    def generate_kot_json(
        display: KitchenDisplay,
        items: List[KitchenDisplayItem],
        station: KitchenStation
    ) -> Dict:
        """
        Generate JSON format KOT for integration with printer systems
        """
        return {
            "kot_id": f"KOT-{display.id}",
            "timestamp": datetime.utcnow().isoformat(),
            "station": {
                "id": station.id,
                "name": station.name,
                "type": station.station_type,
                "printer_tags": station.printer_tags
            },
            "order": {
                "id": display.order_id,
                "order_number": display.order_number,
                "order_type": display.order_type,
                "table_number": display.table_number,
                "customer_name": display.customer_name,
                "received_at": display.received_at.isoformat(),
                "is_rush": display.is_rush,
                "priority": display.priority
            },
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "modifiers": item.modifiers,
                    "customization": item.customization,
                    "notes": item.notes,
                    "is_complimentary": item.is_complimentary,
                    "requires_attention": item.requires_attention
                }
                for item in items
            ],
            "special_instructions": display.special_instructions,
            "kitchen_notes": display.kitchen_notes,
            "timing": {
                "estimated_prep_time": display.estimated_prep_time,
                "due_time": display.due_time.isoformat() if display.due_time else None
            }
        }
