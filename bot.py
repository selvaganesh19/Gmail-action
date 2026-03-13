import os
import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

gmail_token = json.loads(os.getenv("GMAIL_TOKEN"))

creds = Credentials.from_authorized_user_info(gmail_token)

service = build("gmail", "v1", credentials=creds)

results = service.users().messages().list(
    userId="me",
    labelIds=["INBOX", "UNREAD"],
    maxResults=10
).execute()

messages = results.get("messages", [])

emails = []

for msg in messages:
    m = service.users().messages().get(userId="me", id=msg["id"]).execute()

    headers = m["payload"]["headers"]

    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
    date = next((h["value"] for h in headers if h["name"] == "Date"), "")

    snippet = m.get("snippet", "")

    emails.append({
        "sender": sender,
        "subject": subject,
        "date": date,
        "body": snippet
    })

# Build prompt for AI
prompt = """
Summarize the following emails.

Return output in this EXACT format:

Email Name -
Summary -

Example:

Email Name - Apple
Summary - Apple announced the new iPad Air powered by the M4 chip.

Keep summaries short (1 sentence).
Remove marketing noise and signatures.
Make it clean and readable.
"""

for e in emails:
    prompt += f"\nSender: {e['sender']}\nSubject: {e['subject']}\nDate: {e['date']}\nContent: {e['body']}\n"

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "z-ai/glm-4.5-air:free",
        "messages": [
            {"role": "system", "content": "You summarize emails clearly."},
            {"role": "user", "content": prompt}
        ]
    }
)

summary = response.json()["choices"][0]["message"]["content"]

message = f"📬 Unread Gmail Summary\n\n{summary}"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
