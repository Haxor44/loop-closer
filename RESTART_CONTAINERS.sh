#!/bin/bash

echo "🔄 Restarting containers to apply database changes..."
echo "Password: Theman22"
echo ""

ssh root@38.242.194.79 << 'ENDSSH'
cd customer-service-saas

echo "🔄 Restarting backend container..."
docker compose restart backend

echo ""
echo "⏳ Waiting for backend to start..."
sleep 8

echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "📝 Backend logs:"
docker compose logs backend --tail=30

echo ""
echo "🧪 Testing API endpoint..."
curl -s http://localhost:8000/api/users | head -20

echo ""
echo "✅ Restart complete!"
echo ""
echo "🌐 Now check: https://theloopcloser.com"
ENDSSH
