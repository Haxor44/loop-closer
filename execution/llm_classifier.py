"""
LLM Classifier using Google Gemini API

Analyzes social media posts for:
- Sentiment (positive/negative/neutral)
- Sarcasm detection
- Intent classification (complaint/question/praise/feature_request)
- Urgency scoring
- Response suggestions
"""

import os
import json
import requests

# Configuration
GEMINI_API_KEY = None
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def get_api_key():
    global GEMINI_API_KEY
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
    
    # Try environment first
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
    
    # Try .env file in current dir and parent dirs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, "..", ".env"),  # Parent of execution/
        ".env",
        os.path.join(script_dir, ".env"),
    ]
    
    for env_path in possible_paths:
        try:
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        GEMINI_API_KEY = line.strip().split("=", 1)[1]
                        return GEMINI_API_KEY
        except Exception:
            pass
    
    return GEMINI_API_KEY


def analyze_post(content: str, platform: str = "unknown", user_handle: str = "unknown", product_name: str = None, brand_voice: str = None) -> dict:
    """
    Analyzes a social media post using Gemini.
    
    Returns:
    {
        "sentiment": "negative",      # positive/negative/neutral
        "sarcasm": true,              # boolean
        "intent": "complaint",        # complaint/question/praise/feature_request/general
        "urgency": "high",            # high/medium/low
        "ticket_type": "BUG",         # BUG/FEATURE/QUESTION
        "suggested_response": "...",  # AI-generated response
        "confidence": 0.85,           # 0-1 score
        "summary": "..."              # Brief summary for ticket
    }
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment or .env")
    
    # Construct Contextual Prompt
    context_instruction = ""
    if product_name:
        context_instruction = f"""
    CONTEXT CHECK:
    The user is interested in the product "{product_name}".
    If this post is NOT about "{product_name}" (or related industry/competitors), return strict JSON with "ticket_type": "IRRELEVANT" and "summary": "Irrelevant post".
    """
    
    voice_instruction = ""
    if brand_voice:
        voice_instruction = f"""
    BRAND VOICE:
    Adopt the following persona for the 'suggested_response':
    "{brand_voice}"
    """

    prompt = f"""Analyze this social media post and respond with ONLY a valid JSON object.
{context_instruction}
    
POST:
Platform: {platform}
User: {user_handle}
Content: "{content}"

Analyze for:
1. Sentiment: Is this positive, negative, or neutral?
2. Sarcasm: Is the user being sarcastic? (true/false)
3. Intent: What does the user want? (complaint, question, praise, feature_request, general)
4. Urgency: How urgent is this? (high, medium, low)
5. Ticket Type: What type of support ticket is this? (BUG, FEATURE, QUESTION, IRRELEVANT)
6. Summary: A brief 1-sentence summary
7. Suggested Response: Draft a helpful response.{voice_instruction}
8. Confidence: [0.0-1.0]

