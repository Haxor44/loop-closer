from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from typing import List, Optional, Dict
from pydantic import BaseModel
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add execution directory to path so we can import ticket_manager and others
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "execution"))

# Import DB and Models
from database import get_db, engine, Base
from models import User as UserModel, Ticket as TicketModel, Transaction as TransactionModel
import ticket_manager 
import llm_classifier

# Create tables if they don't exist (redundant if migrate.py ran, but good for safety)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="The Loop Closer API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "https://theloopcloser.com",
        "https://www.theloopcloser.com",
        "https://api.theloopcloser.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Requests ---
class UserDTO(BaseModel):
    email: str
    name: str = "Unknown"
    plan: str = "Free"
    joined_at: float = 0.0

class UserConfig(BaseModel):
    email: str
    keywords: str
    subreddits: Optional[str] = ""
    twitter_keywords: Optional[str] = ""
    product_name: Optional[str] = ""
    brand_voice: Optional[str] = ""

class ProfileUpdate(BaseModel):
    email: str
    name: str

class PlanUpdate(BaseModel):
    plan: str

class IntegrationsUpdate(BaseModel):
    email: str
    platform: str
    connected: bool
    config: UserConfig

class TwitterOAuthTokens(BaseModel):
    email: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None

class UpgradeRequest(BaseModel):
    email: str

class TicketUpdate(BaseModel):
    status: str

class ReplyPayload(BaseModel):
    content: str
    platform: str

class ReplyRequest(BaseModel):
    content: str
    tone: str
    context: Optional[str] = None

# --- API Endpoints ---

@app.get("/api/users")
def get_users(db: Session = Depends(get_db)):
    # Mimic original behavior: return everything
    users = db.query(UserModel).all()
    transactions = db.query(TransactionModel).all()
    return {"users": users, "transactions": transactions}

