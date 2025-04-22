from dotenv import load_dotenv
from servicenow_api import get_user_context
import streamlit as st
import os
import requests

load_dotenv()

# Load all system metadata on launch
if "servicenow_data" not in st.session_state:
    from servicenow_api import load_servicenow_data
    st.session_state.servicenow_data = load_servicenow_data()

def get_user_permissions(user_id):
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    # Get user's sys_id first
    context = get_user_context(user_id)
    user = context.get("user", {})
    user_sys_id = user.get("sys_id")
    if not user_sys_id:
        return []

    # Query knowledge articles accessible to this user
    url = f"{instance}/api/now/table/kb_knowledge?sysparm_query=published=true^active=true^u_readable_by={user_sys_id}&sysparm_fields=number&sysparm_limit=100"
    response = requests.get(url, auth=auth, headers=headers)
    
    if response.status_code == 200:
        return [article["number"] for article in response.json().get("result", [])]
    
    return []
