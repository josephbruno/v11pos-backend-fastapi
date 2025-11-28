# Login API Integration Documentation

## Authentication Endpoint

### POST `/api/v1/auth/login`

Authenticate users and receive an access token for subsequent API requests.

---

## Request

### Headers
```
Content-Type: application/x-www-form-urlencoded
```

### Request Body (Form Data)
```
username=manager@restaurant.com&password=Manager123!
```

#### Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | ✅ Yes | User's email address (field name is "username" but accepts email) |
| password | string | ✅ Yes | User's password |

**Note**: The endpoint uses OAuth2 password flow, so it expects **form data**, not JSON. The field is named `username` but you should pass the user's email address.

---

## Response

### Success Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1440,
  "user": {
    "id": "30953073-d6c1-42c6-a969-d6679706e04a",
    "name": "Manager John",
    "email": "manager@restaurant.com",
    "phone": "1234567891",
    "role": "manager",
    "status": "active",
    "avatar": null,
    "permissions": [],
    "join_date": "2025-11-23",
    "created_at": "2025-11-23T07:58:11",
    "updated_at": "2025-11-23T07:58:11"
  }
}
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT token for authentication |
| token_type | string | Always "bearer" |
| expires_in | integer | Token expiration time in minutes (default: 1440 = 24 hours) |
| user | object | User information object |
| user.id | string | Unique user identifier (UUID) |
| user.name | string | User's full name |
| user.email | string | User's email address |
| user.phone | string | User's phone number |
| user.role | string | User role: "admin", "manager", "staff", "cashier" |
| user.status | string | Account status: "active", "inactive", "suspended" |
| user.avatar | string\|null | URL to user's profile picture |
| user.permissions | array | List of special permissions |
| user.join_date | string | Date user joined (YYYY-MM-DD) |
| user.created_at | string | Account creation timestamp |
| user.updated_at | string | Last update timestamp |

---

## Error Responses

### Invalid Credentials (401 Unauthorized)
```json
{
  "detail": "Incorrect email or password"
}
```

### Inactive/Suspended Account (403 Forbidden)
```json
{
  "detail": "Account is inactive"
}
```

### Validation Error (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Sample Login Accounts

### Manager Account
- **Email**: `manager@restaurant.com`
- **Password**: `Manager123!`
- **Role**: manager
- **Permissions**: Full access to management features

### Cashier Account
- **Email**: `cashier@restaurant.com`
- **Password**: `Cashier123!`
- **Role**: cashier
- **Permissions**: Point of sale operations

### Staff Account
- **Email**: `staff@restaurant.com`
- **Password**: `Staff123!`
- **Role**: staff
- **Permissions**: Order management, customer service

### Admin Account (Default)
- **Email**: `admin@restaurant.com`
- **Password**: `Admin123!`
- **Role**: admin
- **Permissions**: System administration

---

## Integration Examples

### JavaScript (Fetch API)

```javascript
async function login(email, password) {
  try {
    // Create form data (OAuth2 expects form data, not JSON)
    const formData = new URLSearchParams();
    formData.append('username', email);  // OAuth2 uses "username" field
    formData.append('password', password);

    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    
    // Store token for subsequent requests
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

// Usage
login('manager@restaurant.com', 'Manager123!')
  .then(data => {
    console.log('Logged in as:', data.user.name);
    console.log('Role:', data.user.role);
  })
  .catch(error => {
    console.error('Failed to login:', error);
  });
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

async function login(email, password) {
  try {
    // Create form data for OAuth2
    const formData = new URLSearchParams();
    formData.append('username', email);  // OAuth2 uses "username" field
    formData.append('password', password);

    const response = await axios.post(
      'http://localhost:8000/api/v1/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    const { access_token, user } = response.data;
    
    // Store token
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(user));
    
    // Set default authorization header for future requests
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error
      throw new Error(error.response.data.detail || 'Login failed');
    } else {
      // Network error
      throw new Error('Network error. Please check your connection.');
    }
  }
}

// Usage
login('manager@restaurant.com', 'Manager123!')
  .then(data => console.log('Login successful:', data))
  .catch(error => console.error('Login failed:', error));
```

### Python (Requests)

```python
import requests

def login(email: str, password: str):
    url = "http://localhost:8000/api/v1/auth/login"
    
    # OAuth2 expects form data, not JSON
    payload = {
        "username": email,  # OAuth2 uses "username" field
        "password": password
    }
    
    try:
        response = requests.post(
            url, 
            data=payload,  # Use 'data' for form data, not 'json'
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Store token for subsequent requests
        access_token = data['access_token']
        user = data['user']
        
        print(f"Logged in as: {user['name']}")
        print(f"Role: {user['role']}")
        
        return data
        
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get('detail', 'Login failed')
        print(f"Login error: {error_detail}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        raise

# Usage
try:
    result = login('manager@restaurant.com', 'Manager123!')
    access_token = result['access_token']
except Exception as e:
    print(f"Failed to login: {e}")
```