@app.post("/api/users/sync")
def sync_user(user: UserDTO, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    
    if db_user:
        return {"status": "exists", "user": db_user}
    
    # Create new user
    new_user = UserModel(
        email=user.email,
        name=user.name,
        plan=user.plan,
        joined_at=time.time(),
        config={},
        connected_platforms=[]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "created", "user": new_user}

@app.post("/api/users/config")
def save_user_config(config: UserConfig, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == config.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Enforce Free Tier Limits
    if db_user.plan == "Free":
        keywords_list = [k.strip() for k in config.keywords.split(",") if k.strip()]
        subreddits_list = [s.strip() for s in config.subreddits.split(",") if s.strip()]
        
        if len(keywords_list) > 1:
            raise HTTPException(status_code=400, detail="Free Plan limit: 1 Global Keyword. Upgrade to Pro for unlimited.")
        if len(subreddits_list) > 1:
            raise HTTPException(status_code=400, detail="Free Plan limit: 1 Subreddit. Upgrade to Pro for unlimited.")
    
    # Update config. We need to be careful with JSONB updates if partially replacing?
    # Original logic replaced the whole config object derived from pydantic
    # But UserConfig Pydantic model might miss fields if not careful? 
    # The Pydantic model above matches what was there.
    
    db_user.config = config.dict()
    db.commit()
    db.refresh(db_user)
    return {"status": "success", "config": db_user.config}

@app.patch("/api/users/profile")
def update_profile(profile: ProfileUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == profile.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_user.name = profile.name
    db.commit()
    return {"status": "success", "user": db_user}

@app.patch("/api/users/{email}/plan")
def update_user_plan(email: str, update: PlanUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_user.plan = update.plan
    db.commit()
    return {"status": "success", "user": db_user}

@app.post("/api/users/integrations")
def update_integration_status(update: IntegrationsUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == update.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update connected_platforms
    current_platforms = list(db_user.connected_platforms or [])
    if update.connected:
        if update.platform not in current_platforms:
            current_platforms.append(update.platform)
    else:
        if update.platform in current_platforms:
            current_platforms.remove(update.platform)
    
    db_user.connected_platforms = current_platforms

    # Update config fields
    # Merge existing config with updates
    current_config = dict(db_user.config or {})
    new_config_data = update.config.dict()
    
    # Selective update
    current_config["keywords"] = new_config_data.get("keywords", current_config.get("keywords", ""))
    current_config["subreddits"] = new_config_data.get("subreddits", current_config.get("subreddits", ""))
    current_config["twitter_keywords"] = new_config_data.get("twitter_keywords", current_config.get("twitter_keywords", ""))
    current_config["product_name"] = new_config_data.get("product_name", current_config.get("product_name", ""))
    current_config["brand_voice"] = new_config_data.get("brand_voice", current_config.get("brand_voice", ""))
    
    db_user.config = current_config
    
    db.commit()
    return {"status": "success", "user": db_user}

@app.post("/api/users/twitter-tokens")
def save_twitter_tokens(tokens: TwitterOAuthTokens, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == tokens.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update OAuth
    db_user.twitter_oauth = {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "expires_at": tokens.expires_at,
        "connected_at": time.time()
    }
    
    # Initialize quota
    searches_limit = 10 if db_user.plan == "Pro" else 0
    tweets_limit = 100 if db_user.plan == "Pro" else 0
    if db_user.plan == "Teams":
        searches_limit = 20
        tweets_limit = 200
    
    db_user.twitter_quota = {
        "searches_today": 0,
        "tweets_today": 0,
        "searches_limit": searches_limit,
        "tweets_limit": tweets_limit,
        "last_reset": datetime.now().date().isoformat()
    }
    
    # Update connected_platforms
    platforms = list(db_user.connected_platforms or [])
    if "twitter" not in platforms:
        platforms.append("twitter")
        db_user.connected_platforms = platforms
        
    db.commit()
    return {"status": "success", "quota": db_user.twitter_quota}

@app.post("/api/users/twitter-quota")
def get_twitter_quota(req: dict, db: Session = Depends(get_db)):
    email = req.get("email")
    db_user = db.query(UserModel).filter(UserModel.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    quota = dict(db_user.twitter_quota or {
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
        print(f"Resetting quota for {email} from {last_reset} to {today}")
        quota["searches_today"] = 0
        quota["tweets_today"] = 0
        quota["last_reset"] = today
        db_user.twitter_quota = quota
        db.commit()
    
    return {"quota": quota}

# --- PAYMENT ENDPOINTS ---
from pesapal_manager import create_pesapal_order, get_transaction_status

@app.post("/api/payment/upgrade")
def upgrade_user(req: UpgradeRequest, db: Session = Depends(get_db)):
    # 1. Create Recurring Details
    now = datetime.now()
    start_date = now.strftime("%d-%m-%Y")
    try:
        end_date = now.replace(year=now.year + 5).strftime("%d-%m-%Y")
    except ValueError:
        end_date = now.replace(year=now.year + 5, day=28).strftime("%d-%m-%Y")

    subscription_details = {
        "start_date": start_date,
        "end_date": end_date,
        "frequency": "MONTHLY"
    }

    # 2. Create Order (3,770 KES)
    order = create_pesapal_order(
        req.email, 
        amount=3770.00, 
        currency="KES", 
        subscription_details=subscription_details,
        account_number=req.email
    )
    
    if not order:
        raise HTTPException(status_code=500, detail="Failed to create payment order")
    
    # 3. Save Pending Transaction
    new_tx = TransactionModel(
        tracking_id=order["order_tracking_id"],
        merchant_reference=order["merchant_reference"],
        email=req.email,
        status="PENDING",
        created_at=time.time()
    )
    db.add(new_tx)
    db.commit()
    
    return {
        "payment_url": order["redirect_url"], 
        "tracking_id": order["order_tracking_id"]
    }

@app.get("/api/payment/callback")
def payment_callback(OrderTrackingId: str, OrderMerchantReference: str = None, db: Session = Depends(get_db)):
    # 1. Check status from PesaPal
    status_data = get_transaction_status(OrderTrackingId)
    if not status_data:
        return {"status": "error", "message": "Failed to verify transaction status"}
        
    pesapal_status = status_data.get("payment_status_description", "").upper()
    
    # 2. Update Local DB
    tx = db.query(TransactionModel).filter(TransactionModel.tracking_id == OrderTrackingId).first()
    
    if not tx:
        return {"status": "error", "message": "Transaction not found in local records"}
        
    tx.status = pesapal_status
    user_email = tx.email
    
    # 3. If Completed, Upgrade User
    if pesapal_status == "COMPLETED":
        db_user = db.query(UserModel).filter(UserModel.email == user_email).first()
        if db_user:
            db_user.plan = "Pro"
            
        db.commit()
        
        # Redirect
        from fastapi.responses import RedirectResponse
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/dashboard/settings?payment=success&plan=Pro")
            
    db.commit() # Save status update even if not completed
    
    from fastapi.responses import RedirectResponse
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/dashboard/settings?payment={pesapal_status.lower()}")

@app.get("/api/payment/callback-public")
def payment_callback_public(OrderTrackingId: str, OrderMerchantReference: str = None, db: Session = Depends(get_db)):
    return payment_callback(OrderTrackingId, OrderMerchantReference, db)

@app.get("/api/payment/verify")
def verify_payment(OrderTrackingId: str, db: Session = Depends(get_db)):
    status_data = get_transaction_status(OrderTrackingId)
    if not status_data:
        return {"status": "error", "message": "Failed to verify transaction status"}
        
    pesapal_status = status_data.get("payment_status_description", "").upper()
    
    tx = db.query(TransactionModel).filter(TransactionModel.tracking_id == OrderTrackingId).first()
    if not tx:
        return {"status": "error", "message": "Transaction not found in local records"}
        
    tx.status = pesapal_status
    user_email = tx.email
    
    if pesapal_status == "COMPLETED":
        db_user = db.query(UserModel).filter(UserModel.email == user_email).first()
        if db_user:
            db_user.plan = "Pro"
            db.commit()
            return {
                "status": "success",
                "payment_status": "COMPLETED",
                "plan": "Pro",
                "message": "Payment successful! Upgraded to Pro"
            }
            
    db.commit()
    return {
        "status": "pending" if pesapal_status in ["PENDING", "PROCESSING"] else "failed",
        "payment_status": pesapal_status,
        "message": f"Payment status: {pesapal_status}"
    }

@app.post("/api/payment/mock-success")
def mock_payment_success(req: UpgradeRequest, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == req.email).first()
    if db_user:
        db_user.plan = "Pro"
        db.commit()
        return {"status": "upgraded", "plan": "Pro"}
    return {"status": "user_not_found"}

# --- TICKET ENDPOINTS ---

@app.get("/api/tickets")
async def get_tickets(email: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(TicketModel)
        if email:
            query = query.filter(TicketModel.owner == email)
        tickets = query.all()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, update: TicketUpdate, db: Session = Depends(get_db)):
    try:
        ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        ticket.status = update.status.upper()
        db.commit()
        db.refresh(ticket)
        return {"status": "success", "ticket": ticket}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tickets/{ticket_id}/reply")
def send_reply(ticket_id: str, payload: ReplyPayload, db: Session = Depends(get_db)):
    try:
        # 1. Load Ticket
        ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # 2. Get SaaS User (Owner)
        owner_email = ticket.owner
        if not owner_email:
             raise HTTPException(status_code=400, detail="Ticket has no owner linked")
             
        db_user = db.query(UserModel).filter(UserModel.email == owner_email).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Owner user not found")
            
        # 3. Check Platform & Tokens
        if payload.platform.lower() == "twitter":
            oauth = db_user.twitter_oauth
            if not oauth or not oauth.get("access_token"):
                raise HTTPException(status_code=403, detail="Twitter not connected or token expired")
            
            from execution.twitter_api_client import TwitterAPIClient
            client = TwitterAPIClient(oauth["access_token"])
            
            # Logic for reply_to_id
            # Use source_id from DB if available, otherwise try to extract or default to None
            reply_to_id = ticket.source_id
            
            # Fallback for legacy data (if ID was "twitter_123")
            if not reply_to_id and ticket_id.startswith("twitter_"):
                reply_to_id = ticket_id
            
            result = client.create_tweet(payload.content, reply_to_id=reply_to_id)
            
            if result:
                ticket.status = "DONE"
                db.commit()
                return {"status": "success", "data": result}
            else:
                raise HTTPException(status_code=500, detail="Failed to post to Twitter")
                
        else:
            raise HTTPException(status_code=400, detail=f"Platform {payload.platform} not supported yet")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Reply Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(email: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(TicketModel)
        if email:
            query = query.filter(TicketModel.owner == email)
            
        # Optimization: use count queries instead of loading all objects
        # But to be safe on logic match:
        tickets = query.all()
        total_count = len(tickets)
        done_count = len([t for t in tickets if t.status == "DONE"])
        open_count = total_count - done_count
        
        return {
            "total": total_count,
            "open": open_count,
            "done": done_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-reply")
def generate_reply_endpoint(req: ReplyRequest):
    try:
        result = llm_classifier.generate_reply(req.content, req.tone, req.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/pipeline/trigger")
async def trigger_pipeline(payload: Dict[str, str], db: Session = Depends(get_db)):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    import subprocess
    import sys
    
    # Run the pipeline script in the background (or foreground for feedback)
    # Using sys.executable to ensure we use the same python env
    try:
        # We run it detached or wait? For "Scan Now" user probably waits a bit or we return "Started"
        # Let's run it synchronously for immediate feedback since it's a "Scan Now" action
        # But for real prod, background task is better. 
        # Given the scope, let's run it with a timeout or let it run.
        # Actually, let's just trigger it and return success.
        
        # We need to find the script path.
        script_path = os.path.join(os.path.dirname(__file__), "..", "execution", "run_user_pipeline.py")
        
        # We use Popen to run in background
        subprocess.Popen([sys.executable, script_path, "--user_id", email])
        
        return {"status": "success", "message": "Pipeline started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
