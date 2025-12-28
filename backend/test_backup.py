import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "amimedne0229"
ADMIN_PASSWORD = "#/%/#med_22-&-am/%/ine_09-&-haytham2001#/%/#"  # Replace with your actual password

def test_backup_system():
    session = requests.Session()
    
    # 1. Login first to get session and CSRF token
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    print("🔐 Logging in...")
    login_response = session.post(
        f"{BASE_URL}/api/admin/login", 
        json=login_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_result = login_response.json()
    print("✅ Login successful!")
    
    # Get CSRF token from login response
    csrf_token = login_result.get('csrf_token', '')
    print(f"🔑 CSRF Token: {csrf_token}")
    
    # 2. Check authentication
    print("🔍 Checking authentication...")
    auth_response = session.get(f"{BASE_URL}/api/admin/check-auth")
    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        print(f"✅ Authenticated as: {auth_data.get('username', 'Unknown')}")
    else:
        print("❌ Not authenticated")
        return
    
    # 3. Create manual backup with CSRF token
    print("🗄️ Creating manual backup...")
    backup_response = session.post(
        f"{BASE_URL}/api/admin/backup/create",
        headers={
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        }
    )
    
    if backup_response.status_code == 200:
        backup_data = backup_response.json()
        print(f"✅ Backup created successfully!")
        print(f"📁 File: {backup_data.get('file', 'Unknown')}")
        print(f"💾 Size: {backup_data.get('size', 0)} bytes")
    else:
        print(f"❌ Backup failed with status {backup_response.status_code}: {backup_response.text}")
    
    # 4. List backups
    print("📋 Listing all backups...")
    list_response = session.get(f"{BASE_URL}/api/admin/backup/list")
    
    if list_response.status_code == 200:
        backups_data = list_response.json()
        backups = backups_data.get('backups', [])
        print(f"📊 Found {len(backups)} backups:")
        for backup in backups:
            print(f"  - {backup['filename']} ({backup['size']} bytes) - {backup['type']}")
    else:
        print(f"❌ List backups failed: {list_response.text}")
    
    # 5. Check backup folder directly
    print("📁 Checking backup folder directly...")
    backup_dir = 'backups'
    if os.path.exists(backup_dir):
        backup_files = os.listdir(backup_dir)
        print(f"📁 Backup folder contains {len(backup_files)} files:")
        for file in backup_files:
            file_path = os.path.join(backup_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file} ({file_size} bytes)")
    else:
        print("❌ Backup folder doesn't exist")

if __name__ == "__main__":
    test_backup_system()