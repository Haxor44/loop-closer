"""
Automated Social Feedback Pipeline

This script orchestrates the full workflow:
1. Fetch social media posts (via Apify or mock data)
2. Classify each post with LLM (sentiment, sarcasm, intent)
3. Create/update tickets in the system
4. Store analysis for dashboard display

Run with: python3 execution/run_pipeline.py --query "@MyBrand"
"""

import argparse
import json
import os
import time
from datetime import datetime

# Import our modules
from llm_classifier import analyze_post, batch_analyze
from ticket_manager import find_similar_ticket, create_ticket, link_user, load_db, save_db

# Try to import apify_manager, but allow running without it
try:
    from apify_manager import scrape_all
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    print("Warning: apify_manager not available, using mock data")


ANALYZED_POSTS_FILE = "analyzed_posts.json"


def get_mock_posts():
    """Returns mock social media posts for testing."""
    return [
        {
            "id": "mock_001",
            "platform": "twitter",
            "user_handle": "@frustrated_user",
            "content": "Your app crashes every time I try to login. This is the third time this week!",
            "url": "https://twitter.com/status/mock_001",
            "timestamp": time.time()
        },
        {
            "id": "mock_002",
            "platform": "reddit",
            "user_handle": "u/happy_customer",
            "content": "Just discovered this tool and I'm loving it! The dark mode is amazing 🔥",
            "url": "https://reddit.com/r/saas/mock_002",
            "timestamp": time.time()
        },
        {
            "id": "mock_003",
            "platform": "twitter",
            "user_handle": "@sarcastic_dev",
            "content": "Oh great, another 'update' that broke everything. Quality work as always 👏",
            "url": "https://twitter.com/status/mock_003",
            "timestamp": time.time()
        },
        {
            "id": "mock_004",
            "platform": "twitter",
            "user_handle": "@feature_requester",
            "content": "Would be great if you could add CSV export. That would make my life so much easier!",
            "url": "https://twitter.com/status/mock_004",
            "timestamp": time.time()
        },
        {
            "id": "mock_005",
            "platform": "reddit",
            "user_handle": "u/confused_newbie",
            "content": "How do I reset my password? Can't find the option anywhere in the settings.",
            "url": "https://reddit.com/r/support/mock_005",
            "timestamp": time.time()
        }
    ]


def load_analyzed_posts():
    """Load previously analyzed posts to avoid duplicates."""
    if os.path.exists(ANALYZED_POSTS_FILE):
        with open(ANALYZED_POSTS_FILE, "r") as f:
            return json.load(f)
    return {"posts": [], "last_run": None}


def save_analyzed_posts(data):
    """Save analyzed posts."""
    with open(ANALYZED_POSTS_FILE, "w") as f:
        json.dump(data, indent=2, fp=f)


def get_analyzed_ids(data):
    """Get set of already analyzed post IDs."""
    return set(p.get("id") for p in data.get("posts", []))


def run_pipeline(query: str = None, use_mock: bool = False, max_items: int = 5):
    """
    Main pipeline function.
    
    1. Fetch posts
    2. Filter already processed
    3. Analyze with LLM
    4. Create tickets
    5. Store results
    """
    print("=" * 60)
    print("🚀 LOOP CLOSER PIPELINE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Query: {query or 'mock data'}")
    print()
    
    # Step 1: Fetch posts
    print("📥 Step 1: Fetching social media posts...")
    if use_mock or not APIFY_AVAILABLE or not query:
        posts = get_mock_posts()
        print(f"   Using mock data: {len(posts)} posts")
    else:
        posts = scrape_all(query, max_items)
        print(f"   Fetched {len(posts)} posts from Apify")
    
    if not posts:
        print("   ⚠️ No posts found. Exiting.")
        return
    
    # Step 2: Filter already processed
    print("\n🔍 Step 2: Filtering already processed posts...")
    analyzed_data = load_analyzed_posts()
    analyzed_ids = get_analyzed_ids(analyzed_data)
    
    new_posts = [p for p in posts if p.get("id") not in analyzed_ids]
    print(f"   New posts to process: {len(new_posts)} (skipped {len(posts) - len(new_posts)} duplicates)")
    
    if not new_posts:
        print("   ✅ No new posts. All caught up!")
        return
    
    # Step 3: Analyze with LLM
    print("\n🧠 Step 3: Analyzing posts with Gemini LLM...")
    analyzed_posts = []
    
    for i, post in enumerate(new_posts):
        print(f"   [{i+1}/{len(new_posts)}] Analyzing: {post['content'][:50]}...")
        
        analysis = analyze_post(
            post["content"],
            post.get("platform", "unknown"),
            post.get("user_handle", "unknown")
        )
        
        enriched = {**post, "analysis": analysis, "processed_at": time.time()}
        analyzed_posts.append(enriched)
        
        print(f"         Sentiment: {analysis['sentiment']}, Sarcasm: {analysis['sarcasm']}, Intent: {analysis['intent']}")
        
        # Rate limiting - be nice to API
        time.sleep(0.5)
    
    # Step 4: Create tickets
    print("\n🎫 Step 4: Creating/updating tickets...")
    tickets_created = 0
    tickets_linked = 0
    
    for post in analyzed_posts:
        analysis = post["analysis"]
        
        # Skip positive/neutral praise unless it's a question
        if analysis["sentiment"] == "positive" and analysis["intent"] == "praise":
            print(f"   ✓ Skipping praise post (no ticket needed)")
            continue
        
        # Check for similar existing ticket
        existing_id = find_similar_ticket(analysis["summary"])
        
        if existing_id:
            # Link user to existing ticket
            link_user(existing_id, post["user_handle"])
            post["ticket_id"] = existing_id
            tickets_linked += 1
        else:
            # Create new ticket
            ticket_id = create_ticket(analysis["summary"], post["user_handle"])
            post["ticket_id"] = ticket_id
            tickets_created += 1
    
    print(f"   Created: {tickets_created} new tickets")
    print(f"   Linked: {tickets_linked} users to existing tickets")
    
    # Step 5: Save results
    print("\n💾 Step 5: Saving results...")
    analyzed_data["posts"].extend(analyzed_posts)
    analyzed_data["last_run"] = datetime.now().isoformat()
    save_analyzed_posts(analyzed_data)
    print(f"   Saved {len(analyzed_posts)} analyzed posts to {ANALYZED_POSTS_FILE}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Posts processed: {len(analyzed_posts)}")
    print(f"Tickets created: {tickets_created}")
    print(f"Users linked: {tickets_linked}")
    
    # Print analysis summary
    print("\n📊 Analysis Summary:")
    sentiments = {}
    intents = {}
    sarcasm_count = 0
    
    for post in analyzed_posts:
        a = post["analysis"]
        sentiments[a["sentiment"]] = sentiments.get(a["sentiment"], 0) + 1
        intents[a["intent"]] = intents.get(a["intent"], 0) + 1
        if a["sarcasm"]:
            sarcasm_count += 1
    
    print(f"   Sentiment: {sentiments}")
    print(f"   Intent: {intents}")
    print(f"   Sarcasm detected: {sarcasm_count}")
    
    return analyzed_posts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the social feedback pipeline")
    parser.add_argument("--query", help="Search query for social media", required=False)
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real scraping")
    parser.add_argument("--max", type=int, default=5, help="Max items to fetch per platform")
    
    args = parser.parse_args()
    
    run_pipeline(args.query, args.mock, args.max)
