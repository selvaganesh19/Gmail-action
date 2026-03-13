import { OpenRouter } from "@openrouter/sdk";
import fetch from "node-fetch";

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

const openrouter = new OpenRouter({
  apiKey: OPENROUTER_API_KEY
});

const emails = [
  { sender: "Amazon", subject: "Order shipped", body: "Your package will arrive tomorrow" },
  { sender: "GitHub", subject: "Security alert", body: "A vulnerability was detected" }
];

let prompt = "Summarize these emails clearly:\n\n";

for (const e of emails) {
  prompt += `${e.sender} - ${e.subject} - ${e.body}\n`;
}

try {

  const response = await openrouter.chat.send({
    model: "z-ai/glm-4.5-air:free",
    messages: [
      {
        role: "system",
        content: "Summarize emails into short readable summaries."
      },
      {
        role: "user",
        content: prompt
      }
    ]
  });

  const summary = response.choices?.[0]?.message?.content || "⚠️ AI summarization failed.";

  const message = `📬 Email Summary\n\n${summary}`;

  await fetch(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: CHAT_ID,
      text: message
    })
  });

  console.log("Message sent to Telegram");

} catch (error) {
  console.error("OpenRouter error:", error);
}
