"""
Utility functions for the RestaurantPOS application
"""
from datetime import datetime, timedelta
from typing import Optional, List, Any
import random
import string
import math
from sqlalchemy.orm import Query
from app.schemas.pagination import PaginationParams, PaginationMeta


def paginate_query(query: Query, pagination: PaginationParams) -> tuple[List[Any], PaginationMeta]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        pagination: PaginationParams with page and page_size
        
    Returns:
        Tuple of (items, pagination_meta)
    """
    # Get total count
    total_items = query.count()
    
    # Calculate total pages
    total_pages = math.ceil(total_items / pagination.page_size) if total_items > 0 else 1
    
    # Get paginated items
    items = query.offset(pagination.skip).limit(pagination.limit).all()
    
    # Create pagination metadata
    meta = PaginationMeta(
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_previous=pagination.page > 1
    )
    
    return items, meta


def create_paginated_response(
    items: List[Any],
    pagination_meta: PaginationMeta,
    message: str = "Data retrieved successfully"
) -> dict:
    """
    Create a paginated response dictionary
    
    Args:
        items: List of items to return
        pagination_meta: Pagination metadata
        message: Response message
        
    Returns:
        Dictionary with status, message, data, and pagination
    """
    return {
        "status": "success",
        "message": message,
        "data": items,
        "pagination": pagination_meta.model_dump()
    }


def generate_order_number(prefix: str = "ORD") -> str:
    """
    Generate a unique order number
    Format: ORD-YYMMDD-XXXXXX (e.g., ORD-251110-001234)
    """
    date_part = datetime.now().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}-{date_part}-{random_part}"


def generate_qr_token(length: int = 32) -> str:
    """
    Generate a secure random token for QR codes
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def cents_to_dollars(cents: int) -> float:
    """
    Convert cents to dollars
    Example: 1999 cents -> 19.99 dollars
    """
    return round(cents / 100, 2)


def dollars_to_cents(dollars: float) -> int:
    """
    Convert dollars to cents
    Example: 19.99 dollars -> 1999 cents
    """
    return int(round(dollars * 100))


def percentage_to_int(percentage: float) -> int:
    """
    Convert percentage to integer storage format
    Example: 10.50% -> 1050
    """
    return int(round(percentage * 100))


def int_to_percentage(value: int) -> float:
    """
    Convert integer storage format to percentage
    Example: 1050 -> 10.50%
    """
    return round(value / 100, 2)


def calculate_tax(amount: int, tax_rate: int) -> int:
    """
    Calculate tax amount
    
    Args:
        amount: Amount in cents
        tax_rate: Tax rate as integer (e.g., 1050 for 10.50%)
    
    Returns:
        Tax amount in cents
    """
    return int(round(amount * tax_rate / 10000))


def calculate_discount(amount: int, discount_percentage: int) -> int:
    """
    Calculate discount amount
    
    Args:
        amount: Amount in cents
        discount_percentage: Discount as integer (e.g., 1000 for 10%)
    
    Returns:
        Discount amount in cents
    """
    return int(round(amount * discount_percentage / 10000))


def calculate_order_total(
    subtotal: int,
    tax_rate: int = 0,
    service_charge_rate: int = 0,
    discount: int = 0,
    tip: int = 0
) -> dict:
    """
    Calculate complete order total breakdown
    
    Args:
        subtotal: Subtotal in cents
        tax_rate: Tax rate as integer (e.g., 1050 for 10.50%)
        service_charge_rate: Service charge rate as integer
        discount: Discount amount in cents
        tip: Tip amount in cents
    
    Returns:
        Dictionary with breakdown
    """
    tax_amount = calculate_tax(subtotal, tax_rate)
    service_charge = calculate_tax(subtotal, service_charge_rate)
    
    total = subtotal + tax_amount + service_charge - discount + tip
    
    return {
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "service_charge": service_charge,
        "discount": discount,
        "tip": tip,
        "total": total
    }


def calculate_loyalty_points(
    amount: int,
    earn_rate: int = 100
) -> int:
    """
    Calculate loyalty points earned
    
    Args:
        amount: Order amount in cents
        earn_rate: Points per dollar (as integer, e.g., 100 for 1.00 points/$1)
    
    Returns:
        Loyalty points earned
    """
    dollars = amount / 100
    points = int(round(dollars * earn_rate / 100))
    return points


