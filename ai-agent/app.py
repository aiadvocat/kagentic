from flask import Flask, request, jsonify
from shared.db import DatabaseManager
import openai
import os
import uuid
import requests
from functools import wraps
from datetime import datetime

app = Flask(__name__)
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
@retry_on_failure(max_retries=1)
def process_chat():
    data = request.json
    if 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    session_id = data.get('session_id', str(uuid.uuid4()))
    db.create_session(session_id)
    db.add_chat_message(session_id, data['message'], 'user')
    
    # Get available tools
    tools = db.get_active_tools()
    
    # Create system message with available tools
    system_message = create_system_message(tools)
    
    # Get response from OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": data['message']}
        ]
    )
    
    assistant_message = response.choices[0].message.content
    
    # Check if we need to use any tools
    tool_responses = process_tool_calls(assistant_message, tools)
    if tool_responses:
        # If tools were used, get a final response incorporating their results
        final_response = get_final_response(data['message'], assistant_message, tool_responses)
        db.add_chat_message(session_id, final_response, 'assistant')
        return jsonify({
            "response": final_response,
            "session_id": session_id,
            "tools_used": True
        })
    
    db.add_chat_message(session_id, assistant_message, 'assistant')
    return jsonify({
        "response": assistant_message,
        "session_id": session_id,
        "tools_used": False
    })

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
    # Simple keyword matching for tool selection
    tool_responses = []
    for tool in tools:
        if any(cap.lower() in message.lower() for cap in tool['capabilities']):
            try:
                response = requests.post(
                    tool['endpoint_url'],
                    json={"query": message},
                    timeout=5
                )
                if response.status_code == 200:
                    tool_responses.append({
                        "tool": tool['name'],
                        "response": response.json()
                    })
            except requests.exceptions.RequestException:
                continue
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
        # Test database connection
        db.get_active_tools()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 