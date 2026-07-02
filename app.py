import streamlit as st
import requests
import uuid
import time

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="MediConnect Care Assistant",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# CONFIG — update this with your n8n production webhook URL
# ---------------------------------------------------------
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]
REQUEST_TIMEOUT = 60  # seconds

# ---------------------------------------------------------
# CUSTOM CSS — healthcare-themed rich chat UI
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Overall page */
    .main {
        background-color: #F4F8FB;
    }

    /* Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 18px 22px;
        background: linear-gradient(135deg, #0EA5A4 0%, #0891B2 100%);
        border-radius: 16px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(8, 145, 178, 0.25);
    }
    .app-header h1 {
        color: white;
        font-size: 22px;
        margin: 0;
        font-weight: 700;
    }
    .app-header p {
        color: #E0F7F6;
        font-size: 13px;
        margin: 0;
    }

    /* Chat bubbles */
    .stChatMessage {
        border-radius: 16px !important;
        padding: 4px 6px !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #E5E9EF;
    }

    .sidebar-card {
        background: #F4F8FB;
        border: 1px solid #E1EEF0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 14px;
    }
    .sidebar-card h4 {
        margin: 0 0 6px 0;
        font-size: 13px;
        color: #0891B2;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sidebar-card p {
        margin: 0;
        font-size: 13px;
        color: #475569;
    }

    .status-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .status-online { background-color: #22C55E; }
    .status-offline { background-color: #EF4444; }

    /* Suggested question chips */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #0891B2;
        color: #0891B2;
        background: white;
        font-size: 13px;
        padding: 6px 14px;
    }
    .stButton>button:hover {
        background: #0891B2;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown("""
<div class="app-header">
    <div style="font-size:34px;">🩺</div>
    <div>
        <h1>MediConnect Care Assistant</h1>
        <p>Ask me anything about the project documentation — powered by RAG</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hi! I'm the MediConnect Care Assistant. I can answer questions about the project scope, team, timeline, and more — based on the official project documents. What would you like to know?",
        }
    ]

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Session")

    st.markdown(f"""
    <div class="sidebar-card">
        <h4>Session ID</h4>
        <p style="font-family: monospace; font-size:11px;">{st.session_state.session_id[:18]}...</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 New conversation started. What would you like to know about MediConnect Care?",
            }
        ]
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Try asking")
    suggestions = [
        "What is the project overview?",
        "Who is on the project team?",
        "What is the project timeline?",
        "What are the key risks and assumptions?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=s):
            st.session_state.pending_prompt = s
            st.rerun()

    st.markdown("---")
    st.markdown("""
    <div class="sidebar-card">
        <h4>About</h4>
        <p>This assistant retrieves answers directly from the MediConnect Care project documentation using a Retrieval-Augmented Generation (RAG) pipeline built in n8n.</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Built with Streamlit · n8n · Groq · Cohere · Supabase")

# ---------------------------------------------------------
# CHAT HISTORY DISPLAY
# ---------------------------------------------------------
for msg in st.session_state.messages:
    avatar = "🩺" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ---------------------------------------------------------
# FUNCTION: Call n8n webhook
# ---------------------------------------------------------
def get_agent_response(user_message: str) -> str:
    payload = {
        "chatInput": user_message,
        "sessionId": st.session_state.session_id,
    }
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # n8n chat trigger responses commonly come back as one of these shapes
        if isinstance(data, dict):
            for key in ["output", "text", "answer", "response"]:
                if key in data:
                    return data[key]
            return str(data)
        elif isinstance(data, list) and len(data) > 0:
            item = data[0]
            for key in ["output", "text", "answer", "response"]:
                if key in item:
                    return item[key]
            return str(item)
        return str(data)

    except requests.exceptions.Timeout:
        return "⏱️ The request timed out. The agent may be processing a large query — please try again."
    except requests.exceptions.ConnectionError:
        return "🔌 Could not connect to the assistant. Please check that the n8n workflow is active and the webhook URL is correct."
    except requests.exceptions.HTTPError as e:
        return f"⚠️ The assistant returned an error: {e}"
    except Exception as e:
        return f"⚠️ Something went wrong: {e}"

# ---------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------
prompt = st.chat_input("Type your question about the MediConnect Care project...")

# Handle sidebar suggestion clicks
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner("Searching project documents..."):
            reply = get_agent_response(prompt)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
