# PesaPal Production Setup Guide

## Current Configuration

The application is now configured to use PesaPal with environment-based settings.

### Environment Variables

Located in `.env` file:

```bash
# PesaPal Configuration
PESAPAL_ENV=sandbox                    # Change to "live" for production
PESAPAL_CONSUMER_KEY=<your_key>        # Replace with production key
PESAPAL_CONSUMER_SECRET=<your_secret>  # Replace with production secret
PESAPAL_CALLBACK_URL=https://api.theloopcloser.com/api/payment/callback
```

### Current Setup (Sandbox/Testing)

- **Environment**: Sandbox (testing)
- **API Base URL**: https://cybqa.pesapal.com/pesapalv3
- **Callback URL**: https://api.theloopcloser.com/api/payment/callback
- **Test Credentials**: Using sandbox credentials

## Switching to Production

### Step 1: Get Production Credentials

1. **Open a PesaPal Business Account**:
   - Visit: https://www.pesapal.com/
   - Register for a merchant account
   - Complete KYC verification

2. **Obtain Production Credentials**:
   - After account approval, PesaPal will send your production `consumer_key` and `consumer_secret` to your merchant email
   - Keep these credentials secure

### Step 2: Update Environment Variables

On your VPS, update the `.env` file:

```bash
ssh root@38.242.194.79
cd /root/customer-service-saas
nano .env
```

Update these values:

```bash
PESAPAL_ENV=live
PESAPAL_CONSUMER_KEY=<your_production_consumer_key>
PESAPAL_CONSUMER_SECRET=<your_production_consumer_secret>
PESAPAL_CALLBACK_URL=https://api.theloopcloser.com/api/payment/callback
```

### Step 3: Register Callback URL with PesaPal

The callback URL is automatically registered when the first payment is initiated. However, you can also register it manually through the PesaPal dashboard.

**Important**: Ensure your callback URL is publicly accessible:
- **URL**: https://api.theloopcloser.com/api/payment/callback
- **Method**: GET
- **Purpose**: PesaPal redirects users here after payment with transaction status

### Step 4: Restart Application

After updating the environment variables:

```bash
cd /root/customer-service-saas
docker compose down
docker compose up -d --build
```

### Step 5: Test Payment Flow

1. **Initiate Test Payment**:
   - Go to https://theloopcloser.com/dashboard/settings
   - Click "Upgrade to Pro"
   - Complete payment using a real payment method

2. **Verify Callback**:
   - After payment, PesaPal will redirect to your callback URL
   - The system will automatically upgrade the user to Pro
   - User will be redirected to dashboard with success message

3. **Check Logs**:
   ```bash
   docker compose logs -f backend
   ```

## API Endpoints

### Production URLs

When `PESAPAL_ENV=live`:
- **Auth Token**: https://pay.pesapal.com/v3/api/Auth/RequestToken
- **Submit Order**: https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest
- **Transaction Status**: https://pay.pesapal.com/v3/api/Transactions/GetTransactionStatus
- **Register IPN**: https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN

### Application Endpoints

- **Upgrade User**: `POST /api/payment/upgrade`
  - Creates payment order
  - Returns redirect URL for PesaPal payment page

- **Payment Callback**: `GET /api/payment/callback`
  - Receives callback from PesaPal
  - Updates transaction status
  - Upgrades user if payment successful

- **Verify Payment**: `GET /api/payment/verify?OrderTrackingId=<id>`
  - Check payment status
  - Used by frontend for AJAX verification

## Security Notes

1. **Credentials Storage**:
   - Production credentials are stored in `.env` file
   - Never commit `.env` to version control
   - Keep backups in secure location

2. **Callback URL Security**:
   - Callback URL is public (required by PesaPal)
   - Always verify transaction status with PesaPal API
   - Don't trust client-side data

3. **SSL/TLS**:
   - All communication uses HTTPS
   - Certificates are auto-renewed via Let's Encrypt

## Testing vs Production

| Feature | Sandbox | Production |
|---------|---------|------------|
| Base URL | cybqa.pesapal.com | pay.pesapal.com |
| Credentials | Test credentials | Live credentials from PesaPal |
| Payment | Test payments (no real money) | Real payments |
| Environment Variable | `PESAPAL_ENV=sandbox` | `PESAPAL_ENV=live` |

## Troubleshooting

### Issue: Payment not working

1. Check environment variables are set correctly
2. Verify callback URL is publicly accessible
3. Check backend logs: `docker compose logs -f backend`
4. Ensure credentials are valid for the environment (sandbox vs live)

### Issue: Callback not received

1. Verify callback URL is registered with PesaPal
2. Check firewall/security groups allow incoming HTTPS traffic
3. Test callback URL manually: `curl https://api.theloopcloser.com/api/payment/callback`

### Issue: Token generation fails

1. Verify `PESAPAL_CONSUMER_KEY` and `PESAPAL_CONSUMER_SECRET` are correct
2. Check if using correct credentials for environment (sandbox vs live)
3. Ensure base URL matches environment

## Monitoring

### View Payment Logs

```bash
docker compose logs -f backend | grep "💰"
```

### Check Transaction Database

Transactions are stored in `users_db.json`:
```bash
cat /root/customer-service-saas/users_db.json | jq '.transactions'
```

## Support

- **PesaPal Documentation**: https://developer.pesapal.com/
- **PesaPal Support**: support@pesapal.com
- **Your App Logs**: `docker compose logs -f backend`
