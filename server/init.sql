-- Users Table
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    name TEXT,
    plan TEXT DEFAULT 'Free',
    joined_at FLOAT,
    config JSONB DEFAULT '{}',
    connected_platforms TEXT[],
    twitter_oauth JSONB,
    twitter_quota JSONB
);

-- Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    summary TEXT,
    status TEXT, -- OPEN, DONE, IN_PROGRESS
    type TEXT,   -- BUG, FEATURE, QUESTION
    urgency TEXT, -- low, medium, high
    linked_users TEXT[],
    created_at FLOAT,
    notified BOOLEAN DEFAULT FALSE,
    owner TEXT REFERENCES users(email)
);

-- Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    tracking_id UUID PRIMARY KEY,
    merchant_reference UUID,
    email TEXT REFERENCES users(email),
    status TEXT,
    created_at FLOAT
);
