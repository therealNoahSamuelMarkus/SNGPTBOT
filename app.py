import streamlit as st
from servicenow_api import query_kb_articles, open_ticket
from gpt_agent import generate_response
from auth import get_user_permissions

st.set_page_config(page_title="IT Service GPT", layout="centered")

st.title("💻 IT Service Desk Assistant")

user_id = st.text_input("Enter your user ID", value="employee1")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input("What can I help you with today?")

if st.button("Ask GPT"):
    if question.strip():
        permissions = get_user_permissions(user_id)
        kb_articles = query_kb_articles(question, permissions)

        response = generate_response(user_id, question, kb_articles)

        st.session_state.chat_history.append((question, response))

# Display chat history
for q, r in st.session_state.chat_history[::-1]:
    st.markdown(f"**You:** {q}")
    st.markdown(f"**IT Assistant:** {r}")
    st.markdown("---")
