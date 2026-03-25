# Test script for login endpoint with both JSON and form-encoded data
# PowerShell version for Windows

$BASE_URL = "http://localhost:8000/api/v1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "POS Backend API - Login Endpoint Tests" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Base URL: $BASE_URL`n" -ForegroundColor White

# Test 1: JSON Login
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "TEST 1: Login with JSON payload" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "Request:"
Write-Host "  URL: $BASE_URL/auth/login"
Write-Host "  Content-Type: application/json"
Write-Host '  Body: {"email": "superadmin@restaurant.com", "password": "Super@123"}'
Write-Host "`nResponse:"

try {
    $jsonBody = @{
        email = "superadmin@restaurant.com"
        password = "Super@123"
    } | ConvertTo-Json

    $response1 = Invoke-RestMethod -Uri "$BASE_URL/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Write-Host ($response1 | ConvertTo-Json -Depth 10) -ForegroundColor Green
    
    if ($response1.success) {
        Write-Host "`n✅ JSON Login Test: PASSED" -ForegroundColor Green
        $accessToken = $response1.data.access_token
    } else {
        Write-Host "`n❌ JSON Login Test: FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host "`n❌ JSON Login Test: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Form-Encoded Login
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "TEST 2: Login with Form-Encoded payload" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "Request:"
Write-Host "  URL: $BASE_URL/auth/login"
Write-Host "  Content-Type: application/x-www-form-urlencoded"
Write-Host "  Body: email=superadmin@restaurant.com&password=Super@123"
Write-Host "`nResponse:"

try {
    $formBody = "email=superadmin@restaurant.com&password=Super@123"

    $response2 = Invoke-RestMethod -Uri "$BASE_URL/auth/login" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $formBody

    Write-Host ($response2 | ConvertTo-Json -Depth 10) -ForegroundColor Green
    
    if ($response2.success) {
        Write-Host "`n✅ Form Login Test: PASSED" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Form Login Test: FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host "`n❌ Form Login Test: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Authenticated Endpoint
if ($accessToken) {
    Write-Host "==========================================" -ForegroundColor Yellow
    Write-Host "TEST 3: Testing Authenticated Endpoint" -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor Yellow
    Write-Host "Using access token from JSON login..."
    Write-Host "Token: $($accessToken.Substring(0, [Math]::Min(50, $accessToken.Length)))..."
    Write-Host "`nTesting /users/me endpoint:"

    try {
        $headers = @{
            "Authorization" = "Bearer $accessToken"
        }

        $response3 = Invoke-RestMethod -Uri "$BASE_URL/users/me" `
            -Method Get `
            -Headers $headers `
            -ContentType "application/json"

        Write-Host ($response3 | ConvertTo-Json -Depth 10) -ForegroundColor Green
        
        if ($response3.success) {
            Write-Host "`n✅ Authenticated Endpoint Test: PASSED" -ForegroundColor Green
        } else {
            Write-Host "`n❌ Authenticated Endpoint Test: FAILED" -ForegroundColor Red
        }
    } catch {
        Write-Host "`n❌ Authenticated Endpoint Test: FAILED - $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Skipping authenticated endpoint test - no token available" -ForegroundColor Yellow
}

Write-Host ""

# Test 4: Error Response Format
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "TEST 4: Error Response Format" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "Testing with invalid credentials..."

try {
    $invalidBody = @{
        email = "invalid@test.com"
        password = "wrongpassword"
    } | ConvertTo-Json

    $response4 = Invoke-RestMethod -Uri "$BASE_URL/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $invalidBody

    Write-Host ($response4 | ConvertTo-Json -Depth 10) -ForegroundColor Cyan
    
    $requiredFields = @("success", "status_code", "message", "data", "error", "timestamp")
    $missingFields = $requiredFields | Where-Object { -not $response4.PSObject.Properties.Name.Contains($_) }
    
    if ($missingFields.Count -eq 0) {
        Write-Host "`n✅ Response Format Test: PASSED" -ForegroundColor Green
        Write-Host "   - All required fields present: $($requiredFields -join ', ')"
    } else {
        Write-Host "`n❌ Response Format Test: FAILED - Missing fields: $($missingFields -join ', ')" -ForegroundColor Red
    }
} catch {
    # For error responses, PowerShell throws an exception, so we need to parse it
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd() | ConvertFrom-Json
        Write-Host ($responseBody | ConvertTo-Json -Depth 10) -ForegroundColor Cyan
        
        $requiredFields = @("success", "status_code", "message", "data", "error", "timestamp")
        $missingFields = $requiredFields | Where-Object { -not $responseBody.PSObject.Properties.Name.Contains($_) }
        
        if ($missingFields.Count -eq 0) {
            Write-Host "`n✅ Response Format Test: PASSED" -ForegroundColor Green
            Write-Host "   - All required fields present: $($requiredFields -join ', ')"
        } else {
            Write-Host "`n❌ Response Format Test: FAILED - Missing fields: $($missingFields -join ', ')" -ForegroundColor Red
        }
    } else {
        Write-Host "`n❌ Response Format Test: FAILED - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "All Tests Completed" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
