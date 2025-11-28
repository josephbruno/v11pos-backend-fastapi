# 🔐 Forgot Password API Documentation

## Overview

Complete password reset flow using email-based OTP (One-Time Password) for the Restaurant POS system.

---

## 📋 Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Flow Diagram](#flow-diagram)
3. [Implementation Details](#implementation-details)
4. [Integration Examples](#integration-examples)
5. [Email Templates](#email-templates)
6. [Security Features](#security-features)
7. [Testing](#testing)

---

## 🚀 API Endpoints

### Base URL
```
http://localhost:8000/api/v1/auth
```

### 1. Request Password Reset (Send OTP)

**Endpoint**: `POST /forgot-password`

**Description**: Sends a 6-digit OTP to the user's email address.

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "If the email exists, an OTP has been sent",
  "data": {
    "email": "user@example.com",
    "expires_in": 600
  }
}
```

**Notes**:
- OTP expires in 10 minutes
- Previous unused OTPs are automatically invalidated
- Response doesn't reveal if email exists (security measure)

---

### 2. Verify OTP (Optional)

**Endpoint**: `POST /verify-otp`

**Description**: Verify OTP without resetting password (useful for UI feedback).

**Request Body**:
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "OTP verified successfully",
  "data": {
    "email": "user@example.com",
    "valid": true
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Invalid or expired OTP"
}
```

---

### 3. Reset Password with OTP

**Endpoint**: `POST /reset-password`

**Description**: Reset password using verified OTP.

**Request Body**:
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewSecurePassword123!"
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "Password reset successfully",
  "data": {
    "email": "user@example.com"
  }
}
```

**Error Responses**:

*Invalid/Expired OTP* (400 Bad Request):
```json
{
  "detail": "Invalid or expired OTP"
}
```

*User Not Found* (404 Not Found):
```json
{
  "detail": "User not found"
}
```

**Notes**:
- OTP is marked as used after successful reset
- Confirmation email is sent after password reset
- User can login with new password immediately

---

## 🔄 Flow Diagram

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ 1. Enter email
       ▼
┌─────────────────────────┐
│  POST /forgot-password  │
└──────┬──────────────────┘
       │
       │ 2. Generate OTP
       │    Store in DB
       │    Send Email
       ▼
┌─────────────────────────┐
│  📧 Email with OTP      │
│  Valid for 10 minutes   │
└──────┬──────────────────┘
       │
       │ 3. User receives OTP
       ▼
┌─────────────────────────┐
│                         │
│  POST /verify-otp       │ ← Verify before reset
└──────┬──────────────────┘
       │
       │ 4. Enter OTP + New Password
       ▼
┌─────────────────────────┐
│  POST /reset-password   │
└──────┬──────────────────┘
       │
       │ 5. Validate OTP
       │    Update Password
       │    Mark OTP as used
       │    Send Confirmation
       ▼
┌─────────────────────────┐
│  ✅ Password Reset      │
│  📧 Confirmation Email  │
└─────────────────────────┘
```

---

## 💻 Integration Examples

### JavaScript (Fetch API)

```javascript
// Step 1: Request OTP
async function requestPasswordReset(email) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/forgot-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('OTP sent to email');
      return result;
    } else {
      throw new Error(result.detail || 'Failed to send OTP');
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Step 2: Verify OTP (Optional)
async function verifyOTP(email, otp) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/verify-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, otp })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      return true;
    } else {
      throw new Error('Invalid OTP');
    }
  } catch (error) {
    console.error('Error:', error);
    return false;
  }
}

// Step 3: Reset Password
async function resetPassword(email, otp, newPassword) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        otp,
        new_password: newPassword
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('Password reset successfully!');
      return result;
    } else {
      throw new Error(result.detail || 'Failed to reset password');
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Complete flow
async function handleForgotPassword() {
  const email = prompt('Enter your email:');
  
  // Step 1: Request OTP
  await requestPasswordReset(email);
  alert('OTP sent to your email!');
  
  const otp = prompt('Enter the 6-digit OTP from your email:');
  
  // Step 2: Verify OTP (optional but recommended)
  const isValid = await verifyOTP(email, otp);
  if (!isValid) {
    alert('Invalid OTP!');
    return;
  }
  
  const newPassword = prompt('Enter your new password:');
  
  // Step 3: Reset password
  await resetPassword(email, otp, newPassword);
  alert('Password reset successfully! You can now login.');
}
```

---

### React Component

```jsx
import React, { useState } from 'react';

function ForgotPasswordFlow() {
  const [step, setStep] = useState(1); // 1: email, 2: otp, 3: success
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      if (response.ok) {
        setStep(2);
      } else {
        setError('Failed to send OTP');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          otp,
          new_password: newPassword
        })
      });
      
      if (response.ok) {
        setStep(3);
      } else {
        const result = await response.json();
        setError(result.detail || 'Failed to reset password');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-password-container">
      {step === 1 && (
        <form onSubmit={handleRequestOTP}>
          <h2>Forgot Password</h2>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}

      {step === 2 && (
        <form onSubmit={handleResetPassword}>
          <h2>Reset Password</h2>
          <p>OTP sent to {email}</p>
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          <input
            type="password"
            placeholder="Enter new password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            minLength={6}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}

      {step === 3 && (
        <div className="success">
          <h2>✅ Password Reset Successful!</h2>
          <p>You can now login with your new password.</p>
          <button onClick={() => window.location.href = '/login'}>
            Go to Login
          </button>
        </div>
      )}
    </div>
  );
}

export default ForgotPasswordFlow;
```

---

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/auth"

def forgot_password(email: str):
    """Request password reset OTP"""
    response = requests.post(
        f"{BASE_URL}/forgot-password",
        json={"email": email}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"OTP sent to {email}")
        print(f"Expires in: {result['data']['expires_in']} seconds")
        return True
    else:
        print(f"Error: {response.json().get('detail')}")
        return False

def verify_otp(email: str, otp: str):
    """Verify OTP (optional step)"""
    response = requests.post(
        f"{BASE_URL}/verify-otp",
        json={"email": email, "otp": otp}
    )
    
    return response.status_code == 200

def reset_password(email: str, otp: str, new_password: str):
    """Reset password with OTP"""
    response = requests.post(
        f"{BASE_URL}/reset-password",
        json={
            "email": email,
            "otp": otp,
            "new_password": new_password
        }
    )
    
    if response.status_code == 200:
        print("Password reset successfully!")
        return True
    else:
        print(f"Error: {response.json().get('detail')}")
        return False

# Usage
if __name__ == "__main__":
    email = "user@example.com"
    
    # Step 1: Request OTP
    if forgot_password(email):
        # Step 2: Get OTP from user
        otp = input("Enter OTP from email: ")
        
        # Step 3: Verify OTP (optional)
        if verify_otp(email, otp):
            print("OTP verified!")
            
            # Step 4: Reset password
            new_password = input("Enter new password: ")
            reset_password(email, otp, new_password)
```

---

### cURL Examples

```bash
# Step 1: Request OTP
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@restaurant.com"}'

# Response:
# {
#   "status": "success",
#   "message": "If the email exists, an OTP has been sent",
#   "data": {
#     "email": "admin@restaurant.com",
#     "expires_in": 600
#   }
# }

# Step 2: Verify OTP (Optional)
curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@restaurant.com", "otp": "123456"}'

# Step 3: Reset Password
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@restaurant.com",
    "otp": "123456",
    "new_password": "NewSecurePassword123!"
  }'

# Response:
# {
#   "status": "success",
#   "message": "Password reset successfully",
#   "data": {
#     "email": "admin@restaurant.com"
#   }
# }
```

---

## 📧 Email Templates

### OTP Email

The system sends a beautifully formatted HTML email with the following features:

**Email Subject**: "Password Reset OTP - Restaurant POS"

**Content**:
- User's name personalization
- Large, prominent OTP display
- 10-minute expiration notice
- Security warning
- Professional branding

**Email Preview**:
```
┌────────────────────────────────────┐
│   🔐 Password Reset                │
├────────────────────────────────────┤
│  Hello Admin User,                 │
│                                     │
│  Your OTP is:                       │
│                                     │
│  ┌──────────────┐                  │
│  │   123456     │                  │
│  └──────────────┘                  │
│                                     │
│  Expires in 10 minutes              │
│                                     │
│  ⚠️ Security Notice:                │
│  If you didn't request this,        │
│  please ignore or contact support.  │
└────────────────────────────────────┘
```

### Confirmation Email

**Email Subject**: "Password Reset Successful - Restaurant POS"

**Content**:
- Success notification
- Security reminder
- Login instructions

---

## 🔒 Security Features

### 1. **OTP Expiration**
- OTPs expire after 10 minutes
- Expired OTPs cannot be used
- Automatic cleanup possible

### 2. **Single Use OTPs**
- Each OTP can only be used once
- Marked as `is_used=true` after successful reset
- Prevents replay attacks

### 3. **Previous Token Invalidation**
- New OTP request invalidates all previous unused OTPs
- Prevents OTP accumulation

### 4. **Email Enumeration Protection**
- Response doesn't reveal if email exists
- Same response for existing and non-existing emails
- Prevents user enumeration attacks

### 5. **Account Status Validation**
- Only active accounts can reset passwords
- Inactive/suspended accounts are rejected

### 6. **Secure Password Storage**
- Passwords hashed with PBKDF2-SHA256
- Never stored in plain text
- Automatic password strength validation (min 6 characters)

### 7. **Rate Limiting** (Recommended)
- Implement rate limiting on forgot-password endpoint
- Prevent brute force OTP attempts
- Example: 5 requests per hour per IP

---

## 🧪 Testing

### Test Accounts

```
Email: admin@restaurant.com
Password: Admin123!

Email: manager@restaurant.com
Password: Manager123!

Email: cashier@restaurant.com
Password: Cashier123!

Email: staff@restaurant.com
Password: Staff123!
```

### Complete Test Flow

```bash
#!/bin/bash

EMAIL="admin@restaurant.com"

echo "=== Testing Forgot Password Flow ==="
echo ""

# Step 1: Request OTP
echo "1. Requesting OTP for $EMAIL..."
curl -s -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\"}" \
  | python3 -m json.tool

echo ""
echo "2. Check your email or database for OTP"
echo "   Run: SELECT otp FROM password_reset_tokens WHERE email='$EMAIL' AND is_used=false;"
echo ""

read -p "Enter OTP: " OTP

# Step 2: Verify OTP
echo ""
echo "3. Verifying OTP..."
curl -s -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"otp\": \"$OTP\"}" \
  | python3 -m json.tool

# Step 3: Reset Password
echo ""
echo "4. Resetting password..."
curl -s -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"otp\": \"$OTP\", \"new_password\": \"NewPassword123!\"}" \
  | python3 -m json.tool

# Step 4: Test Login
echo ""
echo "5. Testing login with new password..."
curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=$EMAIL&password=NewPassword123!" \
  | python3 -c "import sys, json; r=json.loads(sys.stdin.read()); print('✓ Login successful!' if 'access_token' in r else '✗ Login failed')"

echo ""
echo "=== Test Complete ==="
```

### Get OTP from Database

```python
from app.database import SessionLocal
from app.models.user import PasswordResetToken
from datetime import datetime

db = SessionLocal()
token = db.query(PasswordResetToken).filter(
    PasswordResetToken.email == 'admin@restaurant.com',
    PasswordResetToken.is_used == False,
    PasswordResetToken.expires_at > datetime.utcnow()
).first()

if token:
    print(f"OTP: {token.otp}")
else:
    print("No valid OTP found")
```

---

## 📝 Database Schema

### password_reset_tokens Table

```sql
CREATE TABLE password_reset_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_email (email),
    INDEX idx_user_id (user_id)
);
```

---

## 🔧 SMTP Configuration (Production)

For production, configure SMTP environment variables:

```bash
# .env file
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@yourcompany.com
SENDER_NAME=Restaurant POS
```

### Gmail App Password Setup

1. Enable 2-Factor Authentication
2. Go to Google Account → Security
3. Generate App Password
4. Use app password in SMTP_PASSWORD

---

## ⚠️ Common Errors

### "Invalid or expired OTP"
- **Cause**: OTP expired (>10 minutes) or already used
- **Solution**: Request new OTP

### "Account is not active"
- **Cause**: User account is suspended/inactive
- **Solution**: Contact administrator

### "Email not configured"
- **Development**: OTP printed to console/logs
- **Production**: Configure SMTP settings

---

## 📊 Summary

✅ **3 API Endpoints**: forgot-password, verify-otp, reset-password  
✅ **Email OTP**: 6-digit code, 10-minute expiration  
✅ **Security**: Single-use OTPs, email enumeration protection  
✅ **Email Templates**: Professional HTML emails  
✅ **Database**: password_reset_tokens table created  
✅ **Testing**: Complete flow tested and verified  

**Ready to integrate!** All endpoints are working and documented.
