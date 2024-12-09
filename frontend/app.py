import streamlit as st
import requests
import uuid
from datetime import datetime

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

@st.cache_data(ttl=60)
def health_check():
    try:
        # Test connection to AI Agent
        response = requests.get('http://ai-agent:5000/api/health', timeout=5)
        ai_agent_health = response.status_code == 200
    except:
        ai_agent_health = False
    
    return {
        "status": "healthy" if ai_agent_health else "degraded",
        "ai_agent_connected": ai_agent_health,
        "timestamp": datetime.now().isoformat()
    }

def run_health_server():
    from flask import Flask, jsonify
    health_app = Flask(__name__)
    
    @health_app.route('/health')
    def health():
        status = health_check()
        return jsonify(status), 200 if status["status"] == "healthy" else 503
    
    health_app.run(host='0.0.0.0', port=8502)

# Start health check server
threading.Thread(target=run_health_server, daemon=True).start()

def send_message(message):
    try:
        response = requests.post(
            'http://ai-agent:5000/api/chat',
            json={
                'message': message,
                'session_id': st.session_state.session_id
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error: {response.status_code}", "response": "Sorry, I encountered an error."}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "response": "Sorry, I'm having trouble connecting to the AI agent."}

st.title("🤖 Kagentic AI Assistant")

# Chat interface
st.markdown("""
<style>
.user-message {
    background-color: #e6f3ff;
    padding: 15px;
    border-radius: 15px;
    margin: 5px 0;
}
.assistant-message {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 15px;
    margin: 5px 0;
}
.timestamp {
    color: #666;
    font-size: 0.8em;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong><br>{message["content"]}
            <div class="timestamp">{message["timestamp"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <strong>Assistant:</strong><br>{message["content"]}
            <div class="timestamp">{message["timestamp"]}</div>
        </div>
        """, unsafe_allow_html=True)

# Input area
with st.container():
    message = st.text_area("Type your message:", key="message_input", height=100)
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("Send", use_container_width=True):
            if message:
                # Add user message to chat
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.messages.append({
                    "role": "user",
                    "content": message,
                    "timestamp": timestamp
                })
                
                # Get AI response
                response = send_message(message)
                
                if "error" in response:
                    st.error(response["error"])
                    assistant_message = response["response"]
                else:
                    assistant_message = response["response"]
                
                # Add assistant response to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # Clear input
                st.session_state.message_input = ""
                st.experimental_rerun()
    
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.experimental_rerun()

# Display session ID in sidebar
with st.sidebar:
    st.markdown("### Session Information")
    st.code(f"Session ID: {st.session_state.session_id}")
    st.markdown("### System Status")
    status = health_check()
    if status["status"] == "healthy":
        st.success("All Systems Operational")
    else:
        st.warning("Some Services Degraded")
    with st.expander("Details"):
        st.json(status) 