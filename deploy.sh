#!/bin/bash

# Deployment script for The Loop Closer production server
# Usage: ./deploy.sh [server_user@server_ip]

set -e

SERVER=${1:-""}

if [ -z "$SERVER" ]; then
    echo "❌ Error: Server address required"
    echo "Usage: ./deploy.sh user@server_ip"
    echo "Example: ./deploy.sh root@theloopcloser.com"
    exit 1
fi

echo "🚀 Deploying to production server: $SERVER"

# SSH into server and run deployment commands
ssh $SERVER << 'ENDSSH'
    set -e
    
    echo "📁 Navigating to project directory..."
    cd /root/customer-service-saas || cd /home/*/customer-service-saas || cd ~/customer-service-saas
    
    echo "📥 Pulling latest changes from GitHub..."
    git pull origin main
    
    echo "🐳 Stopping containers..."
    docker-compose down
    
    echo "🔨 Rebuilding Docker images..."
    docker-compose build --no-cache
    
    echo "🚀 Starting containers..."
    docker-compose up -d
    
    echo "🧹 Cleaning up unused images..."
    docker image prune -f
    
    echo "✅ Deployment complete!"
    echo ""
    echo "📊 Container status:"
    docker-compose ps
ENDSSH

echo ""
echo "✅ Deployment finished successfully!"
echo "🌐 Frontend: https://theloopcloser.com"
echo "🔧 Backend: https://api.theloopcloser.com"
