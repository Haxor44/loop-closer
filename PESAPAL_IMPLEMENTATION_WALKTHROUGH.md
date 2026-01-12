# Pesapal Payment Integration - Implementation Walkthrough

This document provides a complete step-by-step guide for implementing Pesapal Payment Gateway (API v3.0) in a Laravel application.

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Environment Configuration](#step-1-environment-configuration)
4. [Step 2: Create Configuration File](#step-2-create-configuration-file)
5. [Step 3: Database Migrations](#step-3-database-migrations)
6. [Step 4: Create Payment Models](#step-4-create-payment-models)
7. [Step 5: Pesapal Service Class](#step-5-pesapal-service-class)
8. [Step 6: Payment Service Class](#step-6-payment-service-class)
9. [Step 7: Payment Controller](#step-7-payment-controller)
10. [Step 8: Routes Configuration](#step-8-routes-configuration)
11. [Step 9: Logging Configuration](#step-9-logging-configuration)
12. [Step 10: Testing Setup](#step-10-testing-setup)
13. [Payment Flow](#payment-flow)
14. [Security Considerations](#security-considerations)
15. [Troubleshooting](#troubleshooting)

---

## Overview

This implementation enables payment processing using Pesapal's REST API v3.0, supporting:
- M-Pesa payments
- Credit/Debit card payments
- Webhook notifications (IPN)
- Transaction status tracking
- Payment audit trail

**Architecture:**
- **PesapalService**: Handles all direct API communication with Pesapal
- **PaymentService**: Business logic and database operations
- **PaymentController**: HTTP endpoints for payment operations
- **PaymentTransaction Model**: Audit trail for all transactions

---

## Prerequisites

1. **Pesapal Account**
   - Sign up at https://www.pesapal.com
   - Get Consumer Key and Consumer Secret from dashboard
   - Use sandbox credentials for testing

2. **Laravel Application**
   - Laravel 10+ recommended
   - GuzzleHTTP for API calls: `composer require guzzlehttp/guzzle`

3. **ngrok** (for testing webhooks locally)
   - Download from https://ngrok.com

---

## Step 1: Environment Configuration

Add these variables to your `.env` file:

```env
# Pesapal Configuration
PESAPAL_ENVIRONMENT=sandbox
PESAPAL_SANDBOX_URL=https://cybqa.pesapal.com/pesapalv3
PESAPAL_LIVE_URL=https://pay.pesapal.com/v3
PESAPAL_CONSUMER_KEY=your_consumer_key_here
PESAPAL_CONSUMER_SECRET=your_consumer_secret_here
PESAPAL_CALLBACK_URL=http://localhost:8000/api/payment/callback
```

**Notes:**
- `PESAPAL_ENVIRONMENT`: Use `sandbox` for testing, `live` for production
- `PESAPAL_CALLBACK_URL`: This will be your webhook endpoint (update with ngrok URL during testing)
- Never commit credentials to version control

---

## Step 2: Create Configuration File

Create `config/pesapal.php`:

```php
<?php

return [
    'environment' => env('PESAPAL_ENVIRONMENT', 'sandbox'),

    'sandbox' => [
        'url' => env('PESAPAL_SANDBOX_URL', 'https://cybqa.pesapal.com/pesapalv3'),
        'consumer_key' => env('PESAPAL_CONSUMER_KEY'),
        'consumer_secret' => env('PESAPAL_CONSUMER_SECRET'),
    ],

    'live' => [
        'url' => env('PESAPAL_LIVE_URL', 'https://pay.pesapal.com/v3'),
        'consumer_key' => env('PESAPAL_CONSUMER_KEY'),
        'consumer_secret' => env('PESAPAL_CONSUMER_SECRET'),
    ],

    'callback_url' => env('PESAPAL_CALLBACK_URL', 'http://localhost:8000/api/payment/callback'),

    'endpoints' => [
        'request_token' => '/api/Auth/RequestToken',
        'register_ipn' => '/api/URLSetup/RegisterIPN',
        'get_ipn_list' => '/api/URLSetup/GetIpnList',
        'submit_order' => '/api/Transactions/SubmitOrderRequest',
        'transaction_status' => '/api/Transactions/GetTransactionStatus',
    ],

    'token_cache_key' => 'pesapal_auth_token',
    'token_cache_minutes' => 50, // Pesapal tokens expire in 60 min, cache for 50

    'currency' => 'KES',
    'request_timeout' => 30,
    'log_channel' => 'pesapal',
];
```

---

## Step 3: Database Migrations

### Migration 1: Add Payment Fields to Your Main Table

Assuming you have a table like `service_requests`, `orders`, or `bookings`:

```bash
php artisan make:migration add_payment_fields_to_service_requests_table
```

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('service_requests', function (Blueprint $table) {
            $table->string('payment_method')->nullable()->after('status');
            $table->string('pesapal_order_tracking_id')->nullable()->unique()->after('payment_method');
            $table->string('pesapal_transaction_id')->nullable()->unique()->after('pesapal_order_tracking_id');
            $table->string('payment_status')->default('pending')->after('pesapal_transaction_id');
            $table->timestamp('payment_initiated_at')->nullable()->after('payment_status');
            $table->timestamp('payment_completed_at')->nullable()->after('payment_initiated_at');
            $table->text('payment_error_message')->nullable()->after('payment_completed_at');
        });
    }

    public function down(): void
    {
        Schema::table('service_requests', function (Blueprint $table) {
            $table->dropUnique(['pesapal_order_tracking_id']);
            $table->dropUnique(['pesapal_transaction_id']);
            $table->dropColumn([
                'payment_method',
                'pesapal_order_tracking_id',
                'pesapal_transaction_id',
                'payment_status',
                'payment_initiated_at',
                'payment_completed_at',
                'payment_error_message',
            ]);
        });
    }
};
```

### Migration 2: Create Payment Transactions Table

```bash
php artisan make:migration create_payment_transactions_table
```

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('payment_transactions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('service_request_id')->constrained()->onDelete('cascade');
            $table->string('pesapal_order_tracking_id')->nullable()->unique();
            $table->string('pesapal_transaction_id')->nullable()->unique();
            $table->string('payment_method');
            $table->decimal('amount', 10, 2);
            $table->string('currency')->default('KES');
            $table->string('status')->default('pending');
            $table->json('response_data')->nullable();
            $table->timestamps();

            $table->index('pesapal_transaction_id');
            $table->index('status');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('payment_transactions');
    }
};
```

**Run migrations:**
```bash
php artisan migrate
```

---

## Step 4: Create Payment Models

Create `app/Models/PaymentTransaction.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class PaymentTransaction extends Model
{
    protected $fillable = [
        'service_request_id',
        'pesapal_order_tracking_id',
        'pesapal_transaction_id',
        'payment_method',
        'amount',
        'currency',
        'status',
        'response_data',
    ];

    protected $casts = [
        'amount' => 'decimal:2',
        'response_data' => 'array',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];

    public function serviceRequest(): BelongsTo
    {
        return $this->belongsTo(ServiceRequest::class);
    }
}
```

**Update your main model** (e.g., `ServiceRequest`):

```php
// Add to fillable array
protected $fillable = [
    // ... existing fields
    'payment_method',
    'pesapal_order_tracking_id',
    'pesapal_transaction_id',
    'payment_status',
    'payment_initiated_at',
    'payment_completed_at',
    'payment_error_message',
];

// Add relationship
public function paymentTransaction()
{
    return $this->hasOne(PaymentTransaction::class);
}
```

---

## Step 5: Pesapal Service Class

Create `app/Services/PesapalService.php`:

```php
<?php

namespace App\Services;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class PesapalService
{
    protected Client $client;
    protected string $baseUrl;
    protected string $consumerKey;
    protected string $consumerSecret;
    protected string $callbackUrl;

    public function __construct()
    {
        $environment = config('pesapal.environment');
        $config = config("pesapal.{$environment}");

        $this->baseUrl = $config['url'];
        $this->consumerKey = $config['consumer_key'];
        $this->consumerSecret = $config['consumer_secret'];
        $this->callbackUrl = config('pesapal.callback_url');

        $this->client = new Client([
            'timeout' => config('pesapal.request_timeout', 30),
        ]);
    }

    /**
     * Get OAuth2 authentication token from Pesapal (with caching)
     */
    public function getAuthToken(): ?string
    {
        try {
            $cacheKey = config('pesapal.token_cache_key');
            $token = Cache::get($cacheKey);

            if ($token) {
                Log::channel('pesapal')->debug('Using cached auth token');
                return $token;
            }

            Log::channel('pesapal')->info('Requesting new auth token from Pesapal');

            $endpoint = config('pesapal.endpoints.request_token');
            $response = $this->client->post("{$this->baseUrl}{$endpoint}", [
                'json' => [
                    'consumer_key' => $this->consumerKey,
                    'consumer_secret' => $this->consumerSecret,
                ],
            ]);

            $body = json_decode($response->getBody()->getContents(), true);

            if (isset($body['token'])) {
                $token = $body['token'];
                $cacheMinutes = config('pesapal.token_cache_minutes', 50);
                Cache::put($cacheKey, $token, now()->addMinutes($cacheMinutes));

                Log::channel('pesapal')->info('Auth token obtained successfully');
                return $token;
            }

            Log::channel('pesapal')->error('No token in Pesapal response', ['response' => $body]);
            return null;
        } catch (GuzzleException $e) {
            Log::channel('pesapal')->error('Failed to get auth token', [
                'error' => $e->getMessage(),
            ]);
            return null;
        }
    }

    /**
     * Submit order to Pesapal for payment
     */
    public function submitOrder(array $orderData): ?array
    {
        try {
            $token = $this->getAuthToken();
            if (!$token) {
                Log::channel('pesapal')->error('Cannot submit order: No auth token');
                return null;
            }

            Log::channel('pesapal')->info('Submitting order to Pesapal', ['order_data' => $orderData]);

            $endpoint = config('pesapal.endpoints.submit_order');
            $response = $this->client->post("{$this->baseUrl}{$endpoint}", [
                'headers' => [
                    'Authorization' => "Bearer {$token}",
                    'Content-Type' => 'application/json',
                ],
                'json' => $orderData,
            ]);

            $body = json_decode($response->getBody()->getContents(), true);

            if (isset($body['order_tracking_id'])) {
                Log::channel('pesapal')->info('Order submitted successfully', [
                    'tracking_id' => $body['order_tracking_id'],
                ]);
                return $body;
            }

            Log::channel('pesapal')->error('Failed to submit order', ['response' => $body]);
            return null;
        } catch (GuzzleException $e) {
            Log::channel('pesapal')->error('Error submitting order', [
                'error' => $e->getMessage(),
            ]);
            return null;
        }
    }

    /**
     * Get transaction status from Pesapal
     */
    public function getTransactionStatus(string $trackingId): ?array
    {
        try {
            $token = $this->getAuthToken();
            if (!$token) {
                return null;
            }

            $endpoint = config('pesapal.endpoints.transaction_status');
            $response = $this->client->get("{$this->baseUrl}{$endpoint}", [
                'headers' => [
                    'Authorization' => "Bearer {$token}",
                    'Content-Type' => 'application/json',
                ],
                'query' => [
                    'orderTrackingId' => $trackingId,
                ],
            ]);

            $body = json_decode($response->getBody()->getContents(), true);

            if (isset($body['payment_status_description'])) {
                return $body;
            }

            return null;
        } catch (GuzzleException $e) {
            Log::channel('pesapal')->error('Error fetching transaction status', [
                'error' => $e->getMessage(),
            ]);
            return null;
        }
    }

    /**
     * Format your model data into Pesapal order format
     */
    public function formatOrderData($serviceRequest): array
    {
        $serviceRequest->load(['service', 'user']);

        $uniqueId = (string) $serviceRequest->id . '-' . $serviceRequest->request_number;

        $payload = [
            'id' => $uniqueId,
            'currency' => config('pesapal.currency'),
            'amount' => (float) $serviceRequest->quoted_price,
            'description' => $serviceRequest->service->name,
            'callback_url' => $this->callbackUrl,
            'billing_address' => [
                'email_address' => $serviceRequest->user->email,
                'phone_number' => $serviceRequest->phone,
                'country_code' => 'KE',
                'first_name' => explode(' ', $serviceRequest->user->name)[0],
                'last_name' => explode(' ', $serviceRequest->user->name, 2)[1] ?? '',
                'line_1' => $serviceRequest->address,
                'city' => $serviceRequest->city ?? '',
            ],
        ];

        return $payload;
    }

    /**
     * Validate webhook data (basic validation)
     */
    public function isWebhookValid(array $data, string $signature = ''): bool
    {
        $requiredFields = ['id', 'pesapal_transaction_id', 'status', 'amount', 'currency'];

        foreach ($requiredFields as $field) {
            if (!isset($data[$field])) {
                return false;
            }
        }

        return true;
    }

    /**
     * Get Pesapal redirect URL for payment
     */
    public function getRedirectUrl(string $trackingId): string
    {
        return rtrim($this->baseUrl, '/') . '/api/Transactions/SubmitOrder?orderTrackingId=' . $trackingId;
    }
}
```

---

## Step 6: Payment Service Class

Create `app/Services/PaymentService.php`:

```php
<?php

namespace App\Services;

use App\Models\PaymentTransaction;
use App\Models\ServiceRequest;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class PaymentService
{
    protected PesapalService $pesapalService;

    public function __construct(PesapalService $pesapalService)
    {
        $this->pesapalService = $pesapalService;
    }

    /**
     * Initiate payment process
     */
    public function initiatePayment(ServiceRequest $serviceRequest, string $paymentMethod): ?array
    {
        try {
            DB::beginTransaction();

            Log::channel('pesapal')->info('Initiating payment', [
                'service_request_id' => $serviceRequest->id,
                'payment_method' => $paymentMethod,
            ]);

            // Format order data
            $orderData = $this->pesapalService->formatOrderData($serviceRequest);

            // Submit to Pesapal
            $pesapalResponse = $this->pesapalService->submitOrder($orderData);

            if (!$pesapalResponse || !isset($pesapalResponse['order_tracking_id'])) {
                DB::rollBack();
                return null;
            }

            $trackingId = $pesapalResponse['order_tracking_id'];

            // Update service request
            $serviceRequest->update([
                'payment_method' => $paymentMethod,
                'pesapal_order_tracking_id' => $trackingId,
                'payment_status' => 'pending',
                'payment_initiated_at' => now(),
            ]);

            // Create transaction record
            PaymentTransaction::create([
                'service_request_id' => $serviceRequest->id,
                'pesapal_order_tracking_id' => $trackingId,
                'payment_method' => $paymentMethod,
                'amount' => $serviceRequest->quoted_price,
                'currency' => config('pesapal.currency'),
                'status' => 'pending',
                'response_data' => $pesapalResponse,
            ]);

            DB::commit();

            $redirectUrl = $pesapalResponse['redirect_url'] ?? $this->pesapalService->getRedirectUrl($trackingId);

            return [
                'success' => true,
                'tracking_id' => $trackingId,
                'redirect_url' => $redirectUrl,
            ];
        } catch (\Exception $e) {
            DB::rollBack();
            Log::channel('pesapal')->error('Error initiating payment', [
                'error' => $e->getMessage(),
            ]);
            return null;
        }
    }

    /**
     * Handle payment callback from Pesapal webhook
     */
    public function handlePaymentCallback(array $pesapalData): array
    {
        try {
            Log::channel('pesapal')->info('Processing payment callback', ['data' => $pesapalData]);

            // Validate webhook
            if (!$this->pesapalService->isWebhookValid($pesapalData)) {
                return ['status' => 'error', 'message' => 'Invalid webhook data'];
            }

            DB::beginTransaction();

            // Find service request
            $serviceRequest = ServiceRequest::where('pesapal_order_tracking_id', $pesapalData['id'])->first();

            if (!$serviceRequest) {
                DB::rollBack();
                return ['status' => 'error', 'message' => 'Service request not found'];
            }

            // Map Pesapal status to our status
            $status = strtolower($pesapalData['payment_status_description'] ?? $pesapalData['status'] ?? 'pending');
            $paymentStatus = match ($status) {
                'completed' => 'completed',
                'failed', 'invalid', 'reversed' => 'failed',
                default => 'pending',
            };

            // Update service request
            $serviceRequest->update([
                'pesapal_transaction_id' => $pesapalData['pesapal_transaction_id'] ?? null,
                'payment_status' => $paymentStatus,
                'payment_completed_at' => $paymentStatus === 'completed' ? now() : null,
                'payment_error_message' => $paymentStatus === 'failed' ? ($pesapalData['error'] ?? 'Payment failed') : null,
            ]);

            // Update transaction
            $transaction = PaymentTransaction::where('service_request_id', $serviceRequest->id)->first();
            if ($transaction) {
                $transaction->update([
                    'pesapal_transaction_id' => $pesapalData['pesapal_transaction_id'] ?? null,
                    'status' => $paymentStatus,
                    'response_data' => $pesapalData,
                ]);
            }

            DB::commit();

            return ['status' => 'success', 'message' => 'Transaction processed'];
        } catch (\Exception $e) {
            DB::rollBack();
            Log::channel('pesapal')->error('Error processing callback', ['error' => $e->getMessage()]);
            return ['status' => 'error', 'message' => 'Error processing transaction'];
        }
    }

    /**
     * Update payment status by querying Pesapal
     */
    public function updatePaymentStatus(ServiceRequest $serviceRequest): bool
    {
        try {
            if (!$serviceRequest->pesapal_order_tracking_id) {
                return false;
            }

            $status = $this->pesapalService->getTransactionStatus($serviceRequest->pesapal_order_tracking_id);

            if (!$status) {
                return false;
            }

            $pesapalStatus = strtolower($status['payment_status_description'] ?? 'pending');
            $paymentStatus = match ($pesapalStatus) {
                'completed' => 'completed',
                'failed', 'invalid', 'reversed' => 'failed',
                default => 'pending',
            };

            if ($serviceRequest->payment_status !== $paymentStatus) {
                $serviceRequest->update([
                    'pesapal_transaction_id' => $status['pesapal_transaction_id'] ?? null,
                    'payment_status' => $paymentStatus,
                    'payment_completed_at' => $paymentStatus === 'completed' ? now() : null,
                ]);
            }

            return true;
        } catch (\Exception $e) {
            Log::channel('pesapal')->error('Error updating payment status', ['error' => $e->getMessage()]);
            return false;
        }
    }
}
```

---

## Step 7: Payment Controller

Create `app/Http/Controllers/PaymentController.php`:

```php
<?php

namespace App\Http\Controllers;

use App\Models\ServiceRequest;
use App\Services\PaymentService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class PaymentController extends Controller
{
    protected PaymentService $paymentService;

    public function __construct(PaymentService $paymentService)
    {
        $this->paymentService = $paymentService;
    }

    /**
     * Initiate payment for a service request
     */
    public function initiate(ServiceRequest $serviceRequest, Request $request)
    {
        // Verify ownership
        if ($serviceRequest->user_id !== auth()->id()) {
            abort(403, 'Unauthorized access');
        }

        $validated = $request->validate([
            'payment_method' => 'required|in:mpesa,credit_card',
        ]);

        // Initiate payment
        $result = $this->paymentService->initiatePayment(
            $serviceRequest,
            $validated['payment_method']
        );

        if (!$result || !$result['success']) {
            return redirect()->back()
                ->with('error', 'Failed to initiate payment. Please try again.');
        }

        // Redirect to Pesapal
        return redirect($result['redirect_url']);
    }

    /**
     * Webhook callback from Pesapal
     */
    public function callback(Request $request)
    {
        $data = $request->all();

        Log::channel('pesapal')->info('Pesapal callback received', [
            'method' => $request->method(),
            'data' => $data,
        ]);

        // If GET request (redirect), forward to verify
        if ($request->isMethod('get')) {
            $trackingId = $data['OrderTrackingId'] ?? $data['orderTrackingId'] ?? null;
            if ($trackingId) {
                return redirect()->route('payment.return', ['OrderTrackingId' => $trackingId]);
            }
            return redirect()->route('dashboard')->with('error', 'No tracking ID provided');
        }

        // POST webhook - process callback
        $result = $this->paymentService->handlePaymentCallback($data);
        return response()->json($result, 200);
    }

    /**
     * Check payment status (AJAX)
     */
    public function status(ServiceRequest $serviceRequest)
    {
        if ($serviceRequest->user_id !== auth()->id()) {
            abort(403);
        }

        $this->paymentService->updatePaymentStatus($serviceRequest);
        $serviceRequest->refresh();

        return response()->json([
            'status' => $serviceRequest->payment_status,
            'message' => match ($serviceRequest->payment_status) {
                'completed' => 'Payment successful!',
                'failed' => 'Payment failed: ' . $serviceRequest->payment_error_message,
                'pending' => 'Payment is pending...',
                default => 'Unknown status',
            },
        ]);
    }

    /**
     * Verify payment after returning from Pesapal
     */
    public function verify(Request $request)
    {
        $trackingId = $request->query('OrderTrackingId');

        if (!$trackingId) {
            return redirect()->route('dashboard')
                ->with('error', 'No payment tracking ID provided');
        }

        $serviceRequest = ServiceRequest::where('pesapal_order_tracking_id', $trackingId)->first();

        if (!$serviceRequest || $serviceRequest->user_id !== auth()->id()) {
            abort(403);
        }

        // Query Pesapal for status
        $this->paymentService->updatePaymentStatus($serviceRequest);
        $serviceRequest->refresh();

        if ($serviceRequest->payment_status === 'completed') {
            return redirect()->route('dashboard')
                ->with('success', 'Payment successful!');
        } elseif ($serviceRequest->payment_status === 'failed') {
            return redirect()->route('dashboard')
                ->with('error', 'Payment failed: ' . $serviceRequest->payment_error_message);
        } else {
            return redirect()->route('dashboard')
                ->with('info', 'Payment is still being processed.');
        }
    }
}
```

---

## Step 8: Routes Configuration

Add to `routes/web.php`:

```php
use App\Http\Controllers\PaymentController;

// Authenticated payment routes
Route::middleware(['auth', 'verified'])->group(function () {
    Route::post('/payment/initiate/{serviceRequest}', [PaymentController::class, 'initiate'])
        ->name('payment.initiate');
    Route::get('/payment/status/{serviceRequest}', [PaymentController::class, 'status'])
        ->name('payment.status');
    Route::get('/payment/return', [PaymentController::class, 'verify'])
        ->name('payment.return');
});

// Webhook - public route (no CSRF)
Route::post('/api/payment/callback', [PaymentController::class, 'callback'])
    ->name('payment.callback')
    ->withoutMiddleware(\App\Http\Middleware\VerifyCsrfToken::class);

// Also allow GET for Pesapal redirect
Route::get('/api/payment/callback', [PaymentController::class, 'callback'])
    ->name('payment.callback.get')
    ->withoutMiddleware(\App\Http\Middleware\VerifyCsrfToken::class);
```

**Update CSRF exceptions** in `app/Http/Middleware/VerifyCsrfToken.php`:

```php
protected $except = [
    'api/payment/callback',
];
```

---

## Step 9: Logging Configuration

Add to `config/logging.php`:

```php
'channels' => [
    // ... existing channels

    'pesapal' => [
        'driver' => 'daily',
        'path' => storage_path('logs/pesapal.log'),
        'level' => env('LOG_LEVEL', 'debug'),
        'days' => 14,
    ],
],
```

---

## Step 10: Testing Setup

### Local Testing with ngrok

1. **Start your Laravel server:**
```bash
php artisan serve
```

2. **In another terminal, start ngrok:**
```bash
ngrok http 8000
```

3. **Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

4. **Update `.env`:**
```env
PESAPAL_CALLBACK_URL=https://abc123.ngrok.io/api/payment/callback
```

5. **Clear config cache:**
```bash
php artisan config:clear
```

6. **Test the flow:**
   - Create a service request/order
   - Select payment method
   - Complete payment on Pesapal sandbox
   - Monitor logs: `tail -f storage/logs/pesapal.log`
   - Check ngrok dashboard: `http://localhost:4040`

---

## Payment Flow

### Complete Payment Journey

1. **Customer creates order/service request**
2. **Customer selects payment method** (M-Pesa or Card)
3. **Application calls `PaymentController::initiate()`**
4. **PaymentService creates database records** (transaction)
5. **PesapalService submits order** to Pesapal API
6. **Customer redirected to Pesapal** payment page
7. **Customer completes payment** on Pesapal
8. **Pesapal sends webhook** to `/api/payment/callback`
9. **PaymentService processes webhook** and updates status
10. **Customer redirected back** to application
11. **Application verifies status** via `PaymentController::verify()`
12. **Dashboard shows success/failure**

### Status Flow

```
pending → completed (success)
pending → failed (failure)
```

---

## Security Considerations

1. **HTTPS Only**: All production URLs must use HTTPS
2. **Credentials**: Never commit API keys to version control
3. **CSRF**: Webhook endpoint must be CSRF-exempt
4. **Authorization**: Always verify user ownership of requests
5. **Database Transactions**: Use DB transactions for atomicity
6. **Webhook Validation**: Validate all webhook data
7. **Token Caching**: Auth tokens cached for 50 minutes
8. **Logging**: Never log sensitive data (credentials, tokens)

---

## Troubleshooting

### Issue: "Failed to initiate payment"
- Check Pesapal credentials in `.env`
- Verify sandbox account is active
- Check logs: `tail -f storage/logs/pesapal.log`

### Issue: Webhook not received
- Ensure ngrok is running
- Verify callback URL in `.env`
- Check ngrok dashboard: `http://localhost:4040`
- Verify firewall allows inbound traffic

### Issue: Payment status not updating
- Manually check status: `GET /payment/status/{id}`
- Query Pesapal transaction history
- Review API logs

### Issue: "Order tracking ID already exists"
- Ensure unique order IDs per transaction
- Check for duplicate submissions

---

## Production Checklist

Before going live:

- [ ] Get Pesapal live account approval
- [ ] Update `.env` with live credentials
- [ ] Set `PESAPAL_ENVIRONMENT=live`
- [ ] Update callback URL to production domain (HTTPS)
- [ ] Test complete flow in staging
- [ ] Set up monitoring and alerts
- [ ] Configure proper logging
- [ ] Implement webhook signature verification (enhanced security)
- [ ] Add rate limiting to webhook endpoint
- [ ] Set up SSL certificates
- [ ] Test error scenarios

---

## Additional Resources

- **Pesapal Docs**: https://developer.pesapal.com/
- **API Reference**: https://developer.pesapal.com/how-to-integrate/e-commerce/api-30-json/api-reference
- **ngrok Docs**: https://ngrok.com/docs
- **Laravel Docs**: https://laravel.com/docs

---

## Summary

This implementation provides:
- ✅ Complete Pesapal v3 API integration
- ✅ Support for M-Pesa and card payments
- ✅ Webhook handling (IPN notifications)
- ✅ Transaction audit trail
- ✅ Status polling and verification
- ✅ Comprehensive logging
- ✅ Database transaction safety
- ✅ Error handling and recovery
- ✅ Production-ready architecture

**Total files created:**
- 1 config file
- 2 migrations
- 1 model
- 2 service classes
- 1 controller
- Route definitions
- Logging configuration

**Ready to implement!** 🚀
