import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def check_mock_payment():
    print(f"Checking {BASE_URL}/api/payment/mock-success...")
    try:
        # First ensure a user exists or use a dummy one
        # We need a user in the DB for the mock to work?
        # The code checks `if u["email"] == req.email`.
        # so we pass any email.
        
        email = "testVal@example.com"
        
        # 1. Sync/Create User first to ensure they exist
        print("Syncing user...")
        resp = requests.post(f"{BASE_URL}/api/users/sync", json={"email": email, "name": "Test User"})
        if resp.status_code != 200:
            print(f"FAILED to sync user: {resp.status_code} {resp.text}")
            return False
            
        # 2. Try Mock Payment
        print("Attempting mock payment...")
        resp = requests.post(f"{BASE_URL}/api/payment/mock-success", json={"email": email})
        
        if resp.status_code == 200:
            print("SUCCESS: Mock payment endpoint works!")
            print(resp.json())
            return True
        else:
            print(f"FAILED: Mock payment endpoint returned {resp.status_code}")
            print(resp.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("FAILED: Could not connect to server at " + BASE_URL)
        return False
    except Exception as e:
        print(f"FAILED: Error running test: {e}")
        return False

if __name__ == "__main__":
    success = check_mock_payment()
    if not success:
        sys.exit(1)
