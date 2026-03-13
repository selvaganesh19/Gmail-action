import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

emails = [
    {"sender": "Amazon", "subject": "Order shipped", "body": "Your package will arrive tomorrow"},
    {"sender": "GitHub", "subject": "Security alert", "body": "A vulnerability was detected"}
]

prompt = "Summarize these emails clearly:\n"

for e in emails:
    prompt += f"{e['sender']} - {e['subject']} - {e['body']}\n"


# OpenRouter request
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
)

summary = response.json()["choices"][0]["message"]["content"]

message = f"📬 Email Summary:\n\n{summary}"

# Send to Telegram
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

requests.post(url, json={
    "chat_id": CHAT_ID,
    "text": message
})
