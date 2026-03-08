import requests
import json
import random

BASE_URL = "http://localhost:8000/api"
TENANT_HOST = "www.sunrisepublicschool.edu.in"
TENANT_HEADERS = {"Host": TENANT_HOST}

def test_auth():
    print("\n--- 🔐 Testing Authentication ---")
    login_payload = {"username": "admin", "password": "admin123"}
    try:
        response = requests.post(f"{BASE_URL}/users/auth/login/", json=login_payload)
        if response.status_code == 200:
            token = response.json().get('access')
            print("✅ Super Admin Login Successful.")
            return token
        else:
            print(f"❌ Login Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def setup_data(token):
    headers = TENANT_HEADERS.copy()
    headers['Authorization'] = f"Bearer {token}"
    
    # 1. Get or Create Student
    print("\n--- 🛠 Setting up Data ---")
    student_id = None
    try:
        response = requests.get(f"{BASE_URL}/students/records/", headers=headers)
        students = response.json()
        if len(students) > 0:
            student_id = students[0]['id']
            print(f"✅ Using existing Student ID: {student_id}")
        else:
            print("❌ No students found. Please run verify_all_apis.py first.")
            return None
    except Exception as e:
        print(f"❌ Error fetching students: {e}")
        return None

    # 2. Create Subject
    subject_id = None
    try:
        payload = {"name": "Mathematics", "code": f"MATH{random.randint(100,999)}"}
        response = requests.post(f"{BASE_URL}/academics/subjects/", json=payload, headers=headers)
        if response.status_code == 201:
            subject_id = response.json()['id']
            print(f"✅ Subject Created: {subject_id}")
        else:
            # Maybe already exists?
            pass
    except:
        pass

    # 3. Create Exam
    exam_id = None
    try:
        payload = {"name": "Finals 2024", "start_date": "2024-03-01", "end_date": "2024-03-10"}
        response = requests.post(f"{BASE_URL}/academics/exams/", json=payload, headers=headers)
        if response.status_code == 201:
            exam_id = response.json()['id']
            print(f"✅ Exam Created: {exam_id}")
    except:
        pass

    # 4. Create Result (if Subject and Exam exists)
    if student_id and subject_id and exam_id:
        try:
            payload = {
                "student": student_id,
                "exam": exam_id,
                "subject": subject_id,
                "marks_obtained": 85.5,
                "max_marks": 100
            }
            requests.post(f"{BASE_URL}/academics/exam-results/", json=payload, headers=headers)
            print("✅ Exam Result Created")
        except:
            pass
            
    return student_id

def test_report_card(token, student_id):
    print("\n--- 📄 Testing PDF Generation ---")
    headers = TENANT_HEADERS.copy()
    headers['Authorization'] = f"Bearer {token}"
    
    try:
        url = f"{BASE_URL}/academics/reports/student/{student_id}/"
        print(f"Requesting Report Card: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type')
            print(f"✅ Response Received. Content-Type: {content_type}")
            
            if 'application/pdf' in content_type:
                filename = "test_report_card.pdf"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✅ PDF saved to {filename}")
            else:
                 print("❌ Response is not a PDF")
        else:
            print(f"❌ Failed to get Report Card: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    token = test_auth()
    if token:
        student_id = setup_data(token)
        if student_id:
            test_report_card(token, student_id)
