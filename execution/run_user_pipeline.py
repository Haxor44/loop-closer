"""
User-Based Pipeline Runner

This script runs the monitoring pipeline for ALL users based on their configurations.
Each user's keywords, subreddits, and Twitter terms are used to fetch and analyze posts.

Usage:
    python3 execution/run_user_pipeline.py
"""

import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (root directory)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_classifier import analyze_post
from ticket_manager import find_similar_ticket, create_ticket, link_user
from twitter_scraper import search_twitter_for_user

# Database paths
USERS_DB_PATH = os.path.join(os.path.dirname(__file__), "../server/users_db.json")
ANALYZED_POSTS_FILE = os.path.join(os.path.dirname(__file__), "analyzed_posts.json")


def load_users_db():
    """Load users database."""
    with open(USERS_DB_PATH, "r") as f:
        return json.load(f)


def save_users_db(db):
    """Save users database."""
    with open(USERS_DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def load_analyzed_posts():
    """Load previously analyzed posts."""
    if os.path.exists(ANALYZED_POSTS_FILE):
        with open(ANALYZED_POSTS_FILE, "r") as f:
            return json.load(f)
    return {"posts": [], "last_run": None}


def save_analyzed_posts(data):
    """Save analyzed posts."""
    with open(ANALYZED_POSTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_analyzed_ids(data):
    """Get set of already analyzed post IDs."""
    return set(p.get("id") for p in data.get("posts", []))


def run_pipeline_for_user(user, analyzed_ids):
    """
    Run pipeline for a single user.
    
    Returns:
        List of newly analyzed posts
    """
    print(f"\n{'='*60}")
    print(f"👤 Processing user: {user['email']}")
    print(f"   Plan: {user['plan']}")
    print(f"   Connected: {', '.join(user.get('connected_platforms', []))}")
    print(f"{'='*60}\n")
    
    all_posts = []
    
    # 1. Twitter scraping (if connected)
    if "twitter" in user.get("connected_platforms", []):
        print("🐦 Fetching Twitter posts...")
        tweets = search_twitter_for_user(user, max_tweets_per_search=10)
        all_posts.extend(tweets)
        print(f"   Found {len(tweets)} tweets\n")
    
    # 2. Reddit scraping (Config-based, no OAuth required)
    config = user.get("config", {})
    subreddits = config.get("subreddits", "").split(",")
    # Check if we have subreddits configured (even if empty string exists)
    has_reddit_config = any(s.strip() for s in subreddits)
    
    if has_reddit_config or "reddit" in user.get("connected_platforms", []):
        print("🔴 Fetching Reddit posts...")
        
        # Import Reddit scraper
        try:
            from apify_manager import scrape_reddit
            
            config = user.get("config", {})
            keywords = config.get("keywords", "").split(",")
            subreddits = config.get("subreddits", "").split(",")
            
            # Clean up keywords and subreddits
            keywords = [k.strip() for k in keywords if k.strip()]
            subreddits = [s.strip() for s in subreddits if s.strip()]
            product_name = config.get("product_name", "").strip()
            
            reddit_posts = []
            
            # Search by keywords (Inject Product Name if configured)
            for keyword in keywords[:3]:  # Limit to 3 keywords to avoid quota
                if keyword:
                    query = keyword
                    if product_name:
                        query = f'"{product_name}" {keyword}'
                    
                    print(f"   🔎 Searching Reddit for: {query}")
                    posts = scrape_reddit(query, max_items=5)
                    reddit_posts.extend(posts)
            
            # Search by subreddits
            for subreddit in subreddits[:2]:  # Limit to 2 subreddits
                if subreddit:
                    # Remove r/ prefix if present
                    subreddit = subreddit.replace("r/", "")
                    # For subreddits, we search generally unless product_name is very specific, 
                    # but usually subreddit implies context. 
                    # Option 3 (Hybrid) implies we grab everything in the subreddit and let LLM filter.
                    # So we leave subreddit search broad.
                    posts = scrape_reddit(f"subreddit:{subreddit}", max_items=5)
                    reddit_posts.extend(posts)
            
            all_posts.extend(reddit_posts)
            print(f"   Found {len(reddit_posts)} Reddit posts\n")
            
        except Exception as e:
            print(f"   ⚠️ Reddit scraping failed: {e}\n")
    
    # Filter already processed posts
    new_posts = [p for p in all_posts if p.get("id") not in analyzed_ids]
    
    if not new_posts:
        print(f"✅ No new posts for {user['email']}\n")
        return []
    
    print(f"📊 Analyzing {len(new_posts)} new posts...\n")
    
    # Analyze posts
    analyzed_posts = []
    config = user.get("config", {}) # Ensure config is available
    
    for i, post in enumerate(new_posts, 1):
        print(f"   [{i}/{len(new_posts)}] {post['content'][:50]}...")
        
        analysis = analyze_post(
            post["content"],
            post.get("platform", "unknown"),
            post.get("user_handle", "unknown"),
            product_name=config.get("product_name"),
            brand_voice=config.get("brand_voice")
        )
        
        enriched = {
            **post,
            "analysis": analysis,
            "processed_at": datetime.now().isoformat(),
            "for_user": user["email"]
        }
        analyzed_posts.append(enriched)
        
        print(f"         → {analysis['sentiment']}, {analysis['intent']}, Sarcasm: {analysis['sarcasm']}")
    
    # Create tickets
    print(f"\n🎫 Creating tickets...")
    tickets_created = 0
    tickets_linked = 0
    
    for post in analyzed_posts:
        analysis = post["analysis"]
        
        # Skip positive praise
        if analysis["sentiment"] == "positive" and analysis["intent"] == "praise":
            continue

        # Skip irrelevant posts (Strict Filtering)
        if analysis.get("ticket_type") == "IRRELEVANT":
            continue
        
        # Check for similar ticket
        existing_id = find_similar_ticket(analysis["summary"], owner_email=user["email"])
        
        if existing_id:
            link_user(existing_id, post["user_handle"])
            post["ticket_id"] = existing_id
            tickets_linked += 1
        else:
            ticket_id = create_ticket(analysis["summary"], post["user_handle"], owner_email=user["email"])
            post["ticket_id"] = ticket_id
            tickets_created += 1
    
    print(f"   Created: {tickets_created} new tickets")
    print(f"   Linked: {tickets_linked} to existing tickets\n")
    
    return analyzed_posts


def run_pipeline_for_all_users():
    """Run pipeline for all users."""
    print("=" * 60)
    print("🚀 LOOP CLOSER USER PIPELINE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Load databases
    db = load_users_db()
    analyzed_data = load_analyzed_posts()
    analyzed_ids = get_analyzed_ids(analyzed_data)
    
    all_analyzed_posts = []
    
    # Process each user
    for user in db.get("users", []):
        try:
            analyzed_posts = run_pipeline_for_user(user, analyzed_ids)
            all_analyzed_posts.extend(analyzed_posts)
        except Exception as e:
            print(f"❌ Error processing {user['email']}: {e}\n")
            continue
    
    # Save results
    if all_analyzed_posts:
        analyzed_data["posts"].extend(all_analyzed_posts)
        analyzed_data["last_run"] = datetime.now().isoformat()
        save_analyzed_posts(analyzed_data)
        print(f"💾 Saved {len(all_analyzed_posts)} analyzed posts\n")
    
    # Save updated quotas
    save_users_db(db)
    
    # Summary
    print("=" * 60)
    print("✅ PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Users processed: {len(db.get('users', []))}")
    print(f"Posts analyzed: {len(all_analyzed_posts)}")
    
    return all_analyzed_posts


if __name__ == "__main__":
    run_pipeline_for_all_users()
