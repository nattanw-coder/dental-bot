from flask import Flask, request
import anthropic
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LINE_TOKEN = os.getenv("LINE_TOKEN")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")

client = anthropic.Anthropic(api_key=CLAUDE_KEY)

# ===== ตั้งค่าหมอ =====
DOCTOR_MODE = False  # เปลี่ยนเป็น True เมื่อมีหมอในกลุ่ม
DOCTORS = []  # เพิ่ม LINE user ID หมอตรงนี้ เช่น ["Uxxxx", "Uxxxx"]

# ===== FAQ =====
FAQ = {
    "ฟันผุ": "ฟันผุเกิดจากแบคทีเรียในปากที่ย่อยน้ำตาลแล้วผลิตกรดกัดฟัน สังเกตได้จากฟันมีจุดดำ เป็นรู หรือปวดเวลากินของหวานหรือของเย็น ป้องกันได้โดยแปรงฟันวันละ 2 ครั้ง เช้าและก่อนนอน และลดของหวาน ถ้ามีอาการควรไปพบทันตแพทย์ค่ะ",
    "หินปูน": "หินปูนคือคราบแบคทีเรียที่แข็งตัวติดกับฟัน แปรงเองไม่ออกค่ะ ถ้าไม่ขูดออกจะทำให้เหงือกอักเสบและฟันโยกได้ แนะนำให้ขูดหินปูนกับทันตแพทย์ปีละ 1-2 ครั้ง ไม่เจ็บและใช้เวลาไม่นานค่ะ",
    "แปรงฟัน": "แปรงฟันให้ถูกวิธีโดยจับแปรงทำมุม 45 องศากับเหงือก วนเป็นวงกลมเบาๆ แปรงทุกซี่ทั้งด้านนอกด้านในและด้านบด ใช้เวลาอย่างน้อย 2 นาที แปรงวันละ 2 ครั้ง เช้าหลังตื่นนอนและก่อนนอนค่ะ",
    "เหงือก": "เหงือกเลือดออกตอนแปรงฟันเป็นสัญญาณของเหงือกอักเสบค่ะ เกิดจากคราบแบคทีเรียสะสม ถ้าปล่อยไว้อาจลามจนฟันโยกได้ แนะนำให้แปรงฟันให้ถูกวิธีและไปพบทันตแพทย์เพื่อขูดหินปูนค่ะ",
    "ฟันเด็ก": "ฟันน้ำนมสำคัญมากค่ะ ถ้าผุแล้วปล่อยทิ้งไว้จะเจ็บปวดและกระทบฟันแท้ที่จะขึ้นมาทีหลัง ควรเริ่มแปรงฟันให้เด็กตั้งแต่ฟันซี่แรกขึ้น ใช้ยาสีฟันผสมฟลูออไรด์นิดเดียวและพาไปพบทันตแพทย์ตั้งแต่อายุ 1 ขวบค่ะ",
}

KEYWORDS = {
    "ฟันผุ": ["ฟันผุ", "ฟันเป็นรู", "ฟันดำ", "ฟันผุทำไง", "ฟันเป็นรู"],
    "หินปูน": ["หินปูน", "ขูดหินปูน", "ฟันเหลือง", "คราบฟัน"],
    "แปรงฟัน": ["แปรงฟัน", "วิธีแปรง", "แปรงยังไง", "ยาสีฟัน"],
    "เหงือก": ["เหงือก", "เหงือกอักเสบ", "เหงือกบวม", "เหงือกเลือดออก", "แปรงแล้วเลือดออก"],
    "ฟันเด็ก": ["ฟันเด็ก", "ฟันน้ำนม", "ฟันผุในเด็ก", "แปรงฟันเด็ก", "ลูกฟันผุ"],
}

def match_keyword(text):
    # ให้ Claude จับว่าใกล้เคียง keyword ไหน
    keyword_list = "\n".join([f"- {k}: {', '.join(v)}" for k, v in KEYWORDS.items()])
    prompt = f"""จากข้อความนี้: "{text}"
ให้ตอบชื่อ keyword ที่ใกล้เคียงที่สุดจากรายการนี้เท่านั้น:
{keyword_list}

ถ้าไม่ตรงกับ keyword ใดเลย ให้ตอบว่า "ไม่ตรง"
ตอบแค่ชื่อ keyword เดียวเท่านั้น ห้ามอธิบายเพิ่ม"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.content[0].text.strip()
    return result if result in FAQ else None

def send_message(reply_token, text):
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={"Authorization": f"Bearer {LINE_TOKEN}"},
        json={
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}]
        }
    )
@app.route("/webhook", methods=["POST"])

# ===== ชื่อที่ใช้เรียกบอท =====
BOT_NAME = "เซียน"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    for event in data.get("events", []):
        
        # Greeting เมื่อบอทเข้า group
        if event["type"] == "join":
            send_message(
                event["replyToken"],
                "สวัสดีค่ะ หนูชื่อเซียน 🦷 ผู้ช่วยด้านสุขภาพช่องปากค่ะ\nถามเรื่องฟันได้เลย แค่เรียก 'เซียน' นำหน้าคำถามก่อนนะคะ\nเช่น 'เซียน ฟันผุเกิดจากอะไร' ค่ะ 😊"
            )
            continue

        if event["type"] != "message":
            continue
        if event["message"]["type"] != "text":
            continue
        if event.get("source", {}).get("type") == "bot":
            continue

        user_msg = event["message"]["text"]
        reply_token = event["replyToken"]
        source_type = event.get("source", {}).get("type")

        # ถ้าอยู่ใน group ต้องเรียก "เซียน" ก่อน
        if source_type == "group":
            if BOT_NAME not in user_msg:
                continue
            # ตัด "เซียน" ออกแล้วเอาแค่คำถาม
            user_msg = user_msg.replace(BOT_NAME, "").strip()

        matched = match_keyword(user_msg)

        if matched:
            send_message(reply_token, FAQ[matched])
        else:
            if DOCTOR_MODE and DOCTORS:
                tags = " ".join([f"@{uid}" for uid in DOCTORS])
                send_message(reply_token, f"รบกวนปรึกษาคุณหมอเพิ่มเติมนะคะ 🙏 {tags}")
            else:
                send_message(reply_token, "รบกวนปรึกษาคุณหมอที่ รพ.สต. เพิ่มเติมนะคะ 🙏")

    return "OK"

if __name__ == "__main__":
    app.run(port=5000)