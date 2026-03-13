import os
import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

gmail_token = json.loads(os.getenv("GMAIL_TOKEN"))

creds = Credentials.from_authorized_user_info(gmail_token)

service = build("gmail", "v1", credentials=creds)

# Only fetch NEW unread emails from the last hour
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

# If no new emails
if not emails:
    message = "📬 No new unread emails in the last hour."

else:

    prompt = """
Summarize each email briefly.

Return output EXACTLY like this:

📧 Email Name - <email_id> - <subject>
📝 Summary - <one short sentence summary>

Rules:
- Keep summary to 1 short sentence
- Remove marketing noise
- Keep it clean and readable
"""

    for e in emails:
        prompt += f"\nSender: {e['sender']}\nSubject: {e['subject']}\nContent: {e['body']}\n"

    try:

        prompt = prompt[:2000]

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You summarize emails clearly and concisely."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.3
            },
            timeout=20
        )

        data = response.json()

        if "choices" in data:
            summary = data["choices"][0]["message"]["content"]
        else:
            summary = "⚠️ AI summarization failed."

    except Exception as e:
        summary = f"⚠️ AI request error: {str(e)}"

    message = f"📬 New Gmail Emails (Last Hour)\n\n{summary}"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
