from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from typing import List, Optional
from pydantic import BaseModel
import time

# Add execution directory to path so we can import ticket_manager
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "execution"))
import ticket_manager

app = FastAPI(title="The Loop Closer API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
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
    for u in db["users"]:
        if u["email"] == user.email:
            return {"status": "exists", "user": u}
    
    # Create new user
    new_user = user.dict()
    new_user["joined_at"] = time.time()
    db["users"].append(new_user)
    save_users_db(db)
    return {"status": "created", "user": new_user}

# PAYMENT ENDPOINTS
from pesapal_manager import create_pesapal_order, get_transaction_status

class UpgradeRequest(BaseModel):
    email: str

@app.post("/api/payment/upgrade")
def upgrade_user(req: UpgradeRequest):
    # 1. Create Order
    # 1000 KES ~ 10 USD
    order = create_pesapal_order(req.email, amount=1000.00, currency="KES")
    
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
            # We need to render an HTML redirect or return a 302
            # FastAPI RedirectResponse
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"http://localhost:3000/dashboard/settings?payment=success&plan=Pro")
            
    # For other statuses or failure
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"http://localhost:3000/dashboard/settings?payment={pesapal_status.lower()}")

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
async def get_tickets():
    try:
        db = ticket_manager.load_db()
        return db.get("tickets", [])
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
        
        ticket_manager.save_db(db)
        return {"message": f"Ticket {ticket_id} updated to {update.status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    try:
        db = ticket_manager.load_db()
        tickets = db.get("tickets", [])
        return {
            "total": len(tickets),
            "open": len([t for t in tickets if t["status"] == "OPEN"]),
            "done": len([t for t in tickets if t["status"] == "DONE"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
