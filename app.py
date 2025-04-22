import streamlit as st
from servicenow_api import query_kb_articles, load_servicenow_data, get_user_context
from auth import get_user_permissions
from gpt_agent import generate_response
from ticket_bot import create_ticket_from_intent

st.set_page_config(page_title="IT Assistant", layout="centered")
st.title("💼 IT Support Assistant")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "issue_log" not in st.session_state:
    st.session_state.issue_log = {}
if "pending_ticket" not in st.session_state:
    st.session_state.pending_ticket = False
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "ticket_metadata" not in st.session_state:
    st.session_state.ticket_metadata = None
if "user_context" not in st.session_state:
    st.session_state.user_context = {}
if "kb_articles" not in st.session_state:
    st.session_state.kb_articles = []
if "user_context_loaded" not in st.session_state:
    st.session_state.user_context_loaded = False
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "show_ticket_prompt" not in st.session_state:
    st.session_state.show_ticket_prompt = False
if "servicenow_data" not in st.session_state:
    st.session_state.servicenow_data = load_servicenow_data()

# Step 1: User login
user_id = st.text_input("Enter your username to begin:", value="", key="username_input")

if user_id and not st.session_state.user_context_loaded:
    st.session_state.user_context = get_user_context(user_id)
    st.session_state.user_context_loaded = True

    user = st.session_state.user_context.get("user", {})
    st.sidebar.markdown(f"**Logged in as:** {user.get('name', 'Unknown')}")
    st.sidebar.markdown(f"**Email:** {user.get('email', '')}")
    st.sidebar.markdown(f"**Title:** {user.get('title', '')}")
    st.sidebar.markdown(f"**Department:** {user.get('department', '')}")
    st.sidebar.markdown("**Devices:**")
    for d in st.session_state.user_context.get("devices", []):
        st.sidebar.write(f"- {d}")
    st.sidebar.markdown("**Open Tickets:**")
    for t in st.session_state.user_context.get("open_tickets", []):
        st.sidebar.write(f"- {t.get('number')}")

# Step 2: Ask a question
if st.session_state.user_context_loaded:
    question = st.text_input("What can I help you with today?")

    if st.button("Ask GPT"):
        if question.strip():
            st.session_state.kb_articles = query_kb_articles(query=question)  # 🔥 FETCH RELEVANT ARTICLES

            response, metadata = generate_response(
                user_id,
                question,
                st.session_state.kb_articles,
                st.session_state.issue_log,
                confirm_ticket=False,
                stored_metadata=None
            )

            st.session_state.last_question = question
            st.session_state.last_response = response
            st.session_state.ticket_metadata = metadata
            st.session_state.show_ticket_prompt = True

# Step 3: Display response + ticket prompt
if st.session_state.get("last_response") and st.session_state.get("show_ticket_prompt"):
    st.markdown("### 💡 GPT Response")
    st.markdown(st.session_state.last_response)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Ask another question"):
            st.session_state.chat_history.append((st.session_state.last_question, st.session_state.last_response))
            st.session_state.last_response = ""
            st.session_state.ticket_metadata = None
            st.session_state.show_ticket_prompt = False
    with col2:
        if st.session_state.ticket_metadata and st.button("📩 Create a ticket based on this issue"):
            st.session_state.chat_history.append((st.session_state.last_question, st.session_state.last_response))
            st.session_state.pending_ticket = True
            st.session_state.show_ticket_prompt = False

# Step 4: Ticket creation UI
if st.session_state.pending_ticket and st.session_state.ticket_metadata:
    st.markdown("### 📝 Confirm Ticket Details")
    sd = st.text_input("Short Description", st.session_state.ticket_metadata.get("short_description", ""))
    cat = st.text_input("Category", st.session_state.ticket_metadata.get("category", ""))
    sub = st.text_input("Subcategory", st.session_state.ticket_metadata.get("subcategory", ""))
    group = st.text_input("Assignment Group", st.session_state.ticket_metadata.get("assignment_group", ""))
    desc = st.text_area("Description", "", placeholder="Leave empty to auto-generate from your user info and request.")

    if st.button("✅ Create Ticket Now"):
        confirm_data = {
            "short_description": sd,
            "category": cat,
            "subcategory": sub,
            "assignment_group": group,
            "description": desc
        }

        result = create_ticket_from_intent(
            user_id=user_id,
            issue=st.session_state.last_question,
            intent_metadata=st.session_state.ticket_metadata,
            confirm_data=confirm_data
        )

        st.session_state.chat_history.append(("(Confirmed Ticket)", result["message"]))
        st.session_state.pending_ticket = False
        st.session_state.ticket_metadata = None

# Step 5: Show chat history
for q, r in st.session_state.chat_history[::-1]:
    st.markdown(f"**You:** {q}")
    st.markdown(f"**IT Assistant:** {r}")
    st.markdown("---")
