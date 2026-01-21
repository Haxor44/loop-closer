import requests
import json
import uuid
import time
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pesapal")

# Configuration (loaded from environment variables)
PESAPAL_ENV = os.getenv("PESAPAL_ENV", "sandbox")  # sandbox or live
PESAPAL_SANDBOX_URL = "https://cybqa.pesapal.com/pesapalv3"
PESAPAL_LIVE_URL = "https://pay.pesapal.com/v3"

# Load credentials from environment variables
CONSUMER_KEY = os.getenv("PESAPAL_CONSUMER_KEY", "qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW")
CONSUMER_SECRET = os.getenv("PESAPAL_CONSUMER_SECRET", "osGQ364R49cXKeOYSpaOnT++rHs=")

# Production callback URL points to API domain
CALLBACK_URL = os.getenv("PESAPAL_CALLBACK_URL", "https://api.theloopcloser.com/api/payment/callback")

class PesapalService:
    def __init__(self):
        self.base_url = PESAPAL_SANDBOX_URL if PESAPAL_ENV == "sandbox" else PESAPAL_LIVE_URL
        self.ensure_slash = lambda url: url if url.endswith('/') else url + '/'
        self.base_url = self.ensure_slash(self.base_url)
        self.token = None
        self.token_expiry = 0

    def get_auth_token(self):
        if self.token and time.time() < self.token_expiry:
            return self.token

        url = f"{self.base_url}api/Auth/RequestToken"
        headers = { "Content-Type": "application/json", "Accept": "application/json" }
        payload = { "consumer_key": CONSUMER_KEY, "consumer_secret": CONSUMER_SECRET }

        try:
            print(f"DEBUG: Requesting Key from {url}", flush=True)
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "token" in data:
                self.token = data["token"]
                self.token_expiry = time.time() + (55 * 60) 
                return self.token
            else:
                print(f"ERROR: No token in response: {data}", flush=True)
                return None
        except Exception as e:
            print(f"ERROR: Failed to get auth token: {str(e)}", flush=True)
            if 'response' in locals():
                print(f"Response Body: {response.text}", flush=True)
            return None

    def register_ipn(self):
        token = self.get_auth_token()
        if not token:
            return None

        url = f"{self.base_url}api/URLSetup/RegisterIPN"
        headers = { "Authorization": f"Bearer {token}", "Content-Type": "application/json" }
        payload = { "url": CALLBACK_URL, "ipn_notification_type": "GET" }
        
        try:
             response = requests.post(url, json=payload, headers=headers)
             response.raise_for_status()
             data = response.json()
             print(f"DEBUG: IPN Registered: {data}", flush=True)
             return data.get("ipn_id")
        except Exception as e:
            print(f"ERROR: Failed to register IPN: {e}", flush=True)
            if 'response' in locals():
                 print(f"Response Body: {response.text}", flush=True)
            return None

    def submit_order(self, user_email, amount=3770.00, currency="KES", description="Subscription Upgrade", 
                     subscription_details=None, account_number=None):
        if not subscription_details or not account_number:
            raise ValueError("subscription_details and account_number are REQUIRED")
        
        if CONSUMER_KEY == "your_consumer_key_here":
            return self.mock_submit_order(user_email, amount, currency)

        token = self.get_auth_token()
        if not token:
            raise Exception("Failed to get Auth Token") # Raise to fail fast
            
        ipn_id = self.register_ipn()
        if not ipn_id:
             print("WARNING: Proceeding without IPN ID", flush=True)
        
        url = f"{self.base_url}api/Transactions/SubmitOrderRequest"
        headers = { "Authorization": f"Bearer {token}", "Content-Type": "application/json" }
        
        merchant_reference = str(uuid.uuid4())
        
        payload = {
            "id": merchant_reference,
            "currency": currency,
            "amount": amount,
            "description": description,
            "callback_url": CALLBACK_URL,
            "notification_id": ipn_id,
            "billing_address": { "email_address": user_email, "country_code": "KE" },
            "account_number": account_number,
            "subscription_details": subscription_details
        }

        try:
            print(f"DEBUG: Submitting order to: {url}", flush=True)
            response = requests.post(url, json=payload, headers=headers)
            print(f"DEBUG: Response Status: {response.status_code}", flush=True)
            print(f"DEBUG: Response Body: {response.text}", flush=True) # CRITICAL LOG
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("order_tracking_id"):
                print(f"CRITICAL ERROR: Pesapal returned success but no tracking_id! Data: {data}", flush=True)
                raise Exception(f"Pesapal returned missing tracking_id. Data: {data}")

            return {
                "order_tracking_id": data.get("order_tracking_id"),
                "merchant_reference": merchant_reference,
                "redirect_url": data.get("redirect_url") 
            }
        except Exception as e:
            print(f"ERROR: Error submitting order: {e}", flush=True)
            raise # Re-raise to crash properly

    def mock_submit_order(self, user_email, amount, currency):
        order_id = str(uuid.uuid4())
        return {
            "order_tracking_id": order_id,
            "merchant_reference": order_id,
            "redirect_url": f"http://localhost:3000/dashboard/settings?mock_payment=success&orderId={order_id}",
            "status": 200
        }

    def get_transaction_status(self, tracking_id):
        token = self.get_auth_token()
        if not token: return None
        url = f"{self.base_url}api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            print(f"Error getting status: {e}", flush=True)
            return None

_service = PesapalService()

def create_pesapal_order(user_email, amount=3770.00, currency="KES", subscription_details=None, account_number=None):
    return _service.submit_order(user_email, amount, currency, subscription_details=subscription_details, account_number=account_number)

def get_transaction_status(tracking_id):
    return _service.get_transaction_status(tracking_id)
