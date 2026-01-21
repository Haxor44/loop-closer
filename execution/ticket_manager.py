import argparse
import json
import os
import sys
import time
import difflib

# Add parent directory to path to import from server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database import SessionLocal
from server.models import Ticket

def get_db():
    return SessionLocal()

def find_similar_ticket(text, owner_email=None):
    db = get_db()
    try:
        query = db.query(Ticket)
        if owner_email:
            query = query.filter(Ticket.owner == owner_email)
            
        tickets = query.all()
        
        best_match = None
        highest_ratio = 0.0
        
        for ticket in tickets:
            ratio = difflib.SequenceMatcher(None, ticket.summary, text).ratio()
            if ratio > 0.6: # loose threshold for demo
                if ratio > highest_ratio:
                    highest_ratio = ratio
                    best_match = ticket
        
        if best_match:
            print(f"Found existing ticket: {best_match.id} (Match: {int(highest_ratio*100)}%)")
            return best_match.id
        return None
    finally:
        db.close()

def classify_ticket(text):
    text = text.lower()
    if any(k in text for k in ["bug", "error", "fail", "broken", "crash"]):
        return "BUG"
    if any(k in text for k in ["feature", "add", "can you", "suggest"]):
        return "FEATURE"
    return "QUESTION"

def create_ticket(summary, user, owner_email=None, source_id=None):
    db = get_db()
    try:
        # Generate ID - simpler to use UUID or just count? 
        # For consistency with migration, we'll use TICKET-count logic or UUID.
        # DB Auto-increment? ID is string "TICKET-XXX".
        # Let's count existing.
        count = db.query(Ticket).count()
        new_id = f"TICKET-{count + 101 + int(time.time() % 1000)}" # Randomize slightly to avoid collision in simple counter
        
        new_ticket = Ticket(
            id=new_id,
            source_id=source_id,
            summary=summary,
            status="OPEN",
            type=classify_ticket(summary),
            urgency="low",
            linked_users=[user],
            created_at=time.time(),
            notified=False,
            owner=owner_email
        )
        
        db.add(new_ticket)
        db.commit()
        print(f"Created new ticket: {new_id} (Owner: {owner_email})")
        return new_id
    except Exception as e:
        db.rollback()
        print(f"Error creating ticket: {e}")
        return None
    finally:
        db.close()

def link_user(ticket_id, user):
    db = get_db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            # Check if user in linked_users
            # generic array append
            if user not in ticket.linked_users:
                # SQLAlchemy MutableList need explicit flagging or reassignment
                # Easier to fetch, append, reassign
                current_users = list(ticket.linked_users)
                current_users.append(user)
                ticket.linked_users = current_users
                db.commit()
                print(f"Linked {user} to {ticket_id}")
            else:
                print(f"User {user} already linked to {ticket_id}")
        else:
            print("Ticket not found")
    finally:
        db.close()

def get_resolved_tickets():
    db = get_db()
    try:
        tickets = db.query(Ticket).filter(Ticket.status == "DONE", Ticket.notified == False).all()
        # Convert to dict for JSON output
        result = []
        for t in tickets:
            result.append({
                "id": t.id,
                "summary": t.summary,
                "status": t.status,
                "owner": t.owner
            })
        print(json.dumps(result, indent=2))
    finally:
        db.close()

def mark_done(ticket_id):
    """Helper to simulate work being done"""
    db = get_db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.status = "DONE"
            db.commit()
            print(f"Marked {ticket_id} as DONE")
        else:
            print("Ticket not found")
    finally:
        db.close()

def mark_notified(ticket_id):
    db = get_db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.notified = True
            db.commit()
    finally:
        db.close()

# Stub for load_db/save_db to keep compatibility if other modules import them
# but they shouldn't run logic anymore.
def load_db():
    print("WARNING: load_db() is deprecated, use DB connection")
    return {"tickets": []}

def save_db(db):
    print("WARNING: save_db() is deprecated, use DB connection")
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    # find_similar
    p_find = subparsers.add_parser("find_similar_ticket")
    p_find.add_argument("text")
    
    # create
    p_create = subparsers.add_parser("create_ticket")
    p_create.add_argument("summary")
    p_create.add_argument("user")
    
    # link
    p_link = subparsers.add_parser("link_social_to_ticket")
    p_link.add_argument("ticket_id")
    p_link.add_argument("user")
    
    # get_resolved
    p_resolved = subparsers.add_parser("get_resolved_tickets")
    
    # mark_done (admin tool)
    p_done = subparsers.add_parser("mark_done")
    p_done.add_argument("ticket_id")

    # mark_notified (system tool)
    p_notified = subparsers.add_parser("mark_notified")
    p_notified.add_argument("ticket_id")

    args = parser.parse_args()
    
    if args.command == "find_similar_ticket":
        find_similar_ticket(args.text)
    elif args.command == "create_ticket":
        create_ticket(args.summary, args.user)
    elif args.command == "link_social_to_ticket":
        link_user(args.ticket_id, args.user)
    elif args.command == "get_resolved_tickets":
        get_resolved_tickets()
    elif args.command == "mark_done":
        mark_done(args.ticket_id)
    elif args.command == "mark_notified":
        mark_notified(args.ticket_id)
