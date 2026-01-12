import argparse
import json
import os
import time
import difflib

DB_FILE = "mock_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"tickets": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, indent=2, fp=f)

def find_similar_ticket(text):
    db = load_db()
    best_match = None
    highest_ratio = 0.0
    
    for ticket in db["tickets"]:
        ratio = difflib.SequenceMatcher(None, ticket["summary"], text).ratio()
        if ratio > 0.6: # loose threshold for demo
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = ticket
    
    if best_match:
        print(f"Found existing ticket: {best_match['id']} (Match: {int(highest_ratio*100)}%)")
        return best_match["id"]
    return None

def create_ticket(summary, user):
    db = load_db()
    new_id = f"TICKET-{len(db['tickets']) + 101}"
    new_ticket = {
        "id": new_id,
        "summary": summary,
        "status": "OPEN",
        "type": classify_ticket(summary),
        "linked_users": [user],
        "created_at": time.time(),
        "notified": False
    }

def classify_ticket(text):
    text = text.lower()
    if any(k in text for k in ["bug", "error", "fail", "broken", "crash"]):
        return "BUG"
    if any(k in text for k in ["feature", "add", "can you", "suggest"]):
        return "FEATURE"
    return "QUESTION"
    db["tickets"].append(new_ticket)
    save_db(db)
    print(f"Created new ticket: {new_id}")
    return new_id

def link_user(ticket_id, user):
    db = load_db()
    for ticket in db["tickets"]:
        if ticket["id"] == ticket_id:
            if user not in ticket["linked_users"]:
                ticket["linked_users"].append(user)
                save_db(db)
                print(f"Linked {user} to {ticket_id}")
            else:
                print(f"User {user} already linked to {ticket_id}")
            return
    print("Ticket not found")

def get_resolved_tickets():
    db = load_db()
    resolved = []
    for ticket in db["tickets"]:
        if ticket["status"] == "DONE" and not ticket.get("notified", False):
            resolved.append(ticket)
    print(json.dumps(resolved, indent=2))

def mark_done(ticket_id):
    """Helper to simulate work being done"""
    db = load_db()
    found = False
    for ticket in db["tickets"]:
        if ticket["id"] == ticket_id:
            ticket["status"] = "DONE"
            found = True
            break
    if found:
        save_db(db)
        print(f"Marked {ticket_id} as DONE")
    else:
        print("Ticket not found")

def mark_notified(ticket_id):
    db = load_db()
    for ticket in db["tickets"]:
        if ticket["id"] == ticket_id:
            ticket["notified"] = True
            save_db(db)
            return

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
