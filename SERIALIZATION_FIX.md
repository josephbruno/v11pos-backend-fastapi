# Serialization Fix Summary

## Issue
**Problem:** The API returned `500 Internal Server Error` (wrapped in a 400 response because of previous error handling) with the message `"Object of type datetime is not JSON serializable"`. 

This occurred because `app/core/response.py` was constructing a response dictionary containing raw Python `datetime` objects from SQLAlchemy models/Pydantic schemas and passing it directly to `JSONResponse`. `JSONResponse` uses the standard library `json.dumps` which does not support datetime objects.

## Fix
**Solution:** Updated `app/core/response.py` to use `fastapi.encoders.jsonable_encoder`.

### Changes in `app/core/response.py`:
1. Imported `jsonable_encoder`:
   ```python
   from fastapi.encoders import jsonable_encoder
   ```

2. Updated `success_response` to encode data before response construction:
   ```python
   "data": jsonable_encoder(data),
   ```
   And for metadata:
   ```python
   response["meta"] = jsonable_encoder(meta)
   ```

3. Updated `error_response` to encodes data as well:
   ```python
   "data": jsonable_encoder(data),
   ```

## Verification
tested the `/api/v1/restaurants/my-restaurants` endpoint using `Invoke-RestMethod` and confirmed it now returns valid JSON with properly serialized ISO-8601 timestamps.

```json
{
    "success": true,
    "status_code": 200,
    "message": "Restaurants retrieved successfully",
    "data": [],
    "timestamp": "2026-01-01T16:10:48.549434+00:00"
}
```
