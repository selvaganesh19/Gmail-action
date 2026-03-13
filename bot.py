import os
import requests
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

creds = service_account.Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES
)

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

    subject = next(h["value"] for h in headers if h["name"] == "Subject")
    sender = next(h["value"] for h in headers if h["name"] == "From")
    date = next(h["value"] for h in headers if h["name"] == "Date")

    snippet = m.get("snippet", "")

    emails.append({
        "sender": sender,
        "subject": subject,
        "date": date,
        "body": snippet
    })

prompt = "Summarize these emails clearly with sender and subject:\n\n"

for e in emails:
    prompt += f"{e['sender']} | {e['subject']} | {e['body']}\n"

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "z-ai/glm-4.5-air:free",
        "messages": [
            {"role": "system", "content": "Summarize each email in 1-2 lines."},
            {"role": "user", "content": prompt}
        ]
    }
)

data = response.json()

summary = data["choices"][0]["message"]["content"]

message = f"📬 Unread Email Summary\n\n{summary}"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
