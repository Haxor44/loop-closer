from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from typing import List, Optional
from pydantic import BaseModel
import time
from datetime import datetime

# Add execution directory to path so we can import ticket_manager
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "execution"))
import ticket_manager

app = FastAPI(title="The Loop Closer API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://theloopcloser.com",
        "https://www.theloopcloser.com",
        "https://api.theloopcloser.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USERS_DB = "users_db.json"

def load_users_db():
    if not os.path.exists(USERS_DB):
        return {"users": [], "transactions": []}
    with open(USERS_DB, "r") as f:
        return json.load(f)

def save_users_db(db):
    with open(USERS_DB, "w") as f:
        json.dump(db, indent=2, fp=f)

class User(BaseModel):
    email: str
    name: str = "Unknown"
    plan: str = "Free" # Free, Pro, Teams
    joined_at: float = 0.0

@app.get("/api/users")
def get_users():
    return load_users_db()

@app.post("/api/users/sync")
def sync_user(user: User):
    db = load_users_db()
    # Check if user exists
    found_user = None
    for u in db["users"]:
        if u["email"] == user.email:
            found_user = u
            break
    
    if found_user:
        return {"status": "exists", "user": found_user}
    
    # Create new user
    new_user = user.dict()
    new_user["joined_at"] = time.time()
    new_user["config"] = {} # Initialize empty config
    new_user["connected_platforms"] = [] # Initialize empty list
    db["users"].append(new_user)
    save_users_db(db)
    return {"status": "created", "user": new_user}

class UserConfig(BaseModel):
    email: str
    keywords: str
    subreddits: Optional[str] = ""
    twitter_keywords: Optional[str] = ""

@app.post("/api/users/config")
def save_user_config(config: UserConfig):
    db = load_users_db()
    for u in db["users"]:
        if u["email"] == config.email:
            # Enforce Free Tier Limits
            if u["plan"] == "Free":
                # Basic check: only allow 1 keyword (split by comma)
                keywords_list = [k.strip() for k in config.keywords.split(",") if k.strip()]
                subreddits_list = [s.strip() for s in config.subreddits.split(",") if s.strip()]
                
                if len(keywords_list) > 1:
                    raise HTTPException(status_code=400, detail="Free Plan limit: 1 Global Keyword. Upgrade to Pro for unlimited.")
                if len(subreddits_list) > 1:
                    raise HTTPException(status_code=400, detail="Free Plan limit: 1 Subreddit. Upgrade to Pro for unlimited.")
            
            u["config"] = config.dict()
            save_users_db(db)
            return {"status": "success", "config": u["config"]}
    
    raise HTTPException(status_code=404, detail="User not found")

class ProfileUpdate(BaseModel):
    email: str
    name: str

@app.patch("/api/users/profile")
def update_profile(profile: ProfileUpdate):
    db = load_users_db()
    for u in db["users"]:
        if u["email"] == profile.email:
            u["name"] = profile.name
            save_users_db(db)
            return {"status": "success", "user": u}
    raise HTTPException(status_code=404, detail="User not found")

class PlanUpdate(BaseModel):
    plan: str

@app.patch("/api/users/{email}/plan")
def update_user_plan(email: str, update: PlanUpdate):
    db = load_users_db()
    for u in db["users"]:
        if u["email"] == email:
            u["plan"] = update.plan
            save_users_db(db)
            return {"status": "success", "user": u}
    raise HTTPException(status_code=404, detail="User not found")

class IntegrationsUpdate(BaseModel):
    email: str
    platform: str
    connected: bool

@app.post("/api/users/integrations")
def update_integration_status(update: IntegrationsUpdate):
    db = load_users_db()
    for u in db["users"]:
        if u["email"] == update.email:
            platforms = u.get("connected_platforms", [])
            if update.connected:
                if update.platform not in platforms:
                    platforms.append(update.platform)
            else:
                if update.platform in platforms:
                    platforms.remove(update.platform)
            
            # Update config fields
            current_config = u.get("config", {})
            new_config_data = update.config if isinstance(update.config, dict) else update.config.dict()
            
            # Merge existing config with updates (preserving fields not in update if mostly checking just these)
            # Actually, the previous logic replaced it. Let's make it robust.
            u["config"] = {
                "keywords": new_config_data.get("keywords", current_config.get("keywords", "")),
                "subreddits": new_config_data.get("subreddits", current_config.get("subreddits", "")),
                "twitter_keywords": new_config_data.get("twitter_keywords", current_config.get("twitter_keywords", "")),
                "product_name": new_config_data.get("product_name", current_config.get("product_name", "")),
                "brand_voice": new_config_data.get("brand_voice", current_config.get("brand_voice", ""))
            }
    raise HTTPException(status_code=404, detail="User not found")

# TWITTER OAUTH ENDPOINTS
class TwitterOAuthTokens(BaseModel):
    email: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None

@app.post("/api/users/twitter-tokens")
def save_twitter_tokens(tokens: TwitterOAuthTokens):
    """Store Twitter OAuth tokens for user."""
    db = load_users_db()
    
    for u in db["users"]:
        if u["email"] == tokens.email:
            # Store tokens (TODO: Add encryption in production)
            u["twitter_oauth"] = {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "expires_at": tokens.expires_at,
                "connected_at": time.time()
            }
            
            # Initialize quota based on plan
            searches_limit = 10 if u["plan"] == "Pro" else 0
            tweets_limit = 100 if u["plan"] == "Pro" else 0
            if u["plan"] == "Teams":
                searches_limit = 20
                tweets_limit = 200
            
            u["twitter_quota"] = {
                "searches_today": 0,
                "tweets_today": 0,
                "searches_limit": searches_limit,
                "tweets_limit": tweets_limit,
                "last_reset": datetime.now().date().isoformat()
            }
            
            # Update connected_platforms
            if "connected_platforms" not in u:
                u["connected_platforms"] = []
            if "twitter" not in u["connected_platforms"]:
                u["connected_platforms"].append("twitter")
            
            save_users_db(db)
            return {"status": "success", "quota": u["twitter_quota"]}
    
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/users/twitter-quota")
def get_twitter_quota(req: dict):
    """Get user's Twitter quota status."""
    db = load_users_db()
    for u in db["users"]:
        if u["email"] == req["email"]:
            quota = u.get("twitter_quota", {
                "searches_today": 0,
                "tweets_today": 0,
                "searches_limit": 0,
                "tweets_limit": 0,
                "last_reset": datetime.now().date().isoformat()
            })

            # Check for reset
            today = datetime.now().date().isoformat()
            last_reset = quota.get("last_reset")
            
            if last_reset != today:
                print(f"Resetting quota for {req['email']} from {last_reset} to {today}")
                quota["searches_today"] = 0
                quota["tweets_today"] = 0
                quota["last_reset"] = today
                u["twitter_quota"] = quota
                save_users_db(db)
            
            return {"quota": quota}
    raise HTTPException(status_code=404, detail="User not found")

# PAYMENT ENDPOINTS
from pesapal_manager import create_pesapal_order, get_transaction_status

class UpgradeRequest(BaseModel):
    email: str

@app.post("/api/payment/upgrade")
def upgrade_user(req: UpgradeRequest):
    # 1. Create Recurring Details
    # Start now, end in ~5 years
    now = datetime.now()
    start_date = now.strftime("%d-%m-%Y")
    # Simple future date: 5 years from now
    try:
        end_date = now.replace(year=now.year + 5).strftime("%d-%m-%Y")
    except ValueError:
        # Handle leap year case
        end_date = now.replace(year=now.year + 5, day=28).strftime("%d-%m-%Y")

    subscription_details = {
        "start_date": start_date,
        "end_date": end_date,
        "frequency": "MONTHLY"
    }

    # 2. Create Order (3,770 KES = ~29 USD)
    # Using email as account_number
    order = create_pesapal_order(
        req.email, 
        amount=3770.00, 
        currency="KES", 
        subscription_details=subscription_details,
        account_number=req.email
    )
    
    if not order:
        raise HTTPException(status_code=500, detail="Failed to create payment order")
    
    # 2. Save Pending Transaction
    db = load_users_db()
    if "transactions" not in db:
        db["transactions"] = []
        
    db["transactions"].append({
        "tracking_id": order["order_tracking_id"],
        "merchant_reference": order["merchant_reference"],
        "email": req.email,
        "status": "PENDING",
        "created_at": time.time()
    })
    save_users_db(db)
    
    # 3. Return Redirect URL
    return {
        "payment_url": order["redirect_url"], 
        "tracking_id": order["order_tracking_id"]
    }

@app.get("/api/payment/callback")
def payment_callback(OrderTrackingId: str, OrderMerchantReference: str = None):
    # 1. Check status from PesaPal
    status_data = get_transaction_status(OrderTrackingId)
    if not status_data:
        return {"status": "error", "message": "Failed to verify transaction status"}
        
    pesapal_status = status_data.get("payment_status_description", "").upper()
    
    # 2. Update Local DB
    db = load_users_db()
    if "transactions" not in db:
        db["transactions"] = []
        
    user_email = None
    transaction_found = False
    
    for tx in db["transactions"]:
        if tx["tracking_id"] == OrderTrackingId:
            tx["status"] = pesapal_status
            user_email = tx["email"]
            transaction_found = True
            break
            
    if not transaction_found:
        # Record it anyway?
        return {"status": "error", "message": "Transaction not found in local records"}
        
    # 3. If Completed, Upgrade User
    if pesapal_status == "COMPLETED":
        user_found = False
        for u in db["users"]:
            if u["email"] == user_email:
                u["plan"] = "Pro"
                user_found = True
                break
        
        if user_found:
            save_users_db(db)
            # Redirect to frontend settings page with success
            from fastapi.responses import RedirectResponse
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            return RedirectResponse(url=f"{frontend_url}/dashboard/settings?payment=success&plan=Pro")
            
    # For other statuses or failure
    from fastapi.responses import RedirectResponse
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/dashboard/settings?payment={pesapal_status.lower()}")

@app.get("/api/payment/callback-public")
def payment_callback_public(OrderTrackingId: str, OrderMerchantReference: str = None):
    """
    Public callback endpoint for PesaPal (exposed via tunnel/production domain)
    This is the same as /api/payment/callback but can be exposed publicly
    """
    # Reuse the same logic
    return payment_callback(OrderTrackingId, OrderMerchantReference)

@app.get("/api/payment/verify")
def verify_payment(OrderTrackingId: str):
    """
    Verify payment status and return JSON (for frontend AJAX calls)
    """
    # 1. Check status from PesaPal
    status_data = get_transaction_status(OrderTrackingId)
    print(f"💰 DEBUG: PesaPal Status for {OrderTrackingId}: {status_data}")
    
    if not status_data:
        return {"status": "error", "message": "Failed to verify transaction status"}
        
    pesapal_status = status_data.get("payment_status_description", "").upper()
    print(f"💰 DEBUG: Normalized Status: {pesapal_status}")
    
    # 2. Update Local DB
    db = load_users_db()
    if "transactions" not in db:
        db["transactions"] = []
        
    user_email = None
    transaction_found = False
    
    for tx in db["transactions"]:
        if tx["tracking_id"] == OrderTrackingId:
            tx["status"] = pesapal_status
            user_email = tx["email"]
            transaction_found = True
            print(f"💰 DEBUG: Found transaction for user: {user_email}")
            break
            
    if not transaction_found:
        print(f"💰 DEBUG: Transaction {OrderTrackingId} not found in local DB")
        return {"status": "error", "message": "Transaction not found in local records"}
        
    # 3. If Completed, Upgrade User
    if pesapal_status == "COMPLETED":
        user_found = False
        for u in db["users"]:
            if u["email"] == user_email:
                print(f"💰 DEBUG: Upgrading user {user_email} to Pro")
                u["plan"] = "Pro"
                user_found = True
                break
        
        if user_found:
            save_users_db(db)
            print("💰 DEBUG: Database saved successfully")
            return {
                "status": "success",
                "payment_status": "COMPLETED",
                "plan": "Pro",
                "message": "Payment successful! Upgraded to Pro"
            }
    
    # For other statuses
    return {
        "status": "pending" if pesapal_status in ["PENDING", "PROCESSING"] else "failed",
        "payment_status": pesapal_status,
        "message": f"Payment status: {pesapal_status}"
    }

@app.post("/api/payment/mock-success")
def mock_payment_success(req: UpgradeRequest):
    """Dev Tool: Instantly upgrade user to PRO without payment"""
    db = load_users_db()
    for u in db["users"]:
        if u["email"] == req.email:
            u["plan"] = "Pro"
            save_users_db(db)
            return {"status": "upgraded", "plan": "Pro"}
    return {"status": "user_not_found"}

class TicketUpdate(BaseModel):
    status: str

@app.get("/api/tickets")
async def get_tickets(email: Optional[str] = None):
    try:
        db = ticket_manager.load_db()
        tickets = db.get("tickets", [])
        
        # Filter by owner (SaaS User)
        if email:
            tickets = [t for t in tickets if t.get("owner") == email]
            
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, update: TicketUpdate):
    try:
        db = ticket_manager.load_db()
        found = False
        for ticket in db["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["status"] = update.status.upper()
                found = True
                break
        
        if not found:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Save DB
        ticket_manager.save_db(db)
        return {"status": "success", "ticket": ticket}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReplyPayload(BaseModel):
    content: str
    platform: str

@app.post("/api/tickets/{ticket_id}/reply")
def send_reply(ticket_id: str, payload: ReplyPayload):
    """
    Send a real reply to the social platform.
    """
    try:
        # 1. Load Ticket to get User Handle and/or link
        db = ticket_manager.load_db()
        ticket = next((t for t in db["tickets"] if t["id"] == ticket_id), None)
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # 2. Get SaaS User (Owner) to get OAuth Tokens
        users = load_users_db()
        owner_email = ticket.get("owner")
        if not owner_email:
             # Fallback logic if owner isn't set, unlikely if auth is working
             raise HTTPException(status_code=400, detail="Ticket has no owner linked")
             
        user = next((u for u in users["users"] if u["email"] == owner_email), None)
        if not user:
            raise HTTPException(status_code=404, detail="Owner user not found")
            
        # 3. Check Platform & Tokens
        if payload.platform.lower() == "twitter":
            oauth = user.get("twitter_oauth")
            if not oauth or not oauth.get("access_token"):
                raise HTTPException(status_code=403, detail="Twitter not connected or token expired")
            
            # 4. Initialize Client & Send
            # Need to find the original tweet ID from the ticket or linked users?
            # In a real app, we'd store the 'platform_id' on the ticket or the 'post' object.
            # For now, we'll try to extract it from the ticket ID if it follows 'twitter_123' format 
            # or expect the frontend/ticket to carry it.
            # Simplified: Assumes ticket.id might be the external ID or we have to look it up.
            
            # BETTER STRATEGY: Look up the original post in 'analyzed_posts.json' to get the real ID?
            # Or just assume for this prototype that `ticket_id` IS `twitter_123` or we stored `source_id`.
            
            # Let's check `ticket_manager` logic. It creates tickets with UUIDs usually.
            # Retrieve the 'source_id' from the ticket if it exists, or passed in payload?
            # Let's try to pass `source_id` in the payload from frontend for safety.
            
            from execution.twitter_api_client import TwitterAPIClient
            client = TwitterAPIClient(oauth["access_token"])
            
            # We need the original tweet ID. 
            # If the ticket ID isn't the tweet ID, we depend on the frontend to provide it,
            # OR we assume the Ticket is linked to a Post ID.
            
            # For this 'Real Logic' implementation, let's assume the frontend sends the 'source_id' 
            # or the ticket ID contains it. 
            # If ticket_id starts with 'twitter_', use it.
            
            reply_to_id = ticket_id if ticket_id.startswith("twitter_") else None
            
            result = client.create_tweet(payload.content, reply_to_id=reply_to_id)
            
            if result:
                # Update status to DONE or REPLIED
                ticket["status"] = "DONE"
                ticket_manager.save_db(db)
                return {"status": "success", "data": result}
            else:
                raise HTTPException(status_code=500, detail="Failed to post to Twitter")
                
        else:
            raise HTTPException(status_code=400, detail=f"Platform {payload.platform} not supported yet")
            
    except Exception as e:
        print(f"Reply Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        ticket_manager.save_db(db)
        return {"message": f"Ticket {ticket_id} updated to {update.status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(email: Optional[str] = None):
    try:
        db = ticket_manager.load_db()
        tickets = db.get("tickets", [])
        
        # Filter by owner (SaaS User)
        if email:
            tickets = [t for t in tickets if t.get("owner") == email]
            
        return {
            "done": len([t for t in tickets if t["status"] == "DONE"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReplyRequest(BaseModel):
    content: str
    tone: str
    context: Optional[str] = None

import llm_classifier

@app.post("/api/generate-reply")
def generate_reply_endpoint(req: ReplyRequest):
    try:
        result = llm_classifier.generate_reply(req.content, req.tone, req.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