### cURL

```bash
# Login request (form data)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager@restaurant.com&password=Manager123!"

# Pretty print response
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager@restaurant.com&password=Manager123!" \
  | python3 -m json.tool
```

---

## Using the Access Token

After successful login, include the access token in the `Authorization` header for all subsequent API requests:

### Header Format
```
Authorization: Bearer <access_token>
```

### Example: Get Products with Authentication

```javascript
// JavaScript
const token = localStorage.getItem('access_token');

fetch('http://localhost:8000/api/v1/products/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

```python
# Python
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.get(
    'http://localhost:8000/api/v1/products/',
    headers=headers
)
```

```bash
# cURL
TOKEN="your_access_token_here"

curl -X GET "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Token Management

### Token Expiration
- Default expiration: **24 hours** (1440 minutes)
- After expiration, users must login again
- Check `expires_in` field in login response

### Storing Tokens Securely

#### Web Applications
```javascript
// ✅ Good: Use localStorage for web apps
localStorage.setItem('access_token', token);

// ❌ Avoid: Storing in cookies without httpOnly flag
// ❌ Avoid: Storing in plain text files
```

#### Mobile Applications
- Use secure storage mechanisms (Keychain for iOS, KeyStore for Android)
- Never store tokens in plain SharedPreferences or UserDefaults

### Refreshing Authentication
```javascript
function isTokenExpired() {
  const loginTime = localStorage.getItem('login_time');
  const expiresIn = 1440 * 60 * 1000; // 24 hours in milliseconds
  
  return Date.now() - loginTime > expiresIn;
}

async function ensureAuthenticated() {
  if (isTokenExpired()) {
    // Redirect to login page or show login modal
    window.location.href = '/login';
  }
}
```

---

## Error Handling Best Practices

### Client-Side Error Handling

```javascript
async function handleLogin(email, password) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      switch (response.status) {
        case 401:
          throw new Error('Invalid email or password');
        case 403:
          throw new Error('Your account is inactive. Please contact support.');
        case 422:
          throw new Error('Please enter valid email and password');
        case 500:
          throw new Error('Server error. Please try again later.');
        default:
          throw new Error('An unexpected error occurred');
      }
    }

    return await response.json();
  } catch (error) {
    // Show error to user
    console.error('Login failed:', error.message);
    throw error;
  }
}
```

---

## Security Considerations

### 1. Always Use HTTPS in Production
```javascript
// ✅ Production
const API_URL = 'https://api.yourrestaurant.com';

// ⚠️ Development only
const API_URL = 'http://localhost:8000';
```

### 2. Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

### 3. Rate Limiting
- Implement rate limiting on login attempts
- Show captcha after multiple failed attempts

### 4. Logout Functionality
```javascript
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}
```

---

## Testing the API

### Test with cURL
```bash
# Test successful login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@restaurant.com",
    "password": "Manager123!"
  }'

# Test invalid credentials
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wrong@email.com",
    "password": "wrongpassword"
  }'

# Test missing fields
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@restaurant.com"
  }'
```

---

## User Roles and Permissions

### Role Hierarchy
1. **admin** - Full system access
   - User management
   - System settings
   - All features

2. **manager** - Management features
   - Reports and analytics
   - Staff management
   - Product management
   - All POS features

3. **staff** - Service operations
   - Order management
   - Table management
   - Customer service

4. **cashier** - Point of sale
   - Create orders
   - Process payments
   - Basic customer lookup

### Checking User Role
```javascript
function checkPermission(userRole, requiredRole) {
  const roleHierarchy = {
    'admin': 4,
    'manager': 3,
    'staff': 2,
    'cashier': 1
  };
  
  return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
}

// Usage
const user = JSON.parse(localStorage.getItem('user'));
if (checkPermission(user.role, 'manager')) {
  // Show manager features
}
```

---

## API Base URL

- **Development**: `http://localhost:8000`
- **Production**: Update to your production URL
- **Docker**: `http://localhost:8000` (mapped from container)

---

## Support

For issues or questions:
1. Check error response messages
2. Verify credentials are correct
3. Ensure API server is running
4. Check network connectivity
5. Review server logs for detailed error information

---

## Next Steps

After successful login:
1. ✅ Store the access token securely
2. ✅ Include token in Authorization header for protected endpoints
3. ✅ Handle token expiration gracefully
4. ✅ Implement logout functionality
5. ✅ Check user role for feature access control

See other API documentation files:
- `API_REFERENCE.md` - Complete API documentation
- `API_ENDPOINTS_LIST.md` - All available endpoints
- `QUICK_REFERENCE.md` - Quick start guide
