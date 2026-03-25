# User List API Integration Guide

This document details the endpoints for retrieving lists of users, suitable for "Manage Users", "Staff List", or "Admin" dashboards in the frontend.

## Base URL
`http://localhost:8000/api/v1`

## Authentication
**Required**: Bearer Token in Authorization header.
`Authorization: Bearer <access_token>`

---

## 1. Get All Users
Retrieve a paginated list of all users in the system. Typically used by Superadmins.

- **Endpoint:** `/users`
- **Method:** `GET`
- **Query Parameters:**
  - `skip` (int, default: 0): Number of records to skip (for pagination).
  - `limit` (int, default: 100): Maximum records to return.

### Request Example
`GET http://localhost:8000/api/v1/users?skip=0&limit=10`

### Success Response (200 OK)
Returns an **Array** of user objects within the `data` field.

```json
{
  "success": true,
  "status_code": 200,
  "message": "Users retrieved successfully",
  "data": [
    {
      "email": "manager@restaurant.com",
      "username": "manager_john",
      "full_name": "John Manager",
      "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "manager",
      "avatar": "https://example.com/avatars/john.jpg",
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "join_date": "2026-01-01T10:00:00",
      "last_login": "2026-01-02T08:30:00",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2026-01-01T09:00:00",
      "updated_at": "2026-01-01T09:00:00"
    },
    { ... }
  ],
  "timestamp": "..."
}
```

---

## 2. Get Users by Restaurant
Retrieve users associated with a specific restaurant (e.g., Staff members of a specific branch).

- **Endpoint:** `/users/restaurant/{restaurant_id}`
- **Method:** `GET`
- **Path Parameters:**
  - `restaurant_id` (string): UUID of the restaurant.
- **Query Parameters:**
  - `skip` (int): default 0.
  - `limit` (int): default 100.

### Request Example
`GET http://localhost:8000/api/v1/users/restaurant/550e8400-e29b-41d4-a716-446655440000`

### Success Response (200 OK)
Returns an **Object** containing the count and a `users` array.

```json
{
  "success": true,
  "status_code": 200,
  "message": "Users retrieved successfully for restaurant ...",
  "data": {
    "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
    "count": 5,
    "users": [
      {
        "id": "...",
        "username": "waiter_tom",
        "role": "staff",
        ...
      }
    ]
  },
  "timestamp": "..."
}
```

---

## 3. Data Field Reference

Here is the description of every field returned in the user object:

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| **id** | string | No | Unique User UUID. Use this for operations like Update/Delete. |
| **email** | string | No | User's email address. |
| **username** | string | No | Unique login username. |
| **full_name** | string | Yes | Display name of the user. |
| **role** | string | Yes | User's permission level (e.g., `owner`, `manager`, `staff`, `cashier`). |
| **is_active** | boolean | No | `true` if user can log in. `false` if banned/disabled. |
| **restaurant_id** | string | Yes | UUID of the restaurant this user belongs to. |
| **avatar** | string | Yes | URL to the user's profile picture. |
| **last_login** | datetime | Yes | Timestamp of last successful login (ISO 8601). |
| **join_date** | datetime | Yes | Date the user joined. |
| **is_superuser** | boolean | No | `true` if this is a System Admin (Platform owner). |
| **created_at** | datetime | No | Account creation timestamp. |
| **updated_at** | datetime | No | Last profile update timestamp. |

---

## Frontend Implementation Tips

1.  **Pagination**: Always send `skip` and `limit`.
    *   Page 1: `skip=0&limit=10`
    *   Page 2: `skip=10&limit=10`
    *   Page 3: `skip=20&limit=10`

2.  **Displaying Roles**:
    *   Map the `role` string to a readable label (e.g., `staff` -> "Staff Member", `owner` -> "Restaurant Owner").
    *   Use badges/chips for roles (e.g., Owner = Gold, Manager = Blue, Staff = Grey).

3.  **Status Handling**:
    *   If `is_active` is `false`, display the row as grayed out or show a "banned" badge.

4.  **Empty States**:
    *   For Endpoint 1: Check if `data.length === 0`.
    *   For Endpoint 2: Check if `data.users.length === 0`.
