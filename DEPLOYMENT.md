# Deployment Instructions for `theloopcloser.com`

## 1. Environment Variables

Update your production environment variables (e.g., in Vercel, Railway, or your `.env.production` file).

### Frontend Variables
| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.theloopcloser.com` |
| `NEXTAUTH_URL` | `https://theloopcloser.com` |

### Backend Variables
| Variable | Value |
|----------|-------|
| `FRONTEND_URL` | `https://theloopcloser.com` |
| `PESAPAL_CALLBACK_URL` | `https://api.theloopcloser.com/api/payment/callback` |

---

## 2. OAuth Configurations (Critical)

You must update the "Callback/Redirect URLs" in your 3rd-party developer dashboards.

### Google Console
*   **Authorized Redirect URI:** `https://theloopcloser.com/api/auth/callback/google`

### Reddit Apps
*   **Redirect URI:** `https://theloopcloser.com/api/auth/callback/reddit`

### X (Twitter) Developer Portal
*   **Callback URL:** `https://theloopcloser.com/api/auth/callback/twitter`
*   **Website URL:** `https://theloopcloser.com`

### TikTok Developers
*   **Redirect URL:** `https://theloopcloser.com/api/integrations/tiktok/callback`

---

## 3. Backend Configuration

### PesaPal
In `server/pesapal_manager.py`, ensure this line matches your production API domain:
```python
CALLBACK_URL = "https://api.theloopcloser.com/api/payment/callback"
```

### CORS Policies
In `server/main.py`, update the `origins` list to allow your new domain:
```python
origins = [
    "https://theloopcloser.com",
    "https://www.theloopcloser.com",
    "http://localhost:3000" # Optional: keep for local dev
]
```

---

## 4. Hosting Strategy

### Option A: Vercel (Frontend) + Railway (Backend)
1.  **Frontend:** Deploy `client/` folder to **Vercel**. Connect your custom domain `theloopcloser.com`.
2.  **Backend:** Deploy `server/` folder to **Railway/Render/DigitalOcean**. Map it to `api.theloopcloser.com`.

### Option B: VPS (All-in-One)
Use Docker Compose to run both behind Nginx:
*   Map `theloopcloser.com` -> Next.js container (Port 3000)
*   Map `api.theloopcloser.com` -> FastAPI container (Port 8000)
