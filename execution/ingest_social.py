import argparse
import json
import time
from apify_manager import scrape_all
from n8n_connector import send_to_webhook

def ingest(content, user):
    """
    Legacy/Mock ingestion for single manual inputs.
    """
    payload = {
        "id": f"soc_{int(time.time())}",
        "platform": "twitter_mock",
        "user_handle": user,
        "content": content,
        "timestamp": time.time()
    }
    return [payload]

def ingest_search_results(query):
    """
    Ingests real results from Apify.
    """
    print(f"--- FETCHING REAL SOCIAL DATA FOR: '{query}' ---")
    results = scrape_all(query, max_items=2)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Search query for fetching real tweets", required=False)
    parser.add_argument("--content", help="Manual content (legacy)", required=False)
    parser.add_argument("--user", help="Manual user (legacy)", required=False)
    parser.add_argument("--webhook", help="URL of n8n Webhook to push data to", required=False)
    
    args = parser.parse_args()
    
    final_output = []
    
    if args.query:
        final_output = ingest_search_results(args.query)
    elif args.content and args.user:
        final_output = ingest(args.content, args.user)
    else:
        print("Error: Must provide --query OR (--content AND --user)")
        exit(1)
        
    # OUTPUT
    if final_output:
        if args.webhook:
            # PUSH MODE (n8n)
            send_to_webhook(final_output, args.webhook)
        else:
            # CLI MODE (Print)
            print(json.dumps(final_output, indent=2))
