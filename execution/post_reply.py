import argparse
import sys
import subprocess

def post_reply(user, ticket_id, message):
    """
    Simulates posting a reply to the social platform.
    """
    print(f"--- POSTING REPLY TO {user} ---")
    print(f"Content: {message}")
    print(f"Context: Ticket {ticket_id}")
    print("--------------------------------")
    
    # Mark as notified to prevent duplicate updates
    # We call ticket_manager.py mark_notified
    cmd = [sys.executable, "execution/ticket_manager.py", "mark_notified", ticket_id]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="User handle")
    parser.add_argument("ticket_id", help="Ticket ID")
    parser.add_argument("message", help="The message content")
    args = parser.parse_args()
    
    post_reply(args.user, args.ticket_id, args.message)
