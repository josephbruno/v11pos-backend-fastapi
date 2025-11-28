"""
Test what the server's email service actually sees
"""
import requests

# Add a temporary debug endpoint
print("Testing email service in running server...")

# Call the actual API
response = requests.post(
    "http://localhost:8000/api/v1/auth/forgot-password",
    json={"email": "brunoakp95@gmail.com"}
)

print(f"API Response: {response.status_code}")
print(f"Response: {response.json()}")

# Now check server logs or output
print("\nThe issue is likely:")
print("1. Server started BEFORE .env was updated with SMTP credentials")
print("2. Server cached the old email_service module")
print("3. --reload flag doesn't reload imported modules at module level")

print("\nSOLUTION: Manually restart the server")
print("  1. Find server: ps aux | grep uvicorn")
print("  2. Kill it: sudo kill -9 <PID>")
print("  3. Restart: cd /home/brunodoss/docs/pos/pos/pos-fastapi && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
