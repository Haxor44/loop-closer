# 🚀 Launch Checklist: The Loop Closer

Target Launch: Within 7 Days

## 🔴 Critical (Must Do)
- [ ] **Open Graph (OG) Assets**: Create `opengraph-image.png` and `twitter-image.png`. Without these, your links on X (Twitter) will just be plain text.
- [ ] **Favicon**: Replace the default Vercel/Next.js icon with a custom one.
- [ ] **Metadata Polish**: Update `layout.tsx` with specific tags for Twitter Cards.
- [ ] **Legal**: Add a basic Privacy Policy & Terms of Service (required for trust and some ad platforms).
- [ ] **Waitlist Export**: A simple Python script or API endpoint to export the `.csv` for CRM import.

## 🟡 High Priority (Should Do)
- [ ] **FastAPI Wrapper**: Implement `server/main.py`. Even if the dashboard isn't 100% finished, having the API live makes the product "real."
- [ ] **Analytics**: Integrate a simple script (PostHog or Google Analytics) to track page visits and conversion rates.
- [ ] **SEO Tags**: Keyword optimization for "AI social listening" and "churn reduction."
- [ ] **Custom Domain**: Get off `trycloudflare.com` and onto a real domain (e.g., `theloopcloser.com`).

## 🟢 Bonus (Next Version)
- [ ] **Product Hunt/X Assets**: 3-4 feature mockups (even if static) showing the "Dashboard" vision.
- [ ] **Post-Signup Referral**: (Already implemented but can be polished with a "leaderboard" concept).
- [ ] **Live Demo Loop**: A GIF/Video in the Hero section showing the bot replying to a real Reddit thread.

---

## Technical Audit Status
- [x] Landing Page (Waitlist + Features + Pricing)
- [x] Social Scrapers (Reddit, Insta, FB)
- [x] Dockerization (One-click VPS deploy)
- [x] n8n Webhook Connector
- [ ] **MISSING**: Backend API (FastAPI)
- [ ] **MISSING**: Professional Landing Page Assets (Icons/OG)
