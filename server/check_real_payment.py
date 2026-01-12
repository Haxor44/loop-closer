import requests
import sys

BASE_URL = "http://localhost:8000"

def check_real_payment():
    print(f"Checking {BASE_URL}/api/payment/upgrade...")
    try:
        email = "testVal@example.com"
        
        # 1. Call Upgrade
        print("Initiating upgrade...")
        resp = requests.post(f"{BASE_URL}/api/payment/upgrade", json={"email": email})
        
        if resp.status_code == 200:
            data = resp.json()
            print("SUCCESS: Upgrade endpoint works!")
            print(data)
            
            if "payment_url" in data and "tracking_id" in data:
                print("Response contains valid payment fields.")
                return True
            else:
                print("FAILED: Response missing payment_url or tracking_id")
                return False
        else:
            print(f"FAILED: Upgrade endpoint returned {resp.status_code}")
            print(resp.text)
            return False
            
    except Exception as e:
        print(f"FAILED: Error running test: {e}")
        return False

if __name__ == "__main__":
    success = check_real_payment()
    if not success:
        sys.exit(1)
