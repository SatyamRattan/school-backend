import requests
import json
import random

BASE_URL = "http://localhost:8000/api"
TENANT_HOST = "www.sunrisepublicschool.edu.in"
TENANT_HEADERS = {"Host": TENANT_HOST}

def get_token(username, password):
    try:
        response = requests.post(f"{BASE_URL}/users/auth/login/", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json().get('access')
    except:
        return None
    return None

def register_user(username, password, role, school_id=None):
    # This might fail if public registration is not open for these roles, 
    # but let's assume we can create them via Admin or similar.
    # Actually, verify_all_apis uses public registration which defaults to STUDENT.
    # To get a Teacher, we need Admin to create it.
    pass

def test_rbac():
    print("🚀 Starting RBAC Verification...")
    
    # 1. Login as Super Admin (Role: SUPER_ADMIN)
    admin_token = get_token("admin", "admin123")
    if not admin_token:
        print("❌ Admin Login Failed")
        return

    admin_headers = TENANT_HEADERS.copy()
    admin_headers['Authorization'] = f"Bearer {admin_token}"

    # 2. Setup: Create a Teacher User (Role: TEACHER)
    print("\n--- 👤 Creating Teacher User (as Admin) ---")
    teacher_username = f"teacher_{random.randint(100,999)}"
    teacher_password = "password123"
    teacher_email = f"{teacher_username}@school.com"
    
    payload = {
        "username": teacher_username,
        "email": teacher_email,
        "password": teacher_password,
        "first_name": "Teacher",
        "last_name": "One",
        "role": "TEACHER"
    }
    
    # We use the UserViewSet to create user (Admin only)
    response = requests.post(f"{BASE_URL}/users/accounts/", json=payload, headers=admin_headers)
    if response.status_code == 201:
        print(f"✅ Teacher User Created: {teacher_username}")
    else:
        print(f"❌ Teacher User Creation Failed: {response.status_code} {response.text}")
        # Try to proceed if user exists or login
        pass

    teacher_token = get_token(teacher_username, teacher_password)
    
    # 3. Setup: Create a Student User (Role: STUDENT)
    print("\n--- 🎓 Creating Student User ---")
    student_username = f"student_{random.randint(100,999)}"
    student_password = "password123"
    
    # Public registration (defaults to STUDENT)
    reg_payload = {
        "username": student_username,
        "email": f"{student_username}@school.com",
        "password": student_password
    }
    requests.post(f"{BASE_URL}/users/auth/register/", json=reg_payload)
    student_token = get_token(student_username, student_password)
    
    if not student_token:
        print("❌ Student Login Failed")
        return

    # --- Scenario 1: Students App (IsSchoolStaff) ---
    print("\n--- 🧪 Scenario 1: Modify Students App ---")
    
    # A. Admin tries to create Dummy Student Profile
    print("👉 Admin attempting to create Student Profile...")
    payload = {
        "first_name": "Dummy",
        "last_name": "Student",
        "admission_number": f"DUMMY_{random.randint(100,9999)}",
        "date_of_birth": "2010-01-01",
        "gender": "M",
         # Parent is required, let's skip creating parent and see if it fails on validation or permission
         # We expect 400 (Validation) or 201, NOT 403.
    }
    # Need a valid parent ID to avoid 400, but 403 check happens before validation often? 
    # Actually DRF checks permission first.
    
    response = requests.post(f"{BASE_URL}/students/records/", json=payload, headers=admin_headers)
    if response.status_code != 403:
        print(f"✅ Admin Access Granted (Status: {response.status_code} - Expected non-403)")
    else:
        print(f"❌ Admin Access Denied (403)")

    # B. Student tries to create Student Profile
    print("👉 Student attempting to create Student Profile...")
    student_headers = TENANT_HEADERS.copy()
    student_headers['Authorization'] = f"Bearer {student_token}"
    
    response = requests.post(f"{BASE_URL}/students/records/", json=payload, headers=student_headers)
    if response.status_code == 403:
        print("✅ Student Access Denied (403) - SUCCESS")
    else:
        print(f"❌ SECURITY FAIL: Student could access (Status: {response.status_code})")

    # --- Scenario 2: Teachers App (IsSchoolAdmin) ---
    print("\n--- 🧪 Scenario 2: Modify Teachers App ---")
    
    # A. Teacher tries to create another Teacher
    print("👉 Teacher attempting to create Teacher Profile...")
    teacher_headers = TENANT_HEADERS.copy()
    if teacher_token:
        teacher_headers['Authorization'] = f"Bearer {teacher_token}"
        payload = {"first_name": "New", "last_name": "Teacher", "employee_id": "EMP123"}
        response = requests.post(f"{BASE_URL}/teachers/staff/", json=payload, headers=teacher_headers)
        if response.status_code == 403:
            print("✅ Teacher Access Denied (403) - SUCCESS")
        else:
            print(f"❌ SECURITY FAIL: Teacher could create teacher (Status: {response.status_code})")
    else:
        print("⚠️ Skipping Teacher test (Token missing)")
        
    # --- Scenario 3: Finance App (IsFinanceStaff) ---
    print("\n--- 🧪 Scenario 3: Modify Finance App ---")
    
    # A. Student tries to create FeeType
    print("👉 Student attempting to create FeeType...")
    payload = {"name": "Tuition Fee", "description": "Monthly"}
    response = requests.post(f"{BASE_URL}/finance/fee-types/", json=payload, headers=student_headers)
    if response.status_code == 403:
        print("✅ Student Access Denied (403) - SUCCESS")
    else:
        print(f"❌ SECURITY FAIL: Student could create FeeType (Status: {response.status_code})")

if __name__ == "__main__":
    test_rbac()
