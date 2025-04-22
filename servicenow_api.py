import os
import requests
from requests.auth import HTTPBasicAuth

def load_servicenow_data():
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    endpoints = {
        "assignment_groups": "sys_user_group",
        "knowledge_articles": "kb_knowledge",
        "users": "sys_user",
        "incidents": "incident",
        "requests": "sc_request"
    }

    data = {}

    for key, table in endpoints.items():
        url = f"{instance}/api/now/table/{table}?sysparm_limit=100"
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            data[key] = response.json().get("result", [])
        else:
            data[key] = []
            print(f"Error loading {key}: {response.status_code}")

    # Build searchable summaries for tickets
    data["previous_ticket_descriptions"] = []
    for item in data.get("incidents", []) + data.get("requests", []):
        desc = item.get("short_description", "")
        if desc:
            data["previous_ticket_descriptions"].append(desc.strip())

    return data

def query_kb_articles(query=None, permissions=None):
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    def fetch_articles(query_string):
        url = f"{instance}/api/now/table/kb_knowledge"
        params = {
            "sysparm_query": f"active=true^workflow=published^{query_string}",
            "sysparm_fields": "number,short_description,text",
            "sysparm_limit": 50
        }
        response = requests.get(url, auth=auth, headers=headers, params=params)
        if response.status_code == 200:
            return [
                {
                    "title": a.get("short_description", "Untitled"),
                    "content": a.get("text", ""),
                    "number": a.get("number", "")
                }
                for a in response.json().get("result", []) if a.get("text")
            ]
        return []

    if not query:
        return fetch_articles("")

    # Step 1: Try full-text query
    full_query = f"short_descriptionLIKE{query}^ORtextLIKE{query}"
    articles = fetch_articles(full_query)
    if articles:
        return articles

    # Step 2: Try breaking into keywords
    keywords = [word.strip() for word in query.split() if word.strip()]
    if not keywords:
        return []

    keyword_query = "^OR".join([f"textLIKE{kw}" for kw in keywords])
    return fetch_articles(keyword_query)

def open_ticket(user_id, short_description, description, category="request", subcategory="software",
                assignment_group="IT Support", ticket_type="incident"):
    instance = os.getenv("SN_INSTANCE")
    user = os.getenv("SN_USERNAME")
    password = os.getenv("SN_PASSWORD")

    url = f"{instance}/api/now/table/{ticket_type}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "caller_id": user_id,
        "short_description": short_description,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "assignment_group": assignment_group,
        "impact": "3",
        "urgency": "3",
        "priority": "4"
    }

    response = requests.post(url, auth=HTTPBasicAuth(user, password), headers=headers, json=payload)

    if response.status_code == 201:
        result = response.json()["result"]
        number = (
            result.get("number") or
            result.get("request_number") or
            result.get("task_number") or
            result.get("u_number") or
            "UNKNOWN"
        )
        sys_id = result.get("sys_id", "")
        link = f"{instance}/nav_to.do?uri={ticket_type}.do?sys_id={sys_id}"
        return {
            "result": number,
            "type": ticket_type,
            "link": link,
            "summary": f"{ticket_type.capitalize()} {number} created for {short_description}"
        }

    return {
        "result": "Error",
        "type": ticket_type,
        "link": "",
        "summary": f"Failed to create {ticket_type}: {response.text}"
    }

def close_ticket(user_id):
    return {"result": f"Ticket closed for {user_id}."}

def get_user_context(user_id):
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    context = {}

    # Get user profile
    user_url = f"{instance}/api/now/table/sys_user?sysparm_query=user_name={user_id}"
    r = requests.get(user_url, auth=auth, headers=headers)
    if r.status_code == 200 and r.json().get("result"):
        user = r.json()["result"][0]
        context["user"] = {
            "name": user.get("name"),
            "email": user.get("email"),
            "title": user.get("title"),
            "department": user.get("department", {}).get("display_value", ""),
            "sys_id": user.get("sys_id")
        }

    # Get devices owned by the user
    asset_url = f"{instance}/api/now/table/cmdb_ci_computer?sysparm_query=assigned_to={context['user']['sys_id']}"
    r = requests.get(asset_url, auth=auth, headers=headers)
    if r.status_code == 200:
        context["devices"] = [a["name"] for a in r.json().get("result", [])]

    # Get user's open incidents and requests
    incidents_url = f"{instance}/api/now/table/incident?sysparm_query=caller_id={context['user']['sys_id']}"
    requests_url = f"{instance}/api/now/table/sc_request?sysparm_query=requested_for={context['user']['sys_id']}"
    context["open_tickets"] = []

    for url in [incidents_url, requests_url]:
        r = requests.get(url, auth=auth, headers=headers)
        if r.status_code == 200:
            context["open_tickets"].extend(r.json().get("result", []))

    return context
def get_user_open_incidents(user_id):
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    # Build query: incidents assigned to the user and not resolved/closed
    query = f"assigned_to.user_name={user_id}^stateNOT IN6,7"  # 6 = Resolved, 7 = Closed

    url = f"{instance}/api/now/table/incident"
    params = {
        "sysparm_query": query,
        "sysparm_fields": "number,short_description,opened_at,caller_id",
        "sysparm_limit": 20
    }

    response = requests.get(url, auth=auth, headers=headers, params=params)
    if response.status_code == 200:
        incidents = response.json().get("result", [])
        return [
            {
                "number": inc.get("number"),
                "short_description": inc.get("short_description", ""),
                "opened_at": inc.get("opened_at", ""),
                "caller": inc.get("caller_id", {}).get("display_value", "")
            }
            for inc in incidents
        ]
    else:
        print("Error fetching incidents:", response.status_code, response.text)
        return []
def get_user_open_tasks(user_id):
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    query = f"assigned_to.user_name={user_id}^stateNOT IN3"  # 3 = Closed
    url = f"{instance}/api/now/table/sc_task"
    params = {
        "sysparm_query": query,
        "sysparm_fields": "number,short_description,opened_at,assigned_to",
        "sysparm_limit": 20
    }

    response = requests.get(url, auth=auth, headers=headers, params=params)
    if response.status_code == 200:
        tasks = response.json().get("result", [])
        return [
            {
                "number": task.get("number"),
                "short_description": task.get("short_description", ""),
                "opened_at": task.get("opened_at", ""),
                "assigned_to": task.get("assigned_to", {}).get("display_value", "")
            }
            for task in tasks
        ]
    else:
        print("Error fetching tasks:", response.status_code, response.text)
        return []

def get_user_open_requests(user_id):
    instance = os.getenv("SN_INSTANCE")
    auth = (os.getenv("SN_USERNAME"), os.getenv("SN_PASSWORD"))
    headers = {"Accept": "application/json"}

    query = f"requested_for.user_name={user_id}^stateNOT IN3"  # 3 = Closed
    url = f"{instance}/api/now/table/sc_request"
    params = {
        "sysparm_query": query,
        "sysparm_fields": "number,short_description,requested_for,opened_at",
        "sysparm_limit": 20
    }

    response = requests.get(url, auth=auth, headers=headers, params=params)
    if response.status_code == 200:
        requests_list = response.json().get("result", [])
        return [
            {
                "number": r.get("number"),
                "short_description": r.get("short_description", ""),
                "opened_at": r.get("opened_at", ""),
                "requested_for": r.get("requested_for", {}).get("display_value", "")
            }
            for r in requests_list
        ]
    else:
        print("Error fetching requests:", response.status_code, response.text)
        return []
