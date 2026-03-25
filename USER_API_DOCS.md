# User API Integration Guide

This document provides detailed integration guidelines for User Create and Update operations.

## Base URL
`http://localhost:8000/api/v1`

---

## 1. Create User (Register)

Create a new user account (Public Endpoint).

- **Endpoint:** `/users`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Auth:** Public (No token required)

### Request Body (JSON)

| Field | Type | Required | Description | Validation / Constraints |
|-------|------|----------|-------------|--------------------------|
| **email** | string | ✅ Yes | User email | Valid email format. Must be unique. |
| **username** | string | ✅ Yes | Unique username | Min 3, Max 100 chars. |
| **password** | string | ✅ Yes | Password | Min 6 chars. |
| **full_name** | string | ❌ No | Display name | Max 255 chars. |
| **role** | string | ❌ No | User role | e.g., `staff`, `manager`. Default: `staff` |
| **avatar** | string | ❌ No | Profile image URL | |
| **restaurant_id** | string | ❌ No | Associate with restaurant | UUID string |

### Example Request
```json
{
  "email": "john.doe@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "manager"
}
```

### Success Response (201 Created)
```json
{
  "success": true,
  "status_code": 201,
  "message": "User created successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "manager",
    "is_active": true,
    "created_at": "2026-01-01T10:00:00Z",
    ...
  }
}
```

### Error Codes
| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `EMAIL_EXISTS` | 400 | Email is already registered. |
| `USERNAME_EXISTS` | 400 | Username is taken. |

---

## 2. Update User

Update an existing user's profile.
**Permission:** 
- Users can update their own profile.
- Restaurant Owners/Managers can update users within their restaurant.
- Superusers can update any profile.

- **Endpoint:** `/users/{user_id}`
- **Method:** `PUT`
- **Content-Type:** `application/json`
- **Auth:** Bearer Token required

### Request Body (JSON)
All fields are optional. Send only the fields you want to update.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| **full_name** | string | Display name | Max 255 chars |
| **email** | string | Update email address | Must be unique |
| **username** | string | Update username | Must be unique |
| **password** | string | Change password | Min 6 chars |
| **avatar** | string | Profile image URL | |
| **role** | string | Change role | |
| **is_active** | boolean | Activate/Deactivate user | |

### Example Request
```json
{
  "full_name": "Johnathan Doe",
  "avatar": "https://example.com/avatar.jpg"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "User updated successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "Johnathan Doe",
    ...
  }
}
```

---

## 3. Get Current User

Retrieve the currently logged-in user's profile.

- **Endpoint:** `/users/me`
- **Method:** `GET`
- **Auth:** Bearer Token required

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "User retrieved successfully",
  "data": {
    "id": "...",
    "email": "...",
    "username": "...",
    "role": "..."
  }
}
```

---

## 4. Get All Users (Admin)

Retrieve a paginated list of users.

- **Endpoint:** `/users?skip=0&limit=100`
- **Method:** `GET`
- **Auth:** Bearer Token required

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Users retrieved successfully",
  "data": [
      { "id": "...", "email": "..." },
      { "id": "...", "email": "..." }
  ]
}
```

---

## 5. Delete User

Delete a user account.

**Permission:**
- Superusers can delete any user.
- Restaurant Owners/Managers can delete users within their restaurant.

- **Endpoint:** `/users/{user_id}`
- **Method:** `DELETE`
- **Auth:** Bearer Token required

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "User deleted successfully",
  "data": {
    "deleted_user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Error Codes
| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `USER_NOT_FOUND` | 404 | User ID does not exist. |
| `FORBIDDEN` | 403 | You do not have permission to delete this user. |
