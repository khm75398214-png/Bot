from flask import Flask, request, jsonify
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Firebase 연결 (Render 환경변수 사용)
if not firebase_admin._apps:
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route("/", methods=["GET"])
def home():
    return "server is running"

@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json(force=True)
    msg = data.get("userRequest", {}).get("utterance", "")
    user_id = data.get("userRequest", {}).get("user", {}).get("id", "")

    if msg == "핑":
        reply = "퐁"

    elif msg == "경고" or msg.startswith("!경고"):
        doc_ref = db.collection("warnings").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            count = doc.to_dict().get("count", 0) + 1
        else:
            count = 1

        doc_ref.set({"count": count})
        reply = f"경고 {count}회"

    elif msg == "경고확인":
        doc_ref = db.collection("warnings").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            count = doc.to_dict().get("count", 0)
        else:
            count = 0

        reply = f"현재 경고: {count}회"

    else:
        reply = "몰루"

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": reply}}
            ]
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)