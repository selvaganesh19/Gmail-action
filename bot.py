import os
import requests
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

emails = [
    {"sender": "Amazon", "subject": "Order shipped", "body": "Your package will arrive tomorrow"},
    {"sender": "GitHub", "subject": "Security alert", "body": "A vulnerability was detected"}
]

prompt = "Summarize these emails clearly:\n\n"

for e in emails:
    prompt += f"{e['sender']} - {e['subject']} - {e['body']}\n"

try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Email Summary Bot"
        },
        json={
            "model": "z-ai/glm-4.5-air:free",
            "messages": [
                {"role": "system", "content": "Summarize emails in 1–2 lines each."},
                {"role": "user", "content": prompt}
            ]
        },
        timeout=30
    )

    data = response.json()
    print("OPENROUTER RESPONSE:", json.dumps(data, indent=2))

    if "choices" in data:
        summary = data["choices"][0]["message"]["content"]
    elif "error" in data:
        summary = f"AI Error: {data['error']['message']}"
    else:
        summary = "⚠️ AI summarization failed."

except Exception as e:
    summary = f"AI request failed: {str(e)}"

message = f"📬 Email Summary\n\n{summary}"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