def calculate_loyalty_discount(
    points: int,
    redeem_rate: int = 100
) -> int:
    """
    Calculate discount from loyalty points
    
    Args:
        points: Loyalty points to redeem
        redeem_rate: Points required per dollar (e.g., 100 for 100 points = $1)
    
    Returns:
        Discount amount in cents
    """
    dollars = points / redeem_rate
    return int(round(dollars * 100))


def format_time_24h(time_str: str) -> bool:
    """
    Validate 24-hour time format (HH:MM)
    
    Args:
        time_str: Time string to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def get_business_day(date: Optional[datetime] = None) -> str:
    """
    Get the day of week in lowercase
    
    Args:
        date: Date to get day for (defaults to today)
    
    Returns:
        Day name in lowercase (e.g., 'monday')
    """
    if date is None:
        date = datetime.now()
    return date.strftime("%A").lower()


def is_within_business_hours(
    business_hours: dict,
    check_time: Optional[datetime] = None
) -> bool:
    """
    Check if given time is within business hours
    
    Args:
        business_hours: Dict with day as key and {isOpen, openTime, closeTime}
        check_time: Time to check (defaults to now)
    
    Returns:
        True if within business hours, False otherwise
    """
    if check_time is None:
        check_time = datetime.now()
    
    day = get_business_day(check_time)
    
    if day not in business_hours:
        return False
    
    day_hours = business_hours[day]
    
    if not day_hours.get("isOpen", False):
        return False
    
    current_time = check_time.strftime("%H:%M")
    open_time = day_hours.get("openTime", "00:00")
    close_time = day_hours.get("closeTime", "23:59")
    
    return open_time <= current_time <= close_time


def calculate_preparation_time(items: list) -> int:
    """
    Calculate estimated preparation time for order
    
    Args:
        items: List of order items with preparation_time
    
    Returns:
        Estimated time in minutes
    """
    if not items:
        return 15  # Default
    
    # Take the maximum preparation time among all items
    max_time = max(item.get("preparation_time", 15) for item in items)
    
    # Add 5 minutes for every 3 items (complexity factor)
    complexity_time = (len(items) // 3) * 5
    
    return max_time + complexity_time


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text
    
    Args:
        text: Text to convert to slug
    
    Returns:
        URL-friendly slug
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")
    
    # Remove special characters
    allowed = string.ascii_lowercase + string.digits + "-"
    slug = ''.join(c for c in slug if c in allowed)
    
    # Remove consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    
    return slug


def validate_phone_number(phone: str) -> bool:
    """
    Basic phone number validation
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid format, False otherwise
    """
    # Remove common formatting characters
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Check if it contains only digits and optional + prefix
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def mask_phone_number(phone: str) -> str:
    """
    Mask phone number for privacy
    
    Args:
        phone: Phone number to mask
    
    Returns:
        Masked phone number (e.g., +1-***-***-1234)
    """
    if len(phone) < 4:
        return "****"
    
    return phone[:-4].replace(phone[-8:-4], "****") + phone[-4:]


def calculate_table_occupancy_rate(tables: list) -> float:
    """
    Calculate table occupancy percentage
    
    Args:
        tables: List of table objects
    
    Returns:
        Occupancy rate as percentage
    """
    if not tables:
        return 0.0
    
    active_tables = [t for t in tables if t.get("is_active", False)]
    if not active_tables:
        return 0.0
    
    occupied = sum(1 for t in active_tables if t.get("is_occupied", False))
    
    return round((occupied / len(active_tables)) * 100, 2)


# Example usage and tests
if __name__ == "__main__":
    # Test order number generation
    print("Order Number:", generate_order_number())
    
    # Test currency conversion
    print("$19.99 in cents:", dollars_to_cents(19.99))
    print("1999 cents in dollars:", cents_to_dollars(1999))
    
    # Test order calculation
    order = calculate_order_total(
        subtotal=5000,  # $50.00
        tax_rate=1000,  # 10%
        service_charge_rate=500,  # 5%
        discount=500,  # $5.00
        tip=1000  # $10.00
    )
    print("Order Total:", order)
    
    # Test loyalty points
    points = calculate_loyalty_points(5000, 100)  # $50 order, 1 point per dollar
    print("Loyalty Points:", points)
    
    # Test slug generation
    print("Slug:", generate_slug("Margherita Pizza Special!"))
