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
    q="is:unread newer_than:1h",
    maxResults=10
).execute()

messages = results.get("messages", [])

emails = []

for msg in messages:
    m = service.users().messages().get(userId="me", id=msg["id"]).execute()

    headers = m["payload"]["headers"]

    subject = next((h["value"] for h in headers if h["name"]=="Subject"), "")
    sender = next((h["value"] for h in headers if h["name"]=="From"), "")
    date = next((h["value"] for h in headers if h["name"]=="Date"), "")

    snippet = m.get("snippet","")

    emails.append({
        "sender": sender,
        "subject": subject,
        "date": date,
        "body": snippet
    })

if not emails:
    message = "📬 No new unread emails in the last hour."
else:

    prompt = """
Summarize each email briefly.

Return output in this EXACT format with emojis:

📧 Email Name - <sender or company name>
📝 Summary - <one short sentence summary>

Rules:
- Maximum 1 short sentence
- Remove marketing fluff
- Keep it clear and user friendly
- Separate each email with a blank line
"""

    for e in emails:
        prompt += f"\nSender: {e['sender']}\nSubject: {e['subject']}\nContent: {e['body']}\n"

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "z-ai/glm-4.5-air:free",
            "messages":[
                {"role":"system","content":"You summarize emails clearly."},
                {"role":"user","content":prompt}
            ]
        }
    )

    summary = response.json()["choices"][0]["message"]["content"]

    message = f"📬 New Gmail Emails (Last Hour)\n\n{summary}"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    json={"chat_id":CHAT_ID,"text":message}
)
