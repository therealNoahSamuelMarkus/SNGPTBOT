import os
from openai import OpenAI
from servicenow_api import open_ticket
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Top of gpt_agent.py
issue_log = {}

def track_issue(user_id, question):
    if user_id not in issue_log:
        issue_log[user_id] = []
    issue_log[user_id].append(question.lower())

def is_repeated_issue(user_id, question):
    repeated_count = issue_log[user_id].count(question.lower())
    return repeated_count >= 2  # trigger ticket if same issue seen twice



def generate_response(user_id, question, kb_articles):
    track_issue(user_id, question)

    context = "\n\n".join(
        [f"Article Title: {a['title']}\nContent: {a['content']}" for a in kb_articles]
    )
    citations = "\n".join([f"- {a['title']}" for a in kb_articles])

    prompt = f"""You are an IT support assistant. Answer the user's question using the knowledge base provided.

    QUESTION:
    {question}

    CONTEXT:
    {context}

    Provide a recommended solution. If this is a repeated issue, advise them a ticket will be created automatically.
    """

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = completion.choices[0].message.content
    repeated = is_repeated_issue(user_id, question)

    if repeated:
        ticket = open_ticket(user_id,question)  # optional: include question as issue description
        answer += f"\n\n🛠 A support ticket has been created: {ticket['result']}"

    return f"{answer}\n\nSources:\n{citations}"
