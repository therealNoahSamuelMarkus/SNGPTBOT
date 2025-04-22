from servicenow_api import open_ticket, get_user_context

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
