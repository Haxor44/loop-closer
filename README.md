# Loop Closer

> AI-powered social media feedback monitoring and customer service platform

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-proprietary-blue)

## Overview

Loop Closer is a B2B SaaS tool that helps businesses monitor and respond to customer feedback across social media platforms including Reddit, X (Twitter), TikTok, and more.

### Key Features

- **Multi-platform monitoring**: Aggregate mentions from Reddit, X, TikTok, Instagram
- **AI-powered analysis**: Sentiment analysis, sarcasm detection, intent classification using Google Gemini
- **Automated ticket creation**: Convert social posts into actionable support tickets
- **Response suggestions**: AI-generated response drafts to help teams respond faster
- **Urgency scoring**: Prioritize high-urgency issues automatically

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js App   │────▶│   FastAPI       │────▶│   LLM Classifier│
│   (Frontend)    │     │   (Backend)     │     │   (Gemini)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   NextAuth      │     │   Social APIs   │
│   (OAuth)       │     │   (Reddit, X)   │
└─────────────────┘     └─────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 16, React, TailwindCSS
- **Backend**: Python FastAPI
- **Authentication**: NextAuth.js (Google, Reddit, X OAuth)
- **AI/ML**: Google Gemini API for NLP
- **Payments**: PesaPal Integration
- **Scraping**: Apify (Reddit, social platforms)

## Reddit API Usage

This application uses the Reddit API for **read-only** purposes:

1. **Search**: Query Reddit for posts/comments mentioning brand keywords
2. **Read**: Fetch post content, comments, and metadata
3. **OAuth**: Authenticate users via Reddit OAuth for personalized monitoring

**We do NOT:**
- Post or comment on behalf of users
- Vote or modify any Reddit content
- Scrape beyond API rate limits
- Store sensitive user data

## Project Structure

```
customer-service-saas/
├── client/                    # Next.js frontend
│   ├── app/                   # App router pages
│   │   ├── dashboard/         # Main dashboard
│   │   ├── admin/             # Admin panel
│   │   └── api/auth/          # NextAuth routes
│   └── components/            # React components
├── server/                    # FastAPI backend
│   ├── main.py                # API endpoints
│   └── pesapal_manager.py     # Payment integration
├── execution/                 # Pipeline scripts
│   ├── llm_classifier.py      # Gemini AI classifier
│   ├── run_pipeline.py        # Automated ingestion
│   ├── ticket_manager.py      # Ticket CRUD
│   └── apify_manager.py       # Social media scraping
└── directives/                # Workflow documentation
```

## Setup

### Prerequisites
- Node.js 20+
- Python 3.10+
- Docker (optional)

### Environment Variables

Create `.env` in the root:
```
GEMINI_API_KEY=your_gemini_key
APIFY_API_TOKEN=your_apify_token
```

Create `client/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_secret
GOOGLE_CLIENT_ID=your_google_id
GOOGLE_CLIENT_SECRET=your_google_secret
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
TWITTER_CLIENT_ID=your_twitter_id
TWITTER_CLIENT_SECRET=your_twitter_secret
```

### Running Locally

```bash
# Start with Docker
docker compose up -d

# Or manually:
# Backend
cd server && pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd client && npm install && npm run dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tickets` | GET | List all tickets |
| `/api/tickets/{id}` | PATCH | Update ticket status |
| `/api/users/sync` | POST | Sync user from OAuth |
| `/api/payment/upgrade` | POST | Initiate payment |

## Pipeline

Run the social feedback pipeline:

```bash
cd execution

# With mock data
python3 run_pipeline.py --mock

# With real Reddit data
python3 run_pipeline.py --query "@YourBrand"
```

## License

Proprietary - All rights reserved

## Contact

For API access or questions: evolmalek04@gmail.com.
