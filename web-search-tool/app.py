from flask import Flask, request, jsonify
import requests
import time
import os
from typing import Optional, Dict, Any

app = Flask(__name__)

CAPABILITIES = [
    "web_search",
    "news_search", 
    "image_search",
    "video_search",
    "shopping_search",
    "find_information",
    "current_events",
    "research"
]

SEARCH_API_KEY = os.getenv('SEARCH_API_KEY', 'your-api-key-here')
BASE_URL = "https://www.searchapi.io/api/v1/search"

def perform_search(query: str, search_type: Optional[str] = "web") -> Dict[Any, Any]:
    """
    Perform a search using SearchAPI
    """
    try:
        params = {
            "engine": "google",  # Can be expanded to other engines
            "q": query,
            "api_key": SEARCH_API_KEY
        }

        # Add specific parameters based on search type
        if search_type == "news":
            params["type"] = "news"
        elif search_type == "images":
            params["type"] = "images"
        elif search_type == "videos":
            params["type"] = "videos"
        elif search_type == "shopping":
            params["type"] = "shopping"

        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            
            # Format the results
            formatted_results = {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results": []
            }

            # Extract relevant information based on search type
            if search_type == "web":
                for result in results.get("organic_results", []):
                    formatted_results["results"].append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                        "source": result.get("source")
                    })
            elif search_type == "news":
                for result in results.get("news_results", []):
                    formatted_results["results"].append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                        "source": result.get("source"),
                        "date": result.get("date")
                    })
            elif search_type == "shopping":
                for result in results.get("shopping_results", []):
                    formatted_results["results"].append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "price": result.get("price"),
                        "currency": result.get("currency"),
                        "source": result.get("source"),
                        "rating": result.get("rating"),
                        "reviews": result.get("reviews_count"),
                        "thumbnail": result.get("thumbnail")
                    })

            return formatted_results
        else:
            return {
                "success": False,
                "error": f"Search API returned status code: {response.status_code}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    search_type = data.get('type', 'web')
    results = perform_search(data['query'], search_type)
    return jsonify(results)

def register_with_agent():
    while True:
        try:
            response = requests.post(
                'http://ai-agent:5000/api/tools/register',
                json={
                    "name": "Advanced Search Tool",
                    "description": "Multi-purpose search tool that can find web pages, news, images, and videos using multiple search engines.",
                    "endpoint_url": "http://search-tool:5000/api/search",
                    "capabilities": CAPABILITIES
                },
                timeout=5
            )
            if response.status_code == 200:
                print("Successfully registered with AI Agent")
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to register with AI Agent: {e}")
            time.sleep(10)

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Test search with a simple query
        test_result = perform_search("test", "web")
        if test_result.get("success"):
            return jsonify({
                "status": "healthy",
                "search_api": "connected",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        return jsonify({
            "status": "degraded",
            "error": "Search API test failed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503

if __name__ == '__main__':
    import threading
    threading.Thread(target=register_with_agent).start()
    app.run(host='0.0.0.0', port=5000) 