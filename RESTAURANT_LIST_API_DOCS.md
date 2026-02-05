# Restaurant List API Integration

To obtain the `restaurant_id` required for other API calls (such as creating categories or products), use the **My Restaurants** endpoint.

## List My Restaurants
Retrieve all restaurants owned by the currently authenticated user.

- **Endpoint:** `/restaurants/my-restaurants`
- **Method:** `GET`
- **Content-Type:** `application/json`
- **Authentication:** `Bearer <token>`

### Success Response
The response contains a list of restaurants. You should capture the `id` and `name` from here to display in your frontend dropdown/selector.

```json
{
  "success": true,
  "status_code": 200,
  "message": "Restaurants retrieved successfully",
  "data": [
    {
      "id": "0ee35128-5079-4b2e-b4cd-b205d4b05832",
      "name": "Pizza Palace Restaurant",
      "slug": "pizza-palace",
      "business_name": "Pizza Palace Ltd",
      "currency": "INR",
      "timezone": "Asia/Kolkata",
      "is_active": true,
      "created_at": "2026-01-01T10:00:00Z"
      ...
    },
    {
      "id": "3c2835af-1ff2-4714-8191-c4c1f5b2246f",
      "name": "Test Restaurant 2021",
      ...
    }
  ]
}
```

### Frontend Implementation Tip
When a user logs in:
1.  Call `GET /restaurants/my-restaurants`.
2.  Store the list of restaurants.
3.  If the user has access to multiple restaurants, force them to select one (or default to the first).
4.  Store the selected `restaurant_id` in your global state/context (e.g., Redux, Context API).
5.  Pass this `restaurant_id` to all subsequent API calls for Products, Customers, Orders, etc.
