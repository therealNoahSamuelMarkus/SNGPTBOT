import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from servicenow_api import *
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔍 Detect ticket inquiries
def detect_password_reset_intent(question):
    """Detects if the user's question is about needing a password reset or login help."""
    q = question.lower()
    triggers = [
        "forgot my password",
        "reset my password",
        "i need to reset my password",
        "help me reset my password",
        "can't log in",
        "can’t login",
        "unable to login",
        "i'm locked out",
        "locked out of my account",
        "lost my password"
    ]
    return any(trigger in q for trigger in triggers)

def format_ticket_list(entries, label):
    if not entries:
        return f"No open {label.lower()} found."
    lines = [f"**Open {label}**"]
    for e in entries:
        line = f"{e['number']} | {e['short_description']} | Opened: {e['opened_at'][:10]} | Caller: {e.get('caller', e.get('assigned_to', e.get('requested_for', 'N/A')))} \n"
        lines.append(line)
    return "\n".join(lines)

def detect_open_ticket_request(question, user_id):
    q = question.lower()
    if "open incidents" in q:
        return format_ticket_list(get_user_open_incidents(user_id), "Incidents")
    elif "open requests" in q:
        return format_ticket_list(get_user_open_requests(user_id), "Requests")
    elif "open tasks" in q:
        return format_ticket_list(get_user_open_tasks(user_id), "Tasks")
    return None

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
    # 🔐 Check password reset first
    if detect_password_reset_intent(question):
        answer = (
            f"Hi {user_id}, it looks like you're having trouble with your password or login. "
            "You can press the **Reset Password** button below to begin the reset process."
        )
        return answer, { "type": "password_reset" }

    # 🧾 Check for open ticket listing next
    ticket_status_response = detect_open_ticket_request(question, user_id)
    if ticket_status_response:
        return ticket_status_response, None

    # Handle ticket status queries first
    ticket_status_response = detect_open_ticket_request(question, user_id)
    if ticket_status_response:
        return ticket_status_response, None

    track_issue(issue_log, user_id, question)

    st.sidebar.markdown("### 📚 KB Articles Sent to GPT")
    if not kb_articles:
        st.sidebar.warning("⚠️ No knowledge base articles were found!")
    else:
        for a in kb_articles:
            st.sidebar.write(f"- {a['title']}")

    numbered_articles = []
    context = ""
    for i, a in enumerate(kb_articles, 1):
        title = a["title"]
        content = a["content"]
        numbered_articles.append(f"{i}. {title}")
        context += f"\n\n[{i}] {title}\n{content.strip()}"

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

def build_description(context, issue):
    name = context["user"].get("name", "Unknown User")
    email = context["user"].get("email", "not provided")
    device = context.get("devices")[0] if context.get("devices") else "unspecified device"
    return (
        f"Hi, this user {name} needs help with the following issue:\n"
        f"{issue}\n\n"
        f"They currently use a {device}. Their work email is {email}."
    )

def create_ticket_from_intent(user_id, issue, intent_metadata, confirm_data=None):
    context = get_user_context(user_id)

    # Prefer confirm_data > intent_metadata > fallback defaults
    short_desc = confirm_data.get("short_description") if confirm_data else intent_metadata.get("short_description", issue)
    category = confirm_data.get("category") if confirm_data else intent_metadata.get("category", "incident")
    subcategory = confirm_data.get("subcategory") if confirm_data else intent_metadata.get("subcategory", "general")
    group = confirm_data.get("assignment_group") if confirm_data else intent_metadata.get("assignment_group", "IT Support")

    # ✅ Default ticket type = incident
    ticket_type = (confirm_data.get("type") if confirm_data else intent_metadata.get("type")) or "incident"

    description = confirm_data.get("description") if confirm_data and confirm_data.get("description") else build_description(context, issue)

    ticket = open_ticket(
        user_id=user_id,
        short_description=short_desc,
        description=description,
        category=category,
        subcategory=subcategory,
        assignment_group=group,
        ticket_type=ticket_type
    )

    # Fallback-safe retrieval of number and type
    ticket_number = (
        ticket.get("result")
        or ticket.get("number")
        or ticket.get("request_number")
        or ticket.get("task_number")
        or "UNKNOWN"
    )
    ticket_type_display = (ticket.get("type") or ticket_type or "incident").capitalize()
    ticket_link = ticket.get("link", "#")

    return {
        "message": f"""
🛠 **Ticket Preview**
- Type: `{ticket_type_display}`
- Number: `{ticket_number}`
- Short Description: {short_desc}
- Category: {category}
- Subcategory: {subcategory}
- Assignment Group: {group}
- Description: {description}

🔗 [View Ticket in ServiceNow]({ticket_link})
""",
        "ticket": ticket
    }
