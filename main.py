from flask import Flask, request, jsonify, render_template
from servicenow_api import query_kb_articles, open_ticket, close_ticket
from gpt_agent import generate_response
from auth import get_user_permissions
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    user_id = request.json['user_id']
    question = request.json['question']

    permissions = get_user_permissions(user_id)
    kb_articles = query_kb_articles(question, permissions)

    response = generate_response(question, kb_articles)
    return jsonify({"response": response})

@app.route('/task', methods=['POST'])
def task_handler():
    task_type = request.json['type']
    user_id = request.json['user_id']

    if task_type == 'reset_password':
        return jsonify({"result": f"Password reset link sent to {user_id}."})
    elif task_type == 'open_ticket':
        return jsonify(open_ticket(user_id))
    elif task_type == 'close_ticket':
        return jsonify(close_ticket(user_id))
    else:
        return jsonify({"error": "Unknown task."}), 400

if __name__ == '__main__':
    app.run(debug=True)