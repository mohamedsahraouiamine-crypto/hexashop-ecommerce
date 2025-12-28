import requests
import json

BASE_URL = "http://127.0.0.1:5000"
ADMIN_USERNAME = "amimedne0229"
ADMIN_PASSWORD = "#/%/#med_22-&-am/%/ine_09-&-haytham2001#/%/#"

# Create a session to handle cookies (like your browser does)
session = requests.Session()

print("1. Attempting to log in via /api/admin/login...")
login_data = {
    "username": ADMIN_USERNAME,
    "password": ADMIN_PASSWORD
}

login_response = session.post(
    f"{BASE_URL}/api/admin/login",
    json=login_data,
    headers={'Content-Type': 'application/json'}
)

print(f"   Status Code: {login_response.status_code}")
print(f"   Response Body: {login_response.text}")

if login_response.status_code == 200:
    print("\n✅ Login successful!")
    login_result = login_response.json()
    csrf_token = login_result.get('csrf_token')
    print(f"   CSRF Token Received: {csrf_token}")
    
    # Now, use the same session to check if we're authenticated
    print("\n2. Checking authentication status via /api/admin/check-auth...")
    auth_check = session.get(f"{BASE_URL}/api/admin/check-auth")
    print(f"   Status Code: {auth_check.status_code}")
    print(f"   Response: {auth_check.text}")
    
else:
    print("\n❌ Login failed. This indicates a problem with the backend login logic.")