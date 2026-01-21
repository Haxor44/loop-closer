import requests
import json
import uuid
import time
import logging
import os

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
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "token" in data:
                self.token = data["token"]
                self.token_expiry = time.time() + (55 * 60) 
                return self.token
            else:
                logger.error(f"No token in response: {data}")
                return None
        except Exception as e:
            logger.error(f"Failed to get auth token: {str(e)}")
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
             return data.get("ipn_id")
        except Exception as e:
            logger.error(f"Failed to register IPN: {e}")
            return None

    def submit_order(self, user_email, amount=3770.00, currency="KES", description="Subscription Upgrade", 
                     subscription_details=None, account_number=None):
        if not subscription_details or not account_number:
            raise ValueError("subscription_details and account_number are REQUIRED")
        
        if CONSUMER_KEY == "your_consumer_key_here":
            return self.mock_submit_order(user_email, amount, currency)

        token = self.get_auth_token()
        if not token:
            raise Exception("Pesapal Auth Failed: Could not get token") 
            
        ipn_id = self.register_ipn()
        if not ipn_id:
             logger.warning("Proceeding without IPN ID")
        
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
            logger.info(f"Submitting order to: {url}")
            response = requests.post(url, json=payload, headers=headers)
            
            # Log response for debugging/audit
            logger.info(f"Pesapal Response Code: {response.status_code}")
            logger.info(f"Pesapal Response Body: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # Validate response
            if not data.get("order_tracking_id"):
                error_msg = f"Pesapal returned success but missing tracking_id. Data: {data}"
                if "error" in data:
                     # Extract Pesapal error message if available
                     err = data.get("error", {})
                     if isinstance(err, dict):
                         error_msg = f"Pesapal Error: {err.get('message', err.get('code', str(err)))}"
                     else:
                         error_msg = f"Pesapal Error: {err}"
                
                logger.error(error_msg)
                raise Exception(error_msg)

            return {
                "order_tracking_id": data.get("order_tracking_id"),
                "merchant_reference": merchant_reference,
                "redirect_url": data.get("redirect_url") 
            }
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            raise

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
            logger.error(f"Error getting status: {e}")
            return None

_service = PesapalService()

def create_pesapal_order(user_email, amount=3770.00, currency="KES", subscription_details=None, account_number=None):
    return _service.submit_order(user_email, amount, currency, subscription_details=subscription_details, account_number=account_number)

def get_transaction_status(tracking_id):
    return _service.get_transaction_status(tracking_id)
