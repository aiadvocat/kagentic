from flask import Flask, request, jsonify
from shared.db import DatabaseManager
import openai
import os
import uuid
import requests
from functools import wraps
from datetime import datetime
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
import torch
from transformers import pipeline

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if MPS (Metal Performance Shaders) is available
if torch.backends.mps.is_available():
    logger.info("Using MPS (Apple Silicon GPU) device")
    device = "mps"
elif torch.cuda.is_available():
    logger.info("Using CUDA device")
    device = "cuda"
else:
    logger.info("Using CPU device")
    device = "cpu"

classifier = pipeline("zero-shot-classification", 
                    model="valhalla/distilbart-mnli-12-1",
                    hypothesis_template="This tool can perform the task: {}.",
                    device=device)



app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.before_request
def log_request():
    logger.info(f"Received {request.method} request to {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    logger.info(f"Returning {response.status_code} to {request.remote_addr}")
    return response

db = DatabaseManager()
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-api-key-here')

def retry_on_failure(max_retries=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        return {"error": str(e)}, 500
            return {"error": "Max retries exceeded"}, 500
        return wrapper
    return decorator

@app.route('/api/tools/register', methods=['POST'])
def register_tool():
    data = request.json
    required_fields = ['name', 'description', 'endpoint_url', 'capabilities']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    tool_id = db.register_tool(
        name=data['name'],
        description=data['description'],
        endpoint_url=data['endpoint_url'],
        capabilities=data['capabilities']
    )
    
    return jsonify({"tool_id": tool_id, "status": "registered"})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
        
        message = data['message']
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        logger.info(f"Processing chat request for session {session_id}")
        
        # Get available tools
        tools = db.get_active_tools()
        logger.info(f"Found {len(tools)} active tools")
        for tool in tools:
            logger.info(f"Available tool: {tool['name']} with capabilities: {tool['capabilities']}")
        
        # Process tool calls
        tool_responses = process_tool_calls(message, tools)
        if tool_responses:
            logger.info("Tools used in response:")
            for resp in tool_responses:
                logger.info(f"- {resp['tool']}: {resp['response']}")
        else:
            logger.info("No tools were used for this request")
        
        # Create system message
        system_message = create_system_message(tools)
        
        # Get initial response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ]
        )
        assistant_message = response.choices[0].message.content
        logger.info("Received initial response from OpenAI")
        
        # If tools were used, get final response
        if tool_responses:
            logger.info("Getting final response incorporating tool results")
            final_response = get_final_response(message, assistant_message, tool_responses)
        else:
            logger.info("Using initial response (no tools used)")
            final_response = assistant_message
        
        # Store chat history
        db.create_session(session_id)
        db.add_chat_message(session_id, message, "user")
        db.add_chat_message(session_id, final_response, "assistant")
        
        logger.info("Chat request completed successfully")
        return jsonify({"response": final_response})
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def create_system_message(tools):
    tool_descriptions = "\n".join([
        f"- {tool['name']}: {tool['description']}" 
        for tool in tools
    ])
    return f"""You are an AI assistant with access to the following tools:

{tool_descriptions}

When a user's request requires using these tools, incorporate them into your response.
If no tools are needed, respond directly to the user's query."""

@retry_on_failure(max_retries=1)
def process_tool_calls(message, tools):
    tool_responses = []
    candidate_labels = []
    tool_map = {}
    logger.info(f"Processing Tools {tools} with message {message}")
    
    # Build tool mapping
    for tool in tools:
        logger.info(f"Processing tool: {tool['name']}")
        namedescription = f"{tool['name']}: {tool['description']}"
        candidate_labels.append(namedescription)
        tool_map[namedescription] = tool
        for capability in tool["capabilities"]:
            logger.info(f"Processing capability: {capability}")
            candidate_labels.append(capability)
            tool_map[capability] = tool    # Map capability to the full tool object

    logger.info("Getting Classification Result")
    try:
        result = classifier(message, candidate_labels)   
        logger.info(f"Classification result: {result}")
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}", exc_info=True)
        return tool_responses

    # Get the highest scoring label and its score
    top_label = result['labels'][0]
    top_score = result['scores'][0]
    logger.info(f"Top label: {top_label} with score: {top_score}")

    # Only use tool if confidence is high enough
    if top_score > 0.3 and top_label in tool_map:
        selected_tool = tool_map[top_label]
        logger.info(f"Selected tool: {selected_tool['name']} with confidence: {top_score}")
        
        try:
            logger.info(f"Calling tool {selected_tool['name']} at {selected_tool['endpoint_url']}")
            response = requests.post(
                selected_tool['endpoint_url'],
                json={"query": message},
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"Successfully used {selected_tool['name']}")
                tool_responses.append({
                    "tool": selected_tool['name'],
                    "response": response.json()
                })
            else:
                logger.warning(f"Tool {selected_tool['name']} returned status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling {selected_tool['name']}: {str(e)}")
    else:
        logger.info(f"No tool selected (top score: {top_score} for label: {top_label})")

    return tool_responses

def get_final_response(user_message, assistant_message, tool_responses):
    tools_context = "\n".join([
        f"{resp['tool']} returned: {resp['response']}"
        for resp in tool_responses
    ])
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
            {"role": "system", "content": f"Tool results:\n{tools_context}\nPlease provide a final response incorporating these tool results."}
        ]
    )
    
    return response.choices[0].message.content

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        logger.debug("Health check called")
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }

        try:
            logger.debug("Checking database connection")
            db.get_active_tools()
            status["database"] = "connected"
            logger.debug("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            status["database"] = f"error: {str(e)}"
            
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/tools/heartbeat', methods=['POST'])
def tool_heartbeat():
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Tool name is required"}), 400
        
        db.update_tool_heartbeat(data['name'])
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Error updating tool heartbeat: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 