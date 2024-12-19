import streamlit as st
import requests
import uuid
from datetime import datetime

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'processing' not in st.session_state:
    st.session_state.processing = False

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

st.markdown("""
<style>
/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Chat container */
[data-testid="stChatFlow"] {
    padding-bottom: 80px;
}

/* Sticky chat input */
section[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0;
    left: 250px;  /* Account for sidebar width */
    right: 0;
    background: white;
    padding: 1rem 5rem;
    z-index: 100;
    border-top: 1px solid #ddd;
}

/* Message styling */
[data-testid="stChatMessage"] {
    background-color: #f0f2f6 !important;
    border-radius: 15px;
    padding: 15px;
    margin: 1rem 0;
    color: #31333F;
}

/* Set default text color for all elements inside chat messages */
[data-testid="stChatMessage"] * {
    color: #31333F !important;
}

/* Override color for specific elements that need different colors */
[data-testid="stChatMessage"] .stMarkdown p {
    font-size: 0.8em;
    color: #666 !important;
    margin-top: 5px;
}

[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #e6f3ff !important;
}

/* List styling in messages */
[data-testid="stChatMessage"] ol {
    list-style-type: decimal;
    margin: 0;
    padding: 0;
    counter-reset: item;
}

[data-testid="stChatMessage"] ul {
    list-style-type: disc;
    margin: 0;
    padding: 0;
}

[data-testid="stChatMessage"] li {
    margin: 0.5em 0;
    padding: 0;
    display: list-item;
}

/* Custom numbered list styling */
[data-testid="stChatMessage"] ol > li {
    list-style: none;
    counter-increment: item;
}

[data-testid="stChatMessage"] ol > li:before {
    content: counter(item) ". ";
    display: inline-block;
    font-family: inherit;
    font-size: inherit;
    font-weight: inherit;
}

/* Custom bullet list styling */
[data-testid="stChatMessage"] ul > li {
    list-style: none;
}

[data-testid="stChatMessage"] ul > li:before {
    content: "• ";
    display: inline-block;
    font-family: inherit;
    font-size: inherit;
}
</style>
""", unsafe_allow_html=True)

# Title and sidebar
st.title("🤖 Kagentic AI Assistant")

# Sidebar content
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
    
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.experimental_rerun()

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        st.caption(f"Time: {message['timestamp']}")

# Chat input
if prompt := st.chat_input("Type your message...", disabled=st.session_state.processing):
    if not st.session_state.processing:
        st.session_state.processing = True
        
        # Add user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        })
        
        # Show user message immediately
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"Time: {timestamp}")
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_message(prompt)
                
                if "error" in response:
                    st.error(response["error"])
                    assistant_message = response["response"]
                else:
                    assistant_message = response["response"]
                
                st.write(assistant_message)
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.caption(f"Time: {timestamp}")
        
        # Add assistant response to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_message,
            "timestamp": timestamp
        })
        
        st.session_state.processing = False 