import streamlit as st
import requests
import uuid
from datetime import datetime

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def send_message(message):
    try:
        response = requests.post(
            'http://ai-agent:5000/api/chat',
            json={
                'message': message,
                'session_id': st.session_state.session_id
            },
            timeout=60
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
/* General text color */
.stMarkdown {
    color: #31333F;
}

.user-message {
    background-color: #e6f3ff;
    padding: 15px;
    border-radius: 15px;
    margin: 5px 0;
    color: #31333F;
}
.assistant-message {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 15px;
    margin: 5px 0;
    color: #31333F;
}
.timestamp {
    color: #666;
    font-size: 0.8em;
    margin-top: 5px;
}

/* Ensure text input and buttons have good contrast */
.stTextArea textarea {
    color: #31333F;
    background-color: white;
}

/* Style the title */
.stTitle {
    color: #31333F;
    font-weight: bold;
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
    # Initialize the clear flag if it doesn't exist
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False

    # Set default value based on clear flag
    if st.session_state.clear_input:
        st.session_state.clear_input = False
        default_value = ""
    else:
        default_value = st.session_state.get("message_input_widget", "")

    # Text input with default value
    message = st.text_area("Type your message:", 
                          value=default_value,
                          key="message_input_widget", 
                          height=100)
    
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
                
                # Set clear flag
                st.session_state.clear_input = True
                st.experimental_rerun()
    
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.clear_input = True
            st.experimental_rerun()

# Display session ID in sidebar
with st.sidebar:
    st.markdown("### Session Information")
    st.code(f"Session ID: {st.session_state.session_id}")
    st.markdown("### System Status")
    try:
        response = requests.get('http://ai-agent:5000/api/health', timeout=5)
        if response.status_code == 200:
            st.success("All Systems Operational")
        else:
            st.warning("Some Services Degraded")
        with st.expander("Details"):
            st.json(response.json())
    except:
        st.error("Unable to connect to AI Agent") 