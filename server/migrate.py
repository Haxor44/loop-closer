import json
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Connection
# Default to localhost for running migration from host machine
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/loopcloser")

def migrate():
    print(f"Connecting to database at {DB_URL}...")
    try:
        engine = create_engine(DB_URL)
        conn = engine.connect()
        print("✅ Connected to Database")
    except Exception as e:
        print(f"❌ Failed to connect to DB: {e}")
        return

    # 1. Migrate Users
    print("\n📦 Migrating Users and Transactions...")
    users_db_path = os.path.join(os.path.dirname(__file__), "users_db.json")
    
    if os.path.exists(users_db_path):
        with open(users_db_path, "r") as f:
            data = json.load(f)
            
            # Users
            for u in data.get("users", []):
                try:
                    # Prepare data
                    config = json.dumps(u.get("config", {}))
                    platforms = u.get("connected_platforms", [])
                    oauth = json.dumps(u.get("twitter_oauth", {}))
                    quota = json.dumps(u.get("twitter_quota", {}))
                    
                    # Insert
                    query = text("""
                        INSERT INTO users (email, name, plan, joined_at, config, connected_platforms, twitter_oauth, twitter_quota)
                        VALUES (:email, :name, :plan, :joined_at, :config, :platforms, :oauth, :quota)
                        ON CONFLICT (email) DO UPDATE 
                        SET name = EXCLUDED.name, plan = EXCLUDED.plan, config = EXCLUDED.config, 
                            twitter_oauth = EXCLUDED.twitter_oauth, twitter_quota = EXCLUDED.twitter_quota;
                    """)
                    conn.execute(query, {
                        "email": u["email"],
                        "name": u.get("name", "Unknown"),
                        "plan": u.get("plan", "Free"),
                        "joined_at": u.get("joined_at", 0.0),
                        "config": config,
                        "platforms": platforms,
                        "oauth": oauth,
                        "quota": quota
                    })
                    print(f"   ✓ Use imported: {u['email']}")
                except Exception as e:
                    print(f"   ❌ Failed to import user {u['email']}: {e}")

            # Transactions
            for t in data.get("transactions", []):
                try:
                    query = text("""
                        INSERT INTO transactions (tracking_id, merchant_reference, email, status, created_at)
                        VALUES (:tid, :mref, :email, :status, :created_at)
                        ON CONFLICT (tracking_id) DO NOTHING;
                    """)
                    conn.execute(query, {
                        "tid": t["tracking_id"],
                        "mref": t["merchant_reference"],
                        "email": t["email"],
                        "status": t["status"],
                        "created_at": t.get("created_at", 0.0)
                    })
                except Exception as e:
                    print(f"   ❌ Failed transaction {t['tracking_id']}: {e}")
            print(f"   ✓ Parsed {len(data.get('transactions', []))} transactions")
            
            conn.commit()

    # 2. Migrate Tickets
    print("\n🎫 Migrating Tickets...")
    # mock_db.json likely in project root or execution folder, checking root based on previous searches
    mock_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_db.json")
    
    if os.path.exists(mock_db_path):
        with open(mock_db_path, "r") as f:
            data = json.load(f)
            
            for t in data.get("tickets", []):
                try:
                    query = text("""
                        INSERT INTO tickets (id, summary, status, type, urgency, linked_users, created_at, notified, owner)
                        VALUES (:id, :summary, :status, :type, :urgency, :linked_users, :created_at, :notified, :owner)
                        ON CONFLICT (id) DO NOTHING;
                    """)
                    
                    conn.execute(query, {
                        "id": t["id"],
                        "summary": t["summary"],
                        "status": t.get("status", "OPEN"),
                        "type": t.get("type", "QUESTION"),
                        "urgency": t.get("urgency", "low"),
                        "linked_users": t.get("linked_users", []),
                        "created_at": t.get("created_at", 0.0),
                        "notified": t.get("notified", False),
                        "owner": t.get("owner")
                    })
                    print(f"   ✓ Ticket imported: {t['id']}")
                except Exception as e:
                    print(f"   ❌ Failed to import ticket {t['id']}: {e}")
            
            conn.commit()
    else:
        print(f"⚠️  mock_db.json not found at {mock_db_path}")

    print("\n✅ Migration Complete!")
    conn.close()

if __name__ == "__main__":
    migrate()
