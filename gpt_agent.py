import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_response(question, kb_articles):
    context = "\n\n".join(
        [f"Article Title: {a['title']}\nContent: {a['content']}" for a in kb_articles]
    )
    citations = "\n".join([f"- {a['title']}" for a in kb_articles])

    prompt = f"""You are an IT support assistant. Answer the question using the knowledge base articles provided.
    
    QUESTION:
    {question}

    CONTEXT:
    {context}

    Respond in a helpful, clear way. Cite the articles used at the end."""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return f"{completion.choices[0].message.content}\n\nSources:\n{citations}"