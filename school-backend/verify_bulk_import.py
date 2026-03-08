import requests
import json
import os

BASE_URL = "http://localhost:8000/api"
CSV_FILE = "students.csv"
TENANT_HOST = "www.sunrisepublicschool.edu.in"
# We need to authenticate as School Admin
# Let's use the 'school' user we reset earlier (role: SCHOOL_ADMIN)
USERNAME = "school"
PASSWORD = "school123"

def get_token():
    try:
        response = requests.post(f"{BASE_URL}/users/auth/login/", json={"username": USERNAME, "password": PASSWORD})
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"❌ Login Failed: {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
    return None

def verify_import():
    print("🚀 Starting Bulk Import Verification...")
    
    token = get_token()
    if not token:
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Host": TENANT_HOST # Ensure we hit the correct tenant structure if applicable
        # Actually our utils uses 'request.user.school_id' which is central.
        # But if we use tenant routing middleware, we might need Host header.
        # Let's try without Host header first, relying on SchoolID in User.
    }
    
    # But wait, our middleware routes DB based on Host header?
    # correct. If we don't provide Host, we might be in 'default' (public) DB.
    # The users are in 'default' DB (public schema).
    # But the Student/Parent profiles are in Tenant DB?
    # Let's check logic:
    # students/utils.py:
    #   User.objects.create -> Shared/Public DB (users app)
    #   Parent.objects.get_or_create -> Student/Parent models are in Tenant DB?
    #   Let's check students/models.py
    
    # If Student/Parent models are tenant-specific, we MUST provide Host header to route to correct DB.
    # Otherwise they will be created in 'default' DB which might not be intended for School Data.
    
    # headers["Host"] = TENANT_HOST

    try:
        with open(CSV_FILE, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/students/upload-csv/", headers=headers, files=files)
            
            if response.status_code == 200:
                print("✅ Import Successful!")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"❌ Import Failed: {response.status_code}")
                print(response.text)
                
    except FileNotFoundError:
        print(f"❌ File {CSV_FILE} not found.")

if __name__ == "__main__":
    verify_import()
