#!/bin/bash

echo "🚀 Running Database Migration on Production"
echo "Password: Theman22"
echo ""

ssh root@38.242.194.79 << 'ENDSSH'
cd customer-service-saas

echo "🔍 Checking data files..."
ls -lh users_db.json mock_db.json server/users_db.json 2>/dev/null || echo "No data files found yet"

echo ""
echo "🚀 Running database migration..."
docker compose exec -T backend python /app/server/migrate.py

echo ""
echo "📊 Verifying migration results..."
docker compose exec -T db psql -U user -d loopcloser -c "SELECT COUNT(*) as users FROM users;"
docker compose exec -T db psql -U user -d loopcloser -c "SELECT COUNT(*) as tickets FROM tickets;"
docker compose exec -T db psql -U user -d loopcloser -c "SELECT COUNT(*) as transactions FROM transactions;"

echo ""
echo "✅ Migration complete! Check the counts above."
ENDSSH
