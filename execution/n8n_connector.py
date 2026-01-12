import requests
import json

def send_to_webhook(data, webhook_url):
    """
    Sends a JSON payload (list of social items) to an n8n webhook.
    """
    if not webhook_url:
        print("Error: No webhook URL provided.")
        return False
        
    try:
        print(f"--- POSTING {len(data)} ITEMS TO N8N ---")
        # Ensure we are sending valid JSON
        headers = {"Content-Type": "application/json"}
        
        # Check if it's a list or dict, wrap if necessary or send as is
        # n8n usually expects a JSON object or array
        response = requests.post(webhook_url, json=data, headers=headers)
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Success! n8n response: {response.status_code}")
            return True
        else:
            print(f"Failed to post to n8n. Status: {response.status_code}, Body: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error connecting to n8n: {e}")
        return False
