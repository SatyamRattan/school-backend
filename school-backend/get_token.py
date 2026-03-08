import requests
import sys

BASE_URL = "http://localhost:8000/api"

def get_token(username, password):
    url = f"{BASE_URL}/users/auth/login/"
    print(f"Requesting token for {username} from {url}...")
    try:
        response = requests.post(url, json={"username": username, "password": password})
        if response.status_code == 200:
            print("\n✅ Login Successful!")
            tokens = response.json()
            print(f"Access Token:\n{tokens['access']}")
            print(f"\nRefresh Token:\n{tokens['refresh']}")
        else:
            print(f"\n❌ Login Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python get_token.py <username> <password>")
    else:
        get_token(sys.argv[1], sys.argv[2])