Respond with this exact JSON structure:
{{"sentiment": "...", "sarcasm": true/false, "intent": "...", "urgency": "...", "ticket_type": "...", "summary": "...", "suggested_response": "...", "confidence": 0.0}}"""

    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code != 200:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
            return get_fallback_analysis(content)
        
        data = response.json()
        
        # Extract the generated text
        try:
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean up the response (remove markdown code blocks if present)
            generated_text = generated_text.strip()
            if generated_text.startswith("```"):
                generated_text = generated_text.split("```")[1]
                if generated_text.startswith("json"):
                    generated_text = generated_text[4:]
            generated_text = generated_text.strip()
            
            result = json.loads(generated_text)
            return result
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {data}")
            return get_fallback_analysis(content)
            
    except Exception as e:
        print(f"Gemini API request failed: {e}")
        return get_fallback_analysis(content)


def get_fallback_analysis(content: str) -> dict:
    """
    Fallback keyword-based analysis when LLM fails.
    """
    content_lower = content.lower()
    
    # Basic sentiment
    negative_words = ["broken", "bug", "error", "fail", "hate", "terrible", "worst", "bad", "problem", "issue", "crash"]
    positive_words = ["love", "great", "awesome", "amazing", "thank", "perfect", "best", "excellent"]
    
    neg_count = sum(1 for w in negative_words if w in content_lower)
    pos_count = sum(1 for w in positive_words if w in content_lower)
    
    if neg_count > pos_count:
        sentiment = "negative"
    elif pos_count > neg_count:
        sentiment = "positive"
    else:
        sentiment = "neutral"
    
    # Intent
    if any(w in content_lower for w in ["?", "how", "what", "why", "where", "when", "can you"]):
        intent = "question"
        ticket_type = "QUESTION"
    elif any(w in content_lower for w in ["feature", "add", "would be nice", "suggestion", "could you"]):
        intent = "feature_request"
        ticket_type = "FEATURE"
    elif any(w in content_lower for w in ["bug", "broken", "error", "crash", "fail"]):
        intent = "complaint"
        ticket_type = "BUG"
    else:
        intent = "general"
        ticket_type = "QUESTION"
    
    # Urgency
    if any(w in content_lower for w in ["urgent", "asap", "immediately", "critical", "emergency"]):
        urgency = "high"
    elif sentiment == "negative":
        urgency = "medium"
    else:
        urgency = "low"
    
    return {
        "sentiment": sentiment,
        "sarcasm": False,
        "intent": intent,
        "urgency": urgency,
        "ticket_type": ticket_type,
        "summary": content[:100] + "..." if len(content) > 100 else content,
        "suggested_response": "Thank you for reaching out! We've received your message and will get back to you shortly.",
        "confidence": 0.5
    }


def batch_analyze(posts: list) -> list:
    """
    Analyzes multiple posts.
    """
    results = []
    for post in posts:
        content = post.get("content", "")
        platform = post.get("platform", "unknown")
        user_handle = post.get("user_handle", "unknown")
        
        analysis = analyze_post(content, platform, user_handle)
        
        # Merge original post with analysis
        enriched = {**post, "analysis": analysis}
        results.append(enriched)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze social media posts with Gemini")
    parser.add_argument("--content", help="Post content to analyze", required=False)
    parser.add_argument("--file", help="JSON file with posts to analyze", required=False)
    parser.add_argument("--platform", default="twitter", help="Platform name")
    parser.add_argument("--user", default="@unknown", help="User handle")
    
    args = parser.parse_args()
    
    if args.content:
        result = analyze_post(args.content, args.platform, args.user)
        print(json.dumps(result, indent=2))
    elif args.file:
        with open(args.file, "r") as f:
            posts = json.load(f)
        results = batch_analyze(posts)
        print(json.dumps(results, indent=2))
    else:
        # Demo
        test_posts = [
            "Your app crashes every time I try to login. Fix this ASAP!",
            "Love the new update! The dark mode is perfect 🔥",
            "Oh great, another 'bug fix' update that broke everything. Classic.",
            "Can you add a feature to export data to CSV?"
        ]
        
        print("=== LLM Classifier Demo ===\n")
        for post in test_posts:
            print(f"Post: {post[:50]}...")
            result = analyze_post(post, "twitter", "@test_user")
            print(f"  Sentiment: {result['sentiment']}")
            print(f"  Sarcasm: {result['sarcasm']}")
            print(f"  Intent: {result['intent']}")
            print(f"  Urgency: {result['urgency']}")
            print(f"  Type: {result['ticket_type']}")
            print(f"  Confidence: {result['confidence']}")
            print()

def generate_reply(content: str, tone: str = "Specific", context: str = None) -> dict:
    """
    Generates a reply for a social media post using Gemini.
    """
    api_key = get_api_key()
    if not api_key:
        return {"reply": "Error: API Key missing", "error": True}
    
    prompt = f"""You are a customer service agent for a brand.
POST CONTENT: "{content}"

INSTRUCTIONS:
1. Generate a reply in a "{tone}" tone.
2. {f"Context details: {context}" if context else "Keep it helpful and concise."}
3. The reply should be ready to send (no quotes, no "Here is a reply:", just the text).
4. Keep it under 280 characters if possible, unless the complexity requires more.

REPLY:"""

    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            return {"reply": "Failed to generate reply.", "error": True}
        
        data = response.json()
        reply_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return {"reply": reply_text, "error": False}
        
    except Exception as e:
        print(f"Gemini Reply Error: {e}")
        return {"reply": "Failed to generate reply due to error.", "error": True}
