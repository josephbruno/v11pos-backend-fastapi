# Timezone & DateTime Handling Implementation

## Overview
This document explains the universal timezone handling implementation for the POS FastAPI backend. All datetime fields are stored in UTC in the database and automatically converted to the restaurant's timezone when fetched.

## Architecture

### 1. Database Storage (UTC)
- **All datetime fields are stored in UTC** in the database
- Uses `app.core.database.utc_now()` for default timestamps
- Example:
  ```python
  from app.core.database import utc_now
  from sqlalchemy import DateTime
  
  created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
  ```

### 2. Restaurant Timezone Configuration
Each restaurant has timezone settings in the `restaurants` table:
- `timezone`: e.g., 'Asia/Kolkata', 'America/New_York', 'Europe/London'
- `country`: e.g., 'India', 'USA', 'UK'
- `date_format`: e.g., 'DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'
- `time_format`: e.g., '24h', '12h'

### 3. Automatic Conversion on API Response
When data is fetched via API:
1. User authentication loads restaurant timezone settings
2. All datetime fields in responses are automatically converted to restaurant timezone
3. Formatted datetime strings can be included in responses

## Implementation Details

### Core Components

#### 1. Timezone Utility (`app/core/timezone.py`)
```python
from app.core.timezone import (
    get_utc_now,                    # Get current UTC time
    convert_to_utc,                 # Convert local time to UTC
    convert_from_utc,               # Convert UTC to local time
    convert_datetime_fields,        # Convert all datetime fields in data
    format_datetime_for_display,    # Format datetime for UI display
    get_restaurant_timezone,        # Get restaurant timezone from DB
    TimezoneConverter               # Context manager for conversions
)
```

#### 2. Enhanced Dependencies (`app/core/dependencies.py`)
```python
# Automatically loads timezone settings with user authentication
async def get_current_user(...) -> User:
    # User object now includes:
    # - user.timezone (e.g., 'Asia/Kolkata')
    # - user.date_format (e.g., 'DD/MM/YYYY')
    # - user.time_format (e.g., '24h')
    # - user.country (e.g., 'India')
    pass

# Get just the timezone string
async def get_restaurant_timezone(...) -> str:
    pass
```

#### 3. Enhanced Response Handler (`app/core/response.py`)
```python
def success_response(
    message: str,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    timezone: Optional[str] = None  # NEW: Automatic timezone conversion
) -> dict:
    # If timezone is provided, all datetime fields in data are converted
    pass
```

## Usage in Routes

### Basic Usage (Recommended)
```python
from app.core.dependencies import get_current_active_user
from app.core.response import success_response

@router.get("/categories")
async def get_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    categories = await CategoryService.get_all(db)
    
    # Automatic timezone conversion using current_user.timezone
    return success_response(
        message="Categories retrieved successfully",
        data=[c.model_dump() for c in categories],
        timezone=getattr(current_user, 'timezone', None)
    )
```

### Advanced Usage with Formatted Dates
```python
from app.core.timezone import format_datetime_for_display

@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.get_by_id(db, order_id)
    order_data = order.model_dump()
    
    # Add formatted datetime for UI display
    order_data['created_at_formatted'] = format_datetime_for_display(
        order.created_at,
        current_user.timezone,
        current_user.date_format,
        current_user.time_format
    )
    
    return success_response(
        message="Order retrieved successfully",
        data=order_data,
        timezone=current_user.timezone
    )
```

### Using TimezoneConverter Context Manager
```python
from app.core.timezone import TimezoneConverter

@router.post("/orders")
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    async with TimezoneConverter(current_user.restaurant_id, db) as tz:
        # Convert input datetime to UTC if needed
        if order_data.scheduled_time:
            order_data.scheduled_time = tz.convert_to_utc(order_data.scheduled_time)
        
        order = await OrderService.create(db, order_data)
        
        # Convert response to local timezone
        response_data = tz.convert_response_data(order.model_dump())
    
    return success_response(
        message="Order created successfully",
        data=response_data
    )
```

## API Response Format

### Without Timezone Conversion (UTC)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Data retrieved successfully",
  "data": {
    "id": "123",
    "name": "Category 1",
    "created_at": "2024-12-31T10:30:00Z",  // UTC
    "updated_at": "2024-12-31T15:45:00Z"   // UTC
  },
  "timestamp": "2024-12-31T16:00:00Z"
}
```

### With Timezone Conversion (Restaurant Local Time)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Data retrieved successfully",
  "data": {
    "id": "123",
    "name": "Category 1",
    "created_at": "2024-12-31T16:00:00+05:30",  // Asia/Kolkata
    "updated_at": "2024-12-31T21:15:00+05:30"   // Asia/Kolkata
  },
  "timestamp": "2024-12-31T21:30:00+05:30"
}
```

### With Formatted Display Dates
```json
{
  "success": true,
  "status_code": 200,
  "message": "Order retrieved successfully",
  "data": {
    "id": "ORD-001",
    "total": 150000,
    "created_at": "2024-12-31T16:00:00+05:30",
    "created_at_formatted": {
      "date": "31/12/2024",           // Based on restaurant date_format
      "time": "16:00",                // Based on restaurant time_format
      "datetime": "31/12/2024 16:00",
      "iso": "2024-12-31T16:00:00+05:30",
      "timestamp": 1735648200,
      "timezone": "Asia/Kolkata"
    }
  }
}
```

## Timezone Conversion Flow

