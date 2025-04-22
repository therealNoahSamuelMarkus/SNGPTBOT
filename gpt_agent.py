import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from ticket_bot import create_ticket_from_intent
import streamlit as st

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ticket routing keywords by category
TICKET_KEYWORDS = {
    "access_issue": ["access", "permission", "denied", "role", "admin rights", "shared document", "restore access"],
    "hardware_request": ["laptop", "monitor", "mouse", "keyboard", "ram", "docking station", "headset", "webcam"],
    "software_request": ["adobe", "vpn", "software installation", "creative cloud"],
    "account_problem": ["locked", "password", "login", "mfa", "deactivated", "reset", "username"],
    "ticket_followup": ["update on my ticket", "escalated", "reopen", "issue reoccurred", "not resolved", "ETA"],
    "data_issue": ["report", "dashboard", "data", "graph", "filter", "export", "mismatch", "duplicates"],
    "workflow_problem": ["request form", "approval", "task assigned", "status stuck", "dropdown empty", "cancel request"],
    "security_concern": ["suspicious email", "malware", "phishing", "data breach", "vulnerability", "antivirus"]
}

CATEGORY_METADATA = {
    "access_issue": {
        "short_description": "Access/Permissions Issue",
        "category": "access",
        "subcategory": "permissions",
        "assignment_group": "IT Access Control",
        "type": "incident"
    },
    "hardware_request": {
        "short_description": "Hardware Request",
        "category": "hardware",
        "subcategory": "laptop",
        "assignment_group": "IT Hardware Support",
        "type": "request"
    },
    "software_request": {
        "short_description": "Software Request",
        "category": "software",
        "subcategory": "installation",
        "assignment_group": "IT Software Support",
        "type": "request"
    },
    "account_problem": {
        "short_description": "User Account Issue",
        "category": "account",
        "subcategory": "login",
        "assignment_group": "IT Account Services",
        "type": "incident"
    },
    "ticket_followup": {
        "short_description": "Follow-up on Existing Ticket",
        "category": "incident",
        "subcategory": "followup",
        "assignment_group": "IT Support",
        "type": "incident"
    },
    "data_issue": {
        "short_description": "Reporting/Data Issue",
        "category": "reporting",
        "subcategory": "dashboard",
        "assignment_group": "Data Analytics",
        "type": "incident"
    },
    "workflow_problem": {
        "short_description": "Workflow/Approval Problem",
        "category": "workflow",
        "subcategory": "approval",
        "assignment_group": "IT Workflow Team",
        "type": "incident"
    },
    "security_concern": {
        "short_description": "Security/Compliance Concern",
        "category": "security",
        "subcategory": "breach",
        "assignment_group": "Cybersecurity Team",
        "type": "incident"
    }
}

def track_issue(issue_log, user_id, question):
    if user_id not in issue_log:
        issue_log[user_id] = []
    issue_log[user_id].append(question.lower())

def detect_ticket_category(question):
    system_msg = {
        "role": "system",
        "content": (
            "You are a classifier. Categorize the user's IT support question into one of the following categories:\n"
            "- access_issue\n- hardware_request\n- software_request\n- account_problem\n"
            "- ticket_followup\n- data_issue\n- workflow_problem\n- security_concern\n"
            "Only return the category. If the request doesn't fit, return 'none'."
        )
    }

    user_msg = {"role": "user", "content": question}

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_msg, user_msg]
        )
        category = response.choices[0].message.content.strip().lower()
        return category if category in CATEGORY_METADATA else None
    except Exception as e:
        print("Category detection error:", e)
        return None

def generate_response(user_id, question, kb_articles, issue_log, confirm_ticket=False, stored_metadata=None):
    st.sidebar.markdown("### 📚 KB Articles Sent to GPT")
    if not kb_articles:
        st.sidebar.warning("⚠️ No knowledge base articles were found!")
    else:
        for a in kb_articles:
            st.sidebar.write(f"- {a['title']}")

    track_issue(issue_log, user_id, question)

    numbered_articles = []
    context = ""
    for i, a in enumerate(kb_articles, 1):
        title = a["title"]
        content = a["content"]
        numbered_articles.append(f"{i}. {title}")
        context += f"\n\n[{i}] {title}\n{content.strip()}"

    # ✨ Smarter prompt that summarizes and interprets, doesn't quote
    prompt = f"""You are an IT support assistant. The user has a question, and you must answer ONLY using the information below from the company's internal knowledge base.

DO NOT guess or use general knowledge. Instead, interpret the relevant content from these articles and summarize the correct answer for the user.

If the answer is not found, say:
"I'm sorry, I couldn’t find that information in the company’s knowledge base."

User: {user_id}
Question: {question}

Relevant Articles (use as background information):
{context}

Now, based on the articles above, answer the user's question as clearly and accurately as possible.
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = completion.choices[0].message.content

    ticket_category = detect_ticket_category(question)
    if ticket_category:
        intent_metadata = CATEGORY_METADATA[ticket_category]
        if confirm_ticket:
            result = create_ticket_from_intent(user_id, question, intent_metadata, answer)
            return f"{answer}\n\n{result['message']}", intent_metadata
        else:
            answer += "\n\n⚠️ This request may require a ticket. Please confirm if you'd like to open one."
            return answer, intent_metadata

    return answer, None