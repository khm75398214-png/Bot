from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

app = Flask(__name__)

# 🔥 Firebase 연결
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 유저 가져오기
def get_user(name):
    ref = db.collection("users").document(name)
    doc = ref.get()

    if not doc.exists:
        ref.set({
            "level": 1,
            "exp": 0,
            "warn": 0,
            "attendance": 0,
            "lastAttendance": ""
        })
        return ref.get().to_dict()

    return doc.to_dict()

# 유저 저장
def update_user(name, data):
    db.collection("users").document(name).set(data)

def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

@app.route("/")
def home():
    return "ATBOT SERVER ON 🔥"

@app.route("/bot", methods=["POST"])
def bot():
    data = request.json

    msg = data.get("msg", "")
    sender = data.get("sender", "")

    user = get_user(sender)

    # 📊 레벨
    if msg == "!레벨":
        return jsonify({
            "reply": f"📊 {sender}\n레벨: {user['level']}\n경험치: {user['exp']}/100\n경고: {user['warn']}"
        })

    # 📅 출석
    if msg == "!출석":
        if user["lastAttendance"] == today():
            return jsonify({"reply": "이미 출석함"})

        user["attendance"] += 1
        user["exp"] += 20
        user["lastAttendance"] = today()

        if user["exp"] >= 100:
            user["level"] += 1
            user["exp"] = 0

        update_user(sender, user)

        return jsonify({"reply": f"출석 완료! 레벨:{user['level']} EXP:{user['exp']}/100"})

    # ⚠️ 경고 추가
    if msg.startswith("!경고추가 "):
        target = msg.replace("!경고추가 ", "")
        target_data = get_user(target)

        target_data["warn"] += 1
        update_user(target, target_data)

        if target_data["warn"] >= 3:
            return jsonify({"reply": f"⚠️ {target} 경고 3회 → 강퇴 요청"})

        return jsonify({"reply": f"{target} 경고 {target_data['warn']}회"})

    # 🏆 랭킹
    if msg == "!랭킹":
        users = db.collection("users").stream()

        ranking = []
        for u in users:
            d = u.to_dict()
            ranking.append((u.id, d["level"], d["exp"]))

        ranking.sort(key=lambda x: (-x[1], -x[2]))

        text = "🏆 랭킹\n\n"
        for i, r in enumerate(ranking[:5]):
            text += f"{i+1}. {r[0]} Lv.{r[1]} ({r[2]})\n"

        return jsonify({"reply": text})

    # 🎮 채팅 EXP
    if not msg.startswith("!"):
        user["exp"] += 5

        if user["exp"] >= 100:
            user["level"] += 1
            user["exp"] = 0
            update_user(sender, user)
            return jsonify({"reply": f"{sender} 레벨업! Lv.{user['level']}"})

        update_user(sender, user)

    return jsonify({"reply": None})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
