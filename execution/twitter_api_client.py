"""
Twitter API Client using OAuth 2.0 tokens

This module provides a client for searching Twitter using user OAuth tokens.
Each user's token is used to search Twitter on their behalf, distributing
rate limits across users.

Rate Limits (per user):
- Search Recent Tweets: 180 requests per 15 minutes
- Our usage: 10 searches per day (Pro), 20 per day (Teams)
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional


class TwitterAPIClient:
    """Client for Twitter API v2 using OAuth 2.0 user tokens."""
    
    def __init__(self, access_token: str):
        """
        Initialize Twitter API client.
        
        Args:
            access_token: OAuth 2.0 access token for the user
        """
        self.access_token = access_token
        self.base_url = "https://api.twitter.com/2"
    
    def search_recent_tweets(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search recent tweets using user's OAuth token.
        
        Args:
            query: Search query (e.g., "customer support")
            max_results: Maximum number of tweets to return (max 100)
        
        Returns:
            List of tweet dictionaries in our standard format
        
        Rate Limit: 180 requests per 15 minutes per user
        """
        url = f"{self.base_url}/tweets/search/recent"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "LoopCloser/1.0"
        }
        
        params = {
            "query": query,
            "max_results": min(max_results, 100),  # API max is 100
            "tweet.fields": "created_at,author_id,public_metrics,lang",
            "expansions": "author_id",
            "user.fields": "username,name,verified"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Transform to our standard format
            tweets = []
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            for tweet in data.get("data", []):
                author = users.get(tweet["author_id"], {})
                tweets.append({
                    "id": f"twitter_{tweet['id']}",
                    "platform": "twitter",
                    "user_handle": f"@{author.get('username', 'unknown')}",
                    "content": tweet["text"],
                    "url": f"https://twitter.com/{author.get('username', 'i')}/status/{tweet['id']}",
                    "timestamp": tweet.get("created_at", datetime.now().isoformat()),
                    "metrics": tweet.get("public_metrics", {})
                })
            
            print(f"✅ Found {len(tweets)} tweets for query: {query}")
            return tweets
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"⚠️ Rate limit hit for query: {query}")
                return []
            elif e.response.status_code == 401:
                print(f"⚠️ Invalid or expired token for query: {query}")
                return []
            else:
                print(f"❌ HTTP error {e.response.status_code}: {e}")
                return []
        
        except Exception as e:
            print(f"❌ Error searching Twitter: {e}")
            return []
    
    def create_tweet(self, text: str, reply_to_id: Optional[str] = None) -> Optional[Dict]:
        """
        Post a tweet (or reply) using the user's OAuth token.
        
        Args:
            text: The content of the tweet.
            reply_to_id: The ID of the tweet to reply to (optional).
            
        Returns:
            The created tweet object from API, or None if failed.
        """
        url = f"{self.base_url}/tweets"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "LoopCloser/1.0"
        }
        
        payload = {"text": text}
        
        if reply_to_id:
             # Clean up ID if it has prefix
            clean_id = reply_to_id.replace("twitter_", "")
            payload["reply"] = {"in_reply_to_tweet_id": clean_id}
            
        try:
            print(f"🚀 Posting tweet: {payload}")
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"✅ Tweet successfully posted!")
                return response.json().get("data", {})
            else:
                print(f"❌ Failed to post tweet ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error posting tweet: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test if the access token is valid.
        
        Returns:
            True if token is valid, False otherwise
        """
        url = f"{self.base_url}/tweets/search/recent"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"query": "test", "max_results": 10}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=5)
            return response.status_code == 200
        except:
            return False


if __name__ == "__main__":
    # Test with a token (for development)
    import sys
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
        client = TwitterAPIClient(token)
        
        print("Testing connection...")
        if client.test_connection():
            print("✅ Token is valid")
            
            print("\nSearching for 'customer support'...")
            tweets = client.search_recent_tweets("customer support", max_results=5)
            
            for i, tweet in enumerate(tweets, 1):
                print(f"\n{i}. {tweet['user_handle']}")
                print(f"   {tweet['content'][:100]}...")
                print(f"   {tweet['url']}")
        else:
            print("❌ Token is invalid")
    else:
        print("Usage: python twitter_api_client.py <access_token>")
