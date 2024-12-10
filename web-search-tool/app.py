from flask import Flask, request, jsonify
import requests
import time
import os
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import threading

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CAPABILITIES = [
    "search",
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
        logger.info(f"Performing {search_type} search for query: {query}")
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

        logger.debug(f"Search parameters: {params}")
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        logger.info(f"Search API response status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            logger.debug(f"Raw search results: {results}")
            
            # Format the results
            formatted_results = {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results": []
            }

            # Extract relevant information based on search type
            if search_type == "web":
                logger.debug(f"Found {len(results.get('organic_results', []))} web results")
                for result in results.get("organic_results", []):
                    formatted_results["results"].append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                        "source": result.get("source")
                    })
            elif search_type == "news":
                logger.debug(f"Found {len(results.get('news_results', []))} news results")
                for result in results.get("news_results", []):
                    formatted_results["results"].append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                        "source": result.get("source"),
                        "date": result.get("date")
                    })
            elif search_type == "shopping":
                logger.debug(f"Found {len(results.get('shopping_results', []))} shopping results")
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

            logger.info(f"Successfully formatted {len(formatted_results['results'])} results")
            return formatted_results
        else:
            error_msg = f"Search API returned status code: {response.status_code}"
            logger.error(error_msg)
            try:
                error_details = response.json()
                logger.error(f"Error details: {error_details}")
            except:
                logger.error("No JSON error details available")
            return {
                "success": False,
                "error": error_msg
            }

    except Exception as e:
        logger.error(f"Search failed with exception: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    logger.info(f"Performing search for query: {data}")

    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    search_type = data.get('type', 'web')
    results = perform_search(data['query'], search_type)
    return jsonify(results)

def register_with_agent():
    while True:
        try:
            logger.info("Attempting to register with AI Agent...")
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
                logger.info("Successfully registered with AI Agent")
                break
            else:
                logger.error(f"Registration failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register with AI Agent: {e}")
            time.sleep(10)

def send_heartbeat():
    while True:
        try:
            logger.debug("Sending heartbeat...")
            response = requests.post(
                'http://ai-agent:5000/api/tools/heartbeat',
                json={"name": "Advanced Search Tool"},
                timeout=5
            )
            if response.status_code == 200:
                logger.debug("Heartbeat successful")
            else:
                logger.warning(f"Heartbeat failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
        time.sleep(60)  # Send heartbeat every minute

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        logger.info("Health check called")
        # Just verify we have the API key configured
        if not SEARCH_API_KEY or SEARCH_API_KEY == 'your-api-key-here':
            logger.error("Search API key not configured")
            return jsonify({
                "status": "unhealthy",
                "error": "Search API key not configured",
                "timestamp": datetime.now().isoformat()
            }), 500

        logger.info("Search API key verified")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Start registration and heartbeat in separate threads
    threading.Thread(target=register_with_agent, daemon=True).start()
    threading.Thread(target=send_heartbeat, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000) 