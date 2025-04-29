import streamlit as st
from servicenow_api import query_kb_articles, load_servicenow_data, get_user_context
from gpt_agent import generate_response, create_ticket_from_intent

# Page config
st.set_page_config(page_title="IT Assistant", layout="centered")
st.title("💼 IT Support Assistant")

# Initialize session state variables
defaults = {
    "page_state": "login",
    "chat_history": [],
    "issue_log": {},
    "pending_ticket": False,
    "last_question": "",
    "ticket_metadata": None,
    "user_context": {},
    "kb_articles": [],
    "user_context_loaded": False,
    "last_response": "",
    "show_ticket_prompt": False,
    "servicenow_data": load_servicenow_data()
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Page functions
def login_page():
    user_id = st.text_input("Enter your username to begin:", value="", key="username_input")
    
    if user_id and not st.session_state.user_context_loaded:
        st.session_state.user_context = get_user_context(user_id)
        st.session_state.user_context_loaded = True

        # Set user ID for later
        st.session_state["user_id"] = user_id

        st.session_state.page_state = "chat"
        st.rerun()

def chat_page():
    question = st.text_input("What can I help you with today?")

        # Show sidebar user info
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

    if st.button("Ask GPT") or question:
        if question.strip():
            st.session_state.kb_articles = query_kb_articles(query=question)
            response, metadata = generate_response(
                user_id=st.session_state["user_id"],
                question=question,
                kb_articles=st.session_state.kb_articles,
                issue_log=st.session_state.issue_log,
                confirm_ticket=False,
                stored_metadata=None
            )
            st.session_state.last_question = question
            st.session_state.last_response = response
            st.session_state.ticket_metadata = metadata
            st.session_state.show_ticket_prompt = True

    if st.session_state.last_response and st.session_state.show_ticket_prompt:
        st.markdown("### 💡 GPT Response")
        st.markdown(st.session_state.last_response)


    if st.session_state.ticket_metadata and st.button("📩 Create a ticket based on this issue"):
        st.session_state.chat_history.append(
            (st.session_state.last_question, st.session_state.last_response)
        )
        st.session_state.pending_ticket = True
        st.session_state.show_ticket_prompt = False
        st.session_state.page_state = "ticket"
        st.rerun()

def ticket_page():
    if st.session_state.pending_ticket and st.session_state.ticket_metadata:
        st.markdown("### 📝 Confirm Ticket Details")
        sd = st.text_input("Short Description", st.session_state.ticket_metadata.get("short_description", ""))
        cat = st.text_input("Category", st.session_state.ticket_metadata.get("category", ""))
        sub = st.text_input("Subcategory", st.session_state.ticket_metadata.get("subcategory", ""))
        group = st.text_input("Assignment Group", st.session_state.ticket_metadata.get("assignment_group", ""))
        desc = st.text_area("Description", "", placeholder="Leave empty to auto-generate.")

        if st.button("✅ Create Ticket Now"):
            confirm_data = {
                "short_description": sd,
                "category": cat,
                "subcategory": sub,
                "assignment_group": group,
                "description": desc
            }

            result = create_ticket_from_intent(
                user_id=st.session_state["user_id"],
                issue=st.session_state.last_question,
                intent_metadata=st.session_state.ticket_metadata,
                confirm_data=confirm_data
            )

            st.session_state.chat_history.append(("(Confirmed Ticket)", result["message"]))
            st.session_state.pending_ticket = False
            st.session_state.ticket_metadata = None
            st.session_state.page_state = "chat"
            st.rerun()

# Routing logic
pages = {
    "login": login_page,
    "chat": chat_page,
    "ticket": ticket_page
}

# Run current page
pages[st.session_state.page_state]()

# Chat history section
if st.session_state.chat_history:
    st.markdown("### 🗂️ Previous Conversations")
    for q, r in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**IT Assistant:** {r}")
        st.markdown("---")
