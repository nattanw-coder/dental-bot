# -*- coding: utf-8 -*-
from flask import Flask, request
import anthropic
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LINE_TOKEN = os.getenv("LINE_TOKEN")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")

client = anthropic.Anthropic(api_key=CLAUDE_KEY)

# ===== ตั้งค่าหมอ =====
DOCTOR_MODE = False
DOCTORS = []

# ===== FAQ =====
FAQ = {
    "ฟันผุ": "ฟันผุเกิดจากแบคทีเรียในปากที่ย่อยน้ำตาลแล้วผลิตกรดกัดฟัน สังเกตได้จากฟันมีจุดดำ เป็นรู หรือปวดเวลากินของหวานหรือของเย็น ป้องกันได้โดยแปรงฟันวันละ 2 ครั้ง เช้าและก่อนนอน และลดของหวาน ถ้ามีอาการควรไปพบทันตแพทย์ค่ะ",
    "หินปูน": "หินปูนคือคราบแบคทีเรียที่แข็งตัวติดกับฟัน แปรงเองไม่ออกค่ะ ถ้าไม่ขูดออกจะทำให้เหงือกอักเสบและฟันโยกได้ แนะนำให้ขูดหินปูนกับทันตแพทย์ปีละ 1-2 ครั้ง ไม่เจ็บและใช้เวลาไม่นานค่ะ",
    "แปรงฟัน": "แปรงฟันให้ถูกวิธีโดยจับแปรงทำมุม 45 องศากับเหงือก วนเป็นวงกลมเบาๆ แปรงทุกซี่ทั้งด้านนอกด้านในและด้านบด ใช้เวลาอย่างน้อย 2 นาที แปรงวันละ 2 ครั้ง เช้าหลังตื่นนอนและก่อนนอนค่ะ",
    "เหงือก": "เหงือกเลือดออกตอนแปรงฟันเป็นสัญญาณของเหงือกอักเสบค่ะ เกิดจากคราบแบคทีเรียสะสม ถ้าปล่อยไว้อาจลามจนฟันโยกได้ แนะนำให้แปรงฟันให้ถูกวิธีและไปพบทันตแพทย์เพื่อขูดหินปูนค่ะ",
    "ฟันเด็ก": "ฟันน้ำนมสำคัญมากค่ะ ถ้าผุแล้วปล่อยทิ้งไว้จะเจ็บปวดและกระทบฟันแท้ที่จะขึ้นมาทีหลัง ควรเริ่มแปรงฟันให้เด็กตั้งแต่ฟันซี่แรกขึ้น ใช้ยาสีฟันผสมฟลูออไรด์นิดเดียวและพาไปพบทันตแพทย์ตั้งแต่อายุ 1 ขวบค่ะ",
}

KEYWORDS = {
    "ฟันผุ": ["ฟันผุ", "ฟันเป็นรู", "ฟันดำ", "ปวดฟัน", "ฟันเจ็บ"],
    "หินปูน": ["หินปูน", "ขูดหินปูน", "ฟันเหลือง", "คราบฟัน"],
    "แปรงฟัน": ["แปรงฟัน", "วิธีแปรง", "แปรงยังไง", "ยาสีฟัน", "แปรงสีฟัน"],
    "เหงือก": ["เหงือก", "เหงือกอักเสบ", "เหงือกบวม", "เหงือกเลือดออก", "แปรงแล้วเลือดออก"],
    "ฟันเด็ก": ["ฟันเด็ก", "ฟันน้ำนม", "ฟันผุในเด็ก", "แปรงฟันเด็ก", "ลูกฟันผุ"],
}

SYSTEM_FAQ_MATCH = """คุณช่วย classify ข้อความว่าใกล้เคียง keyword ไหน
ตอบแค่ชื่อ keyword เดียวเท่านั้น ห้ามอธิบายเพิ่ม
ถ้าไม่ตรงกับ keyword ใดเลย ให้ตอบว่า "ไม่ตรง" """

SYSTEM_AI_ANSWER = """คุณคือผู้ช่วยด้านสุขภาพช่องปากสำหรับ อสม. ในชุมชน
ตอบเฉพาะเรื่องสุขภาพช่องปากเท่านั้น
ตอบในฐานะ "ผู้ช่วย" ไม่ใช่ "หมอ" ใช้ภาษาว่า "อาจจะ" "น่าจะ" เสมอ
ห้ามวินิจฉัยโรคหรือแนะนำยาเฉพาะเจาะจง
ถ้าเรื่องนอกขอบเขตช่องปาก ให้บอกว่า "ขอบเขตหนูมีแค่เรื่องช่องปากนะคะ 😊"
ท้ายคำตอบให้ใส่เสมอว่า "นี่เป็นแค่แนวคิดเบื้องต้นนะคะ ปรึกษาคุณหมอโดยตรงเพื่อความแม่นยำค่ะ 🙏" """
ศัพท์ทันตกรรมที่ต้องใช้ให้ถูกต้อง:
- crown = ครอบฟัน (ไม่ใช่มงกุฎ)
- filling = อุดฟัน
- scaling = ขูดหินปูน
- extraction = ถอนฟัน
- implant = รากฟันเทียม
- braces = จัดฟัน

การเรียงประโยคให้ถูกต้อง:
- ใช้ "สิ่งที่ต้องให้คุณหมอทำ" ไม่ใช่ "สิ่งที่ต้องทำให้คุณหมอ" """

def match_keyword(text):
    keyword_list = "\n".join([f"- {k}: {', '.join(v)}" for k, v in KEYWORDS.items()])
    faq_list = "\n".join([f"- {k}: {v}" for k, v in FAQ.items()])
    
    prompt = f"""จากข้อความนี้: "{text}"

1. keyword ที่ใกล้เคียงที่สุดจากรายการนี้:
{keyword_list}

2. คำตอบจาก FAQ นี้ตอบโจทย์คำถามได้ไหม:
{faq_list}

ตอบในรูปแบบนี้เท่านั้น:
KEYWORD: [ชื่อ keyword หรือ ไม่ตรง]
FAQ_OK: [yes หรือ no]"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=50,
        system=SYSTEM_FAQ_MATCH,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.content[0].text.strip()
    lines = result.split("\n")
    keyword = lines[0].replace("KEYWORD:", "").strip()
    faq_ok = lines[1].replace("FAQ_OK:", "").strip() if len(lines) > 1 else "no"
    
    if keyword in FAQ and faq_ok == "yes":
        return keyword, True   # ตรง FAQ และตอบพอ
    elif keyword in FAQ and faq_ok == "no":
        return keyword, False  # ตรง FAQ แต่ตอบไม่พอ
    else:
        return None, False     # ไม่ตรง keyword เลย

def ai_answer(text):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        system=SYSTEM_AI_ANSWER,
        messages=[{"role": "user", "content": text}]
    )
    return response.content[0].text.strip()

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
def webhook():
    data = request.json
    for event in data.get("events", []):
        if event["type"] != "message":
            continue
        if event["message"]["type"] != "text":
            continue
        if event.get("source", {}).get("type") == "bot":
            continue

        user_msg = event["message"]["text"]
        reply_token = event["replyToken"]

        matched, faq_ok = match_keyword(user_msg)
        if matched and faq_ok:
            send_message(reply_token, FAQ[matched])
        else:
            answer = ai_answer(user_msg)
            send_message(reply_token, answer)

    return "OK"

if __name__ == "__main__":
    app.run(port=5000)