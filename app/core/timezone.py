"""
Timezone utility for converting datetime objects based on restaurant timezone
"""
from datetime import datetime, timezone as dt_timezone
from typing import Optional, Any, Dict, List
from zoneinfo import ZoneInfo
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def get_utc_now() -> datetime:
    """
    Get current UTC datetime with timezone info
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.now(dt_timezone.utc)


def convert_to_utc(dt: datetime, from_timezone: str = 'UTC') -> datetime:
    """
    Convert datetime to UTC
    
    Args:
        dt: Datetime to convert
        from_timezone: Source timezone (default: UTC)
        
    Returns:
        datetime: UTC datetime with timezone info
    """
    if dt is None:
        return None
    
    # If datetime is naive (no timezone), assume it's in the specified timezone
    if dt.tzinfo is None:
        tz = pytz.timezone(from_timezone)
        dt = tz.localize(dt)
    
    # Convert to UTC
    return dt.astimezone(pytz.UTC)


def convert_from_utc(dt: datetime, to_timezone: str = 'UTC') -> datetime:
    """
    Convert UTC datetime to target timezone
    
    Args:
        dt: UTC datetime to convert
        to_timezone: Target timezone (default: UTC)
        
    Returns:
        datetime: Datetime in target timezone
    """
    if dt is None:
        return None
    
    # Ensure datetime is in UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # Convert to target timezone
    target_tz = pytz.timezone(to_timezone)
    return dt.astimezone(target_tz)


def convert_datetime_fields(
    data: Any,
    to_timezone: str = 'UTC',
    datetime_fields: Optional[List[str]] = None
) -> Any:
    """
    Recursively convert datetime fields in data structure to target timezone
    
    Args:
        data: Data to convert (dict, list, or single value)
        to_timezone: Target timezone
        datetime_fields: List of field names to convert (if None, converts all datetime objects)
        
    Returns:
        Converted data
    """
    if data is None:
        return None
    
    # Handle dictionary
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Convert if it's a datetime field or if datetime_fields not specified
            if isinstance(value, datetime):
                if datetime_fields is None or key in datetime_fields:
                    result[key] = convert_from_utc(value, to_timezone)
                else:
                    result[key] = value
            # Recursively handle nested structures
            elif isinstance(value, (dict, list)):
                result[key] = convert_datetime_fields(value, to_timezone, datetime_fields)
            else:
                result[key] = value
        return result
    
    # Handle list
    elif isinstance(data, list):
        return [convert_datetime_fields(item, to_timezone, datetime_fields) for item in data]
    
    # Handle single datetime
    elif isinstance(data, datetime):
        return convert_from_utc(data, to_timezone)
    
    # Return as-is for other types
    return data


def format_datetime_for_display(
    dt: datetime,
    timezone_str: str = 'UTC',
    date_format: str = 'DD/MM/YYYY',
    time_format: str = '24h'
) -> Dict[str, str]:
    """
    Format datetime for display based on restaurant settings
    
    Args:
        dt: Datetime to format
        timezone_str: Timezone string
        date_format: Date format preference (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
        time_format: Time format preference (12h, 24h)
        
    Returns:
        dict: Formatted datetime strings
    """
    if dt is None:
        return None
    
    # Convert to target timezone
    local_dt = convert_from_utc(dt, timezone_str)
    
    # Format date based on preference
    if date_format == 'MM/DD/YYYY':
        formatted_date = local_dt.strftime('%m/%d/%Y')
    elif date_format == 'YYYY-MM-DD':
        formatted_date = local_dt.strftime('%Y-%m-%d')
    else:  # DD/MM/YYYY (default)
        formatted_date = local_dt.strftime('%d/%m/%Y')
    
    # Format time based on preference
    if time_format == '12h':
        formatted_time = local_dt.strftime('%I:%M %p')
    else:  # 24h (default)
        formatted_time = local_dt.strftime('%H:%M')
    
    # ISO format for APIs
    iso_format = local_dt.isoformat()
    
    return {
        'date': formatted_date,
        'time': formatted_time,
        'datetime': f"{formatted_date} {formatted_time}",
        'iso': iso_format,
        'timestamp': int(local_dt.timestamp()),
        'timezone': timezone_str
    }


async def get_restaurant_timezone(db: AsyncSession, restaurant_id: str) -> str:
    """
    Get restaurant timezone from database
    
    Args:
        db: Database session
        restaurant_id: Restaurant ID
        
    Returns:
        str: Restaurant timezone string (default: Asia/Kolkata)
    """
    from app.modules.restaurant.model import Restaurant
    
    try:
        result = await db.execute(
            select(Restaurant.timezone)
            .where(Restaurant.id == restaurant_id)
        )
        timezone = result.scalar_one_or_none()
        return timezone or 'Asia/Kolkata'
    except Exception:
        return 'Asia/Kolkata'


async def get_restaurant_datetime_settings(db: AsyncSession, restaurant_id: str) -> Dict[str, str]:
    """
    Get restaurant datetime display settings
    
    Args:
        db: Database session
        restaurant_id: Restaurant ID
        
    Returns:
        dict: Restaurant datetime settings
    """
    from app.modules.restaurant.model import Restaurant
    
    try:
        result = await db.execute(
            select(
                Restaurant.timezone,
                Restaurant.date_format,
                Restaurant.time_format,
                Restaurant.country
            )
            .where(Restaurant.id == restaurant_id)
        )
        row = result.one_or_none()
        
        if row:
            return {
                'timezone': row[0] or 'Asia/Kolkata',
                'date_format': row[1] or 'DD/MM/YYYY',
                'time_format': row[2] or '24h',
                'country': row[3] or 'India'
            }
    except Exception:
        pass
    
    # Default settings
    return {
        'timezone': 'Asia/Kolkata',
        'date_format': 'DD/MM/YYYY',
        'time_format': '24h',
        'country': 'India'
    }


class TimezoneConverter:
    """
    Context manager for automatic timezone conversion
    """
    
    def __init__(self, restaurant_id: str, db: AsyncSession):
        self.restaurant_id = restaurant_id
        self.db = db
        self.settings = None
    
    async def __aenter__(self):
        """Load restaurant settings on context enter"""
        self.settings = await get_restaurant_datetime_settings(self.db, self.restaurant_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit"""
        pass
    
    def convert_to_local(self, dt: datetime) -> datetime:
        """Convert UTC datetime to restaurant local time"""
        if not self.settings:
            return dt
        return convert_from_utc(dt, self.settings['timezone'])
    
    def convert_to_utc(self, dt: datetime) -> datetime:
        """Convert restaurant local time to UTC"""
        if not self.settings:
            return dt
        return convert_to_utc(dt, self.settings['timezone'])
    
    def format_for_display(self, dt: datetime) -> Dict[str, str]:
        """Format datetime for display"""
        if not self.settings:
            return format_datetime_for_display(dt)
        
        return format_datetime_for_display(
            dt,
            self.settings['timezone'],
            self.settings['date_format'],
            self.settings['time_format']
        )
    
    def convert_response_data(self, data: Any) -> Any:
        """Convert all datetime fields in response data"""
        if not self.settings:
            return data
        
        return convert_datetime_fields(data, self.settings['timezone'])
