import os
from dotenv import load_dotenv
load_dotenv()

def query_kb_articles(query, permissions):
    all_articles = [
        {"id": "KB001", "title": "Reset Network Password", "content": "To reset your password..."},
        {"id": "KB002", "title": "VPN Connection Troubleshooting", "content": "If you have trouble connecting..."}
    ]
    return [a for a in all_articles if a['id'] in permissions and query.lower() in a['content'].lower()]

import requests
from requests.auth import HTTPBasicAuth

def open_ticket(user_id, issue_description):
    instance = os.getenv("SN_INSTANCE")
    user = os.getenv("SN_USERNAME")
    password = os.getenv("SN_PASSWORD")

    url = f"{instance}/api/now/table/incident"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {
        "short_description": f"Issue from user {user_id}: {issue_description}",
        "caller_id": user_id,  # this may need mapping or ServiceNow user ID
        "urgency": "3",
        "impact": "3"
    }

    response = requests.post(url, auth=HTTPBasicAuth(user, password), headers=headers, json=data)

    if response.status_code == 201:
        return {"result": f"Ticket created: {response.json()['result']['number']}"}
    else:
        return {"result": f"Failed to create ticket: {response.status_code} {response.text}"}


def close_ticket(user_id):
    return {"result": f"Ticket closed for {user_id}."}