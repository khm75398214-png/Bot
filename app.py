from flask import Flask, request, jsonify
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# 🔥 Firebase 연결 (중복 방지 포함)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 🔥 홈 확인 (브라우저 테스트용)
@app.route("/", methods=["GET"])
def home():
    return "server is running"

# 🔥 카카오 봇
@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json(force=True)

    # 메시지 / 유저 정보
    msg = data.get("userRequest", {}).get("utterance", "")
    user_id = data.get("userRequest", {}).get("user", {}).get("id", "")

    # 기본 응답
    reply = "몰루"

    # 🏓 핑
    if msg == "핑":
        reply = "퐁"

    # ⚠️ 경고 시스템 (Firebase 저장)
    elif msg == "경고" or msg.startswith("!경고"):
        doc_ref = db.collection("warnings").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            count = doc.to_dict().get("count", 0) + 1
        else:
            count = 1

        doc_ref.set({"count": count})
        reply = f"경고 {count}회"

    # 📊 경고 조회
    elif msg == "경고확인":
        doc_ref = db.collection("warnings").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            count = doc.to_dict().get("count", 0)
        else:
            count = 0

        reply = f"현재 경고: {count}회"

    # 🔁 응답 반환 (카카오 형식)
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": reply}}
            ]
        }
    })

# 🔥 서버 실행 (Render용)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
