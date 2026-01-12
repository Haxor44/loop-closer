import os
import requests
import time
import json

# Using standard HTTP instead of apify-client to avoid dependency issues
BASE_URL = "https://api.apify.com/v2"

def get_token():
    # Load from .env manually since we don't have python-dotenv
    # or rely on environment var if set
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("APIFY_API_TOKEN="):
                        token = line.strip().split("=", 1)[1]
                        break
        except Exception:
            pass
    return token

def run_actor(actor_id, run_input):
    token = get_token()
    if not token:
        raise ValueError("APIFY_API_TOKEN not found in environment or .env")
    
    url = f"{BASE_URL}/acts/{actor_id}/runs?token={token}"
    headers = {"Content-Type": "application/json"}
    
    print(f"Starting Apify Actor: {actor_id}...")
    response = requests.post(url, json=run_input, headers=headers)
    
    if response.status_code != 201:
        raise Exception(f"Failed to start actor: {response.text}")
    
    run_data = response.json()["data"]
    run_id = run_data["id"]
    print(f"Actor started. Run ID: {run_id}")
    return run_id

def wait_for_run(run_id):
    token = get_token()
    url = f"{BASE_URL}/actor-runs/{run_id}?token={token}"
    
    while True:
        response = requests.get(url)
        data = response.json()["data"]
        status = data["status"]
        
        if status == "SUCCEEDED":
            print("Run succeeded!")
            return data["defaultDatasetId"]
        elif status in ["FAILED", "ABORTED"]:
            raise Exception(f"Run failed with status: {status}")
        
        print(f"Run status: {status}. Waiting 5s...")
        time.sleep(5)

def get_dataset_items(dataset_id):
    token = get_token()
    url = f"{BASE_URL}/datasets/{dataset_id}/items?token={token}"
    response = requests.get(url)
    return response.json()

def scrape_instagram(query, max_items=5):
    """
    Scrapes Instagram using 'apify/instagram-scraper'.
    Best used with Hashtags (e.g. query="#AI").
    """
    actor_id = "apify~instagram-scraper" 
    
    # Ensure query implies a hashtag search if not explicit
    search_term = query if query.startswith("#") else f"#{query.replace(' ', '')}"
    
    run_input = {
        "search": search_term,
        "searchType": "hashtag",
        "resultsType": "posts",
        "searchLimit": max_items,
    }
    
    try:
        run_id = run_actor(actor_id, run_input)
        dataset_id = wait_for_run(run_id)
        items = get_dataset_items(dataset_id)
        
        # Transform to our schema
        results = []
        for item in items:
            # Instagram Schema mapping
            text = item.get("caption", "")
            user = item.get("ownerUsername", "unknown_user")
            post_id = item.get("id", "000")
            url = item.get("url", "")
            
            # Filter out posts with no text if desired, or keep them
            if not text:
                continue

            results.append({
                "id": f"ig_{post_id}",
                "platform": "instagram",
                "user_handle": f"@{user}",
                "content": text,
                "url": url,
                "timestamp": time.time() # Simplification
            })
        return results
        
    except Exception as e:
        print(f"Apify Error: {e}")
def scrape_facebook(query, max_items=2):
    """
    Scrapes Facebook using 'apify/facebook-posts-scraper'.
    Note: Facebook scraping is notoriously difficult/expensive.
    We defaults to a 'Public Page' scraper if query looks like a page vs a search term.
    For this demo, we assume query is a page name (e.g. "techcrunch").
    """
    actor_id = "apify~facebook-posts-scraper"
    
    # Simple heuristic: treat query as startUrl if possible, or just a profile name
    run_input = {
        "startUrls": [{"url": f"https://www.facebook.com/{query}"}],
        "resultsLimit": max_items,
    }
    
    try:
        run_id = run_actor(actor_id, run_input)
        dataset_id = wait_for_run(run_id)
        items = get_dataset_items(dataset_id)
        
        results = []
        for item in items:
            text = item.get("text", "") or item.get("postText", "")
            user = item.get("user", {}).get("name") or query
            post_id = item.get("postId", "000")
            url = item.get("url", "")
            
            if not text:
                continue

            results.append({
                "id": f"fb_{post_id}",
                "platform": "facebook",
                "user_handle": user, # FB doesn't always have handles like @
                "content": text,
                "url": url,
                "timestamp": time.time()
            })
        return results
    except Exception as e:
        print(f"Apify FB Error: {e}")
        return []

def scrape_reddit(query, max_items=5):
    """
    Scrapes Reddit using 'apify/reddit-scraper'.
    """
    actor_id = "trudax~reddit-scraper-lite"
    
    run_input = {
        "searches": [query],
        "maxItems": max_items,
        "sort": "new",
    }
    
    try:
        run_id = run_actor(actor_id, run_input)
        dataset_id = wait_for_run(run_id)
        items = get_dataset_items(dataset_id)
        
        results = []
        for item in items:
            title = item.get("title", "")
            body = item.get("body", "") or item.get("selftext", "")
            text = f"{title}\n\n{body}".strip()
            user = item.get("author", "unknown")
            post_id = item.get("id", "000")
            url = item.get("url", "")
            
            results.append({
                "id": f"rd_{post_id}",
                "platform": "reddit",
                "user_handle": f"u/{user}",
                "content": text,
                "url": url,
                "timestamp": time.time()
            })
        return results
    except Exception as e:
        print(f"Apify Reddit Error: {e}")
        return []

# Unified scraper entry point
def scrape_all(query, max_items=2):
    results = []
    # results.extend(scrape_instagram(query, max_items)) # Insta often fails without login
    results.extend(scrape_reddit(query, max_items))
    # results.extend(scrape_facebook(query, max_items)) # FB often fails on generic keywords
    return results

if __name__ == "__main__":
    # Test run
    print(scrape_twitter("customer service", 1))
