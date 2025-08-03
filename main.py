from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import markdown2  # <-- NEW

app = Flask(__name__)
chat_history = []

# Watsonx config
API_KEY = "Nt5ajg4ixcU9pqW2axn-MlmW6wzu4_c76zRcqdIG2zkE"
DEPLOYMENT_ID = "7fcdc7d6-11b3-4d7c-97b1-d9e60525b241"
REGION = "us-south"
VERSION = "2021-05-01"

def get_access_token():
    res = requests.post(
        'https://iam.cloud.ibm.com/identity/token',
        data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return res.json()["access_token"]

def ask_ai(message_history):
    token = get_access_token()
    url = f"https://{REGION}.ml.cloud.ibm.com/ml/v4/deployments/{DEPLOYMENT_ID}/ai_service_stream?version={VERSION}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    response = requests.post(url, headers=headers, data=json.dumps({"messages": message_history}), stream=True)

    ai_message = ""
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith("data:"):
                data = json.loads(decoded[5:])
                if "choices" in data:
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        ai_message += content
    return ai_message

@app.route('/')
def home():
    return render_template('start.html')

@app.route('/start_chat', methods=['POST'])
def start_chat():
    chat_history.clear()  # clear old chat

    # Build first prompt
    place = request.form['place']
    duration = request.form['duration']
    budget = request.form['budget']
    people = request.form['people']
    pace = request.form['pace']
    food = request.form['food']
    suggestions = request.form['suggestions']

    prompt = (
        f"I want to go to {place} for {duration} days with {people} people. "
        f"My budget is ₹{budget}. I prefer a {pace} pace trip and follow a {food} diet. "
        f"Additional preferences: {suggestions.strip() if suggestions.strip() else 'None'}."
    )

    chat_history.append({"role": "user", "content": prompt})
    ai_reply = ask_ai(chat_history)

    # Convert AI reply from Markdown to HTML
    ai_reply_html = markdown2.markdown(ai_reply)

    chat_history.append({"role": "ai", "content": ai_reply_html})
    return redirect(url_for('chat'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.form['user_input']
        chat_history.append({"role": "user", "content": user_input})
        ai_reply = ask_ai(chat_history)

        # Convert AI reply from Markdown to HTML
        ai_reply_html = markdown2.markdown(ai_reply)

        chat_history.append({"role": "ai", "content": ai_reply_html})
    return render_template('chat.html', messages=chat_history)

if __name__ == '__main__':
    app.run(debug=True)



