#!/bin/bash

# Manual deployment script - Run this to deploy to production
# This will prompt for password

echo "🚀 Deploying to production server..."
echo ""

ssh root@38.242.194.79 << 'ENDSSH'
cd customer-service-saas

echo "📥 Pulling latest changes..."
git pull origin main

echo ""
echo "🔧 Initializing data files..."
chmod +x init-data-files.sh
./init-data-files.sh

echo ""
echo "🐳 Stopping containers..."
docker compose down

echo ""
echo "🔨 Rebuilding images (this takes 2-3 minutes)..."
docker compose build --no-cache

echo ""
echo "🚀 Starting containers..."
docker compose up -d

echo ""
echo "⏳ Waiting for services..."
sleep 10

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "📝 Backend logs:"
docker compose logs backend --tail=20
ENDSSH

echo ""
echo "✅ Deployment finished!"
echo "🌐 Frontend: https://theloopcloser.com"
echo "🔧 Backend: https://api.theloopcloser.com"
