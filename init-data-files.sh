#!/bin/bash

# Initialize data files if they don't exist
# This ensures Docker volumes have files to mount

echo "🔧 Initializing data files..."

# Create users_db.json if it doesn't exist
if [ ! -f "users_db.json" ]; then
    echo "Creating users_db.json..."
    echo '{"users": [], "transactions": []}' > users_db.json
fi

if [ ! -f "server/users_db.json" ]; then
    echo "Creating server/users_db.json..."
    echo '{"users": [], "transactions": []}' > server/users_db.json
fi

# Create mock_db.json if it doesn't exist
if [ ! -f "mock_db.json" ]; then
    echo "Creating mock_db.json..."
    echo '{"tickets": []}' > mock_db.json
fi

# Create analyzed_posts.json if it doesn't exist
if [ ! -f "execution/analyzed_posts.json" ]; then
    echo "Creating execution/analyzed_posts.json..."
    mkdir -p execution
    echo '[]' > execution/analyzed_posts.json
fi

# Create waitlist.csv if it doesn't exist
if [ ! -f "client/waitlist.csv" ]; then
    echo "Creating client/waitlist.csv..."
    echo 'email,timestamp' > client/waitlist.csv
fi

echo "✅ Data files initialized!"