```
┌─────────────────┐
│   Database      │
│   (UTC only)    │
└────────┬────────┘
         │
         │ SQLAlchemy fetch
         ▼
┌─────────────────┐
│  Python Models  │
│  (UTC datetime) │
└────────┬────────┘
         │
         │ Pydantic .model_dump()
         ▼
┌─────────────────┐
│ Response Dict   │
│  (UTC strings)  │
└────────┬────────┘
         │
         │ success_response(timezone=...)
         ▼
┌─────────────────┐
│convert_datetime │
│    _fields()    │
└────────┬────────┘
         │
         │ Convert to restaurant timezone
         ▼
┌─────────────────┐
│  API Response   │
│(Local timezone) │
└─────────────────┘
```

## Supported Timezones

The system supports all IANA timezone names via `pytz`. Common examples:

### Asia
- `Asia/Kolkata` - India Standard Time (IST, UTC+5:30)
- `Asia/Dubai` - Gulf Standard Time (GST, UTC+4:00)
- `Asia/Singapore` - Singapore Time (SGT, UTC+8:00)
- `Asia/Tokyo` - Japan Standard Time (JST, UTC+9:00)

### Americas
- `America/New_York` - Eastern Time (ET, UTC-5:00/-4:00)
- `America/Chicago` - Central Time (CT, UTC-6:00/-5:00)
- `America/Los_Angeles` - Pacific Time (PT, UTC-8:00/-7:00)
- `America/Toronto` - Eastern Time (ET, UTC-5:00/-4:00)

### Europe
- `Europe/London` - Greenwich Mean Time (GMT, UTC+0:00/+1:00)
- `Europe/Paris` - Central European Time (CET, UTC+1:00/+2:00)
- `Europe/Berlin` - Central European Time (CET, UTC+1:00/+2:00)

### Australia
- `Australia/Sydney` - Australian Eastern Time (AET, UTC+10:00/+11:00)
- `Australia/Melbourne` - Australian Eastern Time (AET, UTC+10:00/+11:00)

## Testing

### Test Timezone Conversion
```bash
# 1. Create restaurant with specific timezone
curl -X POST http://localhost:8000/api/v1/restaurants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "timezone": "America/New_York",
    "date_format": "MM/DD/YYYY",
    "time_format": "12h"
  }'

# 2. Create category (timestamps stored in UTC)
curl -X POST http://localhost:8000/api/v1/products/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Beverages", "restaurant_id": "xxx"}'

# 3. Fetch category (timestamps returned in restaurant timezone)
curl -X GET http://localhost:8000/api/v1/products/categories/xxx \
  -H "Authorization: Bearer $TOKEN"
```

### Database Verification
```sql
-- Check stored times (should be UTC)
SELECT id, name, created_at, updated_at 
FROM categories 
WHERE id = 'xxx';

-- Check restaurant timezone settings
SELECT id, name, timezone, date_format, time_format, country
FROM restaurants
WHERE id = 'xxx';
```

## Migration Notes

### Existing Data
If you have existing datetime data that's not in UTC:
1. Create a migration script to convert existing timestamps to UTC
2. Update the data using the restaurant's timezone setting

```python
# Migration example
from app.core.timezone import convert_to_utc

async def migrate_timestamps():
    restaurants = await db.execute(select(Restaurant))
    for restaurant in restaurants:
        categories = await db.execute(
            select(Category).where(Category.restaurant_id == restaurant.id)
        )
        for category in categories:
            category.created_at = convert_to_utc(
                category.created_at, 
                restaurant.timezone
            )
            category.updated_at = convert_to_utc(
                category.updated_at,
                restaurant.timezone
            )
        await db.commit()
```

## Best Practices

1. **Always store UTC in database**
   ```python
   from app.core.database import utc_now
   created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
   ```

2. **Always convert on API response**
   ```python
   return success_response(
       message="Success",
       data=data,
       timezone=getattr(current_user, 'timezone', None)
   )
   ```

3. **Never hardcode timezones**
   ```python
   # ❌ Bad
   timezone = 'Asia/Kolkata'
   
   # ✅ Good
   timezone = current_user.timezone
   ```

4. **Use formatted dates for UI**
   ```python
   formatted = format_datetime_for_display(
       dt, 
       current_user.timezone,
       current_user.date_format,
       current_user.time_format
   )
   ```

5. **Handle timezone-aware datetime input**
   ```python
   # If client sends timezone-aware datetime, convert to UTC before saving
   from app.core.timezone import convert_to_utc
   order_data.scheduled_time = convert_to_utc(
       order_data.scheduled_time,
       current_user.timezone
   )
   ```

## Troubleshooting

### Issue: Datetimes not converting
**Solution**: Ensure `timezone` parameter is passed to `success_response()`

### Issue: Wrong timezone displayed
**Solution**: Check restaurant's timezone setting in database

### Issue: DateTime parse errors
**Solution**: Ensure input datetimes are ISO 8601 formatted with timezone info

### Issue: Timezone not found error
**Solution**: Verify timezone name is valid IANA timezone (use `pytz.all_timezones`)

## Performance Considerations

1. **Timezone conversion is done in-memory** - No database queries
2. **Restaurant settings cached** - Loaded once per request with user authentication
3. **Bulk operations** - Use `convert_datetime_fields()` for lists
4. **Indexed columns** - DateTime columns should be indexed for range queries

## Summary

✅ **All datetime values stored in UTC in database**
✅ **Automatic conversion to restaurant timezone on API fetch**
✅ **Restaurant-specific date/time formatting**
✅ **Country-aware timezone settings**
✅ **Consistent across all modules**
✅ **No changes required to existing business logic**
✅ **Easy to use with simple `timezone` parameter**

This implementation ensures that your POS system can handle restaurants in any timezone worldwide while maintaining data consistency and accuracy.
