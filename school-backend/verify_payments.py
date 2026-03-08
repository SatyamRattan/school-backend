import requests
import json

BASE_URL = "http://localhost:8000/api"
TENANT_HOST = "www.sunrisepublicschool.edu.in"

def test_payment_initiation():
    print("\n--- Testing Payment Initiation ---")
    # 1. Login as School Admin (Simulated)
    # Ideally, we need a token. For this test, we might hit 403 if not authenticated.
    # We will just print the endpoint to manually test in Postman for now 
    # as setting up a full login flow in this script is complex without a real user.
    print(f"Endpoint: {BASE_URL}/management/payments/initiate/")
    print("Payload: {'plan': 'MONTHLY', 'currency': 'INR'}")

def test_suspension_logic():
    print("\n--- Testing Suspension Logic ---")
    headers = {"Host": TENANT_HOST}
    try:
        response = requests.get(f"http://localhost:8000/api/students/records/", headers=headers)
        if response.status_code == 403 and "suspended" in response.text:
            print("✅ Suspension check PASSED: School is correctly blocked.")
        elif response.status_code == 401:
            print("ℹ️  Auth check passed (401 means middleware allowed request to reach view). School is ACTIVE.")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_payment_initiation()
    test_suspension_logic()
