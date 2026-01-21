#!/bin/bash

echo "🔍 Checking Pesapal logs on production server..."
echo "Password: Theman22"
echo ""

ssh root@38.242.194.79 << 'ENDSSH'
cd customer-service-saas

echo "📝 Recent Pesapal API logs:"
docker compose logs backend --tail=200 | grep -B 3 -A 10 "Submitting order\|Response status\|Response body\|Parsed data\|Error submitting" | tail -100

echo ""
echo "=================================="
echo ""
echo "📊 Summary:"
echo "If you see 'Response body' above, that shows what Pesapal returned"
echo "If empty, try making a payment and run this script again"
ENDSSH
