import streamlit as st
from agent.main import run_agent

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Travel Agent",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
    }
    .welcome-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.25rem 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1.5rem;
        max-width: 100%;
    }
    .chat-container {
        padding: 0 1rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Session state setup
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "1"

# chat input handling
if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

pending = st.session_state.pending_message

if pending:
    chat_message = pending
    st.session_state.pending_message = None
else:
    chat_message = st.chat_input("Send a message...")



# -----------------------------
# Sidebar UI
# -----------------------------
with st.sidebar:
    st.header("✈️ Travel Agent")
    st.markdown("Your AI assistant for finding flights and hotels.")

    st.divider()

    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(int(st.session_state.thread_id) + 1)

    st.divider()

    st.subheader("💡 Example prompts:")
    examples = [
        "Find flights from NYC to Paris on March 15",
        "Search hotels in Tokyo for next weekend",
        "I need a round trip from LA to London",
    ]

    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state.pending_prompt = example


# -----------------------------
# Main UI
# -----------------------------
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-box">
        <h2>Welcome! 👋</h2>
        <p>I can help you find <strong>flights</strong> and <strong>hotels</strong> for your next trip.</p>
        <p>Try an example in the sidebar or type below.</p>
    </div>
    """, unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# User input
# -----------------------------

if chat_message:
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.chat_message("user").markdown(chat_message)
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_agent(chat_message, st.session_state.thread_id)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        with st.chat_message("assistant"):
            st.error("⚠️ Something went wrong while processing your request.")
            st.write(str(e))

