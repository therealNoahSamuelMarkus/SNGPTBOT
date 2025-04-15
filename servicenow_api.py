import os

def query_kb_articles(query, permissions):
    all_articles = [
        {"id": "KB001", "title": "Reset Network Password", "content": "To reset your password..."},
        {"id": "KB002", "title": "VPN Connection Troubleshooting", "content": "If you have trouble connecting..."}
    ]
    return [a for a in all_articles if a['id'] in permissions and query.lower() in a['content'].lower()]

def open_ticket(user_id):
    return {"result": f"Ticket opened for {user_id}."}

def close_ticket(user_id):
    return {"result": f"Ticket closed for {user_id}."}