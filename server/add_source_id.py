#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/loopcloser")

def add_source_id_column():
    print(f"Connecting to database at {DB_URL}...")
    try:
        engine = create_engine(DB_URL)
        conn = engine.connect()
        print("✅ Connected to Database")
        
        # Add the missing column
        query = text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS source_id TEXT;")
        conn.execute(query)
        conn.commit()
        print("✅ Added source_id column to tickets table")
        
        conn.close()
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    add_source_id_column()
