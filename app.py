import os
import json
import datetime
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

firebase_json = os.environ.get("FIREBASE_KEY")
if not firebase_json:
    raise Exception("FIREBASE_KEY 환경 변수가 없음")

cred_dict = json.loads(firebase_json)

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_user(name):
    ref = db.collection("users").document(name)
    doc = ref.get()

    if not doc.exists:
        data = {
            "level": 1,
            "exp": 0,
            "warn": 0,
            "attendance": 0,
            "lastAttendance": ""
        }
        ref.set(data)
        return data

    return doc.to_dict()

def update_user(name, data):
    db.collection("users").document(name).set(data)

def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

@app.route("/")
def home():
    return "ATBOT SERVER ON"

@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json(force=True)

    msg = data.get("msg", "")
    sender = data.get("sender", "")

    if not sender:
        return jsonify({"reply": "sender 없음"})

    user = get_user(sender)

    if msg == "!레벨":
        return jsonify({
            "reply": f"📊 {sender}\n레벨: {user['level']}\n경험치: {user['exp']}/100\n경고: {user['warn']}"
        })

    if msg == "!출석":
        if user["lastAttendance"] == today():
            return jsonify({"reply": "이미 출석했어."})

        user["attendance"] += 1
        user["exp"] += 20
        user["lastAttendance"] = today()

        while user["exp"] >= 100:
            user["level"] += 1
            user["exp"] -= 100

        update_user(sender, user)
        return jsonify({
            "reply": f"출석 완료!\n레벨: {user['level']}\n경험치: {user['exp']}/100"
        })

    if msg.startswith("!경고추가 "):
        target = msg.replace("!경고추가 ", "").strip()
        target_data = get_user(target)
        target_data["warn"] += 1
        update_user(target, target_data)

        if target_data["warn"] >= 3:
            return jsonify({"reply": f"⚠️ {target} 경고 3회 → 강퇴 요청"})

        return jsonify({"reply": f"{target} 경고 {target_data['warn']}회"})

    if msg == "!랭킹":
        users = db.collection("users").stream()
        ranking = []

        for u in users:
            d = u.to_dict()
            ranking.append((u.id, d.get("level", 1), d.get("exp", 0)))

        ranking.sort(key=lambda x: (-x[1], -x[2]))

        text = "🏆 랭킹\n\n"
        for i, r in enumerate(ranking[:5]):
            text += f"{i+1}. {r[0]} Lv.{r[1]} ({r[2]}/100)\n"

        return jsonify({"reply": text.strip()})

    if not msg.startswith("!"):
        user["exp"] += 5

        leveled_up = False
        while user["exp"] >= 100:
            user["level"] += 1
            user["exp"] -= 100
            leveled_up = True

        update_user(sender, user)

        if leveled_up:
            return jsonify({"reply": f"🎉 {sender} 레벨업! Lv.{user['level']}"})

    return jsonify({"reply": None})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)