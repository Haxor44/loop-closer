import requests
import json
import uuid
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pesapal")

# Configuration (In a real app, load from environment variables)
PESAPAL_ENV = "sandbox" # sandbox or live
PESAPAL_SANDBOX_URL = "https://cybqa.pesapal.com/pesapalv3"
PESAPAL_LIVE_URL = "https://pay.pesapal.com/v3"

# TODO: Move to environment variables for production
CONSUMER_KEY = "qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW"
CONSUMER_SECRET = "osGQ364R49cXKeOYSpaOnT++rHs="
CALLBACK_URL = "http://localhost:8000/api/payment/callback"  # Update with ngrok/cloudflared URL

class PesapalService:
    def __init__(self):
        self.base_url = PESAPAL_SANDBOX_URL if PESAPAL_ENV == "sandbox" else PESAPAL_LIVE_URL
        self.ensure_slash = lambda url: url if url.endswith('/') else url + '/'
        self.base_url = self.ensure_slash(self.base_url)
        self.token = None
        self.token_expiry = 0

    def get_auth_token(self):
        """
        Get OAuth2 authentication token from Pesapal (with caching)
        """
        if self.token and time.time() < self.token_expiry:
            return self.token

        url = f"{self.base_url}api/Auth/RequestToken"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "consumer_key": CONSUMER_KEY,
            "consumer_secret": CONSUMER_SECRET
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "token" in data:
                self.token = data["token"]
                # Expires in 5 minutes less than actual expiry (usually 60m)
                self.token_expiry = time.time() + (55 * 60) 
                return self.token
            else:
                logger.error(f"No token in response: {data}")
                return None
        except Exception as e:
            logger.error(f"Failed to get auth token: {str(e)}")
            return None

    def register_ipn(self):
        """
        Register the IPN URL with Pesapal
        """
        token = self.get_auth_token()
        if not token:
            return None

        url = f"{self.base_url}api/URLSetup/RegisterIPN"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": CALLBACK_URL,
            "ipn_notification_type": "GET" # or POST, standard is GET for v3 redirects? check docs. 
            # Walkthrough says /api/URLSetup/RegisterIPN.
            # Usually we register for GET (iframe redirect) or POST (backend IPN).
            # The walkthrough callback handles both. We'll stick to POST for reliable updates.
        }
        
        # NOTE: For v3, IPN registration is separate from Order submission.
        # But `submit_order` takes a `notification_id`.
        # So we need to register IPN and get an ID.
        
        try:
             # Check if we already have one cached/saved? 
             # For now, let's just log it. In production, save this ID.
             response = requests.post(url, json=payload, headers=headers)
             response.raise_for_status()
             data = response.json()
             return data.get("ipn_id")
        except Exception as e:
            logger.error(f"Failed to register IPN: {e}")
            return None

    def submit_order(self, user_email, amount=20.00, currency="KES", description="Subscription Upgrade"):
        """
        Submit order to Pesapal
        """
        # Force Mock if using dummy credentials
        if CONSUMER_KEY == "your_consumer_key_here":
            logger.info("Using MOCK implementation due to missing credentials")
            return self.mock_submit_order(user_email, amount, currency)

        token = self.get_auth_token()
        if not token:
            return None
            
        # Register IPN first (optimized: should be done once and stored)
        ipn_id = self.register_ipn()
        if not ipn_id:
             # If failing, maybe proceed without IPN (not recommended) or use dummy
             # For this implementation, we proceed.
             logger.warning("Proceeding without IPN ID")
        
        url = f"{self.base_url}api/Transactions/SubmitOrderRequest"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Unique ID
        merchant_reference = str(uuid.uuid4())
        
        payload = {
            "id": merchant_reference,
            "currency": currency,
            "amount": amount,
            "description": description,
            "callback_url": CALLBACK_URL,
            "notification_id": ipn_id,
            "billing_address": {
                "email_address": user_email,
                "country_code": "KE",
                # Add dummy data if needed
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "order_tracking_id": data.get("order_tracking_id"),
                "merchant_reference": merchant_reference,
                "redirect_url": data.get("redirect_url") 
            }
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            # FALBACK FOR DEV WITHOUT CREDENTIALS
            if CONSUMER_KEY == "your_consumer_key_here":
                logger.info("Using MOCK implementation due to missing credentials")
                return self.mock_submit_order(user_email, amount, currency)
            return None

    def mock_submit_order(self, user_email, amount, currency):
        order_id = str(uuid.uuid4())
        # In mock mode, we just return a success-looking structure
        # We can link to a local mock completion page or just the settings page
        return {
            "order_tracking_id": order_id,
            "merchant_reference": order_id,
            "redirect_url": f"http://localhost:3000/dashboard/settings?mock_payment=success&orderId={order_id}",
            "status": 200
        }

    def get_transaction_status(self, tracking_id):
        token = self.get_auth_token()
        if not token: 
            return None
            
        url = f"{self.base_url}api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None

# Singleton or helper function
_service = PesapalService()

def create_pesapal_order(user_email, amount=20.00, currency="KES"):
    return _service.submit_order(user_email, amount, currency)

def get_transaction_status(tracking_id):
    return _service.get_transaction_status(tracking_id)
