# API Usage Examples

This document provides examples of how to use the FastAPI POS System API.

## Base URL
```
http://localhost:8000
```

## Standard Response Format

All API responses follow this format:

### Success
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "error": null
}
```

### Error
```json
{
  "success": false,
  "message": "Operation failed",
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "details": "Detailed error message"
  }
}
```

---

## 1. Health Check

### Root Endpoint
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "success": true,
  "message": "FastAPI POS System is running",
  "data": {
    "environment": "development",
    "version": "1.0.0"
  },
  "error": null
}
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## 2. User Registration

### Create a New User
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

**Success Response:**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "id": 1,
    "email": "john@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-16T10:30:00",
    "updated_at": "2025-12-16T10:30:00"
  },
  "error": null
}
```

**Error Response (Email exists):**
```json
{
  "success": false,
  "message": "User creation failed",
  "data": null,
  "error": {
    "code": "EMAIL_EXISTS",
    "details": "Email already exists"
  }
}
```

---

## 3. Authentication

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Success Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Login failed",
  "data": null,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "details": "Invalid email or password"
  }
}
```

### Refresh Access Token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "new_access_token_here",
    "token_type": "bearer"
  },
  "error": null
}
```

### Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer your_access_token_here"
```

---

## 4. User Management (Authenticated)

### Get Current User Info
```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer your_access_token_here"
```

**Response:**
```json
{
  "success": true,
  "message": "User retrieved successfully",
  "data": {
    "id": 1,
    "email": "john@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-16T10:30:00",
    "updated_at": "2025-12-16T10:30:00"
  },
  "error": null
}
```

### Get All Users (with pagination)
```bash
curl "http://localhost:8000/users?skip=0&limit=10" \
  -H "Authorization: Bearer your_access_token_here"
```

**Response:**
```json
{
  "success": true,
  "message": "Users retrieved successfully",
  "data": [
    {
      "id": 1,
      "email": "john@example.com",
      "username": "johndoe",
      "full_name": "John Doe",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-12-16T10:30:00",
      "updated_at": "2025-12-16T10:30:00"
    }
  ],
  "error": null
}
```

### Get User by ID
```bash
curl http://localhost:8000/users/1 \
  -H "Authorization: Bearer your_access_token_here"
```

### Update User
```bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Authorization: Bearer your_access_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Updated Doe",
    "email": "john.updated@example.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "User updated successfully",
  "data": {
    "id": 1,
    "email": "john.updated@example.com",
    "username": "johndoe",
    "full_name": "John Updated Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-16T10:30:00",
    "updated_at": "2025-12-16T10:35:00"
  },
  "error": null
}
```

### Delete User (Superuser only)
```bash
curl -X DELETE http://localhost:8000/users/1 \
  -H "Authorization: Bearer your_access_token_here"
```

**Response:**
```json
{
  "success": true,
  "message": "User deleted successfully",
  "data": {
    "deleted_user_id": 1
  },
  "error": null
}
```

---

## Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create a user
response = requests.post(f"{BASE_URL}/users", json={
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
})
print("Create User:", response.json())

# 2. Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "password123"
})
tokens = response.json()["data"]
access_token = tokens["access_token"]
print("Login successful, access token:", access_token[:20] + "...")

# 3. Get current user info
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print("Current User:", response.json())

# 4. Get all users
response = requests.get(f"{BASE_URL}/users?skip=0&limit=10", headers=headers)
print("All Users:", response.json())

# 5. Update user
response = requests.put(
    f"{BASE_URL}/users/1",
    headers=headers,
    json={"full_name": "Updated Name"}
)
print("Update User:", response.json())
```

---

## JavaScript Example

```javascript
const BASE_URL = "http://localhost:8000";

// 1. Create a user
async function createUser() {
  const response = await fetch(`${BASE_URL}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "test@example.com",
      username: "testuser",
      password: "password123",
      full_name: "Test User"
    })
  });
  const data = await response.json();
  console.log("Create User:", data);
}

// 2. Login
async function login() {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "test@example.com",
      password: "password123"
    })
  });
  const data = await response.json();
  return data.data.access_token;
}

// 3. Get current user
async function getCurrentUser(accessToken) {
  const response = await fetch(`${BASE_URL}/users/me`, {
    headers: { "Authorization": `Bearer ${accessToken}` }
  });
  const data = await response.json();
  console.log("Current User:", data);
}

// Usage
(async () => {
  await createUser();
  const token = await login();
  await getCurrentUser(token);
})();
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `EMAIL_EXISTS` | Email already registered |
| `USERNAME_EXISTS` | Username already taken |
| `INVALID_CREDENTIALS` | Invalid email or password |
| `INVALID_REFRESH_TOKEN` | Refresh token is invalid or expired |
| `USER_NOT_FOUND` | User does not exist |
| `FORBIDDEN` | Insufficient permissions |
| `VALIDATION_ERROR` | Request validation failed |
| `INTEGRITY_ERROR` | Database integrity constraint violated |
| `INTERNAL_ERROR` | Internal server error |

---

## Authentication Flow

1. **Register**: `POST /users` - Create a new user account
2. **Login**: `POST /auth/login` - Get access and refresh tokens
3. **Use API**: Include `Authorization: Bearer {access_token}` header
4. **Refresh**: `POST /auth/refresh` - Get new access token when expired
5. **Logout**: `POST /auth/logout` - Discard tokens client-side

---

## Token Expiration

- **Access Token**: 30 minutes (default)
- **Refresh Token**: 7 days (default)

When access token expires, use the refresh token to get a new access token without requiring the user to login again.
