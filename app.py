from flask import Flask, request
import anthropic
import json
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

LINE_TOKEN = os.getenv("LINE_TOKEN")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")
client = anthropic.Anthropic(api_key=CLAUDE_KEY)

SYSTEM_PROMPT = """
เราคือผู้ช่วยด้านทันตสุขภาพสำหรับ อสม. ในชุมชน
ตอบเฉพาะเรื่องสุขภาพช่องปากเท่านั้น เช่น ฟันผุ หินปูน การแปรงฟัน เหงือก
ใช้ภาษาไทยที่เข้าใจง่าย ไม่ใช้ศัพท์แพทย์
ถ้าถามนอกเหนือจากนี้ให้ตอบว่า 'สอบถามเพิ่มเติมได้ที่ รพ.สต. นะคะ'
"""

def reply(reply_token, text):
    import requests
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={"Authorization": f"Bearer {LINE_TOKEN}"},
        json={
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}]
        }
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    for event in data.get("events", []):
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_msg = event["message"]["text"]
            reply_token = event["replyToken"]
            
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}]
            )
            
            bot_reply = response.content[0].text
            reply(reply_token, bot_reply)
    
    return "OK"

if __name__ == "__main__":
    app.run(port=5000)
    