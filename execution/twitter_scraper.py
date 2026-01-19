"""
Twitter Scraper Module for Pipeline

This module handles Twitter scraping using user OAuth tokens with quota enforcement.
Each user gets 10 searches/day (Pro) or 20 searches/day (Teams).
"""

import sys
import os
from datetime import datetime
from typing import List, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twitter_api_client import TwitterAPIClient


def get_twitter_quota_limits(plan: str) -> Dict[str, int]:
    """Return daily limits based on plan."""
    limits = {
        "Free": {"searches": 0, "tweets": 0},
        "Pro": {"searches": 10, "tweets": 100},
        "Teams": {"searches": 20, "tweets": 200}
    }
    return limits.get(plan, limits["Free"])


def reset_quota_if_needed(user: Dict) -> Dict:
    """Reset quota if it's a new day."""
    today = datetime.now().date().isoformat()
    quota = user.get("twitter_quota", {})
    
    
    if quota.get("last_reset") != today or "tweets_limit" not in quota:
        limits = get_twitter_quota_limits(user["plan"])
        user["twitter_quota"] = {
            "searches_today": 0,
            "tweets_today": 0,
            "last_reset": today,
            "searches_limit": limits["searches"],
            "tweets_limit": limits["tweets"]
        }
    return user


def can_search_twitter(user: Dict) -> tuple[bool, str]:
    """Check if user has quota remaining."""
    if user["plan"] == "Free":
        return False, "Twitter monitoring requires Pro plan"
    
    if "twitter" not in user.get("connected_platforms", []):
        return False, "Twitter not connected"
    
    oauth = user.get("twitter_oauth")
    if not oauth or not oauth.get("access_token"):
        return False, "No Twitter OAuth token found"
    
    quota = user.get("twitter_quota", {})
    searches_today = quota.get("searches_today", 0)
    searches_limit = quota.get("searches_limit", 0)
    
    if searches_today >= searches_limit:
        return False, f"Daily limit reached ({searches_limit} searches/day)"
    
    return True, "OK"


def search_twitter_for_user(user: Dict, max_tweets_per_search: int = 10) -> List[Dict]:
    """
    Search Twitter using user's OAuth token with quota enforcement.
    
    Args:
        user: User dictionary from database
        max_tweets_per_search: Max tweets to fetch per search query
    
    Returns:
        List of tweet dictionaries
    """
    # Reset quota if needed
    user = reset_quota_if_needed(user)
    
    # Check if user can search
    can_search, message = can_search_twitter(user)
    if not can_search:
        print(f"⚠️ Skipping Twitter for {user['email']}: {message}")
        return []
    
    # Get search terms from config
    config = user.get("config", {})
    twitter_keywords = config.get("twitter_keywords", "").split(",")
    twitter_keywords = [k.strip() for k in twitter_keywords if k.strip()]
    
    if not twitter_keywords:
        print(f"⚠️ No Twitter keywords configured for {user['email']}")
        return []
    
    # Initialize Twitter client with user's token
    oauth = user["twitter_oauth"]
    client = TwitterAPIClient(oauth["access_token"])
    
    # Search for each keyword
    all_tweets = []
    quota = user["twitter_quota"]
    
    for keyword in twitter_keywords:
        # Check quota before each search
        if quota["searches_today"] >= quota["searches_limit"]:
            print(f"⚠️ Daily search quota exhausted for {user['email']}")
            break
        
        # Check tweet quota
        tweets_remaining = quota["tweets_limit"] - quota.get("tweets_today", 0)
        if tweets_remaining <= 0:
            print(f"⚠️ Daily tweet quota exhausted for {user['email']}")
            break
        
        max_results = min(max_tweets_per_search, tweets_remaining)
        
        # Inject Product Name if configured (Strict Source Filtering)
        product_name = config.get("product_name", "").strip()
        search_query = keyword
        if product_name:
            search_query = f'"{product_name}" {keyword}'
        
        print(f"🐦 Searching Twitter for: '{search_query}' (max {max_results} tweets)")
        tweets = client.search_recent_tweets(search_query, max_results=max_results)
        
        # Update quota
        quota["searches_today"] += 1
        quota["tweets_today"] = quota.get("tweets_today", 0) + len(tweets)
        
        all_tweets.extend(tweets)
        
        print(f"   Found {len(tweets)} tweets. Quota: {quota['searches_today']}/{quota['searches_limit']} searches, {quota['tweets_today']}/{quota['tweets_limit']} tweets")
    
    # Save updated quota back to user
    user["twitter_quota"] = quota
    
    return all_tweets


if __name__ == "__main__":
    # Test with mock user
    mock_user = {
        "email": "test@example.com",
        "plan": "Pro",
        "connected_platforms": ["twitter"],
        "config": {
            "twitter_keywords": "customer support, help desk"
        },
        "twitter_oauth": {
            "access_token": "YOUR_TOKEN_HERE"
        },
        "twitter_quota": {
            "searches_today": 0,
            "tweets_today": 0,
            "searches_limit": 10,
            "last_reset": datetime.now().date().isoformat()
        }
    }
    
    print("Testing Twitter scraper...")
    tweets = search_twitter_for_user(mock_user)
    print(f"\n✅ Found {len(tweets)} total tweets")
    print(f"Quota used: {mock_user['twitter_quota']['searches_today']}/{mock_user['twitter_quota']['searches_limit']} searches")
